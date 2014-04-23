# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

import operator
from itertools import izip, starmap, repeat
# python2.4 compatibility
from invenio.bibauthorid_general_utils import bai_all as all
from functools import reduce


def approximate(xs, ys, power):
    assert len(xs) == len(ys)

    matrix_size = power + 1
    variables = 2 * power + 1

    xs = map(float, xs)
    ys = map(float, ys)

    xs = reduce(lambda x, y: x + [list(starmap(operator.mul, izip(x[-1], y)))], repeat(
        xs, variables - 1), [[1] * len(xs)])
    assert len(xs) == variables

    s = map(sum, xs)
    assert s[0] == len(ys)

    b = [sum(starmap(operator.mul, izip(ys, x))) for x in xs[:matrix_size]]
    a = [s[i:i + matrix_size] for i in xrange(matrix_size)]

    # So, we have a*x = b and we are looking for x
    matr = [ai + [bi] for ai, bi in izip(a, b)]

    def unify_row(i, j):
        matr[i] = [cell / matr[i][j] for cell in matr[i]]
        assert matr[i][j] == 1

    def subtract_row(i, j, row):
        assert matr[i][j] == 1

        matr[row] = [matr[row][k] - matr[i][k] * matr[row][j] for k in xrange(len(matr[i]))]

        assert matr[row][j] == 0

# NOTE: Example for matrix_size = 3
#    unify_row(0, 0)
#    subtract_row(0, 0, 1)
#    subtract_row(0, 0, 2)
#    unify_row(1, 1)
#    subtract_row(1, 1, 2)
#    unify_row(2, 2)
#    subtract_row(2, 2, 1)
#    subtract_row(2, 2, 0)
#    subtract_row(1, 1, 0)

    for i in xrange(matrix_size):
        unify_row(i, i)
        for j in xrange(matrix_size - i - 1):
            subtract_row(i, i, i + j + 1)

    for i in xrange(matrix_size):
        for j in xrange(matrix_size - i - 1):
            subtract_row(matrix_size - i - 1, matrix_size - i - 1, j)

    assert all(matr[i][:matrix_size] == ([0] * i) + [1] + ([0] * (matrix_size - 1 - i)) for i in xrange(matrix_size))

    ret = map(operator.itemgetter(matrix_size), matr)

    return ret


def to_function(poly):
    power = len(poly) - 1

    def func(x):
        arr = [1.]
        for _ in xrange(power):
            arr.append(arr[-1] * x)

        assert len(arr) == len(poly)
        return sum(p * x for p, x in izip(poly, arr))
    return func
