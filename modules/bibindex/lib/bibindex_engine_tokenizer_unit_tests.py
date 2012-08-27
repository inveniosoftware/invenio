# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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
"""bibindex_engine_tokenizer_tests - unit tests for bibindex_engine_tokenizer

There should always be at least one test class for each class in b_e_t.
"""

import unittest

from invenio.testutils import make_test_suite, run_test_suite

import bibindex_engine_tokenizer as tokenizer_lib


class TestFuzzyNameTokenizerScanning(unittest.TestCase):
    """Test BibIndex name tokenization"""

    def setUp(self):
        self.tokenizer = tokenizer_lib.BibIndexFuzzyNameTokenizer()
        self.scan = self.tokenizer.scan

    def test_bifnt_scan_single(self):
        """BibIndexFuzzyNameTokenizer - scanning single names like 'Dido'"""
        teststr = "Dido"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'], 'lastnames': ['Dido'], 'nonlastnames': [], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_simple_western_forward(self):
        """BibIndexFuzzyNameTokenizer - scanning simple Western-style: first last"""
        teststr = "Ringo Starr"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'], 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_simple_western_reverse(self):
        """BibIndexFuzzyNameTokenizer - scanning simple Western-style: last, first"""
        teststr = "Starr, Ringo"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'], 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_multiname_forward(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: first middle last"""
        teststr = "Michael Edward Peskin"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Peskin'], 'nonlastnames': ['Michael', 'Edward'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_multiname_dotcrammed(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: f.m. last"""
        teststr = "M.E. Peskin"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Peskin'], 'nonlastnames': ['M', 'E'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_multiname_dotcrammed_reversed(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: last, f.m."""
        teststr = "Peskin, M.E."
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Peskin'], 'nonlastnames': ['M', 'E'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_multiname_dashcrammed(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: first-middle last"""
        teststr = "Jean-Luc Picard"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Picard'], 'nonlastnames': ['Jean', 'Luc'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_multiname_dashcrammed_reversed(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: last, first-middle"""
        teststr = "Picard, Jean-Luc"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Picard'], 'nonlastnames': ['Jean', 'Luc'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_compound_lastname_dashes(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: first middle last-last"""
        teststr = "Cantina Octavia Jones-Smith"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Jones', 'Smith'], 'nonlastnames': ['Cantina', 'Octavia'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_compound_lastname_dashes_reverse(self):
        """BibIndexFuzzyNameTokenizer - scanning multiword: last-last, first middle"""
        teststr = "Jones-Smith, Cantina Octavia"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Jones', 'Smith'], 'nonlastnames': ['Cantina', 'Octavia'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_compound_lastname_reverse(self):
        """BibIndexFuzzyNameTokenizer - scanning compound last: last last, first"""
        teststr = "Alvarez Gaume, Joachim"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Alvarez', 'Gaume'], 'nonlastnames': ['Joachim'], 'titles': [], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_titled(self):
        """BibIndexFuzzyNameTokenizer - scanning title-bearing: last, first, title"""
        teststr = "Epstein, Brian, The Fifth Beatle"
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Epstein'], 'nonlastnames': ['Brian'], 'titles': ['The Fifth Beatle'], 'raw' : teststr}
        self.assertEqual(output, anticipated)

    def test_bifnt_scan_wildly_interesting(self):
        """BibIndexFuzzyNameTokenizer - scanning last last last, first first, title, title"""
        teststr = "Ibanez y Gracia, Maria Luisa, II., ed."
        output = self.scan(teststr)
        anticipated = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                       'lastnames': ['Ibanez', 'y', 'Gracia'], 'nonlastnames': ['Maria', 'Luisa'], 'titles': ['II.', 'ed.'], 'raw' : teststr}
        self.assertEqual(output, anticipated)


class TestFuzzyNameTokenizerTokens(unittest.TestCase):
    """Test BibIndex name variant token generation from scanned and tagged sets"""

    def setUp(self):
        self.tokenizer = tokenizer_lib.BibIndexFuzzyNameTokenizer()
        self.get_index_tokens = self.tokenizer.parse_scanned

    def test_bifnt_tokenize_single(self):
        """BibIndexFuzzyNameTokenizer - tokens for single-word name

        Ronaldo
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Ronaldo'], 'nonlastnames': [], 'titles': [], 'raw' : 'Ronaldo'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['Ronaldo']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_simple_forward(self):
        """BibIndexFuzzyNameTokenizer - tokens for first last

        Ringo Starr
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': [], 'raw' : 'Ringo Starr'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['R Starr', 'Ringo Starr', 'Starr, R', 'Starr, Ringo']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_simple_reverse(self):
        """BibIndexFuzzyNameTokenizer - tokens for last, first

        Starr, Ringo
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Starr'], 'nonlastnames': ['Ringo'], 'titles': [], 'raw' : 'Starr, Ringo'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['R Starr', 'Ringo Starr', 'Starr, R', 'Starr, Ringo']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_twoname_forward(self):
        """BibIndexFuzzyNameTokenizer - tokens for first middle last

        Michael Edward Peskin
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Peskin'], 'nonlastnames': ['Michael', 'Edward'], 'titles': [], 'raw' : 'Michael Edward Peskin'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['E Peskin', 'Edward Peskin', 'M E Peskin', 'M Edward Peskin', 'M Peskin',
                       'Michael E Peskin', 'Michael Edward Peskin', 'Michael Peskin',
                       'Peskin, E', 'Peskin, Edward', 'Peskin, M',
                       'Peskin, M E', 'Peskin, M Edward', 'Peskin, Michael',
                       'Peskin, Michael E', 'Peskin, Michael Edward']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_compound_last(self):
        """BibIndexFuzzyNameTokenizer - tokens for last last, first

        Alvarez Gaume, Joachim
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Alvarez', 'Gaume'], 'nonlastnames': ['Joachim'], 'titles': [], 'raw' : 'Alvarez Gaume, Joachim'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['Alvarez Gaume, J', 'Alvarez Gaume, Joachim', 'Alvarez, J', 'Alvarez, Joachim', 'Gaume, J',
                       'Gaume, Joachim', 'J Alvarez', 'J Alvarez Gaume', 'J Gaume', 'Joachim Alvarez',
                       'Joachim Alvarez Gaume', 'Joachim Gaume']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_titled(self):
        """BibIndexFuzzyNameTokenizer - tokens for last, first, title

        Epstein, Brian, The Fifth Beatle
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Epstein'], 'nonlastnames': ['Brian'], 'titles': ['The Fifth Beatle'], 'raw' : 'Epstein, Brian, The Fifth Beatle'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['B Epstein', 'B Epstein, The Fifth Beatle', 'Brian Epstein',
                       'Brian Epstein, The Fifth Beatle', 'Epstein, B', 'Epstein, B, The Fifth Beatle',
                       'Epstein, Brian', 'Epstein, Brian, The Fifth Beatle']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_wildly_interesting(self):
        """BibIndexFuzzyNameTokenizer - tokens for last last last, first first, title, title

        Ibanez y Gracia, Maria Luisa, II, (ed.)
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Ibanez', 'y', 'Gracia'], 'nonlastnames': ['Maria', 'Luisa'], 'titles': ['II', '(ed.)'], 'raw' : 'Ibanez y Gracia, Maria Luisa, II, (ed.)'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['Gracia, L', 'Gracia, Luisa', 'Gracia, M', 'Gracia, M L', 'Gracia, M Luisa',
            'Gracia, Maria', 'Gracia, Maria L', 'Gracia, Maria Luisa',
            'Ibanez y Gracia, L', 'Ibanez y Gracia, L, II',
            'Ibanez y Gracia, Luisa', 'Ibanez y Gracia, Luisa, II',
            'Ibanez y Gracia, M', 'Ibanez y Gracia, M L', 'Ibanez y Gracia, M L, II',
            'Ibanez y Gracia, M Luisa', 'Ibanez y Gracia, M Luisa, II',
            'Ibanez y Gracia, M, II',
            'Ibanez y Gracia, Maria',
            'Ibanez y Gracia, Maria L', 'Ibanez y Gracia, Maria L, II',
            'Ibanez y Gracia, Maria Luisa', 'Ibanez y Gracia, Maria Luisa, II',
            'Ibanez y Gracia, Maria, II',
            'Ibanez, L', 'Ibanez, Luisa',
            'Ibanez, M', 'Ibanez, M L', 'Ibanez, M Luisa', 'Ibanez, Maria',
            'Ibanez, Maria L', 'Ibanez, Maria Luisa', 'L Gracia', 'L Ibanez',
            'L Ibanez y Gracia', 'L Ibanez y Gracia, II', 'Luisa Gracia', 'Luisa Ibanez',
            'Luisa Ibanez y Gracia', 'Luisa Ibanez y Gracia, II', 'M Gracia',
            'M Ibanez', 'M Ibanez y Gracia', 'M Ibanez y Gracia, II', 'M L Gracia',
            'M L Ibanez', 'M L Ibanez y Gracia', 'M L Ibanez y Gracia, II',
            'M Luisa Gracia', 'M Luisa Ibanez', 'M Luisa Ibanez y Gracia', 'M Luisa Ibanez y Gracia, II',
            'Maria Gracia',
            'Maria Ibanez', 'Maria Ibanez y Gracia', 'Maria Ibanez y Gracia, II',
            'Maria L Gracia', 'Maria L Ibanez', 'Maria L Ibanez y Gracia', 'Maria L Ibanez y Gracia, II',
            'Maria Luisa Gracia', 'Maria Luisa Ibanez', 'Maria Luisa Ibanez y Gracia',
            'Maria Luisa Ibanez y Gracia, II']
        self.assertEqual(output, anticipated)

    def test_bifnt_tokenize_multimiddle_forward(self):
        """BibIndexFuzzyNameTokenizer - tokens for first middle middle last

        W K H Panofsky
        """
        tagged_data = {'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
                 'lastnames': ['Panofsky'], 'nonlastnames': ['W', 'K', 'H'], 'titles': [], 'raw' : 'W K H Panofsky'}
        output = self.get_index_tokens(tagged_data)
        anticipated = ['H Panofsky', 'K H Panofsky', 'K Panofsky', 'Panofsky, H', 'Panofsky, K',
                       'Panofsky, K H', 'Panofsky, W', 'Panofsky, W H', 'Panofsky, W K',
                       'Panofsky, W K H', 'W H Panofsky',
                       'W K H Panofsky', 'W K Panofsky', 'W Panofsky']
        self.assertEqual(output, anticipated)

    def test_tokenize(self):
        """BibIndexFuzzyNameTokenizer - check tokenize()

        Ringo Starr
        """
        teststr = "Ringo Starr"
        output = self.tokenizer.tokenize(teststr)
        anticipated = ['R Starr', 'Ringo Starr', 'Starr, R', 'Starr, Ringo']
        self.assertEqual(output, anticipated)



class TestExactNameTokenizer(unittest.TestCase):
    """Test exact author name tokenizer."""

    def setUp(self):
        """setup"""
        self.tokenizer = tokenizer_lib.BibIndexExactNameTokenizer()

    def test_exact_author_name_tokenizer_bare(self):
        """BibIndexExactNameTokenizer - bare name"""
        self.assertEqual(self.tokenizer.tokenize('John Doe'),
                         ['John Doe'])

    def test_exact_author_name_tokenizer_dots(self):
        """BibIndexExactNameTokenizer - name with dots"""
        self.assertEqual(self.tokenizer.tokenize('J. Doe'),
                         ['J Doe'])
        self.assertEqual(self.tokenizer.tokenize('J.R. Doe'),
                         ['J R Doe'])
        self.assertEqual(self.tokenizer.tokenize('J. R. Doe'),
                         ['J R Doe'])

    def test_exact_author_name_tokenizer_trailing_dots(self):
        """BibIndexExactNameTokenizer - name with trailing dots"""
        self.assertEqual(self.tokenizer.tokenize('Doe, J'),
                         ['Doe, J'])
        self.assertEqual(self.tokenizer.tokenize('Doe, J.'),
                         ['Doe, J'])

    def test_exact_author_name_tokenizer_hyphens(self):
        """BibIndexExactNameTokenizer - name with hyphens"""
        self.assertEqual(self.tokenizer.tokenize('Doe, Jean-Pierre'),
                         ['Doe, Jean Pierre'])


TEST_SUITE = make_test_suite(TestFuzzyNameTokenizerScanning,
                             TestFuzzyNameTokenizerTokens,
                             TestExactNameTokenizer,)


if __name__ == '__main__':
    #unittest.main()
    run_test_suite(TEST_SUITE)
