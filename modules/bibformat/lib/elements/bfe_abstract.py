# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints English and French abstract.
"""

__revision__ = "$Id$"

#import cgi
import re

from functools import partial
from invenio.bibformat_utils import (get_contextual_content,
                                     highlight as _highlight,
                                     latex_to_html as _latex_to_html)


class AbstractWrapper:
    """Just there to make the loop in format_element work."""
    def __init__(self, bfo, field1, field2, escape_mode, separator):
        self.abstract = bfo.fields(field1, escape=escape_mode)
        self.abstract.extend(bfo.fields(field2, escape=escape_mode))
        self.abstract = separator.join(self.abstract)


def get_languages_to_display(bfo, print_lang):
    if print_lang == 'auto':
        print_lang = bfo.lang
    langs = print_lang.split(',')
    possible_languages = ['en', 'fr']

    return map(lambda x: x in langs, possible_languages)


def get_escape_mode(escape):
    try:
        return int(escape)
    except ValueError:
        return 0


def convert_to_int(val):
    try:
        return int(val)
    except:
        return None


def find_all_occurrences(text, substring):
    return [m.start() for m in re.finditer(re.escape(substring), text)]


def find_substring_positions(text, regex_pattern):
    results = set(re.findall(regex_pattern, text))
    return map(lambda x: (find_all_occurrences(text, x), len(x)), results)


def split_regarding_substrings(s, separator, *searches):
    """Splits a string except for those positions, which are found by the
    searches."""

    def make_split_is_valid(*invalid_positions_list):
        """Checks if a position in a string is valid for a split"""
        def split_is_valid(position):
            for invalid_positions in invalid_positions_list:
                for pos in invalid_positions:
                    eq_length = pos[1]
                    for p in pos[0]:
                        if p <= position <= p + eq_length:
                            return False
            return True
        return split_is_valid

    split_positions = find_all_occurrences(s, separator)

    invalid_splits = map(partial(find_substring_positions, s), searches)

    splits = filter(make_split_is_valid(*invalid_splits),
                    split_positions)

    return map(lambda x: s[x[0]+len(separator):x[1]],
               zip([-len(separator)]+splits, splits+[len(s)]))


def extend_max_chars(max_chars, positions):
    for positions, length in positions:
        for position in positions:
            if position < max_chars:
                max_chars += length

    return max_chars


def format_element(bfo, prefix_en, prefix_fr, suffix_en, suffix_fr, limit,
                   max_chars, extension_en="[...] ", extension_fr="[...] ",
                   contextual="no", highlight='no', print_lang='en,fr',
                   escape="3", separator_en="<br/>", separator_fr="<br/>",
                   latex_to_html='no'):
    """ Prints the abstract of a record in HTML. By default prints
    English and French versions.

    Printed languages can be chosen with the 'print_lang' parameter.

    @param bfo: BibFormatObject from invenio.bibformat_engine
    @param prefix_en: a prefix for english abstract (printed only if english abstract exists)
    @param prefix_fr: a prefix for french abstract (printed only if french abstract exists)
    @param limit: the maximum number of sentences of the abstract to display (for each language)
    @param max_chars: the maximum number of chars of the abstract to display (for each language)
    @param extension_en: a text printed after english abstracts longer than parameter 'limit'
    @param extension_fr: a text printed after french abstracts longer than parameter 'limit'
    @param suffix_en: a suffix for english abstract(printed only if english abstract exists)
    @param suffix_fr: a suffix for french abstract(printed only if french abstract exists)
    @parmm contextual if 'yes' prints sentences the most relative to user search keyword (if limit < abstract)
    @param highlight: if 'yes' highlights words from user search keyword
    @param print_lang: the comma-separated list of languages to print. Now restricted to 'en' and 'fr'
    @param escape: escaping method (overrides default escape parameter to not escape separators)
    @param separator_en: a separator between each english abstract
    @param separator_fr: a separator between each french abstract
    @param latex_to_html: if 'yes', interpret as LaTeX abstract
    """
    out = ''

    languages = get_languages_to_display(bfo, print_lang)
    escape_mode = get_escape_mode(escape)

    abstracts = [AbstractWrapper(bfo, '520__a', '520__b',
                                 escape_mode, separator_en),   # EN ABSTRACT
                 AbstractWrapper(bfo, '590__a', '590__b',
                                 escape_mode, separator_fr)]   # FR ABSTRACT
    prefixes = [prefix_en, prefix_fr]
    suffixes = [suffix_en, suffix_fr]

    max_chars = convert_to_int(max_chars)
    limit = convert_to_int(limit)

    if contextual == 'yes' and limit and limit > 0:
        for abstract in abstracts:
            context = get_contextual_content(abstract,
                                             bfo.search_pattern,
                                             max_lines=limit)
            abstract.abstract = "<br/>".join(context)

    for abstract, language, prefix, suffix in zip(abstracts, languages,
                                                  prefixes, suffixes):

        if len(abstract.abstract) > 0 and language:

            out += prefix
            print_extension = False

            if max_chars and max_chars < len(abstract.abstract):
                latex_eqs = find_substring_positions(abstract.abstract,
                                                     '\$.*?\$')
                mathml_eqs = find_substring_positions(abstract.abstract,
                                                      '<math.*?</math>')
                max_chars = extend_max_chars(max_chars, latex_eqs)
                max_chars = extend_max_chars(max_chars, mathml_eqs)

                abstract.abstract = abstract.abstract[:max_chars]

                if max_chars < len(abstract.abstract):
                    print_extension = True

            if limit:
                # Split around DOTSPACE so that we don't split html links.
                # Also check to not split in formulas, eventhough it might
                # never happen
                s_abstract = split_regarding_substrings(abstract.abstract,
                                                        ". ",
                                                        '\$.*?\$',
                                                        '<math.*?</math>')

                if limit < len(s_abstract):
                    print_extension = True
                    s_abstract = s_abstract[:limit]

                #for sentence in s_abstract:
                #    out += sentence + "."
                out += '. '.join(s_abstract)

                # Add final dot if needed
                if abstract.abstract.endswith('.'):
                    out += '.'

                if print_extension:
                    out += " " + extension_en

            else:
                out += abstract.abstract

            out += suffix

    if highlight == 'yes':
        out = _highlight(out, bfo.search_pattern)

    if latex_to_html == 'yes':
        out = _latex_to_html(out)

    return out


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
