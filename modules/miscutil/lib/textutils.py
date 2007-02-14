# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

""" Functions for text handling:
- indenting
- ...
"""

__revision__ = "$Id$"

def indent_text(text,
                nb_tabs=0,
                tab_str="  ",
                linebreak_input="\n",
                linebreak_output="\n"):
    """
    add tabs to each line of text
    @param text: the text to indent
    @param nb_tabs: number of tabs to add
    @param tab_str: type of tab (could be, for example "\t", default: 2 spaces
    @param linebreak_input: linebreak on input
    @param linebreak_output: linebreak on output
    @return indented text as string
    """
    lines = text.split(linebreak_input)
    tabs = nb_tabs*tab_str
    output = ""
    for line in lines:
        output += tabs + line + linebreak_output
    return output
