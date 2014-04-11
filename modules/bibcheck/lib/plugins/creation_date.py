## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
Backdate the creation_date of a record to reflect the earliest date information
available.
Note in case of partial dates (e.g. just the year or just year-month), if there
is another valid date within the
"""

import time

from invenio.dbquery import run_sql
## List of MARC fields from where to read dates.
CFG_DEFAULT_DATE_FIELDS = ["111__d", "260__c", "260__t", "269__d", "542__g", "502__y", "773__y", "111__x", "046__%", "371__t"]
CFG_POSSIBLE_DATE_FORMATS_ONLY_YEAR = ["%Y", "%y"]
CFG_POSSIBLE_DATE_FORMATS_ONLY_YEAR_MONTH = ["%Y-%m", "%Y %b", "%b %Y", "%Y %B", "%B %Y", "%y-%m", "%y %b", "%b %y", "%y %B", "%B %y"]
CFG_POSSIBLE_DATE_FORMATS = ["%Y-%m-%d", "%d %m %Y", "%x", "%d %b %Y", "%d %B %Y", "%d %b %y", "%d %B %y"]


def check_records(records, date_fields=CFG_DEFAULT_DATE_FIELDS):
    """
    Backdate the creation_date of a record to reflect the earliest date information
    available.
    Note in case of partial dates (e.g. just the year or just year-month), if there
    is another valid date within the
    """
    for record in records:
        dates = []
        recid = int(record["001"][0][3])

        creation_date, modification_date = run_sql("SELECT creation_date, modification_date FROM bibrec WHERE id=%s", (recid, ))[0]
        creation_date = creation_date.strftime("%Y-%m-%d %H:%M:%S")
        modification_date = modification_date.strftime("%Y-%m-%d %H:%M:%S")
        dates.append(creation_date)
        dates.append(modification_date)

        if '005' in record:
            dates.append(time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(record["005"][0][3],"%Y%m%d%H%M%S.0")))
        for position, value in record.iterfields(date_fields):
            for format in CFG_POSSIBLE_DATE_FORMATS:
                try:
                    parsed_date = time.strftime("%Y-%m-%d", (time.strptime(value, format)))
                    dates.append(parsed_date)
                    break
                except ValueError:
                    pass
            else:
                for format in CFG_POSSIBLE_DATE_FORMATS_ONLY_YEAR_MONTH:
                    try:
                        parsed_date = time.strftime("%Y-%m-99", (time.strptime(value, format)))
                        dates.append(parsed_date)
                        break
                    except ValueError:
                        pass
                else:
                    for format in CFG_POSSIBLE_DATE_FORMATS_ONLY_YEAR:
                        try:
                            parsed_date = time.strftime("%Y-99-99", (time.strptime(value, format)))
                            dates.append(parsed_date)
                            break
                        except ValueError:
                            pass
        min_date = min(dates)
        ## Let's restore meaningful first month and day
        min_date = min_date.replace("-99", "-01")
        if min_date < creation_date:
            run_sql("UPDATE bibrec SET creation_date=%s WHERE id=%s", (min_date, recid))
            record.warn("record creation_date backported from %s to %s" % (creation_date, min_date))

