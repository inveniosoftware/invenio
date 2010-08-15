# -*- coding: utf-8 -*-
##
## Some functions about dates
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
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

from time import strptime, strftime, localtime

from invenio.config import CFG_SITE_LANG
from invenio.messages import gettext_set_language

datetext_default = '0000-00-00 00:00:00'
datestruct_default = (0, 0, 0, 0, 0, 0, 0, 0, 0)
datetext_format = "%Y-%m-%d %H:%M:%S"

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
        return strptime(datetext, datetext_format)
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
            return strptime(date_time, '%Y/%m/%d %H:%M:%S')
        else:
            # here we have to use '$' + 'Date...' here, otherwise the CVS
            # commit would erase this time format to put commit date:
            return strptime(datecvs, '$' + 'Date: %Y/%m/%d %H:%M:%S $')
    except ValueError:
        return datestruct_default

def get_datetext(year, month, day):
    """
    year=2005, month=11, day=16 => '2005-11-16 00:00:00'
    """
    input_format = "%Y-%m-%d"
    try:
        datestruct = strptime("%i-%i-%i"% (year, month, day), input_format)
        return strftime(datetext_format, datestruct)
    except:
        return datetext_default

def get_datestruct(year, month, day):
    """
    year=2005, month=11, day=16 => (2005, 11, 16, 0, 0, 0, 2, 320, -1)
    """
    input_format = "%Y-%m-%d"
    try:
        return strptime("%i-%i-%i"% (year, month, day), input_format)
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
                   5: _("May"),
                   6: _("June"),
                   7: _("July"),
                   8: _("August"),
                   9: _("September"),
                   10: _("October"),
                   11: _("November"),
                   12: _("December")}
    return months[month_nb]

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
        from_year = localtime()[0]
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
