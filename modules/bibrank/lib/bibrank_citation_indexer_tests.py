# -*- coding: utf-8 -*-
##
## $Id$
##
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

"""Unit tests for the citation indexer."""

# pylint: disable-msg=C0301

__revision__ = "$Id$"

import unittest

from invenio.bibrank_citation_indexer import last_updated_result
from invenio.testutils import make_test_suite, run_test_suite

class TestCitationIndexer(unittest.TestCase):
    """Testing citation indexer."""

    def setUp(self):
        # pylint: disable-msg=C0103
        """Initialize stuff"""
        self.rank_method_code = 'cit'
        self.updated_recid_list = [339705, 339704, 339708]

    def test_last_updated_result(self):
        """bibrank citation indexer - last updated result"""
        self.assert_(last_updated_result(self.rank_method_code,
                                         self.updated_recid_list))

TEST_SUITE = make_test_suite(TestCitationIndexer,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


