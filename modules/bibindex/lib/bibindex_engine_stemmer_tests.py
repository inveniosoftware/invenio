# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""Unit tests for the indexing engine."""

__revision__ = "$Id$"

import unittest

from invenio import bibindex_engine_stemmer

class TestStemmer(unittest.TestCase):
    """Test stemmer."""

    def test_stemmer_none(self):
        """bibindex engine - no stemmer"""
        self.assertEqual("information",
                         bibindex_engine_stemmer.stem("information", None))

    def test_stemmer_english(self):
        """bibindex engine - English stemmer"""
        english_test_cases = [['information', 'inform'],
                              ['experiment', 'experi'],
                              ['experiments', 'experi'],
                              ['experimented', 'experi'],
                              ['experimenting', 'experi'],
                              ['experimental', 'experiment'],
                              ['experimentally', 'experiment'],
                              ['experimentation', 'experiment'],
                              ['experimentalism', 'experiment'],
                              ['experimenter', 'experiment'],
                              ['experimentalise', 'experimentalis'],
                              ['experimentalist', 'experimentalist'],
                              ['experimentalists', 'experimentalist'],
                              ['GeV', 'GeV'],
                              ['$\Omega$', '$\Omega$'],
                              ['e^-', 'e^-']]
        for test_word, expected_result in english_test_cases:
            self.assertEqual(expected_result,
                             bibindex_engine_stemmer.stem(test_word, "en"))

def create_test_suite():
    """Return test suite for the indexing engine."""
    return unittest.TestSuite((unittest.makeSuite(TestStemmer,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
