# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
'''
bibauthorid_string_utils
    Bibauthorid utilities used by many parts of the framework
'''


def string_partition(s, sep, direc='l'):
    '''
    Partition a string by the first occurrence of the separator.
    Mimics the string.partition function, which is not available in Python2.4

    @param s: string to be partitioned
    @type s: string
    @param sep: separator to partition by
    @type sep: string
    @param dir: direction (left 'l' or right 'r') to search the separator from
    @type dir: string

    @return: tuple of (left or sep, sep, right of sep)
    @rtype: tuple
    '''
    if direc == 'r':
        i = s.rfind(sep)
    else:
        i = s.find(sep)
    if i < 0:
        return (s, '', '')
    else:
        return (s[0:i], s[i:i + 1], s[i + 1:])


def unpackbib(bibrecref):
    """
    Creates a tuple (700, 123, 456) from a bibrecref string("100:123,456").
    @param bibrecref and return: bibrecref
    @type bibrecref: string
    @type return: (int, int int)
    """
    table, tail = bibrecref.split(":")
    bibref, bibrec = tail.split(",")
    return (int(table), int(bibref), int(bibrec))


