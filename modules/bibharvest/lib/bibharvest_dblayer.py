## $Id$

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


from invenio.dbquery import run_sql
import datetime

class HistoryEntry:
    date = None
    id = ""
    operation = "i"
    def __init__(self, date, id):
        self.date = date
        self.id = id

def get_history_entries(oai_src_id, monthdate):
    query = "SELECT date_inserted, oai_id  from oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(date_inserted) = %s AND YEAR(date_inserted) = %s ORDER BY date_inserted"
    res = run_sql(query,(str(oai_src_id), str(monthdate.month), str(monthdate.year)))
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0],str(entry[1])))
    return result

def get_history_entries_for_day(oai_src_id, date, limit = -1, start = 0):
    query = "SELECT date_inserted, oai_id  from oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(date_inserted) = %s AND YEAR(date_inserted) = %s  AND DAY(date_inserted) = %s ORDER BY date_inserted"
    if limit > 0:
        query += " LIMIT " + str(start) + "," + str(limit)
    res = run_sql(query,(str(oai_src_id), str(date.month), str(date.year), str(date.day)))
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], str(entry[1])))
    return result

def get_month_inserts_number(oai_src_id, date):
    # Function which returns number of inserts which took place in given month (splited into days)
    # @param oai_src_id - harvesting source identifier
    # @result Dictionary of harvesting statistics - keys describe days. values - numbers of inserted recordds
    query = "SELECT DAY(date_inserted), COUNT(*) FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(date_inserted) = %s AND YEAR(date_inserted)= %s GROUP BY DAY(date_inserted)"
    query_result = run_sql(query, (str(oai_src_id), str(date.month), str(date.year)))
    result = {}
    for entry in query_result:
        result[int(entry[0])] = int(entry[1])
    return result

def get_day_inserts_number(oai_src_id, date):
    # Function which returns number of inserts which took place in given day
    # @param oai_src_id - harvesting source identifier
    # @result Number of inserts during the given day
    query = "SELECT COUNT(*) FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(date_inserted) = %s AND YEAR(date_inserted)= %s AND DAY(date_inserted) = %s"
    query_result = run_sql(query, (str(oai_src_id), str(date.month), str(date.year), str(date.day)))
    for entry in query_result:
        return int(entry[0])
    return 0
