# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibFormat element - meta"""

__revision__ = "$Id$"

import cgi
import re
import time
import string
from datetime import datetime
from invenio.bibformat_elements.bfe_server_info import format_element as server_info
from invenio.bibformat_elements.bfe_client_info import format_element as client_info
from invenio.dateutils import get_i18n_month_name
from invenio.htmlutils import create_tag
from invenio.bibindex_engine_utils import get_field_tags
from invenio.config import \
     CFG_WEBSEARCH_ENABLE_GOOGLESCHOLAR, \
     CFG_WEBSEARCH_ENABLE_OPENGRAPH, \
     CFG_SITE_LANG, \
     CFG_CERN_SITE

def format_element(bfo, name, tag_name='', tag='', kb='', kb_default_output='', var='', protocol='googlescholar'):
    """Prints a custom field in a way suitable to be used in HTML META
    tags.  In particular conforms to Google Scholar harvesting protocol as
    defined http://scholar.google.com/intl/en/scholar/inclusion.html and
    Open Graph http://ogp.me/

    @param tag_name: the name, from tag table, of the field to be exported
    looks initially for names prefixed by "meta-"<tag_name>
    then looks for exact name, then falls through to "tag"
    @param tag: the MARC tag to be exported (only if not defined by tag_name). Comma-separated list of tags.
    @param name: name to be displayed in the meta headers, labelling this value.
    @param kb: a knowledge base through which to process the retrieved value if necessary.
    @param kb: when a '<code>kb</code>' is specified and no match for value is found, what shall we
               return? Either return the given parameter or specify "{value}" to return the retrieved
               value before processing though kb.
    @param var: the name of a variable to output instead of field from metadata.
                Allowed values are those supported by bfe_server_info and
                bfe_client_info. Overrides <code>name</code> and <code>tag_name</code>
    @param protocol: the protocol this tag is aimed at. Can be used to switch on/off support for a given "protocol". Can take values among 'googlescholar', 'opengraph'
    @see: bfe_server_info.py, bfe_client_info.py
    """
    if protocol == 'googlescholar' and not CFG_WEBSEARCH_ENABLE_GOOGLESCHOLAR:
        return ""
    elif protocol == 'opengraph' and not CFG_WEBSEARCH_ENABLE_OPENGRAPH:
        return ""

    matched_by_tag_name_p = False
    tags = []
    if var:
        # delegate to bfe_server_info or bfe_client_info:
        value = server_info(bfo, var)
        if value.startswith("Unknown variable: "):
            # Oops variable was not defined there
            value = client_info(bfo, var)
        return not value.startswith("Unknown variable: ") and \
               create_metatag(name=name, content=cgi.escape(value, True)) \
               or ""
    elif tag_name:
        # First check for special meta named tags
        tags = get_field_tags("meta-" + tag_name)
        if not tags:
            # then check for regular tags
            tags = get_field_tags(tag_name)
        matched_by_tag_name_p = tags and True or False
    if not tags and tag:
        # fall back to explicit marc tag
        if ',' in tag:
            tags = tag.split(',')
        else:
            tags = [tag]
    if not tags:
        return ''
    out = []

    if protocol == 'googlescholar' and \
      (tags == ['100__a'] or tags == ['700__a']):
      # Authors for Google Scholar: remove names that are not purely
      # author (thesis director, coordinator, etc). Assume that
      # existence of $e subfield is a sign. Since this assumption
      # might be wrong, put some strong conditions in order to get
      # into this branch, with easy way to bypass.
      values = [field_instance[tags[0][-1]] for field_instance in bfo.fields(tags[0][:-1], escape=9)
                if 'e' not in field_instance and tags[0][-1] in field_instance]
    else:
        # Standard fetching of values
        values = [bfo.fields(marctag, escape=9) for marctag in tags]


    if name == 'citation_dissertation_institution':
        if CFG_CERN_SITE and \
          'THESIS' in bfo.fields('980__a'):
                authors = bfo.fields('100__', escape=9)
                authors.extend(bfo.fields('700__', escape=9))
                values = [field_instance['u'] for field_instance in authors \
                  if not field_instance.has_key('e') and  field_instance.has_key('u')]
        elif tag == '100__u' and not matched_by_tag_name_p:
            # TODO: find way to map correctly this tag
            values = []

    for value in values:
        if isinstance(value, list):
            for val in value:
                if isinstance(val, dict):
                    out.extend(val.values())
                else:
                    out.append(val)
        elif isinstance(value, dict):
            out.extend(value.values())
        else:
            out.append(value)

    if name == 'citation_date':
        for idx in range(len(out)):
            out[idx] = out[idx].replace('-', '/')

    elif name == 'citation_publication_date':
        for idx in range(len(out)):
            # Stop at first match
            parsed_date = parse_date_for_googlescholar(out[idx])
            if parsed_date:
                out = [parsed_date]
                break

    out = dict(zip(out, len(out)*[''])).keys() # Remove duplicates

    if kb:
        if kb_default_output == "{value}":
            out = [bfo.kb(kb, value, value) for value in out]
        else:
            out = [bfo.kb(kb, value, kb_default_output) for value in out]
    return '\n'.join([create_metatag(name=name, content=value) for value in out])

def create_metatag(name, content):
    """
    Wraps create_tag
    """
    if name.startswith("og:"):
        return create_tag('meta', property=name, content=content)
    else:
        return create_tag('meta', name=name, content=content)

# Build list of expected patterns
CFG_POSSIBLE_DATE_FORMATS = ['%Y %m %d',
                             '%d %m %Y',
                             '%d %B %Y',
                             '%d %b %Y',
                             '%Y %B %d',
                             '%Y %b %d',
                             '%m %Y',
                             '%B %Y',
                             '%b %Y',
                             '%x',
                             '%x %X']
CFG_POSSIBLE_DATE_FORMATS = CFG_POSSIBLE_DATE_FORMATS + \
                            [f + ' %H:%M:%S' for f in CFG_POSSIBLE_DATE_FORMATS] + \
                            [f + 'T%H:%M:%S' for f in CFG_POSSIBLE_DATE_FORMATS]

# Build month translation mapping from CFG_SITE_LANG to English.
CFG_MONTH_NAMES_MAPPING = {}
if CFG_SITE_LANG != 'en':
    CFG_MONTH_NAMES_MAPPING = dict([(get_i18n_month_name(month_nb, display='short', ln=CFG_SITE_LANG).upper(),
                                     get_i18n_month_name(month_nb, display='short', ln='en')) \
                                    for month_nb in range(1, 13)])
    CFG_MONTH_NAMES_MAPPING.update(dict([(get_i18n_month_name(month_nb, display='long', ln=CFG_SITE_LANG).upper(),
                                          get_i18n_month_name(month_nb, display='long', ln='en')) \
                                         for month_nb in range(1, 13)]))
# Build regular expression pattern to match month name in
# CFG_SITE_LANG.  Note the use \W instead of \b for word boundaries
# because of a bug in 're' module with unicode.
CFG_MONTHS_I18N_PATTERN_RE = re.compile(r"(\W|\A)(%s)(\W|\Z)" % "|".join(CFG_MONTH_NAMES_MAPPING.keys()),
                                        re.IGNORECASE | re.UNICODE)

CFG_YEAR_PATTERN_RE = re.compile("((\D|\A)(\d{4})(\D|\Z))")

CFG_PUNCTUATION_PATTERN_RE = re.compile(r'[' + string.punctuation + ']')
CFG_SPACES_PATTERN_RE = re.compile(r'\s+')

def parse_date_for_googlescholar(datetime_string):
    """
    Parse (guess) and return the date in a format adequate for Google
    Scholar. We don't use dateutils.guess_datetime() as this one might
    lead to results not accurate enough.
    """
    datetime_string = CFG_PUNCTUATION_PATTERN_RE.sub(' ', datetime_string)
    datetime_string = CFG_SPACES_PATTERN_RE.sub(' ', datetime_string)

    def replace_month(match_obj):
        "Return translated month in the matching object"
        month = match_obj.group(2).strip()
        return match_obj.group(1) + \
               CFG_MONTH_NAMES_MAPPING.get(month.upper(), month) + \
               match_obj.group(3)

    parsed_datetime = None
    for dateformat in CFG_POSSIBLE_DATE_FORMATS:
        try:
            parsed_datetime = time.strptime(datetime_string.strip(), dateformat)
            break
        except:
            pass

    if not parsed_datetime:
        # Do it all again, with the translated version of the string
        translated_datetime_string = CFG_MONTHS_I18N_PATTERN_RE.sub(replace_month, datetime_string)
        for dateformat in CFG_POSSIBLE_DATE_FORMATS:
            try:
                parsed_datetime = time.strptime(translated_datetime_string.strip(), dateformat)
                break
            except:
                pass

    if parsed_datetime:
        return datetime(*(parsed_datetime[0:6])).strftime('%Y/%m/%d')
    else:
        # Look for a year inside the string:
        try:
            return CFG_YEAR_PATTERN_RE.search(datetime_string).group(3)
        except:
            return ''

    return ''

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
