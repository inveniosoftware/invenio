# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013, 2014 CERN.
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

"""
The Refextract unit test suite

The tests will not modifiy the database.
"""


import re

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
# Import the minimal necessary methods and variables needed to run Refextract
refextract_re = lazy_import('invenio.legacy.refextract.regexs')
tag_arxiv = lazy_import('invenio.legacy.refextract.tag:tag_arxiv')
setup_loggers = lazy_import('invenio.legacy.docextract.utils:setup_loggers')
search_from_reference = lazy_import('invenio.legacy.refextract.api:search_from_reference')
extract_journal_reference = lazy_import('invenio.legacy.refextract.api:extract_journal_reference')
rebuild_reference_lines = lazy_import('invenio.legacy.refextract.text:rebuild_reference_lines')


class ReTest(InvenioTestCase):
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


class IbidTest(InvenioTestCase):
    """Testing output of refextract"""
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_identify_ibids_empty(self):
        from invenio.legacy.refextract.tag import identify_ibids
        r = identify_ibids("")
        self.assertEqual(r, ({}, ''))

    def test_identify_ibids_simple(self):
        from invenio.legacy.refextract.tag import identify_ibids
        ref_line = u"""[46] E. Schrodinger, Sitzungsber. Preuss. Akad. Wiss. Phys. Math. Kl. 24, 418(1930); ibid, 3, 1(1931)"""
        r = identify_ibids(ref_line.upper())
        self.assertEqual(r, ({85: u'IBID'}, u'[46] E. SCHRODINGER, SITZUNGSBER. PREUSS. AKAD. WISS. PHYS. MATH. KL. 24, 418(1930); ____, 3, 1(1931)'))


class FindNumerationTest(InvenioTestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_vol_page_year(self):
        "<vol>, <page> (<year>)"
        from invenio.legacy.refextract.tag import find_numeration
        ref_line = u"""24, 418 (1930)"""
        r = find_numeration(ref_line)
        self.assertEqual(r['volume'], u"24")
        self.assertEqual(r['year'], u"1930")
        self.assertEqual(r['page'], u"418")

    def test_vol_year_page(self):
        "<vol>, (<year>) <page> "
        from invenio.legacy.refextract.tag import find_numeration
        ref_line = u"""24, (1930) 418"""
        r = find_numeration(ref_line)
        self.assertEqual(r['volume'], u"24")
        self.assertEqual(r['year'], u"1930")
        self.assertEqual(r['page'], u"418")

    def test_year_title_volume_page(self):
        "<year>, <title> <vol> <page> "
        from invenio.legacy.refextract.tag import find_numeration_more
        ref_line = u"""1930 <cds.JOURNAL>J.Phys.</cds.JOURNAL> 24, 418"""
        r = find_numeration_more(ref_line)
        self.assertEqual(r['volume'], u"24")
        self.assertEqual(r['year'], u"1930")
        self.assertEqual(r['page'], u"418")

    def test_journal_extract(self):
        r = extract_journal_reference("Science Vol. 338 no. 6108 (2012) pp. 773-775")
        self.assertEqual(r['year'], u'2012')
        self.assertEqual(r['volume'], u'338')
        self.assertEqual(r['page'], u'773-775')
        self.assertEqual(r['title'], u'Science')


class FindSectionTest(InvenioTestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_simple(self):
        from invenio.legacy.refextract.find import get_reference_section_beginning
        sect = get_reference_section_beginning([
            "Hello",
            "References",
            "[1] Ref1"
        ])
        self.assertEqual(sect, {
            'marker': '[1]',
            'marker_pattern': u'\\s*(?P<mark>\\[\\s*(?P<marknum>\\d+)\\s*\\])',
            'start_line': 1,
            'title_string': 'References',
            'title_marker_same_line': False,
            'how_found_start': 1,
        })

    def test_no_section(self):
        from invenio.legacy.refextract.find import get_reference_section_beginning
        sect = get_reference_section_beginning("")
        self.assertEqual(sect, None)

    def test_no_title_via_brackets(self):
        from invenio.legacy.refextract.find import get_reference_section_beginning
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
        from invenio.legacy.refextract.find import get_reference_section_beginning
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
        from invenio.legacy.refextract.find import get_reference_section_beginning
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
        from invenio.legacy.refextract.find import get_reference_section_beginning
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


class SearchTest(InvenioTestCase):
    def setUp(self):
        setup_loggers(verbosity=1)
        from invenio.legacy.refextract import kbs as refextract_kbs
        self.old_override = refextract_kbs.CFG_REFEXTRACT_KBS_OVERRIDE
        refextract_kbs.CFG_REFEXTRACT_KBS_OVERRIDE = {}

    def tearDown(self):
        from invenio.legacy.refextract import kbs as refextract_kbs
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

    def test_not_recognized_unicode_1(self):
        field, pattern = search_from_reference(u'País Valencià')
        self.assertEqual(field, '')
        self.assertEqual(pattern, '')

    def test_not_recognized_unicode_2(self):
        field, pattern = search_from_reference(u'Capellà Pere')
        self.assertEqual(field, '')
        self.assertEqual(pattern, '')


class RebuildReferencesTest(InvenioTestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_simple(self):
        marker_pattern = ur"^\s*(?P<mark>\[\s*(?P<marknum>\d+)\s*\])"
        refs = [
            u"[1] hello",
            u"hello2",
            u"[2] foo",
        ]
        rebuilt_refs = rebuild_reference_lines(refs, marker_pattern)
        self.assertEqual(rebuilt_refs, [
            u"[1] hello hello2",
            u"[2] foo",
        ])

    # def test_pagination_removal(self):
    #     marker_pattern = ur"^\s*(?P<mark>\[\s*(?P<marknum>\d+)\s*\])"
    #     refs = [
    #         u"[1] hello",
    #         u"hello2",
    #         u"[42]",
    #         u"[2] foo",
    #     ]
    #     rebuilt_refs = rebuild_reference_lines(refs, marker_pattern)
    #     self.assertEqual(rebuilt_refs, [
    #         u"[1] hello hello2",
    #         u"[2] foo",
    #     ])

    def test_pagination_non_removal(self):
        marker_pattern = ur"^\s*(?P<mark>\[\s*(?P<marknum>\d+)\s*\])"
        refs = [
            u"[1] hello",
            u"hello2",
            u"[2]",
            u"foo",
        ]
        rebuilt_refs = rebuild_reference_lines(refs, marker_pattern)
        self.assertEqual(rebuilt_refs, [
            u"[1] hello hello2",
            u"[2] foo",
        ])

    def test_2_lines_together(self):
        marker_pattern = ur"\s*(?P<mark>\[\s*(?P<marknum>\d+)\s*\])"
        refs = [
            u"[1] hello",
            u"hello2 [2] foo",
        ]
        rebuilt_refs = rebuild_reference_lines(refs, marker_pattern)
        self.assertEqual(rebuilt_refs, [
            u"[1] hello hello2",
            u"[2] foo",
        ])


class tagArxivTest(InvenioTestCase):
    def setUp(self):
        setup_loggers(verbosity=1)

    def test_4_digits(self):
        ref_line = u"""{any prefix}arXiv:1003.1111{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1003.1111</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_suffix(self):
        ref_line = u"""{any prefix}arXiv:1104.2222 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1104.2222 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits(self):
        ref_line = u"""{any prefix}arXiv:1303.33333{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1303.33333</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_2012(self):
        ref_line = u"""{any prefix}arXiv:1203.33333{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}arXiv:1203.33333{any postfix}")

    def test_5_digits_suffix(self):
        ref_line = u"""{any prefix}arXiv:1304.44444 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1304.44444 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_version(self):
        ref_line = u"""{any prefix}arXiv:1003.1111v9{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1003.1111</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_suffix_version(self):
        ref_line = u"""{any prefix}arXiv:1104.2222v9 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1104.2222 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_version(self):
        ref_line = u"""{any prefix}arXiv:1303.33333v9{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1303.33333</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_suffix_version(self):
        ref_line = u"""{any prefix}arXiv:1304.44444v9 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1304.44444 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_new(self):
        ref_line = u"""{any prefix}9910.1234{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:9910.1234</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_suffix_new(self):
        ref_line = u"""{any prefix}9910.1234 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:9910.1234 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_new(self):
        ref_line = u"""{any prefix}1310.12345{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1310.12345</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_suffix_new(self):
        ref_line = u"""{any prefix}1310.12345 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1310.12345 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_version_new(self):
        ref_line = u"""{any prefix}9910.1234v9{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:9910.1234</cds.REPORTNUMBER>{any postfix}")

    def test_4_digits_suffix_version_new(self):
        ref_line = u"""{any prefix}9910.1234v9 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:9910.1234 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_version_new(self):
        ref_line = u"""{any prefix}1310.12345v9{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1310.12345</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_suffix_version_new(self):
        ref_line = u"""{any prefix}1310.12345v9 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}<cds.REPORTNUMBER>arXiv:1310.12345 [physics.ins-det]</cds.REPORTNUMBER>{any postfix}")

    def test_5_digits_suffix_version_new_2012(self):
        ref_line = u"""{any prefix}1210.12345v9 [physics.ins-det]{any postfix}"""
        r = tag_arxiv(ref_line)
        self.assertEqual(r.strip(': '), u"{any prefix}1210.12345v9 [physics.ins-det]{any postfix}")


TEST_SUITE = make_test_suite(ReTest,
                             IbidTest,
                             FindNumerationTest,
                             FindSectionTest,
                             SearchTest,
                             RebuildReferencesTest)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
