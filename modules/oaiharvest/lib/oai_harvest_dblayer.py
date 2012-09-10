## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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


from invenio.dbquery import run_sql

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
    def __repr__(self):
        return str(self)

    def __str__(self):
        return "HistoryEntry(" + \
               "date_harvested: " + str(self.date_harvested) + ', ' + \
               "date_inserted: " + str(self.date_inserted) + ', ' + \
               "oai_id: " + str(self.oai_id) + ', ' + \
               "record_id: " + str(self.record_id) + ', ' + \
               "bibupload_task_id: " + str(self.bibupload_task_id) + ', ' + \
               "inserted_to_db: " + str(self.inserted_to_db) + ', ' + \
               "oai_src_id: " + str(self.oai_src_id) + ', ' + ")"

def get_history_entries_raw(query_suffix, sqlparameters):
    """
       Internally used function which obtains sql query suffix ( starting from WHERE)
       and
    """
    query_prefix = "SELECT date_harvested, date_inserted, id_oaiHARVEST, oai_id, id_bibrec, inserted_to_db, bibupload_task_id FROM oaiHARVESTLOG "
    query = query_prefix + query_suffix
    res = run_sql(query, sqlparameters)
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], entry[1], \
                      int(entry[2]), str(entry[3]), int(entry[4]),\
                      str(entry[5]), int(entry[6])))
    return result

def get_history_entries(oai_src_id, monthdate, method = "harvested"):
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"
    query_suffix = "WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column + ") = %s ORDER BY " + sql_column
    return get_history_entries_raw(query_suffix,(str(oai_src_id), str(monthdate.month), str(monthdate.year)))

def get_history_entries_for_day(oai_src_id, date, limit = -1, start = 0, method = "harvested"):
    """
       Returns harvesting history entries for a given day
       @param oai_src_id: harvesting source identifier
       @param date: Date designing the deserved day
       @param limit: How many records (at most) do we want to get
       @param start: From which index do we want to start ?
       @param method: method of getting data (two possible values "harvested" and "inserted")
                 Describes if the harvesting or inserting data should be used
    """
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"

    query_suffix = "WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column + ") = %s  AND DAY(" + sql_column + ") = %s ORDER BY " + sql_column
    if limit > 0:
        query_suffix += " LIMIT " + str(start) + "," + str(limit)
    return get_history_entries_raw(query_suffix, (str(oai_src_id), str(date.month), str(date.year), str(date.day)))

def get_entry_history(oai_id, start = 0, limit = -1 , method = "harvested"):
    """
       Returns harvesting history entries for a given OAI identifier ( Show results from multiple sources )
       @limit - How many records (at most) do we want to get
       @start - From which index do we want to start ?
       @method - method of getting data (two possible values "harvested" and "inserted")
                 Describes if the harvesting or inserting data should be used
    """
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"
    query_suffix = "WHERE oai_id = %s ORDER BY " + sql_column
    if limit > 0:
        query_suffix += " LIMIT " + str(start) + "," + str(limit)
    return get_history_entries_raw(query_suffix, (str(oai_id),))


def get_month_logs_size(oai_src_id, date, method = "harvested"):
    """
    Function which returns number of inserts which took place in given month (splited into days)
    @param oai_src_id: harvesting source identifier
    @return: Dictionary of harvesting statistics - keys describe days. values - numbers of inserted recordds
    """
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
    """
    Function which returns number of inserts which took place in given day
    @param oai_src_id: harvesting source identifier
    @return: Number of inserts during the given day
    """
    sql_column = "date_harvested"
    if method == "inserted":
        sql_column = "date_inserted"
    query = "SELECT COUNT(*) FROM oaiHARVESTLOG WHERE id_oaiHARVEST = %s AND MONTH(" + sql_column + ") = %s AND YEAR(" + sql_column+ ")= %s AND DAY(" + sql_column + ") = %s"
    query_result = run_sql(query, (str(oai_src_id), str(date.month), str(date.year), str(date.day)))
    for entry in query_result:
        return int(entry[0])
    return 0

def get_entry_logs_size(oai_id):
    """
    Function which returns number of inserts which took place in given day
    @param oai_src_id: harvesting source identifier
    @return: Number of inserts during the given day
    """
    query = "SELECT COUNT(*) FROM oaiHARVESTLOG WHERE oai_id = %s"
    query_result = run_sql(query, (str(oai_id),))
    for entry in query_result:
        return int(entry[0])
    return 0

def get_holdingpen_entries(start = 0, limit = 0):
    query = "SELECT oai_id, changeset_date, update_id FROM bibHOLDINGPEN ORDER BY changeset_date"
    if limit > 0 or start > 0:
        query += " LIMIT " + str(start) + "," + str(limit)

    return run_sql(query)

def get_holdingpen_entry(oai_id, date_inserted):
    query = "SELECT changeset_xml FROM bibHOLDINGPEN WHERE changeset_date = %s AND oai_id = %s"
    return run_sql(query, (str(date_inserted), str(oai_id)))[0][0]

def delete_holdingpen_entry(hpupdate_id):
    query = "DELETE FROM bibHOLDINGPEN WHERE changeset_id=%s"
    run_sql(query, (hpupdate_id, ))


def get_holdingpen_day_fragment(year, month, day, limit, start, filter):
    """
       returning the entries form the a particular day
    """
   # query = "SELECT oai_id, changeset_date FROM bibHOLDINGPEN WHERE year(changeset_date) = '%i' and month(changeset_date) = '%i' and day(changeset_date) = '%i' ORDER BY changeset_date LIMIT %i, %i" % (year, month, day, start, limit)
    filterSql = ""
    if filter != "":
        filterSql = " and oai_id like '%%%s%%' " % (filter, )
    query = "SELECT oai_id, changeset_date, changeset_id FROM bibHOLDINGPEN WHERE changeset_date >= '%i-%i-%i 00:00:00' and changeset_date <= '%i-%i-%i 23:59:59' %s ORDER BY changeset_date LIMIT %i, %i" % (year, month, day, year, month, day, filterSql, start, limit)
    query_results = run_sql(query)
    return query_results

def get_holdingpen_day_size(year, month, day, filter):
    """
       returning the entries form the a particular day
    """
    filterSql = ""
    if filter != "":
        filterSql = " and oai_id like '%%%s%%' " % (filter, )
    query = "SELECT count(*) FROM bibHOLDINGPEN WHERE year(changeset_date) = '%i' and month(changeset_date) = '%i' and day(changeset_date) = '%i' %s" % (year, month, day, filterSql)
    query_results = run_sql(query)
    return int(query_results[0][0])


def get_holdingpen_month(year, month, filter):
    """
       Returning the statistics about the entries form a particular month
    """
    filterSql = ""
    if filter != "":
        filterSql = " and oai_id like '%%%s%%' " % (filter, )

    query = "select day(changeset_date), count(*) from bibHOLDINGPEN where year(changeset_date) = '%i' and month(changeset_date) = '%i' %s group by day(changeset_date)" % (year, month, filterSql)
    return run_sql(query)


def get_holdingpen_year(year, filter):
    """
    Returning the statistics about the entries from a particular year
    """
    filterSql = ""
    if filter != "":
        filterSql = " and oai_id like '%%%s%%' " % (filter, )
    query = "select month(changeset_date), count(*) from bibHOLDINGPEN where year(changeset_date) = '%i' %s group by month(changeset_date)" % (year, filterSql)
    return run_sql(query)



def get_holdingpen_years(filter):
    """
    Returning the particular years of records present in the holding pen
    """
    filterSql = ""
    if filter != "":
        filterSql = " where oai_id like '%%%s%%' " % (filter, )
    query = "select year(changeset_date), count(*) changeset_date from bibHOLDINGPEN %s group by year(changeset_date)" % (filterSql,)
    results = run_sql(query)
    return results

def get_holdingpen_entry_details(hpupdate_id):
    """
    Returning the detials of the Holding Pen entry, the result of this function is a tuple:
    (oai_id, record_id,  date_inserted, content)
    """
    query = "SELECT oai_id, id_bibrec, changeset_date, changeset_xml FROM bibHOLDINGPEN WHERE changeset_id=%s"
    return run_sql(query, (hpupdate_id,))[0]
