# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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

"""Unit tests for dateutils library."""

__revision__ = "$Id$"


import datetime
import calendar
import time
import os

from time import mktime, strptime, tzset, struct_time

import invenio.utils.date as dateutils
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

# FIXME check if the languages are configured
lang_english_configured = True
lang_slovak_configured = True

def format_timestamp(t):
    return t.strftime("%Y-%m-%d %H:%M:%S")


def format_timestamp_tuples(t):
    return (
        format_timestamp(t[0][0]), format_timestamp(t[0][1]),
        format_timestamp(t[1][0]), format_timestamp(t[1][1])
    )


class ConvertFromDateCVSTest(InvenioTestCase):
    """Testing conversion of CVS dates."""

    def test_convert_good_cvsdate(self):
        """dateutils - conversion of good CVS dates"""
        # here we have to use '$' + 'Date...' here, otherwise the CVS
        # commit would erase this time format to put commit date:
        datecvs = "$" + "Date: 2006/09/21 10:07:22 $"
        datestruct_beginning_expected = (2006, 9, 21, 10, 7, 22)
        self.assertEqual(dateutils.convert_datecvs_to_datestruct(datecvs)[:6],
                         datestruct_beginning_expected)

        datecvs = "$Id: dateutils_tests.py,v 1.6 2007/02/14 18:33:02 tibor " \
                  "Exp $"
        datestruct_beginning_expected = (2007, 2, 14, 18, 33, 2)
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
    """Testing conversion into dategui with various languages."""
    if lang_english_configured:
        def test_convert_good_to_dategui_en(self):
            """dateutils - conversion of good text date into English GUI date
            """
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
            dategui_en_expected = "N/A"
            dategui_en = dateutils.convert_datetext_to_dategui(datetext,
                                                               ln='en')
            self.assertEqual(dategui_en, dategui_en_expected)

    if lang_slovak_configured:
        def test_convert_bad_to_dategui_sk(self):
            """dateutils - conversion of bad text date into Slovak GUI date"""
            from invenio.base.i18n import gettext_set_language
            ln = 'sk'
            _ = gettext_set_language(ln)
            datetext = "2006-02-AA 18:36:01"
            dategui_sk_expected = _('N/A')
            dategui_sk = dateutils.convert_datetext_to_dategui(datetext,
                                                               ln=ln)
            self.assertEqual(dategui_sk, dategui_sk_expected)


class ConvertIntoDateStructTest(InvenioTestCase):
    """Testing conversion into date struct"""
    def test_convert_datetext_to_datestruct(self):
        datetext = '2005-11-16 15:11:57'
        expected = struct_time((2005, 11, 16, 15, 11, 57, 2, 320, -1))
        result = dateutils.convert_datetext_to_datestruct(datetext)
        self.assertEqual(expected, result)


class ConvertDateStructIntoGUI(InvenioTestCase):
    """Testing convertion from date struct to date GUI"""
    if lang_english_configured:
        def test_convert_datestruct_to_dategui_en(self):
            expected = '16 Nov 2005, 15:11'
            struct = struct_time((2005, 11, 16, 15, 11, 44, 2, 320, 0))
            result = dateutils.convert_datestruct_to_dategui(struct, "en")
            self.assertEqual(expected, result)

        def test_convert_incomplete_datestruct_to_dategui_en(self):
            expected = 'N/A'
            struct = struct_time((0, 0, 0, 15, 11, 44, 2, 320, 0))
            result = dateutils.convert_datestruct_to_dategui(struct, "en")
            self.assertEqual(expected, result)

        def test_convert_buggy_datestruct_to_dategui_en(self):
            expected = 'N/A'
            struct = struct_time((-1, 11, 16, 15, 11, 44, 2, 320, 0))
            result = dateutils.convert_datestruct_to_dategui(struct, "en")
            self.assertEqual(expected, result)

    if lang_slovak_configured:
        def test_convert_datestruct_to_dategui_sk(self):
            expected = '16 júl 2005, 15:11'
            struct = struct_time((2005, 7, 16, 15, 11, 44, 2, 320, 1))
            result = dateutils.convert_datestruct_to_dategui(struct, "sk")
            self.assertEqual(expected, result)

        def test_convert_incomplete_datestruct_to_dategui_sk(self):
            expected = 'nepríst.'
            struct = struct_time((0, 11, 16, 15, 11, 44, 2, 320, 0))
            result = dateutils.convert_datestruct_to_dategui(struct, "sk")
            self.assertEqual(expected, result)

        def test_convert_buggy_datestruct_to_dategui_sk(self):
            expected = 'nepríst.'
            struct = struct_time((-1, 11, 16, 15, 11, 44, 2, 320, 0))
            result = dateutils.convert_datestruct_to_dategui(struct, "sk")
            self.assertEqual(expected, result)


class ParseRuntimeLimitTest(InvenioTestCase):
    """Testing the runtime limit parser used by BibSched to determine task
    runtimes and also by the errorlib.register_emergency function to parse the
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES configuration
    """
    def test_parse_runtime_limit_day_abbr_plus_times(self):
        """dateutils - parse runtime using a weekday abbreviation plus a time
        range
        """
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

    def test_parse_runtime_limit_days_only(self):
        """dateutils - parse runtime using just inside a week range"""
        limit = 'Mon-Fri'
        now = datetime.datetime(year=2000, month=1, day=3)
        present_from = now
        present_to = now + datetime.timedelta(days=1)
        future_from = present_from + datetime.timedelta(days=1)
        future_to = present_to + datetime.timedelta(days=1)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit, now=now)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_days_only_2(self):
        """dateutils - parse runtime using just outside week range"""
        limit = 'Mon-Fri'
        now = datetime.datetime(year=2000, month=1, day=1)
        present_from = now + datetime.timedelta(days=2)
        present_to = now + datetime.timedelta(days=3)
        future_from = present_from + datetime.timedelta(days=1)
        future_to = present_to + datetime.timedelta(days=1)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit, now=now)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_days_only_3(self):
        """dateutils - parse runtime using just at the end of a week range"""
        limit = 'Mon-Fri'
        now = datetime.datetime(year=2000, month=1, day=7)
        present_from = now
        present_to = now + datetime.timedelta(days=1)
        future_from = now + datetime.timedelta(days=3)
        future_to = now + datetime.timedelta(days=4)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit, now=now)
        self.assertEqual(expected, result)

    def test_parse_runtime_limit_days_times(self):
        """dateutils - parse runtime using just a week range"""
        limit = 'Mon-Fri 06:00-18:00'
        now = datetime.datetime(year=2000, month=1, day=3)
        day = now.date()
        t = now.time()
        present_from = datetime.datetime.combine(day, t.replace(hour=6))
        present_to = datetime.datetime.combine(day, t.replace(hour=18))
        future_from = present_from + datetime.timedelta(days=1)
        future_to = present_to + datetime.timedelta(days=1)
        expected = (
            (present_from, present_to),
            (future_from, future_to),
        )
        result = dateutils.parse_runtime_limit(limit, now=now)
        self.assertEqual(expected, result)

class STRFTimeTest(InvenioTestCase):
    """Testing support of datest before 1900 for function strftime"""
    def test_strftime_date_over_1900(self):
        test_date = "12.03.1908"
        expected = "Thu, 12 Mar 1908 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                    strptime(test_date, "%d.%m.%Y"))
        self.assertEqual(expected, result)

    def test_strftime_date_under_1900(self):
        test_date = "3.1.1765"
        expected = "Thu, 03 Jan 1765 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", strptime(test_date, "%d.%m.%Y"))
        self.assertEqual(expected, result)

    def test_strftime_date_over_1900_object(self):
        expected = "Thu, 12 Mar 1908 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", datetime.date(1908, 3, 12))
        self.assertEqual(expected, result)

    def test_strftime_date_under_1900_object(self):
        expected = "Thu, 03 Jan 1765 00:00:00 +0000"
        result = dateutils.strftime("%a, %d %b %Y %H:%M:%S +0000", datetime.date(1765, 1, 3))
        self.assertEqual(expected, result)


class DateTest(InvenioTestCase):
    """Testing creation of date object"""
    def test_date_creation(self):
        expected = datetime.date.today()
        result = dateutils.date.today()
        self.assertEqual(expected, result)

    def test_date_strftime(self):
        expected = datetime.date.today().strftime("%a, %d %b %Y %H:%M:%S "
                                                  "+0000")
        date_object = dateutils.date.today()
        result = date_object.strftime("%a, %d %b %Y %H:%M:%S +0000")
        self.assertEqual(expected, result)


class DateTimeTest(InvenioTestCase):
    """Testing creation of date object"""
    def test_datetime_creation_after_1900(self):
        expected = datetime.datetime(1908, 3, 12, 12, 12, 12)
        result = dateutils.datetime(1908, 3, 12, 12, 12, 12)
        self.assertEqual(expected, result)

    def test_datetime_creation_before_1900(self):
        expected = datetime.datetime(1765, 1, 3, 10, 2, 13)
        result = dateutils.datetime(1765, 1, 3, 10, 2, 13)
        self.assertEqual(expected, result)

    def test_datetime_strftime_before_1900(self):
        new_datetime = dateutils.datetime(1765, 1, 3, 10, 2, 13)
        expected = "Thu, 03 Jan 1765 10:02:13 +0000"
        result = new_datetime.strftime("%a, %d %b %Y %H:%M:%S +0000")
        self.assertEqual(expected, result)

    def test_datatime_combine(self):
        expected = datetime.datetime(1987, 6, 5, 4, 3, 2, 1, None)
        result = dateutils.datetime.combine(datetime.date(1987, 6, 5),
                                            datetime.time(4, 3, 2, 1))
        self.assertEqual(expected, result)

    def test_datetime_date(self):
        expected = datetime.date(1987, 6, 5)
        dt = dateutils.datetime(1987, 6, 5, 4, 3, 2, 1, None)
        self.assertEqual(expected, dt.date())


class LocaltimeToUTCTest(InvenioTestCase):
    """
    Testing transformation between localtime to utc time
    """
    def setUp(self):
        if 'TZ' in os.environ:
            self.old_timezone = os.environ['TZ']
        else:
            self.old_timezone = None

    def tearDown(self):
        if self.old_timezone is None:
            del os.environ['TZ']
        else:
            os.environ['TZ'] = self.old_timezone
        tzset()

    def test_localtime_to_utc_cet(self):
        os.environ['TZ'] = 'Europe/Oslo'
        tzset()

        expected = "2012-06-12T14:15:00Z"
        result = dateutils.localtime_to_utc("2012-06-12 16:15:00")
        self.assertEqual(expected, result)

        expected = "2012-12-12T15:15:00Z"
        result = dateutils.localtime_to_utc("2012-12-12 16:15:00")
        self.assertEqual(expected, result)

    def test_localtime_to_utc_uk(self):
        os.environ['TZ'] = 'Europe/London'
        tzset()

        expected = "2012-06-12T15:15:00Z"
        result = dateutils.localtime_to_utc("2012-06-12 16:15:00")
        self.assertEqual(expected, result)

        expected = "2012-12-12T16:15:00Z"
        result = dateutils.localtime_to_utc("2012-12-12 16:15:00")
        self.assertEqual(expected, result)

    def test_utc_to_localtime_cet(self):
        os.environ['TZ'] = 'Europe/Oslo'
        tzset()

        expected = "2012-06-12 16:15:00"
        result = dateutils.utc_to_localtime("2012-06-12T14:15:00Z")
        self.assertEqual(expected, result)

        expected = "2012-12-12 16:15:00"
        result = dateutils.utc_to_localtime("2012-12-12T15:15:00Z")
        self.assertEqual(expected, result)

    def test_utc_to_localtime_uk(self):
        os.environ['TZ'] = 'Europe/London'
        tzset()

        expected = "2012-06-12 16:15:00"
        result = dateutils.utc_to_localtime("2012-06-12T15:15:00Z")
        self.assertEqual(expected, result)

        expected = "2012-12-12 16:15:00"
        result = dateutils.utc_to_localtime("2012-12-12T16:15:00Z")
        self.assertEqual(expected, result)


TEST_SUITE = make_test_suite(ConvertFromDateCVSTest,
                             ConvertIntoDateGUITest,
                             ConvertIntoDateStructTest,
                             ParseRuntimeLimitTest,
                             STRFTimeTest,
                             DateTest,
                             DateTimeTest,
                             LocaltimeToUTCTest,
                             )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
