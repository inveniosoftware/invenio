# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

"""Unit tests for dateutils library."""

__revision__ = "$Id$"

import unittest
import dateutils

from invenio.config import CFG_SITE_LANGS
from invenio.testutils import make_test_suite, run_test_suite

if 'en' in CFG_SITE_LANGS:
    lang_english_configured = True
else:
    lang_english_configured = False

if 'sk' in CFG_SITE_LANGS:
    lang_slovak_configured = True
else:
    lang_slovak_configured = False

class ConvertFromDateCVSTest(unittest.TestCase):
    """
    Testing conversion of CVS dates.
    """

    def test_convert_good_cvsdate(self):
        """dateutils - conversion of good CVS dates"""
        # here we have to use '$' + 'Date...' here, otherwise the CVS
        # commit would erase this time format to put commit date:
        datecvs = "$" + "Date: 2006/09/21 10:07:22 $"
        datestruct_beginning_expected = (2006, 9, 21, 10, 7, 22)
        self.assertEqual(dateutils.convert_datecvs_to_datestruct(datecvs)[:6],
                         datestruct_beginning_expected)

        # here we have to use '$' + 'Date...' here, otherwise the CVS
        # commit would erase this time format to put commit date:
        datecvs = "$" + "Id: dateutils_tests.py,v 1.6 2007/02/14 18:33:02 tibor Exp $"
        datestruct_beginning_expected = (2007, 2, 14, 18, 33, 02)
        self.assertEqual(dateutils.convert_datecvs_to_datestruct(datecvs)[:6],
                         datestruct_beginning_expected)

    def test_convert_bad_cvsdate(self):
        """dateutils - conversion of bad CVS dates"""
        # here we have to use '$' + 'Date...' here, otherwise the CVS
        # commit would erase this time format to put commit date:
        datecvs = "$" + "Date: 2006/AA/21 10:07:22 $"
        datestruct_beginning_expected = (0, 0, 0, 0, 0, 0)
        self.assertEqual(dateutils.convert_datecvs_to_datestruct(datecvs)[:6],
                         datestruct_beginning_expected)

class ConvertIntoDateGUITest(unittest.TestCase):
    """
    Testing conversion into dategui with various languages.
    """

    if lang_english_configured:
        def test_convert_good_to_dategui_en(self):
            """dateutils - conversion of good text date into English GUI date"""
            datetext = "2006-07-16 18:36:01"
            dategui_en_expected = "16 Jul 2006, 18:36"
            dategui_en = dateutils.convert_datetext_to_dategui(datetext,
                                                               ln='en')
            self.assertEqual(dategui_en, dategui_en_expected)

    if lang_slovak_configured:
        def test_convert_good_to_dategui_sk(self):
            """dateutils - conversion of good text date into Slovak GUI date"""
            datetext = "2006-07-16 18:36:01"
            dategui_sk_expected = "16 júl 2006, 18:36"
            dategui_sk = dateutils.convert_datetext_to_dategui(datetext,
                                                               ln='sk')
            self.assertEqual(dategui_sk, dategui_sk_expected)

    if lang_english_configured:
        def test_convert_bad_to_dategui_en(self):
            """dateutils - conversion of bad text date into English GUI date"""
            datetext = "2006-02-AA 18:36:01"
            dategui_sk_expected = "N/A"
            dategui_sk = dateutils.convert_datetext_to_dategui(datetext,
                                                               ln='en')
            self.assertEqual(dategui_sk, dategui_sk_expected)

    if lang_slovak_configured:
        def test_convert_bad_to_dategui_sk(self):
            """dateutils - conversion of bad text date into Slovak GUI date"""
            datetext = "2006-02-AA 18:36:01"
            dategui_sk_expected = "nepríst."
            dategui_sk = dateutils.convert_datetext_to_dategui(datetext,
                                                               ln='sk')
            self.assertEqual(dategui_sk, dategui_sk_expected)

TEST_SUITE = make_test_suite(ConvertFromDateCVSTest,
                             ConvertIntoDateGUITest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
