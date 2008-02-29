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
Functions useful for text wrapping (in a box) and indenting.
"""

__revision__ = "$Id$"

import sys
import re
import textwrap

CFG_WRAP_TEXT_IN_A_BOX_STYLES = {
    '__DEFAULT' : {
        'horiz_sep' : '*',
        'max_col' : 72,
        'min_col' : 40,
        'tab_str' : '    ',
        'tab_num' : 0,
        'border' : ('**', '*', '**', '** ', ' **', '**', '*', '**'),
        'prefix' : '\n',
        'suffix' : '\n',
        'break_long' : False,
        'force_horiz' : False,
    },
    'squared' : {
        'horiz_sep' : '-',
        'border' : ('+', '-', '+', '| ', ' |', '+', '-', '+')
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
    },
    'conclusion' : {
        'border' : ('', '', '', '', '', '', '', ''),
        'prefix' : '',
        'horiz_sep' : '-',
        'force_horiz' : True,
    },
    'important' : {
        'tab_num' : 1,
    },
}

def indent_text(text,
                nb_tabs=0,
                tab_str="  ",
                linebreak_input="\n",
                linebreak_output="\n",
                wrap=False):
    """
    add tabs to each line of text
    @param text: the text to indent
    @param nb_tabs: number of tabs to add
    @param tab_str: type of tab (could be, for example "\t", default: 2 spaces
    @param linebreak_input: linebreak on input
    @param linebreak_output: linebreak on output
    @param wrap wethever to apply smart text wrapping.
        (by means of wrap_text_in_a_box)
    @return indented text as string
    """
    if not wrap:
        lines = text.split(linebreak_input)
        tabs = nb_tabs*tab_str
        output = ""
        for line in lines:
            output += tabs + line + linebreak_output
        return output
    else:
        return wrap_text_in_a_box(body=text, style='no_border',
            tab_str=tab_str, tab_num=nb_tabs)

_RE_BEGINNING_SPACES = re.compile('^\s*')
def wrap_text_in_a_box(body='', title='', style='double_star', **args):
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
    @param style the name of one of the style in CFG_WRAP_STYLES. By default
        the double_star style is used.

    You can further tune the desired style by setting various optional
    parameters:
        @param horiz_sep a string that is repeated in order to produce a
            separator row between the title and the body (if needed)
        @param max_col the maximum number of coulmns used by the box
            (including indentation)
        @param min_col the symmetrical minimum number of columns
        @param tab_str a string to represent indentation
        @param tab_num the number of leveles of indentations
        @param border a tuple of 8 element in the form
            (tl, t, tr, l, r, bl, b, br) of strings that represent the
            different corners and sides of the box
        @param prefix a prefix string added before the box
        @param suffix a suffix string added after the box
        @param break_long wethever to break long words in order to respect
            max_col
        @param force_horiz True in order to print the horizontal line even when
            there is no title

    e.g.:
    print wrap_text_in_a_box(title='prova',
        body='  123 prova.\n    Vediamo come si indenta',
        horiz_sep='-', style='no_border', max_col=20, tab_num=1)

        prova
        ----------------
        123 prova.
            Vediamo come
            si indenta

    """

    def _wrap_row(row, max_col, break_long):
        """Wrap a single row"""
        spaces = _RE_BEGINNING_SPACES.match(row).group()
        row = row[len(spaces):]
        spaces = spaces.expandtabs()
        return textwrap.wrap(row, initial_indent=spaces,
            subsequent_indent=spaces, width=max_col,
            break_long_words=break_long)

    astyle = dict(CFG_WRAP_TEXT_IN_A_BOX_STYLES['__DEFAULT'])
    if CFG_WRAP_TEXT_IN_A_BOX_STYLES.has_key(style):
        astyle.update(CFG_WRAP_TEXT_IN_A_BOX_STYLES[style])
    astyle.update(args)

    horiz_sep = astyle['horiz_sep']
    border = astyle['border']
    tab_str = astyle['tab_str'] * astyle['tab_num']
    max_col = astyle['max_col'] \
        - len(border[3]) - len(border[4]) - len(tab_str)
    min_col = astyle['min_col']
    prefix = astyle['prefix']
    suffix = astyle['suffix']
    force_horiz = astyle['force_horiz']
    break_long = astyle['break_long']

    tmp_rows = [_wrap_row(row, max_col, break_long)
                        for row in body.split('\n')]
    body_rows = []
    for rows in tmp_rows:
        if rows:
            body_rows += rows
        else:
            body_rows.append('')
    if not ''.join(body_rows).strip():
        # Concrete empty body
        body_rows = []

    tmp_rows = [_wrap_row(row, max_col, break_long)
                        for row in title.split('\n')]
    title_rows = []
    for rows in tmp_rows:
        if rows:
            title_rows += rows
        else:
            title_rows.append('')
    if not ''.join(title_rows).strip():
        # Concrete empty title
        title_rows = []

    max_col = max([len(row) for row in body_rows + title_rows] + [min_col])

    mid_top_border_len = max_col \
        + len(border[3]) + len(border[4]) - len(border[0]) - len(border[2])
    mid_bottom_border_len = max_col \
        + len(border[3]) + len(border[4]) - len(border[5]) - len(border[7])
    top_border = border[0] \
        + (border[1] * mid_top_border_len)[:mid_top_border_len] + border[2]
    bottom_border = border[5] \
        + (border[6] * mid_bottom_border_len)[:mid_bottom_border_len] \
        + border[7]
    horiz_line = border[3] + (horiz_sep * max_col)[:max_col] + border[4]

    title_rows = [tab_str + border[3] + row
        + ' ' * (max_col - len(row)) + border[4] for row in title_rows]
    body_rows = [tab_str + border[3] + row
        + ' ' * (max_col - len(row)) + border[4] for row in body_rows]

    ret = []
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
