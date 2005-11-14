# -*- coding: utf-8 -*-
## $Id$
## 
## Some functions about dates
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# External imports
from time import strptime, strftime

# CDS imports
from cdsware.config import cdslang
from cdsware.messages import gettext_set_language


def date_convert_MySQL_to_text(db_date, ln=cdslang):
    """
    Convert a date from mySQL to the appropriate format.
    e.g.: "2004-02-28 14:53:02" => "28 feb 2004, 14:53"
    Month is internationalized 
    @param db_date: date from mySQL
    @return a formatted string
    """
    def to_str(int_val):
        """
        """
        if int_val == 0:
            return '00'
        else:
            return str(int_val)
    _ = gettext_set_language(ln)
    format = "%Y-%m-%d %H:%M:%S"
    pythonic_date = (0,0,0,0,0,0,0,0,-1)
    try:
        pythonic_date = strptime(db_date, format)
    except ValueError:
        pass
    (y, m, d, h, mm, junk, junk, junk, junk) = map(to_str, pythonic_date)
    return ("%s %s %s, %s:%s") %\
           (d, get_i18n_month_name(month_nb=int(m),ln=ln),y, h, mm)

def date_convert_to_MySQL(year, month, day):
    """
    convert a given date to mySQL notation
    @param year: year as an int
    @param month: month as an int
    @param day: day as an int
    @return string representation of date
    """
    format = "%Y-%m-%d %H:%M:%S"
    if ((year, month, day)!=(0, 0, 0)):
        out = strftime(format, (year, month, day, 0, 0, 0, 0, 0, 0))
    else:
        out = '0000-00-00 00:00:00'
    return out

def get_i18n_date(pythonic_date, ln=cdslang):
    """
    Convert a given date (formatted in python's way to a textual representation
    """
    def to_str(int_val):
        """
        """
        if int_val == 0:
            return '00'
        else:
            return str(int_val)
    _ = gettext_set_language(ln)
    (y, m, d, h, mm, junk, junk, junk, junk) = map(to_str, pythonic_date)
    
    return ("%s %s %s, %s:%s") %\
           (d, get_i18n_month_name(month_nb=int(m),ln=ln),y, h, mm)

    
def get_i18n_day_name(day_nb, display='short', ln=cdslang):
    """
    get the string representation of a weekday, internationalized
    @param day_nb: number of weekday UNIX like.
                   =>0=Sunday
    @param ln: language for output
    @return the string representation of the day
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

def get_i18n_month_name(month_nb, display='short', ln=cdslang):
    """
    get a non-numeric representation of a month, internationalized.
    @param month_nb: number of month, (1 based!)
                     =>1=jan,..,12=dec
    @param ln: language for output
    @return the string representation of month
    """
    _ = gettext_set_language(ln)
    if display == 'short':
        monthes = {0: _("Month"),
                   1: _("jan"),
                   2: _("feb"),
                   3: _("mar"),
                   4: _("apr"),
                   5: _("may"),
                   6: _("jun"),
                   7: _("jul"),
                   8: _("aug"),
                   9: _("sep"),
                   10: _("oct"),
                   11: _("nov"),
                   12: _("dec")}
    else:
        monthes = {0: _("Month"),
                   1: _("january"),
                   2: _("february"),
                   3: _("march"),
                   4: _("april"),
                   5: _("may"),
                   6: _("june"),
                   7: _("july"),
                   8: _("august"),
                   9: _("september"),
                   10: _("october"),
                   11: _("november"),
                   12: _("december")}
    return monthes[month_nb]

def create_day_selectbox(name, selected_day=0, ln=cdslang):
    """
    Creates an HTML menu for day selection. (0..31 values).
    @param name: name of the control (i.e. name of the var you'll get)
    @param selected_day: preselect a day. Use 0 for the label 'Day'
    @param ln: language of the menu
    @return html a string
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

def create_month_selectbox(name, selected_month=0, ln=cdslang):
    """
    Creates an HTML menu for month selection. Value of selected field is numeric
    @param name: name of the control (your form will be sent with name=value...)
    @param selected_month: preselect a month. use 0 for the Label 'Month'
    @param ln: language of the menu
    @return html as string
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
    @return html as string
    """
    out = "<input type=\"text\" name=\"%s\" value=\"%i\"/>\n"% (name, value)
    return out

def create_year_selectbox(name, from_year, to_year, selected_year=0, ln=cdslang):
    """
    Creates an HTML menu for year selection. Value of selected field is numeric
    @param name: name of the control (your form will be sent with name=value...)
    @param from_year: first year selectable (int)
    @param to_year: last year selectable (int)
    @param selected_year: preselect a month. use 0 for the Label 'Year'
    @param ln: language of the menu
    @return html as string
    """
    _ = gettext_set_language(ln)
    out = "<select name=\"%s\">\n"% name
    for i in range(from_year, to_year + 1):
        out += "<option value=\"%i\""% i
        if (i == selected_year):
            out += " selected=\"selected\""
        if (i == 0):
            out += ">%s</option>\n"% _("Year")
        out += ">%i</option>\n"% i
    out += "</select>\n"
    return out
