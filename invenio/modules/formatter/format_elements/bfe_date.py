# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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
"""BibFormat element - Prints imprint publication date
"""
__revision__ = "$Id$"

from invenio.utils.date import strftime, strptime, guess_datetime

def format_element(bfo, date_format='%d %B %Y', source_formats='%Y-%m-%d', source_fields="260__c",
                   guess_source_format="no", ignore_date_format_for_year_only="yes"):
    """
    Prints the imprint publication date.

    Parameter <code>date_format</code> allows to specify the string
    representation of the output.

    The format string has the same behaviour as the strftime() function:
        <pre>Eg: 1982-09-24 07:32:00
            "%d %B %Y"   -> 24 September 1982
            "%I:%M"      -> 07:32
        </pre>

    Note that if input date is simply a year (4 digits), it is
    returned as such if <code>ignore_date_format_for_year_only</code>
    is set to 'yes', regardless of <code>date_format</code>.

    Parameter <code>source_formats</code> allows to specify the
    expected format of the date in the metadata. If the format does
    not match, the date cannot be parsed, and cannot be formatted
    according to <code>date_format</code>. Comma-separated values can
    be provided in order to test several input formats.

    Parameter <code>source_fields</code> defined the list of MARC
    fields where we would like to retrieve the date. First one
    matching <code>source_formats</code> is used. if none, fall back to
    first non-empty one.

    Parameter <code>guess_source_formats</code> when set to 'yes'
    allows to guess the date source format.


    @see: pagination.py, publisher.py, reprints.py, imprint.py, place.py
    @param date_format: output date format.
    @param source_formats: expected (comma-separated values) input date format.
    @param source_fields: the MARC fields (comma-separated values) to look up
                   for the date. First non-empty one is used.
    @param guess_source_format: if 'yes', ignore 'source_format' and
                                try to guess format using Python mxDateTime module.
    #param ignore_date_format_for_year_only: if 'yes', ignore 'date_format' when the
                                             metadata in the record contains a single
                                             year (4 digits).
    """
    guess_source_format_p = guess_source_format.lower() == 'yes'
    source_marc_fields = [source_marc_field.strip() for source_marc_field in source_fields.split(',')]
    source_formats = [source_format.strip() for source_format in source_formats.split(',')]
    ignore_date_format_for_year_only_p = ignore_date_format_for_year_only.lower() == 'yes'
    parsed_datetime_value = None
    first_matched_raw_date = ''
    for source_marc_field in source_marc_fields:
        date_value = bfo.field(source_marc_field)
        if date_value:
            if not first_matched_raw_date:
                first_matched_raw_date = date_value
            if ignore_date_format_for_year_only_p and \
                   date_value.isdigit() and len(date_value) == 4:
                # Year. Return as such
                return date_value
            if guess_source_format_p:
                try:
                    parsed_datetime_value = guess_datetime(date_value)
                    break
                except:
                    pass
            else:
                for source_format in source_formats:
                    try:
                        parsed_datetime_value = strptime(date_value, source_format)
                        break
                    except:
                        pass
            if parsed_datetime_value:
                # We have correctly parsed one date!
                break

    if parsed_datetime_value:
        return strftime(date_format, parsed_datetime_value)
    else:
        return first_matched_raw_date
