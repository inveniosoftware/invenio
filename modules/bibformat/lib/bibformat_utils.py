# -*- coding: utf-8 -*-
## $Id$
## Set of utilities functions to be used in format elements.

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

import re


def highlight(text, keywords_string="", prefix_tag='<b style="color: black; background-color: rgb(255, 255, 102);">', suffix_tag="</b>"):
    """ Returns text with all words highlighted with given tags
    (this function places 'prefix_tag' and 'suffix_tag' before and after keywords from 'keywords_string' in 'text' with respectively)

    'and', 'or' are words that are not highlighted

    @param text the text to modify
    @param keywords_string a string with keywords separated by spaces
    @return highlighted text
    """

    def replace_highlight(match):
        """ replace match.group() by prefix_tag + match.group() + suffix_tag"""
        return prefix_tag + match.group() + suffix_tag

    cleaned_keywords_string = keywords_string
    #Remove 'and' 'or' from keywords
    cleaned_keywords_string =  re.sub(r'\band\b', '', keywords_string)
    cleaned_keywords_string =  re.sub(r'\bor\b', '', cleaned_keywords_string)
    
    #Build a pattern of the kind keyword1 | keyword2 | keyword3
    pattern =  re.sub(r'(\\\s)+', '|', re.escape(cleaned_keywords_string))
    compiled_pattern = re.compile(pattern)

    #Replace and return keywords with prefix+keyword+suffix
    return compiled_pattern.sub(replace_highlight, text) 

    
def get_contextual_content(text, keywords_string="", max_lines=2):
    """
    Returns some lines from a text contextually to the keywords in 'keywords_string'

    @param text the text from which we want to get contextual content
    @param keywords_string a string with keywords separated by spaces ("the context")
    @param max_lines the maximum number of line to return from the record
    @return a string
    """
    return ''
