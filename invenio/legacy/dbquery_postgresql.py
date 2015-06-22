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

The main API function is run_sql(), but see the others as well.
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
            return str(ablob)
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


def get_table_status_info(table_name, run_on_slave=False):
    """Return table status information on table_name.

    Returns a dict with keys Name, Rows, Data_length, and Index_length.
    If table_name does not exist, returns an empty dict.
    """
    result = run_sql('''
        SELECT
            relname,
            n_tup_ins - n_tup_del,
            pg_total_relation_size(relname::text) - pg_indexes_size(relname::text),
            pg_indexes_size(relname::text)
        FROM
            pg_stat_all_tables
        WHERE
            relname=%s''',
        (table_name,), run_on_slave=run_on_slave)

    if result:
        return {'Name': result[0][0], 'Rows': result[0][1],
                'Data_length': result[0][2], 'Index_length': result[0][3]}

    return {}


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
    # connection_object = db.engine.raw_connection()
    # escaped_string = connection_object.escape(unescaped_string)
    from psycopg2.extensions import adapt
    return str(adapt(unescaped_string))


def check_table_exists(table_name):
    """Check if a table exists."""
    return run_sql(
        """
        SELECT EXISTS (
            SELECT 1
            FROM   pg_catalog.pg_class c
            JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE    c.relname = %s
            AND    c.relkind = 'r'
        )""", (table_name,))[0][0]


def get_table_names():
    """get list tables."""
    return run_sql(
        """
        select relname
        FROM   pg_catalog.pg_class c
        JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        where nspname = 'public'
        """)


def rlike():
    """Mysql RLIKE operator."""
    return "~*"


def date_format(value, use_double_percent=True):
    """Format query to get date format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    date_format = "YYYY-mm-dd"
    return "to_char(" + value + ", '" + date_format + "')"


def datetime_format(value, use_double_percent=True, use_quad_percent=False):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    date_format = "YYYY-mm-dd HH24:MI:SS"
    return "to_char(" + value + ", '" + date_format + "')"


def date_format_year_month(value, use_double_percent=True):
    """Format query to get date format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    date_format = "YYYY-mm"
    return "to_char(" + value + ", '" + date_format + "')"


def date_format_year_month_day_hour(value, use_double_percent=True):
    """Format query to get date format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    date_format = "YYYY-mm-dd HH24"
    return "to_char(" + value + ", '" + date_format + "')"


def date_format_ymdhis(value, use_double_percent=True):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    date_format = "YYYYmmdd HH24MISS"
    return "to_char(" + value + ", '" + date_format + "')"


def date_format_dby(value, use_double_percent=True):
    """Format query to get date/time format.

    :param value: date
    :param use_double_percent: True if, t's needed use %%Y instead %Y
    :return: partial query
    """
    date_format = "dd month YYYY"
    return "to_char(" + value + ", '" + date_format + "')"


def regexp():
    """mysql REGEXP operator."""
    return "~"


def truncate_table(table_name):
    """truncade table."""
    return run_sql(
        """TRUNCATE TABLE "%s" RESTART IDENTITY CASCADE""" % table_name)
