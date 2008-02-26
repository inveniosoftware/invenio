# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""
Functions useful for text handling.
"""

__revision__ = "$Id$"

import sys
from formatter import AbstractFormatter, DumbWriter
from cStringIO import StringIO

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

def wrap_text_in_a_box(title='', body='', char_sep=' ', max_col=72, nb_tabs=1, tab_str="  "):
    """Return a nicely formatted text box:

       ******************
       **  title       **
       **--------------**
       **  body        **
       ******************

    if no title is specified it will return:
       *************
       ** body     *
       *************

    The width of the box will be set in order to fit in max_col columns
    considering tab characters if they are requested.
    """
    max_col = max_col - len(tab_str) * nb_tabs
    tabs = tab_str * nb_tabs
    ret = ''
    out = StringIO()
    tool = AbstractFormatter(DumbWriter(out, maxcol=max_col))
    for row in body.split('\n'):
        tool.add_flowing_data(row)
        tool.end_paragraph(0)
    body_rows = out.getvalue().split('\n')[:-1]

    out = StringIO()
    tool = AbstractFormatter(DumbWriter(out, maxcol=max_col))
    tool.add_flowing_data(title)
    title_rows = out.getvalue().split('\n')

    max_len = max([len(row) for row in title_rows + body_rows]) + 6
    ret += tabs + '*' * max_len + '\n'
    if title:
        for row in title_rows:
            ret += tabs + '** %s%s **\n' % (row, ' ' * (max_len - len(row) - 6))
        ret += tabs + '**' + char_sep * (max_len - 4) + '**\n'
    for row in body_rows:
        ret += tabs + '** %s%s **\n' % (row, ' ' * (max_len - len(row) - 6))
    ret += tabs + '*' * max_len + '\n'

    return ret

def prefix_text(text, max_col=72, prefix_str="-", nb_tabs=0, tab_str="  "):
    """Return:
    --------------
    text text text
    """
    max_col = max_col - len(tab_str) * nb_tabs
    tabs = tab_str * nb_tabs

    out = StringIO()
    tool = AbstractFormatter(DumbWriter(out, maxcol=max_col))
    for row in text.split('\n'):
        tool.add_flowing_data(row)
        tool.end_paragraph(0)
    text = out.getvalue().split('\n')[:-1]

    max_len = max([len(row) for row in text])

    ret = tabs + '%s\n' % (prefix_str * max_len)[:max_len] # Just in case prefix_str is longer
                                           # than one character
    for row in text:
        ret += tabs + row + '\n'

    return ret

def wait_for_user(msg):
    """Print MSG and prompt user for confirmation."""
    try:
        raw_input(msg)
    except KeyboardInterrupt:
        print "\n\nInstallation aborted."
        sys.exit(1)
    except EOFError:
        print " (continuing in batch mode)"
        return
