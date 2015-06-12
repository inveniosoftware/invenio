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

The main API function is run_sql(), but see the others as well.
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


def get_table_update_time(table_name, run_on_slave=False):
    """Return update time of table_name.

    table_name can contain the wildcard '%', in which case we return the
    maximum update time value.
    """
    result = max(run_sql('''
        SELECT update_time
        FROM information_schema.tables
        WHERE table_name LIKE %s and table_schema=%s''',
        (table_name, cfg['CFG_DATABASE_NAME']), run_on_slave=run_on_slave))

    return str(result[0])


def get_table_status_info(table_name, run_on_slave=False):
    """Return table status information on table_name.

    Returns a dict with keys Name, Rows, Data_length, and Index_length.
    If table_name does not exist, returns an empty dict.
    """
    result = run_sql('''
        SELECT
            table_name,
            table_rows,
            data_length,
            index_length
        FROM
            information_schema.tables
        WHERE
            table_name=%s AND table_schema=%s''',
        (table_name, cfg['CFG_DATABASE_NAME']), run_on_slave=run_on_slave)

    if result:
        return {'Name': result[0][0], 'Rows': result[0][1],
                'Data_length': result[0][2], 'Index_length': result[0][3]}

    return {}


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


def check_table_exists(table_name):
    """Check if a table exists."""
    return run_sql("show tables like %s""", (table_name,))


def get_table_names():
    """get list tables."""
    return run_sql(
        """
        SHOW TABLES
        """)


def rlike():
    """Mysql RLIKE operator."""
    return "rlike"


def date_format(value, use_double_percent=True):
    """Format query to get date format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    if use_double_percent:
        date_format = "%%Y-%%m-%%d"
    else:
        date_format = "%Y %m %d"
    return "DATE_FORMAT(" + value + ", '" + date_format + "')"


def datetime_format(value, use_double_percent=True, use_quad_percent=False):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    if use_double_percent:
        date_format = "%%Y-%%m-%%d  %%H:%%i:%%s"
    elif not use_quad_percent:
        date_format = "%Y-%m-%d %H:%i:%s"
    else:
        date_format = "%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s"
    return "DATE_FORMAT(" + value + ", '" + date_format + "')"


def date_format_year_month(value, use_double_percent=True):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    if use_double_percent:
        date_format = "%%Y-%%m"
    else:
        date_format = "%Y-%m"
    return "DATE_FORMAT(" + value + ", '" + date_format + "')"


def date_format_year_month_day_hour(value, use_double_percent=True):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    if use_double_percent:
        date_format = "%%Y-%%m-%%d %%H"
    else:
        date_format = "%Y-%m-%d %H"
    return "DATE_FORMAT(" + value + ", '" + date_format + "')"


def date_format_ymdhis(value, use_double_percent=True):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    if use_double_percent:
        date_format = "%%Y%%m%%d%%H%%i%%s"
    else:
        date_format = "%Y%m%d%H%i%s"
    return "DATE_FORMAT(" + value + ", '" + date_format + "')"


def date_format_dby(value, use_double_percent=True):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    if use_double_percent:
        date_format = "%%d %%b %%Y"
    else:
        date_format = "%d %b %y"
    return "DATE_FORMAT(" + value + ", '" + date_format + "')"


def regexp():
    """mysql REGEXP operator."""
    return "REGEXP"


def truncate_table(table_name):
    """Truncade table."""
    run_sql("""TRUNCATE TABLE "%s" """ % table_name)
