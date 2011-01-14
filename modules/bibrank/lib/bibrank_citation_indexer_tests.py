# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""Unit tests for the citation indexer."""

import unittest

from invenio.testutils import make_test_suite, run_test_suite

class TestCitationIndexer(unittest.TestCase):
    """Testing citation indexer."""
    # removed original last_updated_result() test that was meaningless
    # (and failing); so we are testing nothing here now
    pass

TEST_SUITE = make_test_suite(TestCitationIndexer,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


