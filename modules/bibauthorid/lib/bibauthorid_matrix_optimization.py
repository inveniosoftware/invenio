# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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

from operator import itemgetter


def maximized_mapping(matrix):
    '''
    Finds nearly maximized sum mapping from a matrix.
    With this matrix
    ((4, 1, 10),
    (7, 4, 2),
    (20, 4, 15))
    the function will return ((1, 3), (2, 2), (3, 1)).
    For performance reasons the function will not always return
    the optimal mapping.
    '''
    if not matrix or not matrix[0]:
        return []

    sorts = sorted(
        [(i,
          j,
          v) for i,
         row in enumerate(matrix) for j,
         v in enumerate(row)],
        key=itemgetter(2),
        reverse=True)
    freei = set(range(len(matrix)))
    freej = set(range(len(matrix[0])))
    res = []
    for i, j, v in sorts:
        if i in freei and j in freej:
            res.append((i, j, v))
            freei.remove(i)
            freej.remove(j)
            if not freei or not freej:
                return res
    assert False  # you shouldn't be here
    return res
