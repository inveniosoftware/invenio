# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
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

from __future__ import print_function

import time

from datetime import datetime
from sqlalchemy import func

from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.legacy.dbquery import run_sql
from invenio.modules.oaiharvester.models import OaiHARVEST, OaiHARVESTLOG
from invenio.legacy.bibrecord import create_records, record_extract_oai_id


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


def update_lastrun(index):
    """ A method that updates the lastrun of a repository
        successfully harvested """
    try:
        today = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        OaiHARVEST.query.filter(OaiHARVEST.id == index).update({"lastrun": today})
        return 1
    except StandardError as e:
        return (0, e)


@session_manager
def create_oaiharvest_log_str(task_id, oai_src_id, xml_content):
    """
    Function which creates the harvesting logs
    @param task_id bibupload task id
    """
    records = create_records(xml_content)
    for record in records:
        oai_id = record_extract_oai_id(record[0])
        my_new_harvest_log = OaiHARVESTLOG()
        my_new_harvest_log.id_oaiHARVEST = oai_src_id
        my_new_harvest_log.oai_id = oai_id
        my_new_harvest_log.date_harvested = datetime.now()
        my_new_harvest_log.bibupload_task_id = task_id
        db.session.add(my_new_harvest_log)


def get_history_entries(oai_src_id, oai_date, method="harvested"):
    if method == "inserted":
        column = OaiHARVESTLOG.date_inserted
    else:
        column = OaiHARVESTLOG.date_harvested

    res = db.query(OaiHARVESTLOG.date_harvested, OaiHARVESTLOG.date_inserted,
                   OaiHARVESTLOG.id_oaiHARVEST, OaiHARVESTLOG.oai_id, OaiHARVESTLOG.id_bibrec,
                   OaiHARVESTLOG.inserted_to_db, OaiHARVESTLOG.bibupload_task_id) \
        .filter(OaiHARVESTLOG.id_oaiHARVEST == oai_src_id) \
        .filter(func.MONTH(column) == oai_date.month) \
        .filter(func.YEAR(column) == oai_date.year) \
        .order_by(column).all()
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], entry[1],
                                   int(entry[2]), str(entry[3]), int(entry[4]),
                                   str(entry[5]), int(entry[6])))
    return result


def get_history_entries_for_day(oai_src_id, oai_date, limit=-1, start=0, method="harvested"):
    """
       Returns harvesting history entries for a given day
       @param oai_src_id: harvesting source identifier
       @param oai_date: Date designing the deserved day
       @param limit: How many records (at most) do we want to get
       @param start: From which index do we want to start ?
       @param method: method of getting data (two possible values "harvested" and "inserted")
                 Describes if the harvesting or inserting data should be used
    """

    if method == "inserted":
        column = OaiHARVESTLOG.date_inserted
    else:
        column = OaiHARVESTLOG.date_harvested
    res = db.query(OaiHARVESTLOG.date_harvested, OaiHARVESTLOG.date_inserted,
                   OaiHARVESTLOG.id_oaiHARVEST, OaiHARVESTLOG.oai_id, OaiHARVESTLOG.id_bibrec,
                   OaiHARVESTLOG.inserted_to_db, OaiHARVESTLOG.bibupload_task_id) \
        .filter(OaiHARVESTLOG.id_oaiHARVEST == oai_src_id) \
        .filter(func.MONTH(column) == oai_date.month) \
        .filter(func.YEAR(column) == oai_date.year) \
        .filter(func.DAY(column) == oai_date.day) \
        .order_by(column)
    if limit > 0:
        res = res.all()[start:start + limit]
    else:
        res = res.all()
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], entry[1],
                                   int(entry[2]), str(entry[3]), int(entry[4]),
                                   str(entry[5]), int(entry[6])))
    return result


def get_entry_history(oai_src_id, start=0, limit=-1, method="harvested"):
    """
       Returns harvesting history entries for a given OAI identifier ( Show results from multiple sources )
       @limit - How many records (at most) do we want to get
       @start - From which index do we want to start ?
       @method - method of getting data (two possible values "harvested" and "inserted")
                 Describes if the harvesting or inserting data should be used
    """

    if method == "inserted":
        column = OaiHARVESTLOG.date_inserted
    else:
        column = OaiHARVESTLOG.date_harvested
    res = db.query(OaiHARVESTLOG.date_harvested, OaiHARVESTLOG.date_inserted,
                   OaiHARVESTLOG.id_oaiHARVEST, OaiHARVESTLOG.oai_id, OaiHARVESTLOG.id_bibrec,
                   OaiHARVESTLOG.inserted_to_db, OaiHARVESTLOG.bibupload_task_id) \
        .filter(OaiHARVESTLOG.id_oaiHARVEST == oai_src_id) \
        .order_by(column)
    if limit > 0:
        res = res[start:start + limit]
    else:
        res = res.all()
    result = []
    for entry in res:
        result.append(HistoryEntry(entry[0], entry[1],
                                   int(entry[2]), str(entry[3]), int(entry[4]),
                                   str(entry[5]), int(entry[6])))
    return result


def get_month_logs_size(oai_src_id, oai_date, method="harvested"):
    """
    Function which returns number of inserts which took place in given month (splited into days)
    @param oai_src_id: harvesting source identifier
    @return: Dictionary of harvesting statistics - keys describe days. values - numbers of inserted recordds
    """
    if method == "inserted":
        column = OaiHARVESTLOG.date_inserted
    else:
        column = OaiHARVESTLOG.date_harvested
    res = db.session.query(func.DAY(column), func.count(func.DAY(column)))\
        .filter(OaiHARVESTLOG.id_oaiHARVEST == oai_src_id) \
        .filter(func.MONTH(column) == oai_date.month) \
        .filter(func.YEAR(column) == oai_date.year) \
        .group_by(func.DAY(column)).all()
    result = {}
    for entry in res:
        if int(entry[0]) != 0:
            result[int(entry[0])] = int(entry[1])
    return result


def get_day_logs_size(oai_src_id, oai_date, method="harvested"):
    """
    Function which returns number of inserts which took place in given day
    @param oai_src_id: harvesting source identifier
    @return: Number of inserts during the given day
    """
    #sql_column = "date_harvested"
    #if method == "inserted":
    #    sql_column = "date_inserted"
    #

    if method == "inserted":
        column = OaiHARVESTLOG.date_inserted
    else:
        column = OaiHARVESTLOG.date_harvested
    res = db.session.query(func.count(column)).filter(OaiHARVESTLOG.id_oaiHARVEST == oai_src_id)\
        .filter(func.MONTH(column) == oai_date.month)\
        .filter(func.YEAR(column) == oai_date.year)\
        .filter(func.DAY(column) == oai_date.day).one()
    if res:
        return int(res[0])
    return 0


def get_entry_logs_size(oai_src_id):
    """
    Function which returns number of inserts which took place in given day
    @param oai_src_id: harvesting source identifier
    @return: Number of inserts during the given day
    """
    return OaiHARVESTLOG.query.filter(OaiHARVESTLOG.id_oaiHARVEST == oai_src_id).count()


def delete_holdingpen_entry(hpupdate_id):
    query = "DELETE FROM bibHOLDINGPEN WHERE changeset_id=%s"
    run_sql(query, (hpupdate_id, ))


def get_holdingpen_day_fragment(year, month, day, limit, start, filter_key):
    """
       returning the entries form the a particular day
    """
    filtersql = ""
    if filter_key != "":
        filtersql = " and oai_id like '%%%s%%' " % (filter_key, )
    query = "SELECT oai_id, changeset_date, changeset_id FROM bibHOLDINGPEN WHERE changeset_date > '%i-%i-%i 00:00:00' and changeset_date <= '%i-%i-%i 23:59:59' %s ORDER BY changeset_date LIMIT %i, %i" % (
        year, month, day, year, month, day, filtersql, start, limit)
    query_results = run_sql(query)
    return query_results


def get_holdingpen_day_size(year, month, day, filter_key):
    """
       returning the entries form the a particular day
    """
    filtersql = ""
    if filter_key != "":
        filtersql = " and oai_id like '%%%s%%' " % (filter_key, )
    query = "SELECT count(*) FROM bibHOLDINGPEN WHERE year(changeset_date) = '%i' and month(changeset_date) = '%i' and day(changeset_date) = '%i' %s" % (
        year, month, day, filtersql)
    query_results = run_sql(query)
    return int(query_results[0][0])


def get_holdingpen_month(year, month, filter_key):
    """
       Returning the statistics about the entries form a particular month
    """
    filtersql = ""
    if filter_key != "":
        filtersql = " and oai_id like '%%%s%%' " % (filter_key, )

    query = "select day(changeset_date), count(*) from bibHOLDINGPEN where year(changeset_date) = '%i' and month(changeset_date) = '%i' %s group by day(changeset_date)" % (
        year, month, filtersql)
    return run_sql(query)


def get_holdingpen_year(year, filter_key):
    """
    Returning the statistics about the entries from a particular year
    """
    filterSql = ""
    if filter_key != "":
        filterSql = " and oai_id like '%%%s%%' " % (filter_key, )
    query = "select month(changeset_date), count(*) from bibHOLDINGPEN where year(changeset_date) = '%i' %s group by month(changeset_date)" % (
        year, filterSql)
    return run_sql(query)


def get_holdingpen_years(filter_key):
    """
    Returning the particular years of records present in the holding pen
    """
    filtersql = ""
    if filter_key != "":
        filtersql = " where oai_id like '%%%s%%' " % (filter_key, )
    query = "select year(changeset_date), count(*) changeset_date from bibHOLDINGPEN %s group by year(changeset_date)" % (
        filtersql,)
    results = run_sql(query)
    return results


def get_holdingpen_entry_details(hpupdate_id):
    """
    Returning the detials of the Holding Pen entry, the result of this function is a tuple:
    (oai_id, record_id,  date_inserted, content)
    """
    query = "SELECT oai_id, id_bibrec, changeset_date, changeset_xml FROM bibHOLDINGPEN WHERE changeset_id=%s"
    return run_sql(query, (hpupdate_id,))[0]


def get_next_schedule():
    """Return the next scheduled oaiharvest tasks."""
    from sqlalchemy.orm.exc import NoResultFound
    from invenio.modules.scheduler.models import SchTASK
    try:
        res = SchTASK.query.filter(
            SchTASK.proc == "oaiharvest",
            SchTASK.runtime > datetime.now()
        ).order_by(SchTASK.runtime).one()
    except NoResultFound:
        return ("", "")
    else:
        return (res.runtime, res.status)
