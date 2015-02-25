# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

__revision__ = "$Id$"

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

EXTRACT_NOTES_FROM_COMMENT = \
    lazy_import(
        'invenio.modules.annotations.noteutils:extract_notes_from_comment')
GET_NOTE_TITLE = \
    lazy_import('invenio.modules.annotations.noteutils:get_note_title')
PREPARE_NOTES = \
    lazy_import('invenio.modules.annotations.noteutils:prepare_notes')


class TestExtractNotes(InvenioTestCase):
    """Tests for comment note extraction"""

    def test_extract_notes_from_comment(self):
        """Tests note extraction from single comments"""
        fun = EXTRACT_NOTES_FROM_COMMENT

        # marker collection tests; no corners or invalids here, just
        # [MARKER.LOCATION(S): BODY]
        self.assert_(fun('P.1: lorem ipsum dolor', True) ==
                     [{'where': {"marker": 'P.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('P.1,2,3: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'P.1,2,3'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('F.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'F.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('F.1a: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'F.1a'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('F.1,2a,3: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'F.1,2a,3'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('G: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'G'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('L.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'L.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('E.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'E.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('E.1,2,3: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'E.1,2,3'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('T.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'T.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('T.1,2,3: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'T.1,2,3'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('S.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'S.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('S.1.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'S.1.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('S.1a: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'S.1a'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('S.1,2a,3: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'S.1,2a,3'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('PP.1: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'PP.1'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('PP.1,2: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'PP.1,2'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('P.1: F.2: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'P.1_F.2'},
                       'what': 'lorem ipsum dolor'}])
        self.assert_(fun('P.10: R.[Ellis98]: lorem ipsum dolor', True) ==
                     [{'where': {'marker': 'P.10_R.[Ellis98]'},
                       'what': 'lorem ipsum dolor'}])

        # corner cases
        self.assert_(fun('P.1: A comment on page 1\n\nsome bla bla\nF.12: A comment on figure 12',
                         True) ==
                     [{'where': {'marker': 'P.1'},
                       'what': 'A comment on page 1'},
                      {'where': {'marker': 'F.12'},
                       'what': 'A comment on figure 12'}])
        self.assert_(fun('This comment has no notes', True) == [])
        self.assert_(
            fun('P.1:A comment on page 1\nF.12: A comment on figure 12',
                True) ==
            [{'where': {'marker': 'P.1'},
              'what': 'A comment on page 1'},
             {'where': {'marker': 'F.12'},
              'what': 'A comment on figure 12'}])
        self.assert_(fun('bla bla\nF.123a: A comment on a subfigure', True) ==
                     [{'where': {'marker': 'F.123a'},
                       'what': 'A comment on a subfigure'}])
        self.assert_(fun('', True) == [])

        # invalid notes tests
        self.assert_(fun('P.1 An invalid page marker (no column)\n\nF.123a: A comment on a subfigure', True) ==
                     [{'where': {'marker': 'F.123a'},
                       'what': 'A comment on a subfigure'}])
        # legacy interval specification
        self.assert_(len(fun('P.1-3: lorem ipsum dolor', True)) == 0)
        self.assert_(len(fun('P.1-3,4: lorem ipsum dolor', True)) == 0)
        self.assert_(len(fun('PP.1-3: lorem ipsum dolor', True)) == 0)
        self.assert_(len(fun('L.1-3: lorem ipsum dolor', True)) == 0)
        self.assert_(len(fun('F.1-3: lorem ipsum dolor', True)) == 0)

        # FIXME: tests with real CmtRECORDCOMMENT objects

    def test_get_note_title(self):
        """Test note title expansion"""
        fun = GET_NOTE_TITLE
        self.assert_(fun('P.1') == 'Page 1')
        self.assert_(fun('F.2a') == 'Figure 2a')
        self.assert_(fun('G') == 'General aspect')
        self.assert_(fun('X') is "Unknown")
        self.assert_(fun('E') == 'Equation')

    def test_prepare_notes(self):
        """Test note tree preparation"""
        tree = PREPARE_NOTES([
            {'where': {'marker': 'P.1'}, 'what': 'lorem'},
            {'where': {'marker': 'P.1_F.2a'}, 'what': 'ipsum'},
            {'where': {'marker': 'G'}, 'what': 'dolor'},
            {'where': {'marker': 'G'}, 'what': 'elit'},
            {'where': {'marker': 'G_T.4'}, 'what': 'adipisicing'},
            {'where': {'marker': 'E.4'}, 'what': 'sit amet'},
            {'where': {'marker': 'E.4'}, 'what': 'consectetur'}])

        self.assert_(tree['P.1']['leaf'][0]['what'] == 'lorem')
        self.assert_(len(tree['E.4']['leaf']) == 2)
        self.assert_(tree['E.4']['leaf'][0]['what'] == 'sit amet')
        self.assert_(tree['E.4']['leaf'][1]['what'] == 'consectetur')
        self.assert_(tree['G']['path'] == 'G')
        self.assert_(tree['P.1']['F.2a']['path'] == 'P.1_F.2a')
        self.assert_(tree['P.1']['F.2a']['leaf'][0]['what'] == 'ipsum')
        self.assert_(len(tree['G']['leaf']) == 2)
        self.assert_(tree['G']['T.4']['path'] == 'G_T.4')

    def test_get_original_comment(self):
        # FIXME: implement
        pass

TEST_SUITE = make_test_suite(TestExtractNotes)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
