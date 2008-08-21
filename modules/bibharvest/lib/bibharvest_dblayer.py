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
    date_harvested = None
    date_inserted = None
    oai_id = ""
    record_id = 0
    bibupload_task_id = ""
    inserted_to_db = ""
    oai_src_id = 0
    def __init__(self, date_harvested, date_inserted, oai_src_id, oai_id, record_id, inserted_to_db, bibupload_task_id):
        self.date_harvested = date_harvested
        self.date_inserted = date_inserted
        self.record_id = record_id
        self.oai_id = oai_id
        self.bibupload_task_id = bibupload_task_id
        self.oai_src_id = oai_src_id
        self.inserted_to_db = inserted_to_db

def get_history_entries(oai_src_id, monthdate, method = "harvested"):
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"
    query = "SELECT date_harvested, date_inserted, id_oaiHARVEST, oai_id, id_bibrec, inserted_to_db, bibupload_task_id FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column + ") = %s ORDER BY " + sql_column
    res = run_sql(query,(str(oai_src_id), str(monthdate.month), str(monthdate.year)))
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], entry[1], \
                      int(entry[2]), str(entry[3]), int(entry[4]),\
                      str(entry[5]), int(entry[6])))
    return result

def get_history_entries_for_day(oai_src_id, date, limit = -1, start = 0, method = "harvested"):
    """
       Returns harvesting history entries for a given day
       @param oai_src_id - harvesting source identifier
       @param date - Date designing the deserved day
       @limit - How many records (at most) do we want to get
       @start - From which index do we want to start ?
       @method - method of getting data (two possible values "harvested" and "inserted")
                 Describes if the harvesting or inserting data should be used
    """
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"

    query = "SELECT date_harvested, date_inserted, id_oaiHARVEST, oai_id, id_bibrec, inserted_to_db, bibupload_task_id FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column + ") = %s  AND DAY(" + sql_column + ") = %s ORDER BY " + sql_column
    if limit > 0:
        query += " LIMIT " + str(start) + "," + str(limit)
    res = run_sql(query,(str(oai_src_id), str(date.month), str(date.year), str(date.day)))
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], entry[1], \
                      int(entry[2]), str(entry[3]), int(entry[4]),\
                      str(entry[5]), int(entry[6])))
    return result

def get_month_logs_size(oai_src_id, date, method = "harvested"):
    # Function which returns number of inserts which took place in given month (splited into days)
    # @param oai_src_id - harvesting source identifier
    # @result Dictionary of harvesting statistics - keys describe days. values - numbers of inserted recordds
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"
    query = "SELECT DAY(" + sql_column + "), COUNT(*) FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column + ")= %s GROUP BY DAY(" + sql_column+ ")"
    query_result = run_sql(query, (str(oai_src_id), str(date.month), str(date.year)))
    result = {}
    for entry in query_result:
        if int(entry[0]) != 0:
            result[int(entry[0])] = int(entry[1])
    return result

def get_day_logs_size(oai_src_id, date, method = "harvested"):
    # Function which returns number of inserts which took place in given day
    # @param oai_src_id - harvesting source identifier
    # @result Number of inserts during the given day
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"
    query = "SELECT COUNT(*) FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column+ ")= %s AND DAY(" + sql_column + ") = %s"
    query_result = run_sql(query, (str(oai_src_id), str(date.month), str(date.year), str(date.day)))
    for entry in query_result:
        return int(entry[0])
    return 0
