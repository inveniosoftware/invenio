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
import re
from textwrap import wrap

CFG_WRAP_STYLES = {
    'DEFAULT' : {
        'horiz_sep' : '*',
        'max_col' : 72,
        'tab_str' : '    ',
        'tab_num' : 0,
        'border' : ('**', '*', '**', '** ', ' **', '**', '*', '**'),
        'prefix' : '\n',
        'suffix' : '\n',
        'force_horiz' : False
    },
    'fancy' : {
        'horiz_sep' : '-',
        'border' : ('/', '-', '\\', '| ', ' |', '\\', '-', '/')
    },
    'double_sharp' : {
        'horiz_sep' : '#',
        'border' : ('##', '#', '##', '## ', ' ##', '##', '#', '##')
    },
    'single_sharp' : {
        'horiz_sep' : '#',
        'border' : ('#', '#', '#', '# ', ' #', '#', '#', '#')
    },
    'single_star' : {
        'border' : ('*', '*', '*', '* ', ' *', '*', '*', '*',)
    },
    'double_star' : {
    },
    'no_border' : {
        'horiz_sep' : '',
        'border' : ('', '', '', '', '', '', '', ''),
        'prefix' : '',
        'suffix' : ''
    }
}

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
    return wrap_text_in_a_box(body=text, style='no_border', tab_str=tab_str, tab_num=nb_tabs)

_beginning_space_re = re.compile('^\s*')
def wrap_text_in_a_box(body='', title='', **args):
    """Return a nicely formatted text box:
        e.g.
       ******************
       **  title       **
       **--------------**
       **  body        **
       ******************

    Indentation and newline are respected.
    @param body the main text
    @param title an optional title
    @param horiz_sep a string that is repeated in order to produce a
        separator row between the title and the body (if needed)
    @param max_col the maximum number of coulmns used by the box (including
        indentation)
    @param tab_str a string to represent indentation
    @param tab_num the number of leveles of indentations
    @param border a tuple of 8 element in the form (tl, t, tr, l, r, bl, b, br)
        of strings that represent the different corners and sides of the box
    @param prefix a prefix string added before the box
    @param suffix a suffix string added after the box
    @param force_horiz True in order to print the horizontal line even when
        there is no title
    @param style the name of one of the style in CFG_WRAP_STYLES. By default
        is set to DEFAULT.
    a part from body and title, if you don't specify anything, the DEFAULT
    style is applied. If style is specified it overwrite the DEFAULT one.
    If any other parameter is specified it will overwrite the specific
    parameter of the chosen style.

    e.g.:
    print wrap_text_in_a_box(title='prova', body='  123 prova.\n    Vediamo come si indenta', horiz_sep='-', style='no_border', max_col=20, tab_num=1)


        prova
        ----------------
        123 prova.
            Vediamo come
            si indenta

    """

    def wrap_row(row, max_col):
        """Wrap a single row"""
        spaces = _beginning_space_re.match(row).group()
        row = row[len(spaces):]
        return wrap(row, initial_indent=spaces, subsequent_indent=spaces, width=max_col)

    style = CFG_WRAP_STYLES['DEFAULT']
    if args.has_key('style'):
        style.update(CFG_WRAP_STYLES[args['style']])
    style.update(args)

    horiz_sep = style['horiz_sep']
    border = style['border']
    tab_str = style['tab_str'] * style['tab_num']
    max_col = style['max_col'] - len(border[3]) - len(border[4]) - len(tab_str)
    prefix = style['prefix']
    suffix = style['suffix']
    force_horiz = style['force_horiz']

    tmp_rows = [wrap_row(row, max_col) for row in body.split('\n')]
    body_rows = []
    for rows in tmp_rows:
        body_rows += rows
    tmp_rows = [wrap_row(row, max_col) for row in title.split('\n')]
    title_rows = []
    for rows in tmp_rows:
        title_rows += rows

    max_col = max([len(row) for row in body_rows + title_rows])

    mid_top_border_len = max_col + len(border[3]) + len(border[4]) - len(border[0]) - len(border[2])
    mid_bottom_border_len = max_col + len(border[3]) + len(border[4]) - len(border[5]) - len(border[7])
    top_border = border[0] + (border[1] * mid_top_border_len)[:mid_top_border_len] + border[2]
    bottom_border = border[5] + (border[6] * mid_bottom_border_len)[:mid_bottom_border_len] + border[7]
    horiz_line = border[3] + (horiz_sep * max_col)[:max_col] + border[4]

    title_rows = [tab_str + border[3] + row + ' ' * (max_col - len(row)) + border[4] for row in title_rows]
    body_rows = [tab_str + border[3] + row + ' ' * (max_col - len(row)) + border[4] for row in body_rows]

    ret = ''
    if top_border:
        ret += [tab_str + top_border]
    ret += title_rows
    if title_rows or force_horiz:
        ret += [tab_str + horiz_line]
    ret += body_rows
    if bottom_border:
        ret += [tab_str + bottom_border]
    return prefix + '\n'.join(ret) + suffix

def wait_for_user(msg):
    """Print MSG and prompt user for confirmation."""
    try:
        raw_input(msg)
    except KeyboardInterrupt:
        print "\n\nAborted."
        sys.exit(1)
    except EOFError:
        print " (continuing in batch mode)"
        return
