# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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
from invenio.bibrank_citation_indexer_regression_tests import CONFIG


class TestCitationIndexer(unittest.TestCase):
    def test_abort(self):
        from invenio.bibrank_citation_indexer import check_citations_losses
        fake_config = {'rank_method': 'citation', 'citation': 2}
        try:
            check_citations_losses(fake_config, [1, 2, 81], {1: set([]), 2: set([]), 81: set([])}, {1: set([]), 2: set([]), 81: set([])})
        except Exception as e:  # pylint: disable=W0703
            if 'Lost too many references' not in str(e):
                raise
        else:
            self.fail()

    def test_no_abort(self):
        from invenio.bibrank_citation_indexer import check_citations_losses
        check_citations_losses(CONFIG, [1, 2, 81], {1: set([]), 2: set([]), 81: set([])}, {1: set([]), 2: set([]), 81: set([])})


TEST_SUITE = make_test_suite(TestCitationIndexer)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
