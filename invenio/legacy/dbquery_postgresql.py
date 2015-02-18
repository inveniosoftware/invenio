# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

"""
Invenio utilities to run SQL queries.

The main API functions are:
    - run_sql()
    - run_sql_many()
    - run_sql_with_limit()
but see the others as well.
"""
from __future__ import print_function

import gc

import re

import string

import sys

import time

import warnings

from flask import current_app, has_app_context

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db


def _db_login(*args, **kwargs):
    warnings.warn("Use of _db_login is obsolete for postgresql.",
                  DeprecationWarning)


class InvenioDbQueryWildcardLimitError(Exception):

    """Exception raised when query limit reached."""

    def __init__(self, res):
        """Initialization."""
        self.res = res


def run_sql(sql, param=None, n=0, with_desc=False, with_dict=False,
            run_on_slave=False, connection=None):
    """Run SQL on the server with PARAM and return result.

    :param param: tuple of string params to insert in the query (see
    notes below)
    :param n: number of tuples in result (0 for unbounded)
    :param with_desc: if True, will return a DB API 7-tuple describing
    columns in query.
    :param with_dict: if True, will return a list of dictionaries
    composed of column-value pairs
    :param connection: if provided, uses the given connection.
    :return: If SELECT, SHOW, DESCRIBE statements, return tuples of data,
    followed by description if parameter with_desc is
    provided.
    If SELECT and with_dict=True, return a list of dictionaries
    composed of column-value pairs, followed by description
    if parameter with_desc is provided.
    If INSERT, return last row id.
    Otherwise return SQL result as provided by database.

    @note: When the site is closed for maintenance (as governed by the
    config variable CFG_ACCESS_CONTROL_LEVEL_SITE), do not attempt
    to run any SQL queries but return empty list immediately.
    Useful to be able to have the website up while MySQL database
    is down for maintenance, hot copies, table repairs, etc.
    @note: In case of problems, exceptions are returned according to
    the Python DB API 2.0.  The client code can import them from
    this file and catch them.
    """
    if cfg['CFG_ACCESS_CONTROL_LEVEL_SITE'] == 3:
        # do not connect to the database as the site is closed for maintenance:
        return []
    elif cfg['CFG_ACCESS_CONTROL_LEVEL_SITE'] > 0:
        # Read only website
        if not sql.upper().startswith("SELECT") and \
                not sql.upper().startswith("SHOW"):
            return

    if param:
        param = tuple(param)

    # FIXME port database slave support
    dbhost = cfg['CFG_DATABASE_HOST']
    if run_on_slave and cfg['CFG_DATABASE_SLAVE']:
        dbhost = cfg['CFG_DATABASE_SLAVE']

    if 'sql-logger' in cfg.get('CFG_DEVEL_TOOLS', []):
        log_sql_query(dbhost, sql, param)

    gc.disable()
    engine = db.engine.execution_options(use_unicode=0)
    sql = sql.replace('`', '"')
    current_app.logger.info(sql)
    if param is None:
        cur = engine.execute(sql.replace('%', '%%'))
    else:
        cur = engine.execute(sql, (param, ))
    gc.enable()

    if string.upper(string.split(sql)[0]) in \
            ("SELECT", "SHOW", "DESC", "DESCRIBE"):
        if n:
            recset = cur.fetchmany(n)
        else:
            recset = cur.fetchall()

        from invenio.base.helpers import utf8ifier
        recset = map(dict if with_dict else tuple, recset)
        recset = utf8ifier(recset)

        if with_desc:
            return recset, cur.description
        else:
            return recset
    else:
        if string.upper(string.split(sql)[0]) == "INSERT":
            return cur.lastrowid
        return cur


def run_sql_many(query, params, limit=None, run_on_slave=False):
    """Run SQL on the server with PARAM.

    This method does executemany and is therefore more efficient than execute
    but it has sense only with queries that affect state of a database
    (INSERT, UPDATE). That is why the results just count number of affected rows

    :param params: tuple of tuple of string params to insert in the query

    :param limit: query will be executed in parts when number of
         parameters is greater than limit (each iteration runs at most
         `limit' parameters)

    :return: SQL result as provided by database
    """
    if limit is None:
        limit = cfg['CFG_MISCUTIL_SQL_RUN_SQL_MANY_LIMIT']

    if cfg['CFG_ACCESS_CONTROL_LEVEL_SITE'] == 3:
        # do not connect to the database as the site is closed for maintenance:
        return []
    elif cfg['CFG_ACCESS_CONTROL_LEVEL_SITE'] > 0:
        # Read only website
        if not query.upper().startswith("SELECT") and \
                not query.upper().startswith("SHOW"):
            return

    # dbhost = cfg['CFG_DATABASE_HOST']
    # if run_on_slave and cfg['CFG_DATABASE_SLAVE']:
        # dbhost = cfg['CFG_DATABASE_SLAVE']
    i = 0
    r = None
    while i < len(params):
        # make partial query safely (mimicking procedure from run_sql())
        gc.disable()
        rc = db.session.execute(query, params[i:i + limit]).fetchall()
        gc.enable()
        # collect its result:
        if r is None:
            r = rc
        else:
            r += rc
        i += limit
    return r


def blob_to_string(ablob):
    """Return string representation of ABLOB.

    Useful to treat MySQL BLOBs in the same way for both recent and old
    MySQLdb versions.
    """
    # FIXME it works also for PostgreSQL?
    if ablob:
        if type(ablob) is str:
            # BLOB is already a string in MySQLdb 0.9.2
            return ablob
        else:
            # BLOB is array.array in MySQLdb 1.0.0 and later
            return ablob.tostring()
    else:
        return ablob


def log_sql_query(dbhost, sql, param=None):
    """Log SQL query into prefix/var/log/dbquery.log log file.

    In order to enable logging of all SQL queries, please uncomment one line
    in run_sql() above. Useful for fine-level debugging only!
    """
    from invenio.utils.date import convert_datestruct_to_datetext
    from invenio.utils.text import indent_text
    date_of_log = convert_datestruct_to_datetext(time.localtime())
    message = date_of_log + '-->\n'
    message += indent_text('Host:\n' +
                           indent_text(str(dbhost), 2, wrap=True), 2)
    message += indent_text('Query:\n' + indent_text(str(sql), 2, wrap=True), 2)
    message += indent_text('Params:\n' +
                           indent_text(str(param), 2, wrap=True), 2)
    message += '-----------------------------\n\n'
    if has_app_context():
        current_app.logger.info(message)
    else:
        print(message, file=sys.stderr)


def get_table_update_time(tablename, run_on_slave=False):
    """Return update time of TABLENAME.

    TABLENAME can contain wildcard `%' in which case we return the maximum
    update time value.
    """
    # FIXME how can I implement it with PostgreSQL???
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_table_status_info(tablename, run_on_slave=False):
    """Return table status information on TABLENAME.

    Returned is a dict with keys like Name, Rows, Data_length, Max_data_length,
    etc.  If TABLENAME does not exist, return empty dict.
    """
    # FIXME how can I implement it with PostgreSQL???
    res = run_sql("""SHOW TABLE STATUS LIKE "%s" """, (tablename,),
                  run_on_slave=run_on_slave)
    table_status_info = {}  # store all update times
    for row in res:
        if type(row[10]) is long or \
           row[10] is None:
            # MySQL-4.1 and 5.0 have creation time in 11th position:
            table_status_info['Name'] = row[0]
            table_status_info['Rows'] = row[4]
            table_status_info['Data_length'] = row[6]
            table_status_info['Max_data_length'] = row[8]
            table_status_info['Create_time'] = row[11]
            table_status_info['Update_time'] = row[12]
        else:
            # MySQL-4.0 has creation_time in 10th position, which is
            # of type datetime.datetime or str (depending on the
            # version of MySQLdb):
            table_status_info['Name'] = row[0]
            table_status_info['Rows'] = row[3]
            table_status_info['Data_length'] = row[5]
            table_status_info['Max_data_length'] = row[7]
            table_status_info['Create_time'] = row[10]
            table_status_info['Update_time'] = row[11]
    return table_status_info


def wash_table_column_name(colname):
    """Evaluate table-column name to see if it is clean.

    This function accepts only names containing [a-zA-Z0-9_].

    :param colname: The string to be checked
    @type colname: str

    :return: colname if test passed

    :raise Exception: Raises an exception if colname is invalid.
    """
    if re.search('[^\w]', colname):
        raise Exception('The table column %s is not valid.' % repr(colname))
    return colname


def real_escape_string(unescaped_string, run_on_slave=False):
    """Escape special characters in the unescaped string for use in a DB query.

    :param unescaped_string: The string to be escaped
    :type unescaped_string: str

    :return: Returns the escaped string
    """
    # dbhost = cfg['CFG_DATABASE_HOST']
    # if run_on_slave and cfg['CFG_DATABASE_SLAVE']:
    #    dbhost = cfg['CFG_DATABASE_SLAVE']
    connection_object = db.engine.raw_connection()
    escaped_string = connection_object.escape(unescaped_string)
    return escaped_string


def run_sql_with_limit(query, param=None, n=0, with_desc=False,
                       wildcard_limit=0, run_on_slave=False):
    """Run SQL with limit.

    This function should be used in some cases, instead of run_sql function, in
    order to protect the db from queries that might take a log time to respond
    Ex: search queries like [a-z]+ ; cern*; a->z;
    The parameters are exactly the ones for run_sql function.
    In case the query limit is reached, an InvenioDbQueryWildcardLimitError
    will be raised.
    """
    try:
        int(wildcard_limit)
    except ValueError:
        raise

    if wildcard_limit < 1:  # no limit on the wildcard queries
        return run_sql(query, param, n, with_desc, run_on_slave=run_on_slave)
    safe_query = query + " limit %s" % wildcard_limit
    res = run_sql(safe_query, param, n, with_desc, run_on_slave=run_on_slave)
    if len(res) == wildcard_limit:
        raise InvenioDbQueryWildcardLimitError(res)
    return res
