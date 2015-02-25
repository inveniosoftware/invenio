# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints English and French abstract.
"""

__revision__ = "$Id$"

#import cgi
from invenio.modules.formatter import utils as bibformat_utils

def format_element(bfo, prefix_en, prefix_fr, suffix_en, suffix_fr, limit, max_chars,
           extension_en="[...] ",extension_fr="[...] ", contextual="no",
           highlight='no', print_lang='en,fr', escape="3",
           separator_en="<br/>", separator_fr="<br/>", latex_to_html='no'):
    """ Prints the abstract of a record in HTML. By default prints
    English and French versions.

    Printed languages can be chosen with the 'print_lang' parameter.

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

    if print_lang == 'auto':
        print_lang = bfo.lang
    languages = print_lang.split(',')

    try:
        escape_mode_int = int(escape)
    except ValueError as e:
        escape_mode_int = 0

    abstract_en = bfo.fields('520__a', escape=escape_mode_int)
    abstract_en.extend(bfo.fields('520__b', escape=escape_mode_int))
    abstract_en = separator_en.join(abstract_en)

    abstract_fr = bfo.fields('590__a', escape=escape_mode_int)
    abstract_fr.extend(bfo.fields('590__b', escape=escape_mode_int))
    abstract_fr = separator_fr.join(abstract_fr)

    if contextual == 'yes' and limit != "" and \
           limit.isdigit() and int(limit) > 0:
        context_en = bibformat_utils.get_contextual_content(abstract_en,
                                                            bfo.search_pattern,
                                                            max_lines=int(limit))
        #FIXME add something like [...] before and after
        #contextual sentences when not at beginning/end of abstract
        #if not abstract_en.strip().startswith(context_en[0].strip()):
        #    out += '[...]'
        abstract_en = "<br/>".join(context_en)

        context_fr = bibformat_utils.get_contextual_content(abstract_fr,
                                                            bfo.search_pattern,
                                                            max_lines=int(limit))
        abstract_fr = "<br/>".join(context_fr)

    if len(abstract_en) > 0 and 'en' in languages:

        out += prefix_en
        print_extension = False

        if max_chars != "" and max_chars.isdigit() and \
               int(max_chars) < len(abstract_en):
            print_extension = True
            abstract_en = abstract_en[:int(max_chars)]

        if limit != "" and limit.isdigit():
            s_abstract = abstract_en.split(". ") # Split around
                                                 # DOTSPACE so that we
                                                 # don't split html
                                                 # links

            if int(limit) < len(s_abstract):
                print_extension = True
                s_abstract = s_abstract[:int(limit)]

            #for sentence in s_abstract:
            #    out += sentence + "."
            out = '. '.join(s_abstract)

            # Add final dot if needed
            if abstract_en.endswith('.'):
                out += '.'

            if print_extension:
                out += " " + extension_en

        else:
            out += abstract_en

        out += suffix_en

    if len(abstract_fr) > 0 and 'fr' in languages:

        out += prefix_fr

        print_extension = False

        if max_chars != "" and max_chars.isdigit() and \
               int(max_chars) < len(abstract_fr):
            print_extension = True
            abstract_fr = abstract_fr[:int(max_chars)]

        if limit != "" and limit.isdigit():
            s_abstract = abstract_fr.split(". ") # Split around
                                                 # DOTSPACE so that we
                                                 # don't split html
                                                 # links

            if int(limit) < len(s_abstract):
                print_extension = True
                s_abstract = s_abstract[:int(limit)]

            #for sentence in s_abstract:
            #    out += sentence + "."
            out += '. '.join(s_abstract)

            # Add final dot if needed
            if abstract_fr.endswith('.'):
                out += '.'

            if print_extension:
                out += " "+extension_fr

        else:
            out += abstract_fr

        out += suffix_fr

    if highlight == 'yes':
        out = bibformat_utils.highlight(out, bfo.search_pattern)

    if latex_to_html == 'yes':
        out = bibformat_utils.latex_to_html(out)

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
