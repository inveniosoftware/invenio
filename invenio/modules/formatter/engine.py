# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Format a single record using specified format."""

import re
import time
import types

from invenio.base.globals import cfg
from invenio.base.i18n import language_list_long
from invenio.ext.template import render_template_to_string
from invenio.modules.formatter.registry import template_context_functions

from werkzeug.utils import cached_property

from . import registry
from .api import get_output_format_content_type
from .config import InvenioBibFormatError

# Cache for data we have already read and parsed
format_templates_cache = {}
format_outputs_cache = {}

html_field = '<!--HTML-->' # String indicating that field should be
                           # treated as HTML (and therefore no escaping of
                           # HTML tags should occur.
                           # Appears in some field values.

# Regular expression for finding <lang>...</lang> tag in format templates
pattern_lang = re.compile(r'''
    <lang              #<lang tag (no matter case)
    \s*                #any number of white spaces
    >                  #closing <lang> start tag
    (?P<langs>.*?)     #anything but the next group (greedy)
    (</lang\s*>)       #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Builds regular expression for finding each known language in <lang> tags
ln_pattern_text = r"<("
for lang in language_list_long(enabled_langs_only=False):
    ln_pattern_text += lang[0] +r"|"

ln_pattern_text = ln_pattern_text.rstrip(r"|")
ln_pattern_text += r")>(.*?)</\1>"

ln_pattern = re.compile(ln_pattern_text, re.IGNORECASE | re.DOTALL)

# Regular expression for finding text to be translated
TRANSLATION_PATTERN = re.compile(r'_\((?P<word>.*?)\)_',
                                 re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <name> tag in format templates
pattern_format_template_name = re.compile(r'''
    <name              #<name tag (no matter case)
    \s*                #any number of white spaces
    >                  #closing <name> start tag
    (?P<name>.*?)      #name value. any char that is not end tag
    (</name\s*>)(\n)?  #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <description> tag in format templates
pattern_format_template_desc = re.compile(r'''
    <description           #<decription tag (no matter case)
    \s*                    #any number of white spaces
    >                      #closing <description> start tag
    (?P<desc>.*?)          #description value. any char that is not end tag
    </description\s*>(\n)? #end tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding <BFE_ > tags in format templates
pattern_tag = re.compile(r'''
    <BFE_                        #every special tag starts with <BFE_ (no matter case)
    (?P<function_name>[^/\s]+)   #any char but a space or slash
    \s*                          #any number of spaces
    (?P<params>(\s*              #params here
     (?P<param>([^=\s])*)\s*     #param name: any chars that is not a white space or equality. Followed by space(s)
     =\s*                        #equality: = followed by any number of spaces
     (?P<sep>[\'"])              #one of the separators
     (?P<value>.*?)              #param value: any chars that is not a separator like previous one
     (?P=sep)                    #same separator as starting one
    )*)                          #many params
    \s*                          #any number of spaces
    (/)?>                        #end of the tag
    ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)

# Regular expression for finding params inside <BFE_ > tags in format templates
pattern_function_params = re.compile(r'''
    (?P<param>([^=\s])*)\s*  # Param name: any chars that is not a white space or equality. Followed by space(s)
    =\s*                     # Equality: = followed by any number of spaces
    (?P<sep>[\'"])           # One of the separators
    (?P<value>.*?)           # Param value: any chars that is not a separator like previous one
    (?P=sep)                 # Same separator as starting one
    ''', re.VERBOSE | re.DOTALL)

# Regular expression for finding format elements "params" attributes
# (defined by @param)
pattern_format_element_params = re.compile(r'''
    @param\s*                          # Begins with AT param keyword followed by space(s)
    (?P<name>[^\s=]*):\s*              # A single keyword and comma, then space(s)
    #(=\s*(?P<sep>[\'"])               # Equality, space(s) and then one of the separators
    #(?P<default>.*?)                  # Default value: any chars that is not a separator like previous one
    #(?P=sep)                          # Same separator as starting one
    #)?\s*                             # Default value for param is optional. Followed by space(s)
    (?P<desc>.*)                       # Any text that is not end of line (thanks to MULTILINE parameter)
    ''', re.VERBOSE | re.MULTILINE)

# Regular expression for finding format elements "see also" attribute
# (defined by @see)
pattern_format_element_seealso = re.compile(r'''@see:\s*(?P<see>.*)''',
                                            re.VERBOSE | re.MULTILINE)

#Regular expression for finding 2 expressions in quotes, separated by
#comma (as in template("1st","2nd") )
#Used when parsing output formats
# pattern_parse_tuple_in_quotes = re.compile('''
#      (?P<sep1>[\'"])
#      (?P<val1>.*)
#      (?P=sep1)
#      \s*,\s*
#      (?P<sep2>[\'"])
#      (?P<val2>.*)
#      (?P=sep2)
#      ''', re.VERBOSE | re.MULTILINE)

sub_non_alnum = re.compile('[^0-9a-zA-Z]+')
fix_tag_name = lambda s: sub_non_alnum.sub('_', s.lower())


class LazyTemplateContextFunctionsCache(object):
    """Loads bibformat elements using plugin builder and caches results."""

    @cached_property
    def template_context_functions(self):
        """Returns template context functions"""
        modules = template_context_functions
        elem = {}
        for m in modules:
            register_func = getattr(m, 'template_context_function', None)
            if register_func and isinstance(register_func, types.FunctionType):
                elem[m.__name__.split('.')[-1]] = register_func

        return elem

TEMPLATE_CONTEXT_FUNCTIONS_CACHE = LazyTemplateContextFunctionsCache()


def format_record(record, of, ln=None, verbose=0, search_pattern=None,
                  xml_record=None, user_info=None, **kwargs):
    """Format a record in given output format.

    Return a formatted version of the record in the specified
    language, search pattern, and with the specified output format.
    The function will define which format template must be applied.

    The record to be formatted can be specified with its ID (with
    'recID' parameter) or given as XML representation (with
    'xml_record' parameter). If 'xml_record' is specified 'recID' is
    ignored (but should still be given for reference. A dummy recid 0
    or -1 could be used).
    """
    ln = ln or cfg['CFG_SITE_LANG']

    template = decide_format_template(record, of)

    out = render_template_to_string(
        ['format/record/{0}'.format(template), template],
        recid=record['recid'],
        record=record,
        format_record=format_record,
        **(kwargs or {})
    )

    return out


def format_records(records, of='hb', ln=None, **ctx):
    """Return records using Jinja template."""
    from flask import request
    from invenio.base.i18n import wash_language
    from .registry import export_formats

    of = of.lower()
    jrec = request.values.get('jrec', ctx.get('jrec', 1), type=int)
    rg = request.values.get('rg', ctx.get('rg', 10), type=int)
    ln = ln or wash_language(request.values.get('ln', cfg['CFG_SITE_LANG']))
    ot = (request.values.get('ot', ctx.get('ot')) or '').split(',')

    if jrec > records:
        jrec = rg * (records // rg) + 1

    context = dict(
        of=of, jrec=jrec, rg=rg, ln=ln, ot=ot,
        facets={},
        time=time,
        records=records,
        export_formats=export_formats,
        format_record=format_record,
        **TEMPLATE_CONTEXT_FUNCTIONS_CACHE.template_context_functions
    )
    context.update(ctx)
    return render_template_to_string(
        ['format/records/%s.tpl' % of,
         'format/records/%s.tpl' % of[0],
         'format/records/%s.tpl' % get_output_format_content_type(of).
            replace('/', '_')],
        **context)


def decide_format_template(record, of):
    """Return the format template name that should be used for formatting.

    Look at rules in given output format and take the first matching one.
    If no rule matches, returns None.

    To match we ignore lettercase and spaces before and after value of
    rule and value of record

    :param record: mapping of fields and its values
    :param of: the code of the output format to use
    :return: name of a format template
    """
    output_format = get_output_format(of)

    for rule in output_format.get('rules', []):
        values = record.get(rule['field'], [])

        if not isinstance(values, (list, tuple)):
            values = [values]

        # loop over multiple occurences, but take the first match
        if len(values) > 0:
            for value in values:
                value = value.strip()  # Remove spaces
                pattern = rule['value'].strip()  # Remove spaces
                match_obj = re.match(pattern, value, re.IGNORECASE)
                if match_obj is not None and \
                        match_obj.end() == len(value):
                    return rule['template']

    return output_format['default']


def filter_languages(format_template, ln=None):
    """
    Filters the language tags that do not correspond to the specified language.

    :param format_template: the format template code
    :param ln: the language that is NOT filtered out from the template
    @return: the format template with unnecessary languages filtered out
    """
    ln = ln or cfg['CFG_SITE_LANG']
    # First define search_lang_tag(match) and clean_language_tag(match), used
    # in re.sub() function
    def search_lang_tag(match):
        """
        Searches for the <lang>...</lang> tag and remove inner localized tags
        such as <en>, <fr>, that are not current_lang.

        If current_lang cannot be found inside <lang> ... </lang>, try to use 'CFG_SITE_LANG'

        :param match: a match object corresponding to the special tag that must be interpreted
        """
        current_lang = ln

        def clean_language_tag(match):
            """
            Return tag text content if tag language of match is output language.

            Called by substitution in 'filter_languages(...)'

            :param match: a match object corresponding to the special tag that must be interpreted
            """
            if match.group(1) == current_lang:
                return match.group(2)
            else:
                return ""
            # End of clean_language_tag


        lang_tag_content = match.group("langs")
        # Try to find tag with current lang. If it does not exists,
        # then current_lang becomes CFG_SITE_LANG until the end of this
        # replace
        pattern_current_lang = re.compile(r"<(" + current_lang +
                                          r")\s*>(.*)(</" + current_lang + r"\s*>)", re.IGNORECASE | re.DOTALL)
        if re.search(pattern_current_lang, lang_tag_content) is None:
            current_lang = CFG_SITE_LANG

        cleaned_lang_tag = ln_pattern.sub(clean_language_tag, lang_tag_content)
        return cleaned_lang_tag.strip()
        # End of search_lang_tag


    filtered_format_template = pattern_lang.sub(search_lang_tag, format_template)
    return filtered_format_template


def get_output_format(code, with_attributes=False, verbose=0):
    """Return the structured content of the given output format."""
    try:
        return registry.output_formats[code.lower()]
    except KeyError:
        raise InvenioBibFormatError("Missing output format '{0}'".format(code))
