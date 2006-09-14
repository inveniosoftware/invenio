# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

def format(bfo, prefix_en, prefix_fr, suffix_en,suffix_fr, limit,extension_en="[...] ",extension_fr="[...] ", contextual="no", highlight='no'):
    """
    Prints the abstract of a record in english and then french
    
    @param prefix_en a prefix for english abstract (printed only if english abstract exists)
    @param prefix_fr a prefix for french abstract (printed only if french abstract exists)
    @param limit the maximum number of sentences of the abstract to display (for each language)
    @param extension_en a text printed after english abstracts longer than parameter 'limit'
    @param extension_fr a text printed after french abstracts longer than parameter 'limit'
    @param suffix_en a suffix for english abstract(printed only if english abstract exists)
    @param suffix_fr a suffix for french abstract(printed only if french abstract exists)
    @parmm contextual if 'yes' prints sentences the most relative to user search keyword (if limit < abstract)
    @param highlight if 'yes' highlights words from user search keyword
    """
    out = ''
    
    abstract_en = bfo.fields('520__a')
    abstract_en.extend(bfo.fields('520__b'))
    abstract_en = "<br/>".join(abstract_en)
    
    abstract_fr = bfo.fields('590__a')
    abstract_fr.extend(bfo.fields('590__b'))
    abstract_fr = "<br/>".join(abstract_fr)

    if contextual == 'yes' and limit != "" and limit.isdigit() and int(limit) > 0:
        from invenio import bibformat_utils
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
    
    if len(abstract_en) > 0 :

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
                out+= " "+extension_en

        else:
            out += abstract_en

        out += suffix_en
    
    if len(abstract_fr) > 0 :

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
        from invenio import bibformat_utils
        out = bibformat_utils.highlight(out, bfo.search_pattern)

    return out

