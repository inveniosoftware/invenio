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

"""Format a single record using specified format.

You can have a look at the various escaping modes available in
X{BibFormatObject} in function L{escape_field}

Still it is useful sometimes for debugging purpose to use the
L{BibFormatObject} class directly. For eg:

   >>> from invenio.modules.formatter.engine import BibFormatObject
   >>> bfo = BibFormatObject(102)
   >>> bfo.field('245__a')
   The order Rodentia in South America
   >>> from invenio.modules.formatter.format_elements import bfe_title
   >>> bfe_title.format_element(bfo)
   The order Rodentia in South America

@see: bibformat.py, bibformat_utils.py
"""

import cgi
import inspect
import os
import re
import sys
import traceback
import types
import warnings
from HTMLParser import HTMLParseError
from operator import itemgetter

from flask import current_app, has_app_context
from six import iteritems
from werkzeug.utils import cached_property

import invenio.legacy.bibformat.dblayer as bibformat_dblayer
from invenio.base.globals import cfg
from invenio.base.i18n import gettext_set_language, language_list_long, \
    wash_language
from invenio.config import CFG_BIBFORMAT_CACHED_FORMATS, \
    CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS, CFG_BIBFORMAT_HIDDEN_TAGS, \
    CFG_SITE_LANG
from invenio.ext.logging import register_exception
from invenio.ext.template import render_template_to_string
from invenio.legacy.bibrecord import create_record, record_empty, \
    record_get_field_instances, record_get_field_value, \
    record_get_field_values, record_xml_output
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.formatter.registry import template_context_functions
from invenio.modules.formatter.utils import parse_tag
from invenio.modules.knowledge.api import get_kbr_values
from invenio.utils.deprecation import RemovedInInvenio22Warning
from invenio.utils.html import CFG_HTML_BUFFER_ALLOWED_ATTRIBUTE_WHITELIST, \
    CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST, HTMLWasher
from invenio.utils.memoise import memoize

from . import registry
from .config import CFG_BIBFORMAT_FORMAT_JINJA_TEMPLATE_EXTENSION, \
    CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION, \
    CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION, CFG_BIBFORMAT_OUTPUTS_PATH, \
    CFG_BIBFORMAT_TEMPLATES_DIR, InvenioBibFormatError
from .engines import xslt

# Cache for data we have already read and parsed
format_templates_cache = {}
format_elements_cache = {}
format_outputs_cache = {}

html_field = '<!--HTML-->' # String indicating that field should be
                           # treated as HTML (and therefore no escaping of
                           # HTML tags should occur.
                           # Appears in some field values.

washer = HTMLWasher()      # Used to remove dangerous tags from HTML
                           # sources

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

    @memoize
    def bibformat_elements(self, modules=None):
        """Returns bibformat elements."""
        if modules is None:
            modules = registry.format_elements

        elem = {}
        for m in modules:
            if m is None:
                continue
            name = m.__name__.split('.')[-1]
            if name in elem:
                continue
            filename = m.__file__[:-1] if m.__file__.endswith('.pyc') \
                else m.__file__
            register_func = getattr(m, 'format_element',
                                    getattr(m, 'format', None))
            escape_values = getattr(m, 'escape_values', None)
            if register_func and isinstance(register_func, types.FunctionType):
                register_func._escape_values = escape_values
                register_func.__file__ = filename
                elem[name] = register_func

        return elem

    @cached_property
    def functions(self):

        def insert(name):
            def _bfe_element(bfo, **kwargs):
                warnings.warn(
                    "BFE elements ({0}) are deprecated. "
                    "Use Jinja2 filters or macros.".format(name),
                    RemovedInInvenio22Warning
                )
                # convert to utf-8 for legacy app
                kwargs = dict((k, v.encode('utf-8') if isinstance(v, unicode) else v)
                              for k, v in iteritems(kwargs))
                format_element = get_format_element(name)
                (out, dummy) = eval_format_element(format_element,
                                                   bfo,
                                                   kwargs)
                # returns unicode for jinja2
                return out.decode('utf-8')
            return _bfe_element

        # Old bibformat templates
        tfn_from_files = dict((name.lower(), insert(name.lower()))
                              for name in self.bibformat_elements().keys())
        # Update with new template context functions
        tfn_from_files.update(self.template_context_functions)

        bfe_from_tags = {}
        if has_app_context():
            from invenio.ext.sqlalchemy import db
            from invenio.modules.search.models import Tag

            # get functions from tag table
            bfe_from_tags = dict(('bfe_'+fix_tag_name(name),
                                  insert(fix_tag_name(name)))
                                 for name in map(itemgetter(0),
                                                 db.session.query(Tag.name).all()))

        # overwrite functions from tag table with functions from files
        bfe_from_tags.update(tfn_from_files)
        return bfe_from_tags

TEMPLATE_CONTEXT_FUNCTIONS_CACHE = LazyTemplateContextFunctionsCache()


def get_format_element_path(filename):
    if filename.endswith('.py'):
        filename = filename[:-3]
    return TEMPLATE_CONTEXT_FUNCTIONS_CACHE.bibformat_elements()[filename].__file__


def format_record(recID, of, ln=CFG_SITE_LANG, verbose=0,
                  search_pattern=None, xml_record=None, user_info=None, qid="",
                  **kwargs):
    """
    Formats a record given output format. Main entry function of
    bibformat engine.

    Returns a formatted version of the record in the specified
    language, search pattern, and with the specified output format.
    The function will define which format template must be applied.

    You can either specify an record ID to format, or give its xml
    representation.  if 'xml_record' is not None, then use it instead
    of recID.

    'user_info' allows to grant access to some functionalities on a
    page depending on the user's priviledges. 'user_info' is the same
    object as the one returned by 'webuser.collect_user_info(req)'

    :param recID: the ID of record to format
    :param of: an output format code (or short identifier for the output format)
    :param ln: the language to use to format the record
    :param verbose: the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings, stop if error in format elements
                                                       9: errors and warnings, stop if error (debug mode ))
    :param search_pattern: list of strings representing the user request in web interface
    :param xml_record: an xml string representing the record to format
    :param user_info: the information of the user who will view the formatted page
    @return: formatted record
    """
    if search_pattern is None:
        search_pattern = []

    out = ""

    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    # Temporary workflow (during migration of formats):
    # Call new BibFormat
    # But if format not found for new BibFormat, then call old BibFormat

    #Create a BibFormat Object to pass that contain record and context
    bfo = BibFormatObject(recID, ln, search_pattern, xml_record, user_info, of)

    if of.lower() != 'xm' and (not bfo.get_record()
                                            or record_empty(bfo.get_record())):
        # Record only has recid: do not format, excepted
        # for xm format
        return "", False

    #Find out which format template to use based on record and output format.
    template = decide_format_template(bfo, of)
    if verbose == 9 and template is not None:
        out += """\n<br/><span class="quicknote">
        Using %s template for record %i.
        </span>""" % (template, recID)

    path = registry.format_templates_lookup.get(template)

    if template is None or not (
       template.endswith("." + CFG_BIBFORMAT_FORMAT_JINJA_TEMPLATE_EXTENSION)
       or path is None or os.access(path, os.R_OK)
       ):
        # template not found in new BibFormat. Call old one
        if verbose == 9:
            if template is None:
                out += """\n<br/><span class="quicknote">
                No template found for output format %s and record %i.
                (Check invenio.err log file for more details)
                </span>""" % (of, recID)
            else:
                out += """\n<br/><span class="quicknote">
                Template %s could not be read.
                </span>""" % (template)
        try:
            raise InvenioBibFormatError(_('No template could be found for output format %(code)s.', code=of))
        except InvenioBibFormatError as exc:
            register_exception(req=bfo.req)

            if verbose > 5:
                out += """\n<br/><span class="quicknote">
                          %s
                          </span>""" % str(exc)

        return out, False

    # Format with template
    out_, needs_2nd_pass = format_with_format_template(
        template, bfo, verbose=verbose, extra_context=kwargs)

    out += out_

    return out, needs_2nd_pass


def format_record_1st_pass(recID, of, ln=CFG_SITE_LANG, verbose=0,
                           search_pattern=None, xml_record=None,
                           user_info=None, on_the_fly=False,
                           save_missing=True, **kwargs):
    """
    Format a record in given output format.

    Return a formatted version of the record in the specified
    language, search pattern, and with the specified output format.
    The function will define which format template must be applied.

    The record to be formatted can be specified with its ID (with
    'recID' parameter) or given as XML representation (with
    'xml_record' parameter). If 'xml_record' is specified 'recID' is
    ignored (but should still be given for reference. A dummy recid 0
    or -1 could be used).

    'user_info' allows to grant access to some functionalities on a
    page depending on the user's priviledges. The 'user_info' object
    makes sense only in the case of on-the-fly formatting. 'user_info'
    is the same object as the one returned by
    'webuser.collect_user_info(req)'

    :param recID: the ID of record to format.
    @type recID: int
    :param of: an output format code (or short identifier for the output format)
    @type of: string
    :param ln: the language to use to format the record
    @type ln: string
    :param verbose: the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings, stop if error in format elements
                                                       9: errors and warnings, stop if error (debug mode ))
    @type verbose: int
    :param search_pattern: list of strings representing the user request in web interface
    @type search_pattern: list(string)
    :param xml_record: an xml string represention of the record to format
    @type xml_record: string or None
    :param user_info: the information of the user who will view the formatted page (if applicable)
    :param on_the_fly: if False, try to return an already preformatted version of the record in the database
    @type on_the_fly: boolean
    @return: formatted record
    @rtype: string
    """
    from invenio.legacy.search_engine import record_exists
    if search_pattern is None:
        search_pattern = []

    out = ""

    if verbose == 9:
        out += """\n<span class="quicknote">
        Formatting record %i with output format %s.
        </span>""" % (recID, of)
    if not on_the_fly and \
       (ln == CFG_SITE_LANG or
        of.lower() == 'xm' or
        (of.lower() in CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS)) and \
       record_exists(recID) != -1:
        # Try to fetch preformatted record. Only possible for records
        # formatted in CFG_SITE_LANG language (other are never
        # stored), or of='xm' which does not depend on language.
        # Exceptions are made for output formats defined in
        # CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS, which are
        # always served from the same cache for any language.  Also,
        # do not fetch from DB when record has been deleted: we want
        # to return an "empty" record in that case
        res, needs_2nd_pass = bibformat_dblayer.get_preformatted_record(recID, of)
        if res is not None:
            # record 'recID' is formatted in 'of', so return it
            if verbose == 9:
                last_updated = bibformat_dblayer.get_preformatted_record_date(recID, of)
                out += """\n<br/><span class="quicknote">
                Found preformatted output for record %i (cache updated on %s).
                </span><br/>""" % (recID, last_updated)
            if of.lower() == 'xm':
                res = filter_hidden_fields(res, user_info)
            # try to replace language links in pre-cached res, if applicable:
            if ln != CFG_SITE_LANG and of.lower() in CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS:
                # The following statements try to quickly replace any
                # language arguments in URL links.  Not an exact
                # science, but should work most of the time for most
                # of the formats, with not too many false positives.
                # We don't have time to parse output much here.
                res = res.replace('?ln=' + CFG_SITE_LANG, '?ln=' + ln)
                res = res.replace('&ln=' + CFG_SITE_LANG, '&ln=' + ln)
                res = res.replace('&amp;ln=' + CFG_SITE_LANG, '&amp;ln=' + ln)
            out += res
            return out, needs_2nd_pass
        else:
            if verbose == 9:
                out += """\n<br/><span class="quicknote">
                No preformatted output found for record %s.
                </span>"""% recID


    # Live formatting of records in all other cases
    if verbose == 9:
        out += """\n<br/><span class="quicknote">
        Formatting record %i on-the-fly.
        </span>""" % recID

    try:
        out_, needs_2nd_pass = format_record(recID=recID,
                                             of=of,
                                             ln=ln,
                                             verbose=verbose,
                                             search_pattern=search_pattern,
                                             xml_record=xml_record,
                                             user_info=user_info,
                                             **kwargs)
        out += out_

        if of.lower() in ('xm', 'xoaimarc'):
            out = filter_hidden_fields(out, user_info, force_filtering=of.lower()=='xoaimarc')

        # We have spent time computing this format
        # We want to save this effort if the format is cached
        if save_missing and recID and ln == cfg['CFG_SITE_LANG'] \
                and of.lower() in cfg['CFG_BIBFORMAT_CACHED_FORMATS'] \
                and verbose == 0:
            bibformat_dblayer.save_preformatted_record(recID,
                                                       of,
                                                       out,
                                                       needs_2nd_pass)

        return out, needs_2nd_pass
    except Exception:
        current_app.logger.exception(
            "An error occured while formatting record {recid} in {of}".format(
                recid=recID, of=of
            ))
        raise


def format_record_2nd_pass(recID, template, ln=CFG_SITE_LANG,
                           search_pattern=None, xml_record=None,
                           user_info=None, of=None, verbose=0, **kwargs):
    # Create light bfo object
    bfo = BibFormatObject(recID, ln, search_pattern, xml_record, user_info, of)
    # Translations
    template = translate_template(template, ln)
    # Format template
    r, dummy = format_with_format_template(format_template_filename=None,
                                           format_template_code=template,
                                           bfo=bfo,
                                           verbose=verbose,
                                           extra_context=kwargs)
    return r


def decide_format_template(bfo, of):
    """
    Returns the format template name that should be used for formatting
    given output format and L{BibFormatObject}.

    Look at of rules, and take the first matching one.
    If no rule matches, returns None

    To match we ignore lettercase and spaces before and after value of
    rule and value of record

    :param bfo: a L{BibFormatObject}
    :param of: the code of the output format to use
    @return: name of a format template
    """

    output_format = get_output_format(of)

    for rule in output_format.get('rules', []):
        if rule['field'].startswith('00'):
            # Rule uses controlfield
            values = [bfo.control_field(rule['field']).strip()] #Remove spaces
        else:
            # Rule uses datafield
            values = bfo.fields(rule['field'])
        # loop over multiple occurences, but take the first match
        if len(values) > 0:
            for value in values:
                value = value.strip() #Remove spaces
                pattern = rule['value'].strip() #Remove spaces
                match_obj = re.match(pattern, value, re.IGNORECASE)
                if match_obj is not None and \
                       match_obj.end() == len(value):
                    return rule['template']
    template = output_format.get('default', '')
    if template != '':
        return template
    else:
        return None


def translate_template(template, ln=CFG_SITE_LANG):
    _ = gettext_set_language(ln)

    def translate(match):
        """
        Translate matching values
        """
        word = match.group("word")
        translated_word = _(word)
        return translated_word

    filtered_template = filter_languages(template, ln)
    evaluated_format = TRANSLATION_PATTERN.sub(translate, filtered_template)
    return evaluated_format


def format_with_format_template(format_template_filename, bfo,
                                verbose=0, format_template_code=None, qid="",
                                extra_context=None):
    """ Format a record given a
    format template.

    Returns a formatted version of the record represented by bfo,
    in the language specified in bfo, and with the specified format template.

    If format_template_code is provided, the template will not be loaded from
    format_template_filename (but format_template_filename will still be used to
    determine if bft or xsl transformation applies). This allows to preview format
    code without having to save file on disk.

    :param format_template_filename: the dilename of a format template
    :param bfo: the object containing parameters for the current formatting
    :param format_template_code: if not empty, use code as template instead of reading format_template_filename (used for previews)
    :param verbose: the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings,
                                                       9: errors and warnings, stop if error (debug mode ))
    @return: formatted text
    """
    if format_template_code is not None:
        format_content = str(format_template_code)
    elif not format_template_filename.endswith("." + CFG_BIBFORMAT_FORMAT_JINJA_TEMPLATE_EXTENSION):
        format_content = get_format_template(format_template_filename)['code']

    if format_template_filename is None or \
            format_template_filename.endswith("." + CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION):
        # .bft
        warnings.warn(
            "BFT template format ({0}) is deprecated. "
            "Use Jinja2 templates.".format(format_template_filename),
            RemovedInInvenio22Warning
        )
        evaluated_format, needs_2nd_pass = eval_format_template_elements(
                                                        format_content,
                                                        bfo,
                                                        verbose)
        if not needs_2nd_pass:
            evaluated_format = translate_template(evaluated_format, bfo.lang)


    elif format_template_filename.endswith("." + CFG_BIBFORMAT_FORMAT_JINJA_TEMPLATE_EXTENSION):
        evaluated_format = '<!-- empty -->'
        #try:
        from functools import wraps
        from invenio.modules.records.api import \
            create_record as new_create_record, \
            get_record as new_get_record
        from flask_login import current_user
        from invenio.base.helpers import unicodifier

        def _format_record(recid, of='hb', user_info=current_user, *args, **kwargs):
            from invenio.modules.formatter import format_record
            return format_record(recid, of, user_info=user_info, *args, **kwargs)

        # Fixes unicode problems in Jinja2 templates.
        def encode_utf8(f):
            @wraps(f)
            def wrapper(*args, **kwds):
                return unicodifier(f(*args, **kwds))
            return wrapper

        if bfo.xml_record is None:
            record = new_get_record(bfo.recID)
        else:
            record = new_create_record(bfo.xml_record, master_format='marc')
            bfo.recID = bfo.recID if bfo.recID else 0
        record.__getitem__ = encode_utf8(record.__getitem__)
        record.get = encode_utf8(record.get)

        ctx = TEMPLATE_CONTEXT_FUNCTIONS_CACHE.functions
        if extra_context is not None:
            ctx.update(extra_context)

        evaluated_format = render_template_to_string(
            'format/record/'+format_template_filename,
            recid=bfo.recID,
            record=record,
            format_record=_format_record,
            qid=qid,
            bfo=bfo, **ctx).encode('utf-8')
        needs_2nd_pass = False
    else:
        from invenio.modules.records.api import get_record as new_get_record

        #.xsl
        if bfo.xml_record:
            # bfo was initialized with a custom MARCXML
            xml_record = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
                         record_xml_output(bfo.record)
        else:
            # Fetch MARCXML. On-the-fly xm if we are now formatting in xm
            xml_record = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
                         new_get_record(bfo.recID).legacy_export_as_marc()

        # Transform MARCXML using stylesheet
        evaluated_format = xslt.format(xml_record, template_source=format_content).decode('utf-8')
        needs_2nd_pass = False

    return evaluated_format, needs_2nd_pass


def eval_format_template_elements(format_template, bfo, verbose=0):
    """
    Evalutes the format elements of the given template and replace each element with its value.

    Prepare the format template content so that we can directly replace the marc code by their value.
    This implies:
      1. Look for special tags
      2. replace special tags by their evaluation

    :param format_template: the format template code
    :param bfo: the object containing parameters for the current formatting
    :param verbose: the level of verbosity from 0 to 9 (O: silent,
                    5: errors, 7: errors and warnings,
                    9: errors and warnings, stop if error (debug mode ))
    @return: tuple (result, errors)
    """
    _ = gettext_set_language(bfo.lang)
    status = {'no_cache': False}

    # First define insert_element_code(match), used in re.sub() function
    def insert_element_code(match):
        """
        Analyses 'match', interpret the corresponding code, and return the result of the evaluation.

        Called by substitution in 'eval_format_template_elements(...)'

        :param match: a match object corresponding to the special tag that must be interpreted
        """

        function_name = match.group("function_name")

        # Ignore lang tags the processing is done outside
        if function_name == 'lang':
            return match.group(0)

        try:
            format_element = get_format_element(function_name, verbose)
        except Exception as e:
            register_exception(req=bfo.req)
            format_element = None
            if verbose >= 5:
                return '<b><span style="color: rgb(255, 0, 0);">' + \
                       cgi.escape(str(e)).replace('\n', '<br/>') + \
                       '</span>'
        if format_element is None:
            try:
                raise InvenioBibFormatError(
                    _('Could not find format element named %(function_name)s.',
                      function_name=function_name))
            except InvenioBibFormatError as exc:
                register_exception(req=bfo.req)

            if verbose >= 5:
                return '<b><span style="color: rgb(255, 0, 0);">' + \
                       str(exc.message)+'</span></b>'
        else:
            params = {}
            # Look for function parameters given in format template code
            all_params = match.group('params')
            if all_params is not None:
                function_params_iterator = pattern_function_params.finditer(all_params)
                for param_match in function_params_iterator:
                    name = param_match.group('param')
                    value = param_match.group('value')
                    params[name] = value

            if params.get('no_cache') == '1':
                result = match.group("function_name")
                del params['no_cache']
                if params:
                    params_str = ' '.join('%s="%s"' % (k, v) for k, v in params.iteritems())
                    result = "<bfe_%s %s />" % (result, params_str)
                else:
                    result = "<bfe_%s />" % result
                status['no_cache'] = True
            else:
                # Evaluate element with params and return (Do not return errors)
                result, dummy = eval_format_element(format_element,
                                                    bfo,
                                                    params,
                                                    verbose)
            return result

    # Substitute special tags in the format by our own text.
    # Special tags have the form <BNE_format_element_name [param="value"]* />
    fmt = pattern_tag.sub(insert_element_code, format_template)
    return fmt, status['no_cache']


def eval_format_element(format_element, bfo, parameters=None, verbose=0):
    """
    Returns the result of the evaluation of the given format element
    name, with given L{BibFormatObject} and parameters. Also returns
    the errors of the evaluation.

    :param format_element: a format element structure as returned by get_format_element
    :param bfo: a L{BibFormatObject} used for formatting
    :param parameters: a dict of parameters to be used for formatting. Key is parameter and value is value of parameter
    :param verbose: the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings,
                                                       9: errors and warnings, stop if error (debug mode ))

    @return: tuple (result, errors)
    """
    if parameters is None:
        parameters = {}

    errors = []
    #Load special values given as parameters
    prefix = parameters.get('prefix', "")
    suffix = parameters.get('suffix', "")
    default_value = parameters.get('default', "")
    escape = parameters.get('escape', "")
    output_text = ''

    _ = gettext_set_language(bfo.lang)

    # 3 possible cases:
    # a) format element file is found: we execute it
    # b) format element file is not found, but exist in tag table (e.g. bfe_isbn)
    # c) format element is totally unknown. Do nothing or report error
    if format_element is not None and format_element['type'] == "python":
        # a) We found an element with the tag name, of type "python"
        # Prepare a dict 'params' to pass as parameter to 'format'
        # function of element
        params = {}

        # Look for parameters defined in format element
        # Fill them with specified default values and values
        # given as parameters.
        # Also remember if the element overrides the 'escape'
        # parameter
        format_element_overrides_escape = False
        for param in format_element['attrs']['params']:
            name = param['name']
            default = param['default']
            params[name] = parameters.get(name, default)
            if name == 'escape':
                format_element_overrides_escape = True

        # Add BibFormatObject
        params['bfo'] = bfo

        # Execute function with given parameters and return result.
        function = format_element['code']
        _ = gettext_set_language(bfo.lang)

        try:
            output_text = function(**params)
        except Exception as e:
            register_exception(req=bfo.req)
            name = format_element['attrs']['name']
            try:
                raise InvenioBibFormatError(
                    _('Error when evaluating format element %(x_name)s '
                      'with parameters %(x_params)s.',
                      x_name=name, x_params=str(params)))
            except InvenioBibFormatError, exc:
                errors.append(exc.message)

            # Log exception
            message = _(
                "Error when evaluating format element %(format_element)s with"
                " parameters %(parameters)s.",
                format_element=name,
                parameters=str(params)
            )
            current_app.logger.exception(
                message
            )
            errors.append(message)

            # In debug mode - include traceback in output
            if current_app.debug:
                tb = sys.exc_info()[2]
                stack = traceback.format_exception(
                    Exception, e, tb, limit=None
                )
                output_text = '<span class="well"><pre style="color:red;">' \
                    '%s\n\n%s</pre></span>' % (message, "".join(stack))

        # None can be returned when evaluating function
        if output_text is None:
            output_text = ""
        else:
            try:
                output_text = str(output_text)
            except:
                output_text = output_text.encode('utf-8')

        # Escaping:
        # (1) By default, everything is escaped in mode 1
        # (2) If evaluated element has 'escape_values()' function, use
        #     its returned value as escape mode, and override (1)
        # (3) If template has a defined parameter 'escape' (in allowed
        #     values), use it, and override (1) and (2). If this
        #     'escape' parameter is overriden by the format element
        #     (defined in the 'format' function of the element), leave
        #     the escaping job to this element

        # (1)
        escape_mode = 1

        # (2)
        escape_function = format_element['escape_function']
        if escape_function is not None:
            try:
                escape_mode = escape_function(bfo=bfo)
            except Exception as e:
                try:
                    raise InvenioBibFormatError(_('Escape mode for format element %(x_name)s could not be retrieved. Using default mode instead.', x_name=name))
                except InvenioBibFormatError as exc:
                    register_exception(req=bfo.req)
                    errors.append(exc.message)

                if verbose >= 5:
                    tb = sys.exc_info()[2]

                    output_text += '<b><span style="color: rgb(255, 0, 0);">'+ \
                                   str(exc.message) +'</span></b> '
        # (3)
        if escape in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            escape_mode = int(escape)

        # If escape is equal to 1, then escape all
        # HTML reserved chars.
        if escape_mode > 0 and not format_element_overrides_escape:
            output_text = escape_field(output_text, mode=escape_mode)

        # Add prefix and suffix if they have been given as parameters and if
        # the evaluation of element is not empty
        if output_text.strip() != "":
            output_text = prefix + output_text + suffix

        # Add the default value if output_text is empty
        if output_text == "":
            output_text = default_value

        return output_text, errors

    elif format_element is not None and format_element['type'] == "field":
        # b) We have not found an element in files that has the tag
        # name. Then look for it in the table "tag"
        #
        # <BFE_LABEL_IN_TAG prefix = "" suffix = "" separator = ""
        #                   nbMax="" escape="0"/>
        #

        # Load special values given as parameters
        separator = parameters.get('separator ', "")
        nbMax = parameters.get('nbMax', "")
        escape = parameters.get('escape', "1") # By default, escape here

        # Get the fields tags that have to be printed
        tags = format_element['attrs']['tags']

        output_text = []

        # Get values corresponding to tags
        for tag in tags:
            p_tag = parse_tag(tag)
            values = record_get_field_values(bfo.get_record(),
                                             p_tag[0],
                                             p_tag[1],
                                             p_tag[2],
                                             p_tag[3])
            if len(values)>0 and isinstance(values[0], dict):
                #flatten dict to its values only
                values_list = [x.values() for x in values]
                #output_text.extend(values)
                for values in values_list:
                    output_text.extend(values)
            else:
                output_text.extend(values)

        if nbMax != "":
            try:
                nbMax = int(nbMax)
            except ValueError:
                name = format_element['attrs']['name']
                try:
                    raise InvenioBibFormatError(_('"nbMax" parameter for %(x_param)s must be an "int".', x_param=name))
                except InvenioBibFormatError as exc:
                    register_exception(req=bfo.req)
                    errors.append(exc.message)

                if verbose >= 5:
                    output_text = output_text.append(exc.message)
            else:
                output_text = output_text[:nbMax]

        # Add prefix and suffix if they have been given as parameters and if
        # the evaluation of element is not empty.
        # If evaluation is empty string, return default value if it exists.
        # Else return empty string
        if ("".join(output_text)).strip() != "":
            # If escape is equal to 1, then escape all
            # HTML reserved chars.
            if escape == '1':
                output_text = cgi.escape(separator.join(output_text))
            else:
                output_text = separator.join(output_text)

            output_text = prefix + output_text + suffix
        else:
            #Return default value
            output_text = default_value

        return (output_text, errors)
    else:
        # c) Element is unknown
        try:
            raise InvenioBibFormatError(_('Could not find format element named %(format_element)s.', format_element=format_element))
        except InvenioBibFormatError as exc:
            register_exception(req=bfo.req)
            errors.append(exc.message)

        if verbose < 5:
            return ("", errors)
        elif verbose >= 5:
            if verbose >= 9:
                sys.exit(exc.message)
            return ('<b><span style="color: rgb(255, 0, 0);">' +
                    str(exc.message)+'</span></b>', errors)


def filter_languages(format_template, ln=CFG_SITE_LANG):
    """
    Filters the language tags that do not correspond to the specified language.

    :param format_template: the format template code
    :param ln: the language that is NOT filtered out from the template
    @return: the format template with unnecessary languages filtered out
    """
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

def get_format_template(filename, with_attributes=False):
    """
    Returns the structured content of the given formate template.

    if 'with_attributes' is true, returns the name and description. Else 'attrs' is not
    returned as key in dictionary (it might, if it has already been loaded previously)::
      {'code':"<b>Some template code</b>"
       'attrs': {'name': "a name", 'description': "a description"}
      }

    :param filename: the filename of an format template
    :param with_attributes: if True, fetch the attributes (names and description) for format'
    @return: strucured content of format template
    """
    _ = gettext_set_language(CFG_SITE_LANG)

    if not filename.endswith("."+CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION) and \
           not filename.endswith(".xsl"):
        return None

    # Get from cache whenever possible
    if filename in format_templates_cache:
        # If we must return with attributes and template exist in
        # cache with attributes then return cache.
        # Else reload with attributes
        if with_attributes and \
               'attrs' in format_templates_cache[filename]:
            return format_templates_cache[filename]

    format_template = {'code': ""}
    try:
        path = registry.format_templates_lookup[filename]

        format_file = open(path)
        format_content = format_file.read()
        format_file.close()

        # Load format template code
        # Remove name and description
        if filename.endswith("."+CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION):
            code_and_description = pattern_format_template_name.sub("",
                                                                    format_content, 1)
            code = pattern_format_template_desc.sub("", code_and_description, 1)
        else:
            code = format_content

        format_template['code'] = code

    except:
        register_exception()

    # Save attributes if necessary
    if with_attributes:
        format_template['attrs'] = get_format_template_attrs(filename)

    # Cache and return
    format_templates_cache[filename] = format_template
    return format_template


def get_format_templates(with_attributes=False):
    """
    Returns the list of all format templates, as dictionary with filenames as keys

    if 'with_attributes' is true, returns the name and description. Else 'attrs' is not
    returned as key in each dictionary (it might, if it has already been loaded previously)::

      [{'code':"<b>Some template code</b>"
        'attrs': {'name': "a name", 'description': "a description"}
       },
      ...
      }

    :param with_attributes: if True, fetch the attributes (names and description) for formats
    @return: the list of format templates (with code and info)
    """
    format_templates = {}

    for filename in registry.format_templates:
        if filename.endswith("."+CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION) or \
               filename.endswith(".xsl"):
            filename = os.path.basename(filename)
            format_templates[filename] = get_format_template(filename,
                                                             with_attributes)

    return format_templates

def get_format_template_attrs(filename):
    """
    Returns the attributes of the format template with given filename

    The attributes are {'name', 'description'}
    Caution: the function does not check that path exists or
    that the format element is valid.
    :param filename: the name of a format template
    @return: a structure with detailed information about given format template
    """
    _ = gettext_set_language(CFG_SITE_LANG)
    attrs = {}
    attrs['name'] = ""
    attrs['description'] = ""
    try:
        template_file = open(registry.format_templates_lookup[filename])
        code = template_file.read()
        template_file.close()

        match = None
        if filename.endswith(".xsl"):
            # .xsl
            attrs['name'] = filename[:-4]
        else:
            # .bft
            match = pattern_format_template_name.search(code)
            if match is not None:
                attrs['name'] = match.group('name')
            else:
                attrs['name'] = filename


            match = pattern_format_template_desc.search(code)
            if match is not None:
                attrs['description'] = match.group('desc').rstrip('.')
    except Exception as e:
        try:
            raise InvenioBibFormatError(_('Could not read format template named %(filename)s. %(error)s.', filename=filename, error=str(e)))
        except InvenioBibFormatError:
            register_exception()

        attrs['name'] = filename

    return attrs


def get_format_element(element_name, verbose=0, with_built_in_params=False,
                       soft_fail=False):
    """
    Returns the format element structured content.

    Return None if element cannot be loaded (file not found, not readable or
    invalid)

    The returned structure is::
      {'attrs': {some attributes in dict. See get_format_element_attrs_from_*}
      'code': the_function_code,
      'type':"field" or "python" depending if element is defined in file or table,
      'escape_function': the function to call to know if element output must be escaped}

    :param element_name: the name of the format element to load
    :param verbose: the level of verbosity from 0 to 9 (O: silent,
                                                       5: errors,
                                                       7: errors and warnings,
                                                       9: errors and warnings, stop if error (debug mode ))
    :param with_built_in_params: if True, load the parameters built in all elements
    @return: a dictionary with format element attributes
    """
    _ = gettext_set_language(CFG_SITE_LANG)

    # Resolve filename and prepare 'name' as key for the cache
    filename = resolve_format_element_filename(element_name)
    if filename is not None:
        name = filename.upper()
    else:
        name = element_name.upper()

    if name in format_elements_cache:
        element = format_elements_cache[name]
        if not with_built_in_params or \
               (with_built_in_params and
                'builtin_params' in element['attrs']):
            return element

    if filename is None:
        # Element is maybe in tag table
        if bibformat_dblayer.tag_exists_for_name(element_name):
            format_element = {'attrs': get_format_element_attrs_from_table(
                element_name,
                with_built_in_params),
                              'code': None,
                              'escape_function': None,
                              'type': "field"}
            # Cache and returns
            format_elements_cache[name] = format_element
            return format_element

        elif soft_fail:
            register_exception()
            return None
        else:
            raise InvenioBibFormatError(
                _('Format element %(x_element_name)s could not be found.',
                  x_element_name=element_name))

    else:
        format_element = {}

        module_name = filename
        if module_name.endswith(".py"):
            module_name = module_name[:-3]

        # Load function 'format_element()' inside element
        try:
            function_format = TEMPLATE_CONTEXT_FUNCTIONS_CACHE.\
                bibformat_elements()[module_name]
            format_element['code'] = function_format
        except:
            if soft_fail:
                register_exception()
                return None
            else:
                raise

        # Load function 'escape_values()' inside element
        format_element['escape_function'] = function_format._escape_values

        # Prepare, cache and return
        format_element['attrs'] = get_format_element_attrs_from_function(
                function_format,
                element_name,
                with_built_in_params)
        format_element['type'] = "python"
        format_elements_cache[name] = format_element
        return format_element

def get_format_elements(with_built_in_params=False):
    """
    Returns the list of format elements attributes as dictionary structure

    Elements declared in files have priority over element declared in 'tag' table
    The returned object has this format::
      {element_name1: {'attrs': {'description':..., 'seealso':...
                               'params':[{'name':..., 'default':..., 'description':...}, ...]
                               'builtin_params':[{'name':..., 'default':..., 'description':...}, ...]
                              },
                     'code': code_of_the_element
                    },
       element_name2: {...},
       ...}

     Returns only elements that could be loaded (not error in code)

    @return: a dict of format elements with name as key, and a dict as attributes
    :param with_built_in_params: if True, load the parameters built in all elements
    """
    format_elements = {}

    mappings = bibformat_dblayer.get_all_name_tag_mappings()

    for name in mappings:
        format_elements[name.upper().replace(" ", "_").strip()] = get_format_element(name, with_built_in_params=with_built_in_params)

    for module in registry.format_elements:
        filename = os.path.basename(module.__file__)
        filename_test = filename.upper().replace(" ", "_")
        if filename_test.endswith(".PYC"):
            filename_test = filename_test[:-1]
        if filename_test.endswith(".PY") and not filename.upper().startswith("__INIT__.PY"):
            if filename_test.startswith("BFE_"):
                filename_test = filename_test[4:]
            element_name = filename_test[:-3]
            element = get_format_element(element_name,
                                         with_built_in_params=with_built_in_params,
                                         soft_fail=True)
            if element is not None:
                format_elements[element_name] = element

    return format_elements

def get_format_element_attrs_from_function(function, element_name,
                                           with_built_in_params=False):
    """
    Returns the attributes of the function given as parameter.

    It looks for standard parameters of the function, default
    values and comments in the docstring.

    The attributes are::
                        {'name' : "name of element" #basically the name of 'name' parameter
                        'description': "a string description of the element",
                        'seealso' : ["element_1.py", "element_2.py", ...] #a list of related elements
                        'params': [{'name':"param_name",   #a list of parameters for this element (except 'bfo')
                                    'default':"default value",
                                    'description': "a description"}, ...],
                        'builtin_params': {name: {'name':"param_name",#the parameters builtin for all elem of this kind
                                            'default':"default value",
                                            'description': "a description"}, ...},
                        }
    :param function: the formatting function of a format element
    :param element_name: the name of the element
    :param with_built_in_params: if True, load the parameters built in all elements
    @return: a structure with detailed information of a function
    """

    attrs = {}
    attrs['description'] = ""
    attrs['name'] = element_name.replace(" ", "_").upper()
    attrs['seealso'] = []

    docstring = function.__doc__
    if isinstance(docstring, str):
        # Look for function description in docstring
        #match = pattern_format_element_desc.search(docstring)
        description = docstring.split("@param")[0]
        description = description.split("@see:")[0]
        attrs['description'] = description.strip().rstrip('.')

        # Look for @see: in docstring
        match = pattern_format_element_seealso.search(docstring)
        if match is not None:
            elements = match.group('see').rstrip('.').split(",")
            for element in elements:
                attrs['seealso'].append(element.strip())

    params = {}
    # Look for parameters in function definition
    args, dummy_varargs, dummy_varkw, defaults = inspect.getargspec(function)

    # Prepare args and defaults_list such that we can have a mapping
    # from args to defaults
    args.reverse()
    if defaults is not None:
        defaults_list = list(defaults)
        defaults_list.reverse()
    else:
        defaults_list = []

    for arg, default in map(None, args, defaults_list):
        if arg == "bfo":
            #Don't keep this as parameter. It is hidden to users, and
            #exists in all elements of this kind
            continue
        param = {}
        param['name'] = arg
        if default is None:
            #In case no check is made inside element, we prefer to
            #print "" (nothing) than None in output
            param['default'] = ""
        else:
            param['default'] = default
        param['description'] = "(no description provided)"

        params[arg] = param

    if isinstance(docstring, str):
        # Look for AT param descriptions in docstring.
        # Add description to existing parameters in params dict
        params_iterator = pattern_format_element_params.finditer(docstring)
        for match in params_iterator:
            name = match.group('name')
            if name in params:
                params[name]['description'] = match.group('desc').rstrip('.')

    attrs['params'] = params.values()

    # Load built-in parameters if necessary
    if with_built_in_params:

        builtin_params = []
        # Add 'prefix' parameter
        param_prefix = {}
        param_prefix['name'] = "prefix"
        param_prefix['default'] = ""
        param_prefix['description'] = """A prefix printed only if the
                                         record has a value for this element"""
        builtin_params.append(param_prefix)

        # Add 'suffix' parameter
        param_suffix = {}
        param_suffix['name'] = "suffix"
        param_suffix['default'] = ""
        param_suffix['description'] = """A suffix printed only if the
                                         record has a value for this element"""
        builtin_params.append(param_suffix)

        # Add 'default' parameter
        param_default = {}
        param_default['name'] = "default"
        param_default['default'] = ""
        param_default['description'] = """A default value printed if the
                                          record has no value for this element"""
        builtin_params.append(param_default)

        # Add 'escape' parameter
        param_escape = {}
        param_escape['name'] = "escape"
        param_escape['default'] = ""
        param_escape['description'] = """0 keeps value as it is. Refer to main
                                         documentation for escaping modes
                                         1 to 7"""
        builtin_params.append(param_escape)

        attrs['builtin_params'] = builtin_params

    return attrs

def get_format_element_attrs_from_table(element_name,
                                        with_built_in_params=False):
    """
    Returns the attributes of the format element with given name in 'tag' table.

    Returns None if element_name does not exist in tag table.

    The attributes are::
                       {'name' : "name of element" #basically the name of 'element_name' parameter
                        'description': "a string description of the element",
                        'seealso' : [] #a list of related elements. Always empty in this case
                        'params': [],  #a list of parameters for this element. Always empty in this case
                        'builtin_params': [{'name':"param_name", #the parameters builtin for all elem of this kind
                                            'default':"default value",
                                            'description': "a description"}, ...],
                        'tags':["950.1", 203.a] #the list of tags printed by this element
                       }

    :param element_name: an element name in database
    :param element_name: the name of the element
    :param with_built_in_params: if True, load the parameters built in all elements
    @return: a structure with detailed information of an element found in DB
    """

    attrs = {}
    tags = bibformat_dblayer.get_tags_from_name(element_name)
    field_label = "field"
    if len(tags)>1:
        field_label = "fields"

    attrs['description'] = "Prints %s %s of the record" % (field_label,
                                                           ", ".join(tags))
    attrs['name'] = element_name.replace(" ", "_").upper()
    attrs['seealso'] = []
    attrs['params'] = []
    attrs['tags'] = tags

    # Load built-in parameters if necessary
    if with_built_in_params:
        builtin_params = []

        # Add 'prefix' parameter
        param_prefix = {}
        param_prefix['name'] = "prefix"
        param_prefix['default'] = ""
        param_prefix['description'] = """A prefix printed only if the
                                       record has a value for this element"""
        builtin_params.append(param_prefix)

        # Add 'suffix' parameter
        param_suffix = {}
        param_suffix['name'] = "suffix"
        param_suffix['default'] = ""
        param_suffix['description'] = """A suffix printed only if the
                                         record has a value for this element"""
        builtin_params.append(param_suffix)

        # Add 'separator' parameter
        param_separator = {}
        param_separator['name'] = "separator"
        param_separator['default'] = " "
        param_separator['description'] = """A separator between elements of
                                            the field"""
        builtin_params.append(param_separator)

        # Add 'nbMax' parameter
        param_nbMax = {}
        param_nbMax['name'] = "nbMax"
        param_nbMax['default'] = ""
        param_nbMax['description'] = """The maximum number of values to
                                      print for this element. No limit if not
                                      specified"""
        builtin_params.append(param_nbMax)

        # Add 'default' parameter
        param_default = {}
        param_default['name'] = "default"
        param_default['default'] = ""
        param_default['description'] = """A default value printed if the
                                          record has no value for this element"""
        builtin_params.append(param_default)

        # Add 'escape' parameter
        param_escape = {}
        param_escape['name'] = "escape"
        param_escape['default'] = ""
        param_escape['description'] = """If set to 1, replaces special
                                         characters '&', '<' and '>' of this
                                         element by SGML entities"""
        builtin_params.append(param_escape)

        attrs['builtin_params'] = builtin_params

    return attrs


def get_output_format(code, with_attributes=False, verbose=0):
    """Return the structured content of the given output format."""
    try:
        return registry.output_formats[code.lower()]
    except KeyError:
        raise InvenioBibFormatError("Missing output format '{0}'".format(code))


def get_output_formats(with_attributes=False):
    """Return all output format as a dictionary with their code as key."""
    assert with_attributes == False
    return dict(registry.output_formats)


def resolve_format_element_filename(element_name):
    """
    Returns the filename of element corresponding to x{element_name}

    This is necessary since format templates code call
    elements by ignoring case, for eg. <BFE_AUTHOR> is the
    same as <BFE_author>.
    It is also recommended that format elements filenames are
    prefixed with bfe_ . We need to look for these too.

    The name of the element has to start with "BFE_".

    :param element_name: a name for a format element
    @return: the corresponding filename, with right case
    """

    if not element_name.endswith(".py"):
        name = element_name.replace(" ", "_").upper() +".PY"
    else:
        name = element_name.replace(" ", "_").upper()

    files = registry.format_elements

    for element in files:
        filename = element.__file__
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        basename = os.path.basename(filename)

        test_filename = basename.replace(" ", "_").upper()

        if test_filename == name or \
                test_filename == "BFE_" + name or \
                "BFE_" + test_filename == name:
            return basename

    # No element with that name found
    # Do not log error, as it might be a normal execution case:
    # element can be in database
    return None


def clear_caches():
    """
    Clear the caches (Output Format, Format Templates and Format Elements).

    @return: None
    """
    global format_templates_cache, format_elements_cache, format_outputs_cache
    format_templates_cache = {}
    format_elements_cache = {}
    format_outputs_cache = {}

class BibFormatObject(object):
    """
    An object that encapsulates a record and associated methods, and that is given
    as parameter to all format elements 'format' function.
    The object is made specifically for a given formatting, i.e. it includes
    for example the language for the formatting.

    The object provides basic accessors to the record. For full access, one can get
    the record with get_record() and then use BibRecord methods on the returned object.
    """
    # The record
    record = None

    # The language in which the formatting has to be done
    lang = CFG_SITE_LANG

    # A list of string describing the context in which the record has
    # to be formatted.
    # It represents the words of the user request in web interface search
    search_pattern = []

    # The id of the record
    recID = 0

    # The information about the user, as returned by
    # 'webuser.collect_user_info(req)'
    user_info = None

    # The format in which the record is being formatted
    output_format = ''

    req = None # DEPRECATED: use bfo.user_info instead. Used by WebJournal.

    def __init__(self, recID, ln=CFG_SITE_LANG, search_pattern=None,
                 xml_record=None, user_info=None, output_format=''):
        """
        Creates a new bibformat object, with given record.

        You can either specify an record ID to format, or give its xml representation.
        if 'xml_record' is not None, use 'xml_record' instead of recID for the record.

        'user_info' allows to grant access to some functionalities on
        a page depending on the user's priviledges. It is a dictionary
        in the following form::

            user_info = {
                'remote_ip' : '',
                'remote_host' : '',
                'referer' : '',
                'uri' : '',
                'agent' : '',
                'uid' : -1,
                'nickname' : '',
                'email' : '',
                'group' : [],
                'guest' : '1'
                }

        :param recID: the id of a record
        :param ln: the language in which the record has to be formatted
        :param search_pattern: list of string representing the request used by the user in web interface
        :param xml_record: a xml string of the record to format
        :param user_info: the information of the user who will view the formatted page
        :param output_format: the output_format used for formatting this record
        """
        self.xml_record = None # *Must* remain empty if recid is given
        if xml_record is not None:
            # If record is given as parameter
            self.xml_record = xml_record
            self.record = create_record(xml_record)[0]
            recID = record_get_field_value(self.record, "001") or None
            recID = int(recID) if recID is not None else recID

        try:
            assert isinstance(recID, (int, long, type(None))), 'Argument of wrong type!'
        except AssertionError:
            register_exception(prefix="recid needs to be an integer in BibFormatObject",
                               alert_admin=True)
            recID = int(recID)
        self.recID = recID
        self.lang = wash_language(ln)
        if search_pattern is None:
            search_pattern = []
        self.search_pattern = search_pattern
        self.output_format = output_format
        self.user_info = user_info
        if self.user_info is None:
            from invenio.ext.login.legacy_user import UserInfo
            self.user_info = UserInfo(None)

    def get_record(self):
        """
        Returns the record structure of this L{BibFormatObject} instance

        @return: the record structure as defined by BibRecord library
        """
        from invenio.legacy.search_engine import get_record

        # Create record if necessary
        if self.record is None:
            # on-the-fly creation if current output is xm
            self.record = get_record(self.recID)

        return self.record

    def control_field(self, tag, escape=0):
        """
        Returns the value of control field given by tag in record

        :param tag: the marc code of a field
        :param escape: 1 if returned value should be escaped. Else 0.
        @return: value of field tag in record
        """
        if self.get_record() is None:
            #Case where BibRecord could not parse object
            return ''

        p_tag = parse_tag(tag)
        field_value = record_get_field_value(self.get_record(),
                                             p_tag[0],
                                             p_tag[1],
                                             p_tag[2],
                                             p_tag[3])
        if escape == 0:
            return field_value
        else:
            return escape_field(field_value, escape)

    def field(self, tag, escape=0):
        """
        Returns the value of the field corresponding to tag in the
        current record.

        If the value does not exist, return empty string.  Else
        returns the same as bfo.fields(..)[0] (see docstring below).

        'escape' parameter allows to escape special characters
        of the field. The value of escape can be:
                      0. no escaping
                      1. escape all HTML characters
                      2. remove unsafe HTML tags (Eg. keep <br />)
                      3. Mix of mode 1 and 2. If value of field starts with
                      <!-- HTML -->, then use mode 2. Else use mode 1.
                      4. Remove all HTML tags
                      5. Same as 2, with more tags allowed (like <img>)
                      6. Same as 3, with more tags allowed (like <img>)
                      7. Mix of mode 0 and mode 1. If field_value
                      starts with <!--HTML-->, then use mode 0.
                      Else use mode 1.
                      8. Same as mode 1, but also escape double-quotes
                      9. Same as mode 4, but also escape double-quotes

        :param tag: the marc code of a field
        :param escape: 1 if returned value should be escaped. Else 0. (see above for other modes)
        @return: value of field tag in record
        """
        list_of_fields = self.fields(tag)
        if len(list_of_fields) > 0:
            # Escaping below
            if escape == 0:
                return list_of_fields[0]
            else:
                return escape_field(list_of_fields[0], escape)
        else:
            return ""

    def fields(self, tag, escape=0, repeatable_subfields_p=False):
        """
        Returns the list of values corresonding to "tag".

        If tag has an undefined subcode (such as 999C5),
        the function returns a list of dictionaries, whoose keys
        are the subcodes and the values are the values of tag.subcode.
        If the tag has a subcode, simply returns list of values
        corresponding to tag.
        Eg. for given MARC::
            999C5 $a value_1a $b value_1b
            999C5 $b value_2b
            999C5 $b value_3b $b value_3b_bis

            >>> bfo.fields('999C5b')
            >>> ['value_1b', 'value_2b', 'value_3b', 'value_3b_bis']
            >>> bfo.fields('999C5')
            >>> [{'a':'value_1a', 'b':'value_1b'},
                {'b':'value_2b'},
                {'b':'value_3b'}]

        By default the function returns only one value for each
        subfield (that is it considers that repeatable subfields are
        not allowed). It is why in the above example 'value3b_bis' is
        not shown for bfo.fields('999C5').  (Note that it is not
        defined which of value_3b or value_3b_bis is returned).  This
        is to simplify the use of the function, as most of the time
        subfields are not repeatable (in that way we get a string
        instead of a list).  You can allow repeatable subfields by
        setting 'repeatable_subfields_p' parameter to True. In
        this mode, the above example would return:
            >>> bfo.fields('999C5b', repeatable_subfields_p=True)
            >>> ['value_1b', 'value_2b', 'value_3b']
            >>> bfo.fields('999C5', repeatable_subfields_p=True)
            >>> [{'a':['value_1a'], 'b':['value_1b']},
                {'b':['value_2b']},
                {'b':['value_3b', 'value3b_bis']}]

        NOTICE THAT THE RETURNED STRUCTURE IS DIFFERENT.  Also note
        that whatever the value of 'repeatable_subfields_p' is,
        bfo.fields('999C5b') always show all fields, even repeatable
        ones. This is because the parameter has no impact on the
        returned structure (it is always a list).

        'escape' parameter allows to escape special characters
        of the fields. The value of escape can be:
                      0. No escaping
                      1. Escape all HTML characters
                      2. Remove unsafe HTML tags (Eg. keep <br />)
                      3. Mix of mode 1 and 2. If value of field starts with
                      <!-- HTML -->, then use mode 2. Else use mode 1.
                      4. Remove all HTML tags
                      5. Same as 2, with more tags allowed (like <img>)
                      6. Same as 3, with more tags allowed (like <img>)
                      7. Mix of mode 0 and mode 1. If field_value
                      starts with <!--HTML-->, then use mode 0.
                      Else use mode 1.
                      8. Same as mode 1, but also escape double-quotes
                      9. Same as mode 4, but also escape double-quotes

        :param tag: the marc code of a field
        :param escape: 1 if returned values should be escaped. Else 0.
        @repeatable_subfields_p if True, returns the list of subfields in the dictionary
        @return: values of field tag in record
        """

        if self.get_record() is None:
            # Case where BibRecord could not parse object
            return []

        p_tag = parse_tag(tag)
        if p_tag[3] != "":
            # Subcode has been defined. Simply returns list of values
            values = record_get_field_values(self.get_record(),
                                             p_tag[0],
                                             p_tag[1],
                                             p_tag[2],
                                             p_tag[3])
            if escape == 0:
                return values
            else:
                return [escape_field(value, escape) for value in values]

        else:
            # Subcode is undefined. Returns list of dicts.
            # However it might be the case of a control field.

            instances = record_get_field_instances(self.get_record(),
                                                   p_tag[0],
                                                   p_tag[1],
                                                   p_tag[2])
            if repeatable_subfields_p:
                list_of_instances = []
                for instance in instances:
                    instance_dict = {}
                    for subfield in instance[0]:
                        if subfield[0] not in instance_dict:
                            instance_dict[subfield[0]] = []
                        if escape == 0:
                            instance_dict[subfield[0]].append(subfield[1])
                        else:
                            instance_dict[subfield[0]].append(escape_field(subfield[1], escape))
                    list_of_instances.append(instance_dict)
                return list_of_instances
            else:
                if escape == 0:
                    return [dict(instance[0]) for instance in instances]
                else:
                    return [dict([(subfield[0], escape_field(subfield[1], escape))
                                   for subfield in instance[0]])
                            for instance in instances]

    def kb(self, kb, string, default=""):
        """
        Returns the value of the "string" in the knowledge base "kb".

        If kb does not exist or string does not exist in kb,
        returns 'default' string or empty string if not specified.

        :param kb: a knowledge base name
        :param string: the string we want to translate
        :param default: a default value returned if 'string' not found in 'kb'
        @return: a string value corresponding to translated input with given kb
        """
        if not string:
            return default

        val = get_kbr_values(kb, searchkey=string, searchtype='e')

        try:
            return val[0][0]
        except IndexError:
            return default


# Utility functions
#


def escape_field(value, mode=0):
    """
    Utility function used to escape the value of a field in given mode.

      - mode 0: no escaping
      - mode 1: escaping all HTML/XML characters (escaped chars are shown as escaped)
      - mode 2: escaping unsafe HTML tags to avoid XSS, but
        keep basic one (such as <br />)
        Escaped tags are removed.
      - mode 3: mix of mode 1 and mode 2. If field_value starts with <!--HTML-->,
        then use mode 2. Else use mode 1.
      - mode 4: escaping all HTML/XML tags (escaped tags are removed)
      - mode 5: same as 2, but allows more tags, like <img>
      - mode 6: same as 3, but allows more tags, like <img>
      - mode 7: mix of mode 0 and mode 1. If field_value starts with <!--HTML-->,
        then use mode 0. Else use mode 1.
      - mode 8: same as mode 1, but also escape double-quotes
      - mode 9: same as mode 4, but also escape double-quotes

    :param value: value to escape
    :param mode: escaping mode to use
    @return: an escaped version of X{value} according to chosen X{mode}
    """
    if mode == 1:
        return cgi.escape(value)
    elif mode == 8:
        return cgi.escape(value, True)
    elif mode in [2, 5]:
        allowed_attribute_whitelist = CFG_HTML_BUFFER_ALLOWED_ATTRIBUTE_WHITELIST
        allowed_tag_whitelist = CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST + \
                                ('class',)
        if mode == 5:
            allowed_attribute_whitelist += ('src', 'alt',
                                            'width', 'height',
                                            'style', 'summary',
                                            'border', 'cellspacing',
                                            'cellpadding')
            allowed_tag_whitelist += ('img', 'table', 'td',
                                      'tr', 'th', 'span', 'caption')
        try:
            return washer.wash(value,
                               allowed_attribute_whitelist=
                               allowed_attribute_whitelist,
                               allowed_tag_whitelist=
                               allowed_tag_whitelist
                               )
        except HTMLParseError:
            # Parsing failed
            return cgi.escape(value)
    elif mode in [3, 6]:
        if value.lstrip(' \n').startswith(html_field):
            allowed_attribute_whitelist = CFG_HTML_BUFFER_ALLOWED_ATTRIBUTE_WHITELIST
            allowed_tag_whitelist = CFG_HTML_BUFFER_ALLOWED_TAG_WHITELIST + \
                                    ('class',)
            if mode == 6:
                allowed_attribute_whitelist += ('src', 'alt',
                                                'width', 'height',
                                                'style', 'summary',
                                                'border', 'cellspacing',
                                                'cellpadding')
                allowed_tag_whitelist += ('img', 'table', 'td',
                                          'tr', 'th', 'span', 'caption')
            try:
                return washer.wash(value,
                                   allowed_attribute_whitelist=
                                   allowed_attribute_whitelist,
                                   allowed_tag_whitelist=
                                   allowed_tag_whitelist
                                   )
            except HTMLParseError:
                # Parsing failed
                return cgi.escape(value)
        else:
            return cgi.escape(value)
    elif mode in [4, 9]:
        try:
            out = washer.wash(value,
                              allowed_attribute_whitelist=[],
                              allowed_tag_whitelist=[]
                              )
            if mode == 9:
                out = out.replace('"', '&quot;')
            return out
        except HTMLParseError:
            # Parsing failed
            if mode == 4:
                return cgi.escape(value)
            else:
                return cgi.escape(value, True)
    elif mode == 7:
        if value.lstrip(' \n').startswith(html_field):
            return value
        else:
            return cgi.escape(value)
    else:
        return value


def make_filter_line(hide_tag):
    """Generate a line used for filtering MARCXML."""
    hide_tag = str(hide_tag)
    tag = hide_tag[:3]
    ind1 = hide_tag[3:4]
    ind2 = hide_tag[4:5]

    if ind1 == "_":
        ind1 = " "
    if ind2 == "_":
        ind2 = " "

    if not ind1 and not ind2:
        return 'datafield tag="%s"' % tag
    if not ind2 and ind1:
        return 'datafield tag="%s" ind1="%s"' % (tag, ind1)
    return 'datafield tag="%s" ind1="%s"  ind2="%s"' % (tag, ind1, ind2)


def filter_hidden_fields(recxml, user_info=None, filter_tags=None,
                         force_filtering=False):
    """
    Filter out tags specified by filter_tags from MARCXML.

    If the user is allowed to run bibedit, then filter nothing, unless
    force_filtering is set to True.

    :param recxml: marcxml presentation of the record
    :param user_info: user information; if None, then assume invoked via CLI
                      with all rights :param filter_tags: list of MARC tags to
                      be filtered :param force_filtering: do we force filtering
                      regardless of user rights?
    :return: recxml without the hidden fields
    """
    filter_tags = filter_tags or cfg['CFG_BIBFORMAT_HIDDEN_TAGS']
    if force_filtering:
        pass
    else:
        if user_info is None:
            #by default
            return recxml
        else:
            if (acc_authorize_action(user_info, 'runbibedit')[0] == 0):
                #no need to filter
                return recxml
    #filter..
    out = ""
    omit = False
    filter_lines = map(make_filter_line, filter_tags)
    for line in recxml.splitlines(True):
        #check if this block needs to be omitted
        for htag in filter_lines:
            if htag in line:
                omit = True
        if not omit:
            out += line
        if omit and ('</datafield>' in line or '</marc:datafield>' in line):
            omit = False
    return out
