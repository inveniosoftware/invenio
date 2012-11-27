# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""
The Refextract unit test suite

The tests will not modifiy the database.
"""

import unittest
import re

from invenio.testutils import make_test_suite, run_test_suite
# Import the minimal necessary methods and variables needed to run Refextract
from invenio.docextract_utils import setup_loggers
from invenio.refextract_tag import identify_ibids, tag_numeration
from invenio import refextract_re
from invenio.refextract_find import get_reference_section_beginning
from invenio.refextract_api import search_from_reference


class ReTest(unittest.TestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_word(self):
        r = refextract_re._create_regex_pattern_add_optional_spaces_to_word_characters('ABC')
        self.assertEqual(r, ur'A\s*B\s*C\s*')

    def test_reference_section_title_pattern(self):
        r = refextract_re.get_reference_section_title_patterns()
        self.assert_(len(r) > 2)

    def test_get_reference_line_numeration_marker_patterns(self):
        r = refextract_re.get_reference_line_numeration_marker_patterns()
        self.assert_(len(r) > 2)

    def test_get_reference_line_marker_pattern(self):
        r = refextract_re.get_reference_line_marker_pattern('ABC')
        self.assertNotEqual(r.pattern.find('ABC'), -1)

    def test_get_post_reference_section_title_patterns(self):
        r = refextract_re.get_post_reference_section_title_patterns()
        self.assert_(len(r) > 2)

    def test_get_post_reference_section_keyword_patterns(self):
        r = refextract_re.get_post_reference_section_keyword_patterns()
        self.assert_(len(r) > 2)

    def test_regex_match_list(self):
        s = 'ABC'
        m = refextract_re.regex_match_list(s, [
            re.compile('C.C'),
            re.compile('A.C')
        ])
        self.assert_(m)
        m = refextract_re.regex_match_list(s, [
            re.compile('C.C')
        ])
        self.assertEqual(m, None)


class IbidTest(unittest.TestCase):
    """Testing output of refextract"""
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_identify_ibids_empty(self):
        r = identify_ibids("")
        self.assertEqual(r, ({}, {}, ''))

    def test_identify_ibids_simple(self):
        ref_line = u"""[46] E. Schrodinger, Sitzungsber. Preuss. Akad. Wiss. Phys. Math. Kl. 24, 418(1930); ibid, 3, 1(1931)"""
        r = identify_ibids(ref_line.upper())
        self.assertEqual(r, ({85: 4}, {85: u'IBID'}, u'[46] E. SCHRODINGER, SITZUNGSBER. PREUSS. AKAD. WISS. PHYS. MATH. KL. 24, 418(1930); ____, 3, 1(1931)'))


class TagNumerationTest(unittest.TestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_vol_page_year(self):
        "<vol>, <page> (<year>)"
        ref_line = u"""24, 418 (1930)"""
        r = tag_numeration(ref_line)
        self.assertEqual(r.strip(': '), u"<cds.VOL>24</cds.VOL> <cds.YR>(1930)</cds.YR> <cds.PG>418</cds.PG>")

    def test_vol_year_page(self):
        "<vol>, (<year>) <page> "
        ref_line = u"""24, (1930) 418"""
        r = tag_numeration(ref_line)
        self.assertEqual(r.strip(': '), u"<cds.VOL>24</cds.VOL> <cds.YR>(1930)</cds.YR> <cds.PG>418</cds.PG>")


class FindSectionTest(unittest.TestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_simple(self):
        sect = get_reference_section_beginning([
            "Hello",
            "References",
            "[1] Ref1"
        ])
        self.assertEqual(sect, {
            'marker': '[1]',
            'marker_pattern': u'^\\s*(?P<mark>\\[\\s*(?P<marknum>\\d+)\\s*\\])',
            'start_line': 1,
            'title_string': 'References',
            'title_marker_same_line': False,
            'how_found_start': 1,
        })

    def test_no_section(self):
        sect = get_reference_section_beginning("")
        self.assertEqual(sect, None)

    def test_no_title_via_brackets(self):
        sect = get_reference_section_beginning([
            "Hello",
            "[1] Ref1"
            "[2] Ref2"
        ])
        self.assertEqual(sect, {
            'marker': '[1]',
            'marker_pattern': u'(?P<mark>(?P<left>\\[)\\s*(?P<marknum>\\d+)\\s*(?P<right>\\]))',
            'start_line': 1,
            'title_string': None,
            'title_marker_same_line': False,
            'how_found_start': 2,
        })

    def test_no_title_via_dots(self):
        sect = get_reference_section_beginning([
            "Hello",
            "1. Ref1"
            "2. Ref2"
        ])
        self.assertEqual(sect, {
            'marker': '1.',
            'marker_pattern': u'(?P<mark>(?P<left>)\\s*(?P<marknum>\\d+)\\s*(?P<right>\\.))',
            'start_line': 1,
            'title_string': None,
            'title_marker_same_line': False,
            'how_found_start': 3,
        })

    def test_no_title_via_numbers(self):
        sect = get_reference_section_beginning([
            "Hello",
            "1 Ref1"
            "2 Ref2"
        ])
        self.assertEqual(sect, {
            'marker': '1',
            'marker_pattern': u'(?P<mark>(?P<left>)\\s*(?P<marknum>\\d+)\\s*(?P<right>))',
            'start_line': 1,
            'title_string': None,
            'title_marker_same_line': False,
            'how_found_start': 4,
        })

    def test_no_title_via_numbers2(self):
        sect = get_reference_section_beginning([
            "Hello",
            "1",
            "Ref1",
            "(3)",
            "2",
            "Ref2",
        ])
        self.assertEqual(sect, {
            'marker': '1',
            'marker_pattern': u'(?P<mark>(?P<left>)\\s*(?P<marknum>\\d+)\\s*(?P<right>))',
            'start_line': 1,
            'title_string': None,
            'title_marker_same_line': False,
            'how_found_start': 4,
        })


class SearchTest(unittest.TestCase):
    def setUp(self):
        setup_loggers(verbosity=9)
        from invenio import refextract_kbs
        self.old_override = refextract_kbs.CFG_REFEXTRACT_KBS_OVERRIDE
        refextract_kbs.CFG_REFEXTRACT_KBS_OVERRIDE = {}

    def tearDown(self):
        from invenio import refextract_kbs
        refextract_kbs.CFG_REFEXTRACT_KBS_OVERRIDE = self.old_override

    def test_not_recognized(self):
        field, pattern = search_from_reference('[1] J. Mars, oh hello')
        self.assertEqual(field, '')
        self.assertEqual(pattern, '')

    def test_report(self):
        field, pattern = search_from_reference('[1] J. Mars, oh hello, [hep-ph/0104088]')
        self.assertEqual(field, 'report')
        self.assertEqual(pattern, 'hep-ph/0104088')

    def test_journal(self):
        field, pattern = search_from_reference('[1] J. Mars, oh hello, Nucl.Phys. B76 (1974) 477-482')
        self.assertEqual(field, 'journal')
        self.assert_('Nucl' in pattern)
        self.assert_('B76' in pattern)
        self.assert_('477' in pattern)


if __name__ == '__main__':
    test_suite = make_test_suite(IbidTest, TagNumerationTest)
    run_test_suite(test_suite)
