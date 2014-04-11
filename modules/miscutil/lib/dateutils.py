# -*- coding: utf-8 -*-
##
## Some functions about dates
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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
API for date conversion and date related GUI creation.
Lexicon
    datetext:
        textual format => 'YEAR-MONTH-DAY HOUR:MINUTE:SECOND'
        e.g. '2005-11-16 15:11:44'
        default value: '0000-00-00 00:00:00'

    datestruct:
        tuple format => see http://docs.python.org/lib/module-time.html
        (YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, WEEKDAY, YEARDAY, DAYLIGHT)
        e.g. (2005, 11, 16, 15, 11, 44, 2, 320, 0)
        default value: (0, 0, 0, 0, 0, 0, 0, 0, 0)

    dategui:
        textual format for output => 'DAY MONTH YEAR, HOUR:MINUTE'
        e.g. '16 nov 2005, 15:11'
        default value: _("N/A")
"""

__revision__ = "$Id$"

import re
import time
from datetime import date as real_date, \
                     datetime as real_datetime, \
                     time as real_time, \
                     timedelta
from invenio.config import CFG_SITE_LANG
from invenio.messages import gettext_set_language

try:
    from mx.DateTime import Parser
    CFG_HAS_EGENIX_DATETIME = True
except ImportError:
    CFG_HAS_EGENIX_DATETIME = False

datetext_default = '0000-00-00 00:00:00'
datestruct_default = (0, 0, 0, 0, 0, 0, 0, 0, 0)
datetext_format = "%Y-%m-%d %H:%M:%S"


class date(real_date):
    def strftime(self, fmt):
        return strftime(fmt, self)


class datetime(real_datetime):
    def strftime(self, fmt):
        return strftime(fmt, self)

    def __add__(self, other):
        d = real_datetime.combine(self, self.timetz())
        d += other
        return self.combine(d, d.timetz())

    def date(self):
        return date(self.year, self.month, self.day)

    @staticmethod
    def strptime(date_string, format):
        return datetime(*(time.strptime(date_string, format)[0:6]))


def convert_datetext_to_dategui(datetext, ln=CFG_SITE_LANG, secs=False):
    """
    Convert:
    '2005-11-16 15:11:57' => '16 nov 2005, 15:11'
    Or optionally with seconds:
    '2005-11-16 15:11:57' => '16 nov 2005, 15:11:57'
    Month is internationalized
    """
    try:
        datestruct = convert_datetext_to_datestruct(datetext)
        if datestruct == datestruct_default:
            raise ValueError
        month = get_i18n_month_name(datestruct[1], ln=ln)
        if secs:
            output_format = "%d " + month + " %Y, %H:%M:%S"
        else:
            output_format = "%d " + month + " %Y, %H:%M"
        return strftime(output_format, datestruct)
    except:
        _ = gettext_set_language(ln)
        return _("N/A")

def convert_datetext_to_datestruct(datetext):
    """
    Convert:
    '2005-11-16 15:11:57' => (2005, 11, 16, 15, 11, 44, 2, 320, 0)
    """
    try:
        return time.strptime(datetext, datetext_format)
    except:
        return datestruct_default

def convert_datestruct_to_dategui(datestruct, ln=CFG_SITE_LANG):
    """
    Convert:
    (2005, 11, 16, 15, 11, 44, 2, 320, 0) => '16 nov 2005, 15:11'
    Month is internationalized
    """
    try:
        if datestruct[0] and datestruct[1] and datestruct[2]:
            month = get_i18n_month_name(datestruct[1], ln=ln)
            output_format = "%d " + month + " %Y, %H:%M"
            return strftime(output_format, datestruct)
        else:
            raise ValueError
    except:
        _ = gettext_set_language(ln)
        return _("N/A")

def convert_datestruct_to_datetext(datestruct):
    """
    Convert:
    (2005, 11, 16, 15, 11, 44, 2, 320, 0) => '2005-11-16 15:11:57'
    """
    try:
        return strftime(datetext_format, datestruct)
    except:
        return datetext_default

def convert_datecvs_to_datestruct(datecvs):
    """
    Convert CVS $Date$ and
    $Id$
    formats into datestruct. Useful for later conversion of Last
    updated timestamps in the page footers.

    Example: '$Date$' => (2006, 09, 20, 19, 27, 11, 0, 0)
    """
    try:
        if datecvs.startswith("$Id"):
            date_time = ' '.join(datecvs.split(" ")[3:5])
            return time.strptime(date_time, '%Y/%m/%d %H:%M:%S')
        else:
            # here we have to use '$' + 'Date...' here, otherwise the CVS
            # commit would erase this time format to put commit date:
            return time.strptime(datecvs, '$' + 'Date: %Y/%m/%d %H:%M:%S $')
    except ValueError:
        return datestruct_default

def get_datetext(year, month, day):
    """
    year=2005, month=11, day=16 => '2005-11-16 00:00:00'
    """
    input_format = "%Y-%m-%d"
    try:
        datestruct = time.strptime("%i-%i-%i"% (year, month, day), input_format)
        return strftime(datetext_format, datestruct)
    except:
        return datetext_default

def get_datestruct(year, month, day):
    """
    year=2005, month=11, day=16 => (2005, 11, 16, 0, 0, 0, 2, 320, -1)
    """
    input_format = "%Y-%m-%d"
    try:
        return time.strptime("%i-%i-%i"% (year, month, day), input_format)
    except ValueError or TypeError:
        return datestruct_default

def get_i18n_day_name(day_nb, display='short', ln=CFG_SITE_LANG):
    """
    get the string representation of a weekday, internationalized
    @param day_nb: number of weekday UNIX like.
                   => 0=Sunday
    @param ln: language for output
    @return: the string representation of the day
    """
    _ = gettext_set_language(ln)
    if display == 'short':
        days = {0: _("Sun"),
                1: _("Mon"),
                2: _("Tue"),
                3: _("Wed"),
                4: _("Thu"),
                5: _("Fri"),
                6: _("Sat")}
    else:
        days = {0: _("Sunday"),
                1: _("Monday"),
                2: _("Tuesday"),
                3: _("Wednesday"),
                4: _("Thursday"),
                5: _("Friday"),
                6: _("Saturday")}

    return days[day_nb]

def get_i18n_month_name(month_nb, display='short', ln=CFG_SITE_LANG):
    """
    get a non-numeric representation of a month, internationalized.
    @param month_nb: number of month, (1 based!)
                     =>1=jan,..,12=dec
    @param ln: language for output
    @return: the string representation of month
    """
    _ = gettext_set_language(ln)
    if display == 'short':
        months = {0: _("Month"),
                   1: _("Jan"),
                   2: _("Feb"),
                   3: _("Mar"),
                   4: _("Apr"),
                   5: _("May"),
                   6: _("Jun"),
                   7: _("Jul"),
                   8: _("Aug"),
                   9: _("Sep"),
                   10: _("Oct"),
                   11: _("Nov"),
                   12: _("Dec")}
    else:
        months = {0: _("Month"),
                   1: _("January"),
                   2: _("February"),
                   3: _("March"),
                   4: _("April"),
                   5: _("May "), # trailing space distinguishes short/long form
                   6: _("June"),
                   7: _("July"),
                   8: _("August"),
                   9: _("September"),
                   10: _("October"),
                   11: _("November"),
                   12: _("December")}
    return months[month_nb].strip()

def create_day_selectbox(name, selected_day=0, ln=CFG_SITE_LANG):
    """
    Creates an HTML menu for day selection. (0..31 values).
    @param name: name of the control (i.e. name of the var you'll get)
    @param selected_day: preselect a day. Use 0 for the label 'Day'
    @param ln: language of the menu
    @return: html a string
    """
    _ = gettext_set_language(ln)
    out = "<select name=\"%s\">\n"% name
    for i in range(0, 32):
        out += "  <option value=\"%i\""% i
        if (i == selected_day):
            out += " selected=\"selected\""
        if (i == 0):
            out += ">%s</option>\n"% _("Day")
        else:
            out += ">%i</option>\n"% i
    out += "</select>\n"
    return out

def create_month_selectbox(name, selected_month=0, ln=CFG_SITE_LANG):
    """
    Creates an HTML menu for month selection. Value of selected field is numeric
    @param name: name of the control (your form will be sent with name=value...)
    @param selected_month: preselect a month. use 0 for the Label 'Month'
    @param ln: language of the menu
    @return: html as string
    """
    out = "<select name=\"%s\">\n"% name

    for i in range(0, 13):
        out += "<option value=\"%i\""% i
        if (i == selected_month):
            out += " selected=\"selected\""
        out += ">%s</option>\n"% get_i18n_month_name(i, ln)
    out += "</select>\n"
    return out

def create_year_inputbox(name, value=0):
    """
    Creates an HTML field (simple input) for year selection.
    @param name: name of the control (i.e. name of the variable you'll get)
    @param value: prefilled value (int)
    @return: html as string
    """
    out = "<input type=\"text\" name=\"%s\" value=\"%i\" maxlength=\"4\" size=\"4\"/>\n"% (name, value)
    return out

def create_year_selectbox(name, from_year=-1, length=10, selected_year=0, ln=CFG_SITE_LANG):
    """
    Creates an HTML menu (dropdownbox) for year selection.
    @param name: name of control( i.e. name of the variable you'll get)
    @param from_year: year on which to begin. if <0 assume it is current year
    @param length: number of items in menu
    @param selected_year: initial selected year (if in range), else: label is selected
    @param ln: language
    @return: html as string
    """
    _ = gettext_set_language(ln)
    if from_year < 0:
        from_year = time.localtime()[0]
    out = "<select name=\"%s\">\n"% name
    out += '  <option value="0"'
    if selected_year == 0:
        out += ' selected="selected"'
    out += ">%s</option>\n"% _("Year")
    for i in range(from_year, from_year + length):
        out += "<option value=\"%i\""% i
        if (i == selected_year):
            out += " selected=\"selected\""
        out += ">%i</option>\n"% i
    out += "</select>\n"
    return out

_RE_RUNTIMELIMIT_FULL = re.compile(r"(?:(?P<weekday_begin>[a-z]+)(?:-(?P<weekday_end>[a-z]+))?)?\s*((?P<hour_begin>\d\d?(:\d\d?)?)(-(?P<hour_end>\d\d?(:\d\d?)?))?)?", re.I)
_RE_RUNTIMELIMIT_HOUR = re.compile(r'(?P<hours>\d\d?)(:(?P<minutes>\d\d?))?')
def parse_runtime_limit(value, now=None):
    """
    Parsing CLI option for runtime limit, supplied as VALUE.
    Value could be something like: Sunday 23:00-05:00, the format being
    [Wee[kday]] [hh[:mm][-hh[:mm]]].
    The function will return two valid time ranges. The first could be in the past, containing the present or in the future. The second is always in the future.
    """

    def extract_time(value):
        value = _RE_RUNTIMELIMIT_HOUR.search(value).groupdict()
        return timedelta(hours=int(value['hours']),
                         minutes=int(value['minutes']))

    def extract_weekday(value):
        key = value[:3].lower()
        try:
            return {
                'mon' : 0,
                'tue' : 1,
                'wed' : 2,
                'thu' : 3,
                'fri' : 4,
                'sat' : 5,
                'sun' : 6,
            }[key]
        except KeyError:
            raise ValueError("%s is not a good weekday name." % value)

    if now is None:
        now = datetime.now()

    today = now.date()
    g = _RE_RUNTIMELIMIT_FULL.search(value)
    if not g:
        raise ValueError('"%s" does not seem to be correct format for parse_runtime_limit() [Wee[kday]] [hh[:mm][-hh[:mm]]]).' % value)
    pieces = g.groupdict()

    if pieces['weekday_begin'] is None:
        # No weekday specified. So either today or tomorrow
        first_occasion_day = timedelta(days=0)
        next_occasion_delta = timedelta(days=1)
    else:
        # If given 'Mon' then we transform it to 'Mon-Mon'
        if pieces['weekday_end'] is None:
            pieces['weekday_end'] = pieces['weekday_begin']

        # Day range
        weekday_begin = extract_weekday(pieces['weekday_begin'])
        weekday_end = extract_weekday(pieces['weekday_end'])

        if weekday_begin <= today.weekday() <= weekday_end:
            first_occasion_day = timedelta(days=0)
        else:
            days = (weekday_begin - today.weekday()) % 7
            first_occasion_day = timedelta(days=days)

        weekday = (now + first_occasion_day).weekday()
        if weekday < weekday_end:
            # Fits in the same week
            next_occasion_delta = timedelta(days=1)
        else:
            # The week after
            days = weekday_begin - weekday + 7
            next_occasion_delta = timedelta(days=days)

    if pieces['hour_begin'] is None:
        pieces['hour_begin'] = '00:00'
    if pieces['hour_end'] is None:
        pieces['hour_end'] = '00:00'

    beginning_time = extract_time(pieces['hour_begin'])
    ending_time = extract_time(pieces['hour_end'])

    if not ending_time:
        ending_time = beginning_time + timedelta(days=1)
    elif beginning_time and ending_time and beginning_time > ending_time:
        ending_time += timedelta(days=1)

    start_time = real_datetime.combine(today, real_time(hour=0, minute=0))
    current_range = (
        start_time + first_occasion_day + beginning_time,
        start_time + first_occasion_day + ending_time
    )
    if now > current_range[1]:
        current_range = tuple(t + next_occasion_delta for t in current_range)

    future_range = (
        current_range[0] + next_occasion_delta,
        current_range[1] + next_occasion_delta
    )
    return current_range, future_range

def guess_datetime(datetime_string):
    """
    Try to guess the datetime contained in a string of unknow format.
    @param datetime_string: the datetime representation.
    @type datetime_string: string
    @return: the guessed time.
    @rtype: L{time.struct_time}
    @raises ValueError: in case it's not possible to guess the time.
    """
    if CFG_HAS_EGENIX_DATETIME:
        try:
            return Parser.DateTimeFromString(datetime_string).timetuple()
        except ValueError:
            pass
    else:
        for format in (None, '%x %X', '%X %x', '%Y-%M-%dT%h:%m:%sZ', "%Y-%m-%d", "%d %m %Y"):
            try:
                return time.strptime(datetime_string, format)
            except ValueError:
                pass
    raise ValueError("It is not possible to guess the datetime format of %s" % datetime_string)

def get_time_estimator(total):
    """
    Given a total amount of items to compute, return a function that,
    if called every time an item is computed (or every step items are computed)
    will give a time estimation for how long it will take to compute the whole
    set of itmes. The function will return two values: the first is the
    number of seconds that are still needed to compute the whole set, the second
    value is the time in the future when the operation is expected to end.
    """
    t1 = time.time()
    count = [0]
    def estimate_needed_time(step=1):
        count[0] += step
        t2 = time.time()
        t3 = 1.0 * (t2 - t1) / count[0] * (total - count[0])
        return t3, t3 + t1
    return estimate_needed_time

# This library does not support strftime's "%s" or "%y" format strings.
# Allowed if there's an even number of "%"s because they are escaped.
_illegal_formatting = re.compile(r"((^|[^%])(%%)*%[sy])")

def _findall(text, substr):
    # Also finds overlaps
    sites = []
    i = 0
    while 1:
        j = text.find(substr, i)
        if j == -1:
            break
        sites.append(j)
        i=j+1
    return sites

def strftime(fmt, dt):
    if not isinstance(dt, real_date):
        dt = datetime(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5])
    if dt.year >= 1900:
        return time.strftime(fmt, dt.timetuple())
    illegal_formatting = _illegal_formatting.search(fmt)
    if illegal_formatting:
        raise TypeError("strftime of dates before 1900 does not handle" + illegal_formatting.group(0))

    year = dt.year
    # For every non-leap year century, advance by
    # 6 years to get into the 28-year repeat cycle
    delta = 2000 - year
    off = 6 * (delta // 100 + delta // 400)
    year = year + off

    # Move to around the year 2000
    year = year + ((2000 - year) // 28) * 28
    timetuple = dt.timetuple()
    s1 = time.strftime(fmt, (year,) + timetuple[1:])
    sites1 = _findall(s1, str(year))

    s2 = time.strftime(fmt, (year+28,) + timetuple[1:])
    sites2 = _findall(s2, str(year+28))

    sites = []
    for site in sites1:
        if site in sites2:
            sites.append(site)

    s = s1
    syear = "%04d" % (dt.year,)
    for site in sites:
        s = s[:site] + syear + s[site+4:]
    return s


def get_dst(date_obj):
    """Determine if dst is locally enabled at this time"""
    dst = 0
    if date_obj.year >= 1900:
        tmp_date = time.mktime(date_obj.timetuple())
        # DST is 1 so reduce time with 1 hour.
        dst = time.localtime(tmp_date)[-1]
    return dst


def utc_to_localtime(date_str, fmt="%Y-%m-%d %H:%M:%S", input_fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    Convert UTC to localtime

    Reference:
     - (1) http://www.openarchives.org/OAI/openarchivesprotocol.html#Dates
     - (2) http://www.w3.org/TR/NOTE-datetime

    This function works only with dates complying with the
    "Complete date plus hours, minutes and seconds" profile of
    ISO 8601 defined by (2), and linked from (1).

    Eg:    1994-11-05T13:15:30Z
    """
    date_struct = datetime.strptime(date_str, input_fmt)
    date_struct += timedelta(hours=get_dst(date_struct))
    date_struct -= timedelta(seconds=time.timezone)
    return strftime(fmt, date_struct)


def localtime_to_utc(date_str, fmt="%Y-%m-%dT%H:%M:%SZ", input_fmt="%Y-%m-%d %H:%M:%S"):
    """Convert localtime to UTC"""
    date_struct = datetime.strptime(date_str, input_fmt)
    date_struct -= timedelta(hours=get_dst(date_struct))
    date_struct += timedelta(seconds=time.timezone)
    return strftime(fmt, date_struct)


def strptime(date_string, fmt):
    return real_datetime(*(time.strptime(date_string, fmt)[:6]))
