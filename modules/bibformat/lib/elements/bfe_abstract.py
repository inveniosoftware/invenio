# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""BibFormat element - Prints English and French abstract.
"""

__revision__ = "$Id$"

#import cgi
from invenio import bibformat_utils

def format(bfo, prefix_en, prefix_fr, suffix_en, suffix_fr, limit, 
           extension_en="[...] ",extension_fr="[...] ", contextual="no",
           highlight='no', print_lang='en,fr'):
    """ Prints the abstract of a record in HTML. By default prints English and French versions.

    Printed languages can be chosen with the 'print_lang' parameter.
    
    @param prefix_en a prefix for english abstract (printed only if english abstract exists)
    @param prefix_fr a prefix for french abstract (printed only if french abstract exists)
    @param limit the maximum number of sentences of the abstract to display (for each language)
    @param extension_en a text printed after english abstracts longer than parameter 'limit'
    @param extension_fr a text printed after french abstracts longer than parameter 'limit'
    @param suffix_en a suffix for english abstract(printed only if english abstract exists)
    @param suffix_fr a suffix for french abstract(printed only if french abstract exists)
    @parmm contextual if 'yes' prints sentences the most relative to user search keyword (if limit < abstract)
    @param highlight if 'yes' highlights words from user search keyword
    @param print_lang the comma-separated list of languages to print. Now restricted to 'en' and 'fr'
    """
    out = ''

    languages = print_lang.split(',')
    
    abstract_en = bfo.fields('520__a', escape=3)
    abstract_en.extend(bfo.fields('520__b', escape=3))
    #abstract_en = [cgi.escape(val) for val in abstract_en]
    abstract_en = "<br/>".join(abstract_en)
    
    abstract_fr = bfo.fields('590__a', escape=3)
    abstract_fr.extend(bfo.fields('590__b', escape=3))
    #abstract_fr = [cgi.escape(val) for val in abstract_fr]
    abstract_fr = "<br/>".join(abstract_fr)

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

        if limit != "" and limit.isdigit():
            print_extension = False
            s_abstract = abstract_en.split(".")

            if int(limit) < len(s_abstract):
                print_extension = True
                s_abstract = s_abstract[:int(limit)]

            for sentence in s_abstract:
                out += sentence+ "."

            if print_extension:
                out += " "+extension_en

        else:
            out += abstract_en

        out += suffix_en
    
    if len(abstract_fr) > 0 and 'fr' in languages:

        out += prefix_fr

        if limit != "" and limit.isdigit():
            print_extension = False
            s_abstract = abstract_fr.split(".")

            if int(limit) < len(s_abstract):
                print_extension = True
                s_abstract = s_abstract[:int(limit)]
        
            for sentence in s_abstract:
                out += sentence + "."

            if print_extension:
                out += " "+extension_fr

        else:
            out += abstract_fr
        
        out += suffix_fr

    if highlight == 'yes':
        out = bibformat_utils.highlight(out, bfo.search_pattern)

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
