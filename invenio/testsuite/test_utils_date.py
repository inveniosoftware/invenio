# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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


import datetime
import calendar
from time import strptime

import invenio.utils.date as dateutils
#FIXME
#from invenio.config import CFG_SITE_LANGS
CFG_SITE_LANGS = ['en', 'sk']
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

if 'en' in CFG_SITE_LANGS:
    lang_english_configured = True
else:
    lang_english_configured = False

if 'sk' in CFG_SITE_LANGS:
    lang_slovak_configured = True
else:
    lang_slovak_configured = False


def format_timestamp(t):
    return t.strftime("%Y-%m-%d %H:%M:%S")


def format_timestamp_tuples(t):
    return (
        format_timestamp(t[0][0]), format_timestamp(t[0][1]),
        format_timestamp(t[1][0]), format_timestamp(t[1][1])
    )


class ConvertFromDateCVSTest(InvenioTestCase):
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

class ConvertIntoDateGUITest(InvenioTestCase):
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

class ParseRuntimeLimitTest(InvenioTestCase):
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
            day += datetime.timedelta(days=1)
        present_from = datetime.datetime.combine(day, now.replace(hour=8))
        present_to = datetime.datetime.combine(day, now.replace(hour=16))
        if datetime.datetime.now() >= present_to:
            present_from += datetime.timedelta(days=7)
            present_to += datetime.timedelta(days=7)
        future_from = present_from + datetime.timedelta(days=7)
        future_to = present_to + datetime.timedelta(days=7)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_day_plus_times(self):
        """dateutils - parse runtime using a weekday plus a time range"""
        limit = 'Thursday 18:00-22:00'
        day = datetime.date.today()
        now = datetime.time()
        while day.weekday() != calendar.THURSDAY:
            day += datetime.timedelta(1)
        present_from = datetime.datetime.combine(day, now.replace(hour=18))
        present_to = datetime.datetime.combine(day, now.replace(hour=22))
        if datetime.datetime.now() >= present_to:
            present_from += datetime.timedelta(days=7)
            present_to += datetime.timedelta(days=7)
        future_from = present_from + datetime.timedelta(days=7)
        future_to = present_to + datetime.timedelta(days=7)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_day_abbr_only(self):
        """dateutils - parse runtime using just a weekday abbreviation"""
        limit = 'Tue'
        day = datetime.date.today()
        now = datetime.time()
        while day.weekday() != calendar.TUESDAY:
            day += datetime.timedelta(1)
        present_from = datetime.datetime.combine(day, now.replace(hour=0))
        present_to = present_from + datetime.timedelta(days=1)
        if datetime.datetime.now() >= present_to:
            present_from += datetime.timedelta(days=7)
            present_to += datetime.timedelta(days=7)
        future_from = present_from + datetime.timedelta(days=7)
        future_to = present_to + datetime.timedelta(days=7)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
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
        if present_to <= datetime.datetime.now():
            present_from += datetime.timedelta(days=1)
            present_to += datetime.timedelta(days=1)
        future_from = present_from + datetime.timedelta(days=1)
        future_to = present_to + datetime.timedelta(days=1)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit)
        self.assertEqual(expected, result)

class STRFTimeTest(InvenioTestCase):
    """
    Testing support of datest before 1900 for function strftime
    """
    def test_strftime_date_over_1900(self):
        test_date = "12.03.1908"
        expected = "Thu, 12 Mar 1908 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", strptime(test_date,"%d.%m.%Y"))
        self.assertEqual(expected, result)

    def test_strftime_date_under_1900(self):
        test_date = "3.1.1765"
        expected = "Thu, 03 Jan 1765 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", strptime(test_date,"%d.%m.%Y"))
        self.assertEqual(expected, result)

    def test_strftime_date_over_1900_object(self):
        test_date = "12.03.1908"
        expected = "Thu, 12 Mar 1908 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", datetime.date(1908,3,12))
        self.assertEqual(expected, result)

    def test_strftime_date_under_1900_object(self):
        test_date = "3.1.1765"
        expected = "Thu, 03 Jan 1765 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", datetime.date(1765,1,3))
        self.assertEqual(expected, result)

class DateTest(InvenioTestCase):
    """
    Testing creation of date object
    """
    def test_date_creation(self):
        expected = datetime.date.today()
        result = dateutils.date.today()
        self.assertEqual(expected, result)

    def test_date_strftime(self):
        expected = datetime.date.today().strftime("%a, %d %b %Y %H:%M:%S +0000")
        date_object = dateutils.date.today()
        result = date_object.strftime("%a, %d %b %Y %H:%M:%S +0000")
        self.assertEqual(expected, result)

class DateTimeTest(InvenioTestCase):
    """
    Testing creation of date object
    """
    def test_datetime_creation_after_1900(self):
        expected = datetime.datetime(1908,3,12,12,12,12)
        result = dateutils.datetime(1908,3,12,12,12,12)
        self.assertEqual(expected, result)

    def test_datetime_creation_before_1900(self):
        expected = datetime.datetime(1765,1,3,10,2,13)
        result = dateutils.datetime(1765,1,3,10,2,13)
        self.assertEqual(expected, result)

    def test_datetime_strftime_before_1900(self):
        new_datetime = dateutils.datetime(1765,1,3,10,2,13)
        expected = "Thu, 03 Jan 1765 10:02:13 +0000"
        result = new_datetime.strftime("%a, %d %b %Y %H:%M:%S +0000")
        self.assertEqual(expected, result)

TEST_SUITE = make_test_suite(ConvertFromDateCVSTest,
                             ConvertIntoDateGUITest,
                             ParseRuntimeLimitTest,
                             STRFTimeTest,
                             DateTest,
                             DateTimeTest
                             )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
