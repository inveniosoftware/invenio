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

import operator
from itertools import izip, starmap

def approximate(xs, ys):
    assert len(xs) == len(ys)

    xs = map(float, xs)
    ys = map(float, ys)

    xs0 = [1] * len(xs)
    xs1 = xs
    xs2 = list(starmap(operator.mul, izip(xs, xs)))
    xs3 = list(starmap(operator.mul, izip(xs, xs2)))
    xs4 = starmap(operator.mul, izip(xs, xs3))

    xs = [xs0, xs1, xs2, xs3, xs4]

    s = map(sum, xs)

    assert s[0] == len(ys)

    b = [sum(starmap(operator.mul, izip(ys, x))) for x in xs[:3]]
    a = [s[i:i+3] for i in xrange(3)]

    # So, we have a*x = b and we are looking for x

    matr = [ai + [bi] for ai, bi in izip(a, b)]

    def unify_row(i, j):
        matr[i] = [matr[i][k] / matr[i][j] for k in xrange(len(matr[i]))]

    def subtract_row(i, j, row):
        assert matr[i][j] == 1

        matr[row] = [matr[row][k] - matr[i][k] * matr[row][j] for k in xrange(len(matr[i]))]

        assert matr[row][j] == 0

    unify_row(0, 0)
    subtract_row(0, 0, 1)
    subtract_row(0, 0, 2)
    unify_row(1, 1)
    subtract_row(1, 1, 2)
    unify_row(2, 2)
    subtract_row(2, 2, 1)
    subtract_row(2, 2, 0)
    subtract_row(1, 1, 0)

    assert matr[0][0:3] == [1, 0, 0]
    assert matr[1][0:3] == [0, 1, 0]
    assert matr[2][0:3] == [0, 0, 1]

    return map(operator.itemgetter(3), matr)

