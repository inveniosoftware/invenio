## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
Invenio utilities to run SQL queries.

The main API functions are:
    - run_sql()
    - run_sql_many()
but see the others as well.
"""

__revision__ = "$Id$"

# dbquery clients can import these from here:
# pylint: disable=W0611
from MySQLdb import Warning, Error, InterfaceError, DataError, \
                    DatabaseError, OperationalError, IntegrityError, \
                    InternalError, NotSupportedError, \
                    ProgrammingError
import string
import time
import marshal
import re
import os
from zlib import compress, decompress
from thread import get_ident
from invenio.config import CFG_ACCESS_CONTROL_LEVEL_SITE, \
    CFG_MISCUTIL_SQL_USE_SQLALCHEMY, \
    CFG_MISCUTIL_SQL_RUN_SQL_MANY_LIMIT

if CFG_MISCUTIL_SQL_USE_SQLALCHEMY:
    try:
        import sqlalchemy.pool as pool
        import MySQLdb as mysqldb
        mysqldb = pool.manage(mysqldb, use_threadlocal=True)
        connect = mysqldb.connect
    except ImportError:
        CFG_MISCUTIL_SQL_USE_SQLALCHEMY = False
        from MySQLdb import connect
else:
    from MySQLdb import connect

## DB config variables.  These variables are to be set in
## invenio-local.conf by admins and then replaced in situ in this file
## by calling "inveniocfg --update-dbexec".
## Note that they are defined here and not in config.py in order to
## prevent them from being exported accidentally elsewhere, as no-one
## should know DB credentials but this file.
## FIXME: this is more of a blast-from-the-past that should be fixed
## both here and in inveniocfg when the time permits.
CFG_DATABASE_HOST = 'localhost'
CFG_DATABASE_PORT = '3306'
CFG_DATABASE_NAME = 'invenio'
CFG_DATABASE_USER = 'invenio'
CFG_DATABASE_PASS = 'my123p$ss'

_DB_CONN = {}

def _db_login(relogin = 0):
    """Login to the database."""

    ## Note: we are using "use_unicode=False", because we want to
    ## receive strings from MySQL as Python UTF-8 binary string
    ## objects, not as Python Unicode string objects, as of yet.

    ## Note: "charset='utf8'" is needed for recent MySQLdb versions
    ## (such as 1.2.1_p2 and above).  For older MySQLdb versions such
    ## as 1.2.0, an explicit "init_command='SET NAMES utf8'" parameter
    ## would constitute an equivalent.  But we are not bothering with
    ## older MySQLdb versions here, since we are recommending to
    ## upgrade to more recent versions anyway.

    if CFG_MISCUTIL_SQL_USE_SQLALCHEMY:
        return connect(host=CFG_DATABASE_HOST, port=int(CFG_DATABASE_PORT),
                       db=CFG_DATABASE_NAME, user=CFG_DATABASE_USER,
                       passwd=CFG_DATABASE_PASS,
                       use_unicode=False, charset='utf8')
    else:
        thread_ident = (os.getpid(), get_ident())
    if relogin:
        _DB_CONN[thread_ident] = connect(host=CFG_DATABASE_HOST,
                                         port=int(CFG_DATABASE_PORT),
                                         db=CFG_DATABASE_NAME,
                                         user=CFG_DATABASE_USER,
                                         passwd=CFG_DATABASE_PASS,
                                         use_unicode=False, charset='utf8')
        return _DB_CONN[thread_ident]
    else:
        if _DB_CONN.has_key(thread_ident):
            return _DB_CONN[thread_ident]
        else:
            _DB_CONN[thread_ident] = connect(host=CFG_DATABASE_HOST,
                                             port=int(CFG_DATABASE_PORT),
                                             db=CFG_DATABASE_NAME,
                                             user=CFG_DATABASE_USER,
                                             passwd=CFG_DATABASE_PASS,
                                             use_unicode=False, charset='utf8')
            return _DB_CONN[thread_ident]

def _db_logout():
    """Close a connection."""
    try:
        del _DB_CONN[(os.getpid(), get_ident())]
    except KeyError:
        pass

def close_connection(dbhost=CFG_DATABASE_HOST):
    """
    Enforce the closing of a connection
    Highly relevant in multi-processing and multi-threaded modules
    """
    try:
        db = _DB_CONN[(os.getpid(), get_ident())]
        cur = db.cursor()
        cur.execute("UNLOCK TABLES")
        db.close()
        del _DB_CONN[(os.getpid(), get_ident())]
    except KeyError:
        pass

def run_sql(sql, param=None, n=0, with_desc=0):
    """Run SQL on the server with PARAM and return result.

    @param param: tuple of string params to insert in the query (see
        notes below)

    @param n: number of tuples in result (0 for unbounded)

    @param with_desc: if True, will return a DB API 7-tuple describing
        columns in query.

    @return: If SELECT, SHOW, DESCRIBE statements, return tuples of
        data, followed by description if parameter with_desc is
        provided.  If INSERT, return last row id.  Otherwise return
        SQL result as provided by database.

    @note: When the site is closed for maintenance (as governed by the
        config variable CFG_ACCESS_CONTROL_LEVEL_SITE), do not attempt
        to run any SQL queries but return empty list immediately.
        Useful to be able to have the website up while MySQL database
        is down for maintenance, hot copies, table repairs, etc.

    @note: In case of problems, exceptions are returned according to
        the Python DB API 2.0.  The client code can import them from
        this file and catch them.
    """

    if CFG_ACCESS_CONTROL_LEVEL_SITE == 3:
        # do not connect to the database as the site is closed for maintenance:
        return []

    ### log_sql_query(sql, param) ### UNCOMMENT ONLY IF you REALLY want to log all queries

    if param:
        param = tuple(param)

    try:
        db = _db_login()
        cur = db.cursor()
        rc = cur.execute(sql, param)
    except OperationalError: # unexpected disconnect, bad malloc error, etc
        # FIXME: now reconnect is always forced, we may perhaps want to ping() first?
        try:
            db = _db_login(relogin=1)
            cur = db.cursor()
            rc = cur.execute(sql, param)
        except OperationalError: # again an unexpected disconnect, bad malloc error, etc
            raise

    if string.upper(string.split(sql)[0]) in ("SELECT", "SHOW", "DESC", "DESCRIBE"):
        if n:
            recset = cur.fetchmany(n)
        else:
            recset = cur.fetchall()
        if with_desc:
            return recset, cur.description
        else:
            return recset
    else:
        if string.upper(string.split(sql)[0]) == "INSERT":
            rc =  cur.lastrowid
        return rc

def run_sql_many(query, params, limit=CFG_MISCUTIL_SQL_RUN_SQL_MANY_LIMIT):
    """Run SQL on the server with PARAM.
    This method does executemany and is therefore more efficient than execute
    but it has sense only with queries that affect state of a database
    (INSERT, UPDATE). That is why the results just count number of affected rows

    @param params: tuple of tuple of string params to insert in the query

    @param limit: query will be executed in parts when number of
         parameters is greater than limit (each iteration runs at most
         `limit' parameters)

    @return: SQL result as provided by database
    """
    i = 0
    r = None
    while i < len(params):
        ## make partial query safely (mimicking procedure from run_sql())
        try:
            db = _db_login()
            cur = db.cursor()
            rc = cur.executemany(query, params[i:i+limit])
        except OperationalError:
            try:
                db = _db_login(relogin=1)
                cur = db.cursor()
                rc = cur.executemany(query, params[i:i+limit])
            except OperationalError:
                raise
        ## collect its result:
        if r is None:
            r = rc
        else:
            r += rc
        i += limit
    return r

def blob_to_string(ablob):
    """Return string representation of ABLOB.  Useful to treat MySQL
    BLOBs in the same way for both recent and old MySQLdb versions.
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

def log_sql_query(sql, param=None):
    """Log SQL query into prefix/var/log/dbquery.log log file.  In order
       to enable logging of all SQL queries, please uncomment one line
       in run_sql() above. Useful for fine-level debugging only!
    """
    from invenio.config import CFG_LOGDIR
    from invenio.dateutils import convert_datestruct_to_datetext
    from invenio.textutils import indent_text
    log_path = CFG_LOGDIR + '/dbquery.log'
    date_of_log = convert_datestruct_to_datetext(time.localtime())
    message = date_of_log + '-->\n'
    message += indent_text('Query:\n' + indent_text(str(sql), 2, wrap=True), 2)
    message += indent_text('Params:\n' + indent_text(str(param), 2, wrap=True), 2)
    message += '-----------------------------\n\n'
    try:
        log_file = open(log_path, 'a+')
        log_file.writelines(message)
        log_file.close()
    except:
        pass

def get_table_update_time(tablename):
    """Return update time of TABLENAME.  TABLENAME can contain
       wildcard `%' in which case we return the maximum update time
       value.
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
    res = run_sql("SHOW TABLE STATUS LIKE %s", (tablename, ))
    update_times = [] # store all update times
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

def get_table_status_info(tablename):
    """Return table status information on TABLENAME.  Returned is a
       dict with keys like Name, Rows, Data_length, Max_data_length,
       etc.  If TABLENAME does not exist, return empty dict.
    """
    # Note: again a hack so that it works on all MySQL 4.0, 4.1, 5.0
    res = run_sql("SHOW TABLE STATUS LIKE %s", (tablename, ))
    table_status_info = {} # store all update times
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

def serialize_via_marshal(obj):
    """Serialize Python object via marshal into a compressed string."""
    return compress(marshal.dumps(obj))

def deserialize_via_marshal(astring):
    """Decompress and deserialize string into a Python object via marshal."""
    return marshal.loads(decompress(astring))

def wash_table_column_name(colname):
    """
    Evaluate table-column name to see if it is clean.
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

def real_escape_string(unescaped_string):
    """
    Escapes special characters in the unescaped string for use in a DB query.

    @param unescaped_string: The string to be escaped
    @type unescaped_string: str

    @return: Returns the escaped string
    @rtype: str
    """
    connection_object = _db_login()
    escaped_string = connection_object.escape_string(unescaped_string)
    return escaped_string
