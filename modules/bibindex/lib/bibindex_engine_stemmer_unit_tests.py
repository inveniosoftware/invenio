# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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

"""Unit tests for the indexing engine."""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase

from invenio import bibindex_engine_stemmer
from invenio.testutils import make_test_suite, run_test_suite


class TestStemmer(InvenioTestCase):

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
                              ['e^-', 'e^-'],
                              ['C#', 'C#'],
                              ['C++', 'C++']]
        for test_word, expected_result in english_test_cases:
            self.assertEqual(expected_result,
                             bibindex_engine_stemmer.stem(test_word, "en"))

    def test_stemmer_greek(self):
        """bibindex engine - Greek stemmer"""
        greek_test_cases = [['πληροφορίες', 'ΠΛΗΡΟΦΟΡΙ'],
                            ['πείραμα', 'ΠΕΙΡΑΜ'],
                            ['πειράματα', 'ΠΕΙΡΑΜ'],
                            ['πειραματιστής', 'ΠΕΙΡΑΜΑΤΙΣΤ'],
                            ['πειραματίζομαι', 'ΠΕΙΡΑΜΑΤΙΖ'],
                            ['πειραματίζεσαι', 'ΠΕΙΡΑΜΑΤΙΖ'],
                            ['πειραματίστηκα', 'ΠΕΙΡΑΜΑΤΙΣΤ'],
                            ['πειραματόζωο', 'ΠΕΙΡΑΜΑΤΟΖΩ'],
                            ['ζώο', 'ΖΩ'],
                            ['πειραματισμός', 'ΠΕΙΡΑΜΑΤΙΣΜ'],
                            ['πειραματικός', 'ΠΕΙΡΑΜΑΤΙΚ'],
                            ['πειραματικά', 'ΠΕΙΡΑΜΑΤ'],
                            ['ηλεκτρόνιο', 'ΗΛΕΚΤΡΟΝΙ'],
                            ['ηλεκτρονιακός', 'ΗΛΕΚΤΡΟΝΙΑΚ'],
                            ['ακτίνα', 'ΑΚΤΙΝ'],
                            ['ακτινοβολία', 'ΑΚΤΙΝΟΒΟΛ'],
                            ['E=mc^2', 'E=MC^2'],
                            ['α+β=γ', 'Α+Β=Γ']]
        for test_word, expected_result in greek_test_cases:
            self.assertEqual(expected_result,
                             bibindex_engine_stemmer.stem(test_word, "el"))

TEST_SUITE = make_test_suite(TestStemmer,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
