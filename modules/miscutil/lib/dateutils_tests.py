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
import datetime
import time
import calendar
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

class ParseRuntimeLimitTest(unittest.TestCase):
    """
    Testing the runtime limit parser used by BibSched to determine task
    runtimes and also by the errorlib.register_emergency function to parse the
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES configuration
    """
    def test_parse_runtime_limit_day_abbr_plus_times(self):
        """dateutils - parse runtime using a weekday abbreviation plus a time range"""
        limit = 'Sun 8:00-16:00'
        day = datetime.date.today()
        now = datetime.time()
        while day.weekday() != calendar.SUNDAY:
            day -= datetime.timedelta(1)
        present_from = datetime.datetime.combine(day, now.replace(hour=8))
        present_to = datetime.datetime.combine(day, now.replace(hour=16))
        future_from = present_from + datetime.timedelta(days=7)
        future_to = present_to + datetime.timedelta(days=7)
        expected = (
            (time.mktime(present_from.timetuple()), time.mktime(present_to.timetuple())),
            (time.mktime(future_from.timetuple()), time.mktime(future_to.timetuple())),
            )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_day_plus_times(self):
        """dateutils - parse runtime using a weekday plus a time range"""
        limit = 'Thursday 18:00-22:00'
        day = datetime.date.today()
        now = datetime.time()
        while day.weekday() != calendar.THURSDAY:
            day -= datetime.timedelta(1)
        present_from = datetime.datetime.combine(day, now.replace(hour=18))
        present_to = datetime.datetime.combine(day, now.replace(hour=22))
        future_from = present_from + datetime.timedelta(days=7)
        future_to = present_to + datetime.timedelta(days=7)
        expected = (
            (time.mktime(present_from.timetuple()), time.mktime(present_to.timetuple())),
            (time.mktime(future_from.timetuple()), time.mktime(future_to.timetuple())),
            )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_day_abbr_only(self):
        """dateutils - parse runtime using just a weekday abbreviation"""
        limit = 'Tue'
        day = datetime.date.today()
        now = datetime.time()
        while day.weekday() != calendar.TUESDAY:
            day -= datetime.timedelta(1)
        present_from = datetime.datetime.combine(day, now.replace(hour=0))
        present_to = present_from + datetime.timedelta(days=1)
        future_from = present_from + datetime.timedelta(days=7)
        future_to = present_to + datetime.timedelta(days=7)
        expected = (
            (time.mktime(present_from.timetuple()), time.mktime(present_to.timetuple())),
            (time.mktime(future_from.timetuple()), time.mktime(future_to.timetuple())),
            )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_times_only(self):
        """dateutils - parse runtime using just a time range"""
        limit = '06:00-18:00'
        day = datetime.date.today()
        now = datetime.time()
        present_from = datetime.datetime.combine(day, now.replace(hour=6))
        present_to = datetime.datetime.combine(day, now.replace(hour=18))
        future_from = present_from + datetime.timedelta(days=1)
        future_to = present_to + datetime.timedelta(days=1)
        expected = (
            (time.mktime(present_from.timetuple()), time.mktime(present_to.timetuple())),
            (time.mktime(future_from.timetuple()), time.mktime(future_to.timetuple())),
            )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

TEST_SUITE = make_test_suite(ConvertFromDateCVSTest,
                             ConvertIntoDateGUITest,
                             ParseRuntimeLimitTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
