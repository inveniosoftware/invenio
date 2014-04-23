# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""Unit tests for the search engine."""

__revision__ = \
    "$Id$"

from itertools import chain

from invenio.testutils import InvenioTestCase, make_test_suite, run_test_suite
from invenio.bibauthorid_cluster_set import ClusterSet


class Test_probability_matrix(InvenioTestCase):

    def setUp(self):
        pass


TEST_SUITE = make_test_suite(Test_probability_matrix)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
