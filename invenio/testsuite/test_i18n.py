# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2013 CERN.
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

"""Unit tests for messages library."""

__revision__ = "$Id$"

from invenio.base import i18n as messages
from invenio.base.globals import cfg
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class MessagesLanguageTest(InvenioTestCase):
    """
    Testing language-related functions
    """

    def test_lang_list_long_ordering(self):
        """messages - preserving language order"""
        lang_list_long = messages.language_list_long()

        # Preliminary test: same number of languages in both lists
        self.assertEqual(len(lang_list_long),
                         len(cfg['CFG_SITE_LANGS']))


        for lang, cfg_lang in zip(lang_list_long,
                                  cfg['CFG_SITE_LANGS']):
            self.assertEqual(lang[0],
                             cfg_lang)

    def test_wash_invalid_language(self):
        """messages - washing invalid language code"""
        self.assertEqual(messages.wash_language('python'),
                         cfg['CFG_SITE_LANG'])

    def test_wash_dashed_language(self):
        """messages - washing dashed language code (fr-ca)"""
        if 'fr' not in cfg['CFG_SITE_LANGS']:
            self.assertEqual(messages.wash_language('fr-ca'),
                             cfg['CFG_SITE_LANG'])
        else:
            self.assertEqual(messages.wash_language('fr-ca'),
                             'fr')

    def test_wash_languages(self):
        """messages - washing multiple languages"""
        if 'de' not in cfg['CFG_SITE_LANGS']:
            self.assertEqual(messages.wash_languages(['00',
                                                  '11',
                                                  '22',
                                                  'de']),
                         cfg['CFG_SITE_LANG'])
        else:
            self.assertEqual(messages.wash_languages(['00',
                                                  '11',
                                                  '22',
                                                  'de']),
                         'de')
        self.assertEqual(messages.wash_languages(['00',
                                                  '11',
                                                  '22']),
                         cfg['CFG_SITE_LANG'])

    def test_rtl_direction(self):
        """messages - right-to-left language detection"""
        # Arabic is right-to-left:
        self.assertEqual(messages.is_language_rtl('ar'), True)
        # English is not right-to-left:
        self.assertEqual(messages.is_language_rtl('en'), False)


TEST_SUITE = make_test_suite(MessagesLanguageTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
