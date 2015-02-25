# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013 CERN.
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

"""BibFormat - Unit Test Suite"""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio.base.wrappers import lazy_import

words_start_with_patterns = lazy_import('invenio.modules.formatter.utils:words_start_with_patterns')
cut_out_snippet_core_creation = lazy_import('invenio.modules.formatter.utils:cut_out_snippet_core_creation')


class WordsStartsWithPatternTest(InvenioTestCase):
    """Test for words start with pattern functionality"""

    def test_word_starts_with_single_pattern(self):
        """bibformat - word starts with single pattern"""
        self.assertEqual((False, 0), words_start_with_patterns(['thi'], ['this']))
        self.assertEqual((True, 0), words_start_with_patterns(['this'], ['this']))
        self.assertEqual((True, 0), words_start_with_patterns(['This'], ['this']))
        self.assertEqual((True, 0), words_start_with_patterns(['this'], ['tHis']))
        self.assertEqual((True, 0), words_start_with_patterns(['This'], ['tHis']))
        self.assertEqual((True, 0), words_start_with_patterns(['Thiss'], ['tHis']))

    def test_word_starts_with_multi_pattern(self):
        """bibformat - word starts with multi pattern"""
        self.assertEqual((False, 0), words_start_with_patterns(['thi'], ['this', 'is', 'a']))
        self.assertEqual((False, 0), words_start_with_patterns(['i'], ['this', 'is', 'a']))
        self.assertEqual((True, 0), words_start_with_patterns(['this'], ['this', 'is', 'a']))
        self.assertEqual((True, 0), words_start_with_patterns(['is'], ['this', 'is', 'a']))

    def test_words_start_with_single_pattern(self):
        """bibformat - words start with single pattern"""
        self.assertEqual((True, 0), words_start_with_patterns(['this', 'is'], ['thi']))
        self.assertEqual((False, 0), words_start_with_patterns(['thi', 'this'], ['this']))

    def test_words_start_with_multi_pattern(self):
        """bibformat - words start with multi pattern"""
        # Only the first word is considered
        self.assertEqual((True, 0), words_start_with_patterns(['this', 'is'], ['this', 'it']))
        self.assertEqual((True, 0), words_start_with_patterns(['this', 'is'], ['it', 'thi']))
        self.assertEqual((False, 0), words_start_with_patterns(['this', 'is'], ['it', 'if']))
        self.assertEqual((False, 0), words_start_with_patterns(['this', 'is'], ['is', 'if']))

    def test_words_start_with_phrase(self):
        """bibformat - words start with phrase"""
        self.assertEqual((True, 2), words_start_with_patterns(['this', 'is', 'a', 'test'], ['this is a']))
        self.assertEqual((False, 0), words_start_with_patterns(['this', 'is', 'a', 'test'], ['no I do not]']))
        self.assertEqual((True, 2), words_start_with_patterns(['this', 'is', 'a', 'test'], ['no I do not]', 'this is a']))
        self.assertEqual((False, 0), words_start_with_patterns(['this', 'is'], ['no I do not', 'this is a']))


class SnippetCutOutCoreCreation(InvenioTestCase):
    """Test for snippet cut out core creation"""

    _words = dict()
    _words[0] = ['CERN', 'LIBRARIES,', 'GENEVA', 'SCAN-0005061', 'Development', 'of', 'Photon', 'Beam', 'Diagnostics',
                 'for', 'VUV', 'Radiation', 'from', 'a', 'SASE', 'FEL', 'R.', 'Treusch', '1,', 'T.', 'Lokajczyk,', 'W.',
                 'Xu', '2,', 'U.', 'Jastrow,', 'U.', 'Hahn,', 'Abstract', 'L.', 'Bittner', 'and', 'J.', 'Feldhaus',
                 'HASYLAB', 'at', 'DESY,', 'Notkcstr.', '85,', 'D\xe2\x80\x94226`U3', 'Hamburg,', 'Germany', 'For',
                 'the', 'proof-of-principle', 'experiment', 'of', 'self-amplified', 'spontaneous', 'emission', '[SASE)',
                 'at', 'short', 'wavelengths', 'on', 'the', 'VUV', 'FEL', 'at', 'DESY', 'a', 'multi-facetted', 'photon',
                 'beam', 'diagnostics', 'experiment', 'has', 'been', 'developed', 'employing', 'new', 'detection',
                 'concepts', 'to', 'measure', 'all', 'SASE', 'specific', 'properties', 'on', 'a', 'single', 'pulse',
                 'basis.', 'The', 'present', 'setup', 'includes', 'instrumentation', 'for', 'the', 'measurement', 'of',
                 'the', 'energy', 'and', 'the', 'angular', 'and', 'spectral', 'distribution', 'of', 'individual', 'photon',
                 'pulses.', 'Different', 'types', 'of', 'photon', 'detectors', 'such', 'as', 'PtSi-photodiodes', 'and']

    def test_term_cut_out(self):
        """bibformat - term snippet cut out core creation"""
        self.assertEqual(('This', 0, 0), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['This'], 50))
        self.assertEqual(('This is a test', 0, 3), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['This', 'test'], 50))
        self.assertEqual(('is', 1, 1), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['is'], 50))
        self.assertEqual(('is a new', 1, 3), cut_out_snippet_core_creation(['This', 'is', 'a', 'new', 'test'], ['is', 'new'], 50))
        self.assertEqual(('', -1, -1), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['new'], 50))

        self.assertEqual(('of', 5, 5), cut_out_snippet_core_creation(self._words[0], ['of'], 100))

    def test_phrase_cut_out(self):
        """bibformat - phrase snippet cut out core creation"""
        self.assertEqual(('This is', 0, 1), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['This is'], 50))
        self.assertEqual(('This is a', 0, 2), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['This is a'], 50))
        self.assertEqual(('', -1, -1), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['This not'], 50))
        self.assertEqual(('is a', 1, 2), cut_out_snippet_core_creation(['This', 'is', 'a', 'test'], ['is a'], 50))
        self.assertEqual(('of the', 92, 93), cut_out_snippet_core_creation(self._words[0], ['of the'], 100))


TEST_SUITE = make_test_suite(WordsStartsWithPatternTest,
                             SnippetCutOutCoreCreation,
                             )


if __name__ == '__main__':
    run_test_suite(TEST_SUITE)
