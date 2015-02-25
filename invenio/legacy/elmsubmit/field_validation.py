# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import re

def author(value):
    """
    The author list must be in the following format:
    Put one author per line, and a comma ',' (with no preceding
    space) between the name and the firstname initial letters.

    The name is going first, followed by the firstname initial
    letters.  Precede each initial by a single space.  Place only a
    single space between surnames.

    Example: Put

    Le Meur, J Y
    Baron, T

    for

    Le Meur Jean-Yves & Baron Thomas.
    """

    # Strip each line of leading/trainling whitespace and remove blank lines.
    value = '\n'.join(filter(lambda line: line != '', map(lambda line: line.strip(), value.splitlines())))

    # txt = txt.replace("\r\n", "\n") # Change to unix newline conventions.

    # Allow names like:
    # 'MacDonald Schlüter Wolsey-Smith, P J'

    hyphenated_word = r'\w+(-\w+)*'
    author_surname = r'%s( %s)*' % (hyphenated_word, hyphenated_word)
    comma_space = r', '
    initials = r'\w( \w)*'
    author_re = author_surname + comma_space + initials

    # Allow multiline list with no trailing spaces, and only single
    # (optional) terminating newline:

    author_list = r'(?u)^%s(\n%s)*?$' % (author_re, author_re)

    if re.compile(author_list).search(value):
        return (author.__doc__, value, True)
    else:
        return (author.__doc__, value, False)

def date(value):
    """
    The date field must be in dd/mm/yyyy format.
    eg. 01/03/2010
    """

    value = value.strip()

    day = '(3[01]|[12][0-9]|0[1-9])'
    month = '(1[012]|0[1-9])'
    year = '(\d\d\d\d)'
    date_re = r'^%s/%s/%s(?!\n)$' % (day, month, year)

    if re.compile(date_re).search(value):
        return (date.__doc__, value, True)
    else:
        return (date.__doc__, value, False)

def files(value):

    # Strip each line of leading/trainling whitespace and remove blank lines.
    # Lowercase each filename.
    value = '\n'.join(filter(lambda line: line != '', map(lambda line: line.strip().lower(), value.splitlines())))

    return (files.__doc__, value, True)


