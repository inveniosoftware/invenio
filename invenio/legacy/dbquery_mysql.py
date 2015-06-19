# -*- coding: utf-8 -*-
#
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

"""Invenio utilities to run SQL queries.

The main API functions are:
    - run_sql()
    - run_sql_many()
    - run_sql_with_limit()
but see the others as well.
"""

# dbquery clients can import these from here:
# pylint: disable=W0611
import gc

import os

import re

import string

import time

from flask import current_app

from invenio.base.globals import cfg
from invenio.utils.datastructures import LazyDict

from MySQLdb import OperationalError as MySQLdbOperationalError

from thread import get_ident

from sqlalchemy.exc import InterfaceError, OperationalError

from werkzeug.utils import cached_property

__revision__ = "$Id$"


class DBConnect(object):

    """DBConnect."""

    def __call__(self, *args, **kwargs):
        """Call."""
        return self._connect(*args, **kwargs)

    @cached_property
    def _connect(self):
        if cfg['CFG_MISCUTIL_SQL_USE_SQLALCHEMY']:
            try:
                import sqlalchemy.pool as pool
                import MySQLdb as mysqldb
                mysqldb = pool.manage(mysqldb, use_threadlocal=True)
                connect = mysqldb.connect
            except ImportError:
                cfg['CFG_MISCUTIL_SQL_USE_SQLALCHEMY'] = False
                from MySQLdb import connect
        else:
            from MySQLdb import connect
        return connect


def unlock_all(app):
    """Unlock all."""
    for dbhost in _DB_CONN.keys():
        for db in _DB_CONN[dbhost].values():
            try:
                cur = db.cur()
                cur.execute("UNLOCK TABLES")
            except Exception:
                pass
    return app


def _db_conn():
    current_app.teardown_appcontext_funcs.append(unlock_all)
    out = {}
    out[cfg['CFG_DATABASE_HOST']] = {}
    out[cfg['CFG_DATABASE_SLAVE']] = {}
    return out

connect = DBConnect()
_DB_CONN = LazyDict(_db_conn)


def _get_password_from_database_password_file(user):
    """Parse CFG_DATABASE_PASSWORD_FILE and return password for user."""
    pwfile = cfg.get("CFG_DATABASE_PASSWORD_FILE", None)
    if pwfile and os.path.exists(pwfile):
        for row in open(pwfile):
            if row.strip():
                a_user, pwd = row.strip().split(" // ")
                if user == a_user:
                    return pwd
        raise ValueError("user '%s' not found in database password file '%s'"
                         % (user, pwfile))
    raise IOError("No password defined for user '%s' but database password "
                  "file is not available" % user)


def get_connection_for_dump_on_slave():
    """Return a slave connection for performing dbdump operation on a slave."""
    su_user = cfg.get("CFG_DATABASE_SLAVE_SU_USER", "")
    if "CFG_DATABASE_SLAVE_SU_PASS" not in cfg:
        cfg["CFG_DATABASE_SLAVE_SU_PASS"] = \
            _get_password_from_database_password_file(su_user)

    connection = connect(host=cfg.get("CFG_DATABASE_SLAVE", ""),
                         port=int(cfg.get("CFG_DATABASE_PORT"), 3306),
                         db=cfg.get("CFG_DATABASE_NAME", ""),
                         user=su_user,
                         passwd=cfg.get("CFG_DATABASE_SLAVE_SU_PASS", ""),
                         use_unicode=False, charset='utf8')
    connection.autocommit(True)
    return connection


class InvenioDbQueryWildcardLimitError(Exception):

    """Exception raised when query limit reached."""

    def __init__(self, res):
        """Initialization."""
        self.res = res


def _db_login(dbhost=None, relogin=0):
    """Login to the database."""
    # Note: we are using "use_unicode=False", because we want to
    # receive strings from MySQL as Python UTF-8 binary string
    # objects, not as Python Unicode string objects, as of yet.

    # Note: "charset='utf8'" is needed for recent MySQLdb versions
    # (such as 1.2.1_p2 and above).  For older MySQLdb versions such
    # as 1.2.0, an explicit "init_command='SET NAMES utf8'" parameter
    # would constitute an equivalent.  But we are not bothering with
    # older MySQLdb versions here, since we are recommending to
    # upgrade to more recent versions anyway.
    if dbhost is None:
        dbhost = cfg['CFG_DATABASE_HOST']

    if cfg['CFG_MISCUTIL_SQL_USE_SQLALCHEMY']:
        return connect(host=dbhost,
                       port=int(cfg['CFG_DATABASE_PORT']),
                       db=cfg['CFG_DATABASE_NAME'],
                       user=cfg['CFG_DATABASE_USER'],
                       passwd=cfg['CFG_DATABASE_PASS'],
                       use_unicode=False,
                       charset='utf8')
    else:
        thread_ident = (os.getpid(), get_ident())
    if relogin:
        connection = _DB_CONN[dbhost][thread_ident] = connect(
            host=dbhost,
            port=int(cfg['CFG_DATABASE_PORT']),
            db=cfg['CFG_DATABASE_NAME'],
            user=cfg['CFG_DATABASE_USER'],
            passwd=cfg['CFG_DATABASE_PASS'],
            use_unicode=False, charset='utf8'
        )
        connection.autocommit(True)
        return connection
    else:
        if thread_ident in _DB_CONN[dbhost]:
            return _DB_CONN[dbhost][thread_ident]
        else:
            connection = _DB_CONN[dbhost][thread_ident] = connect(
                host=dbhost,
                port=int(cfg['CFG_DATABASE_PORT']),
                db=cfg['CFG_DATABASE_NAME'],
                user=cfg['CFG_DATABASE_USER'],
                passwd=cfg['CFG_DATABASE_PASS'],
                use_unicode=False, charset='utf8'
            )
            connection.autocommit(True)
            return connection


def _db_logout(dbhost=None):
    """Close a connection."""
    if dbhost is None:
        dbhost = cfg['CFG_DATABASE_HOST']
    try:
        del _DB_CONN[dbhost][(os.getpid(), get_ident())]
    except KeyError:
        pass


def close_connection(dbhost=None):
    """Enforce the closing of a connection.

    Highly relevant in multi-processing and multi-threaded modules
    """
    if dbhost is None:
        dbhost = cfg['CFG_DATABASE_HOST']
    try:
        db = _DB_CONN[dbhost][(os.getpid(), get_ident())]
        cur = db.cursor()
        cur.execute("UNLOCK TABLES")
        db.close()
        del _DB_CONN[dbhost][(os.getpid(), get_ident())]
    except KeyError:
        pass


def run_sql(sql, param=None, n=0, with_desc=False, with_dict=False,
            run_on_slave=False, connection=None):
    """Run SQL on the server with PARAM and return result.

    @param param: tuple of string params to insert in the query (see
    notes below)
    @param n: number of tuples in result (0 for unbounded)
    @param with_desc: if True, will return a DB API 7-tuple describing
    columns in query.
    @param with_dict: if True, will return a list of dictionaries
    composed of column-value pairs
    @param connection: if provided, uses the given connection.
    @return: If SELECT, SHOW, DESCRIBE statements, return tuples of data,
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
        if not sql.upper().startswith("SELECT") \
           and not sql.upper().startswith("SHOW"):
            return

    if param:
        param = tuple(param)

    dbhost = cfg['CFG_DATABASE_HOST']
    if run_on_slave and cfg['CFG_DATABASE_SLAVE']:
        dbhost = cfg['CFG_DATABASE_SLAVE']

    if 'sql-logger' in cfg.get('CFG_DEVEL_TOOLS', []):
        log_sql_query(dbhost, sql, param)

    try:
        db = connection or _db_login(dbhost)
        cur = db.cursor()
        cur.execute("SET SESSION sql_mode = %s", ['ANSI_QUOTES'])
        gc.disable()
        rc = cur.execute(sql, param)
        gc.enable()
    except (OperationalError, MySQLdbOperationalError, InterfaceError):
        # unexpected disconnect, bad malloc error, etc
        # FIXME: now reconnect is always forced, we may perhaps want to ping()
        # first?
        if connection is not None:
            raise
        try:
            db = _db_login(dbhost, relogin=1)
            cur = db.cursor()
            cur.execute("SET SESSION sql_mode = %s", ['ANSI_QUOTES'])
            gc.disable()
            rc = cur.execute(sql, param)
            gc.enable()
        except (OperationalError, MySQLdbOperationalError, InterfaceError):
            # unexpected disconnect, bad malloc error, etc
            raise

    if string.upper(string.split(sql)[0]) in \
       ("SELECT", "SHOW", "DESC", "DESCRIBE"):
        if n:
            recset = cur.fetchmany(n)
        else:
            recset = cur.fetchall()

        if with_dict:  # return list of dictionaries
            # let's extract column names
            keys = [row[0] for row in cur.description]
            # let's construct a list of dictionaries
            list_dict_results = [dict(zip(*[keys, values]))
                                 for values in recset]

            if with_desc:
                return list_dict_results, cur.description
            else:
                return list_dict_results
        else:
            if with_desc:
                return recset, cur.description
            else:
                return recset
    else:
        if string.upper(string.split(sql)[0]) == "INSERT":
            rc = cur.lastrowid
        return rc


def run_sql_many(query, params, limit=None, run_on_slave=False):
    """Run SQL on the server with PARAM.

    This method does executemany and is therefore more efficient than execute
    but it has sense only with queries that affect state of a database
    (INSERT, UPDATE). That is why the results just count number of affected
    rows.

    @param params: tuple of tuple of string params to insert in the query

    @param limit: query will be executed in parts when number of
         parameters is greater than limit (each iteration runs at most
         `limit' parameters)

    @return: SQL result as provided by database
    """
    if limit is None:
        limit = cfg['CFG_MISCUTIL_SQL_RUN_SQL_MANY_LIMIT']

    if cfg['CFG_ACCESS_CONTROL_LEVEL_SITE'] == 3:
        # do not connect to the database as the site is closed for maintenance:
        return []
    elif cfg['CFG_ACCESS_CONTROL_LEVEL_SITE'] > 0:
        # Read only website
        if not query.upper().startswith("SELECT") \
           and not query.upper().startswith("SHOW"):
            return

    dbhost = cfg['CFG_DATABASE_HOST']
    if run_on_slave and cfg['CFG_DATABASE_SLAVE']:
        dbhost = cfg['CFG_DATABASE_SLAVE']
    i = 0
    r = None
    while i < len(params):
        # make partial query safely (mimicking procedure from run_sql())
        try:
            db = _db_login(dbhost)
            cur = db.cursor()
            gc.disable()
            rc = cur.executemany(query, params[i:i + limit])
            gc.enable()
        except (OperationalError, MySQLdbOperationalError, InterfaceError):
            try:
                db = _db_login(dbhost, relogin=1)
                cur = db.cursor()
                gc.disable()
                rc = cur.executemany(query, params[i:i + limit])
                gc.enable()
            except (OperationalError, MySQLdbOperationalError, InterfaceError):
                raise
        # collect its result:
        if r is None:
            r = rc
        else:
            r += rc
        i += limit
    return r


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


def blob_to_string(ablob):
    """Return string representation of ABLOB.

    Useful to treat MySQL BLOBs in the same way for both recent and old
    MySQLdb versions.
    """
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
    from flask import current_app
    from invenio.utils.date import convert_datestruct_to_datetext
    from invenio.utils.text import indent_text
    date_of_log = convert_datestruct_to_datetext(time.localtime())
    message = date_of_log + '-->\n'
    message += indent_text('Host:\n' + indent_text(str(dbhost), 2, wrap=True),
                           2)
    message += indent_text('Query:\n' + indent_text(str(sql), 2, wrap=True), 2)
    message += indent_text('Params:\n' + indent_text(str(param), 2, wrap=True),
                           2)
    message += '-----------------------------\n\n'
    try:
        current_app.logger.info(message)
    except Exception:
        pass


def get_table_update_time(tablename, run_on_slave=False):
    """Return update time of TABLENAME.

    TABLENAME can contain wildcard `%' in which case we return the maximum
    update time value.
    """
    # Note: in order to work with all of MySQL 4.0, 4.1, 5.0, this
    # function uses SHOW TABLE STATUS technique with a dirty column
    # position lookup to return the correct value.  (Making use of
    # Index_Length column that is either of type long (when there are
    # some indexes defined) or of type None (when there are no indexes
    # defined, e.g. table is empty).  When we shall use solely
    # MySQL-5.0, we can employ a much cleaner technique of using
    # SELECT UPDATE_TIME FROM INFORMATION_SCHEMA.TABLES WHERE
    # table_name='collection'.
    res = run_sql("SHOW TABLE STATUS LIKE %s", (tablename,),
                  run_on_slave=run_on_slave)
    update_times = []  # store all update times
    for row in res:
        if type(row[10]) is long or \
           row[10] is None:
            # MySQL-4.1 and 5.0 have creation_time in 11th position,
            # so return next column:
            update_times.append(str(row[12]))
        else:
            # MySQL-4.0 has creation_time in 10th position, which is
            # of type datetime.datetime or str (depending on the
            # version of MySQLdb), so return next column:
            update_times.append(str(row[11]))
    return max(update_times)


def get_table_status_info(tablename, run_on_slave=False):
    """Return table status information on TABLENAME.

    Returned is a dict with keys like Name, Rows, Data_length, Max_data_length,
    etc. If TABLENAME does not exist, return empty dict.
    """
    # Note: again a hack so that it works on all MySQL 4.0, 4.1, 5.0
    res = run_sql("SHOW TABLE STATUS LIKE %s", (tablename,),
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

    @param colname: The string to be checked
    @type colname: str

    @return: colname if test passed
    @rtype: str

    @raise Exception: Raises an exception if colname is invalid.
    """
    if re.search('[^\w]', colname):
        raise Exception('The table column %s is not valid.' % repr(colname))
    return colname


def real_escape_string(unescaped_string, run_on_slave=False):
    """Escape special characters in the unescaped string for use in a DB query.

    @param unescaped_string: The string to be escaped
    @type unescaped_string: str

    @return: Returns the escaped string
    @rtype: str
    """
    dbhost = cfg['CFG_DATABASE_HOST']
    if run_on_slave and cfg['CFG_DATABASE_SLAVE']:
        dbhost = cfg['CFG_DATABASE_SLAVE']
    connection_object = _db_login(dbhost)
    escaped_string = connection_object.escape_string(unescaped_string)
    return escaped_string
