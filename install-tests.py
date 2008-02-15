# -*- coding: utf-8 -*-
##
## $Id$
##
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

"""
Invenio tests to be called after 'make install'.  The script checks
whether the database is accessible, and if not, it advises on how to
setup connection rights.
"""

from invenio.dbquery import CFG_DATABASE_HOST, CFG_DATABASE_NAME, \
     CFG_DATABASE_USER, CFG_DATABASE_PASS

## import modules:
try:
    import MySQLdb
    import sys
    import os
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)

## try to connect to the DB server:
try:
    db = MySQLdb.connect(host=CFG_DATABASE_HOST, db=CFG_DATABASE_NAME, user=CFG_DATABASE_USER, passwd=CFG_DATABASE_PASS)
except MySQLdb.Error, e:
    print """
    ******************************************************
    ** DATABASE CONNECTIVITY ERROR %(errcode)d: %(errmsg)s.
    ******************************************************
    ** Perhaps you need to set up connection rights?    **
    **                                                  **
    ** If yes, then please login as MySQL admin user    **
    ** and run the following commands now:              **
    **
    **  $ mysql -h %(dbhost)s -u root -p mysql
    **    mysql> CREATE DATABASE %(dbname)s DEFAULT CHARACTER SET utf8;
    **    mysql> GRANT ALL PRIVILEGES ON %(dbname)s.* TO %(dbuser)s@%(webhost)s IDENTIFIED BY '%(dbpass)s';
    **    mysql> QUIT
    **
    ** The values printed above were detected from your **
    ** invenio.conf file.  If they are not right, then  **
    ** please edit the conf file and rerun inveniocfg.  **
    **                                                  **
    ** If the problem is not with the connection rights **
    ** then please inspect the above error message and  **
    ** fix the problem before continuing.               **
    ******************************************************
    """ % {'errcode': e.args[0],
           'errmsg': e.args[1],
           'dbname': CFG_DATABASE_NAME,
           'dbhost': CFG_DATABASE_HOST,
           'dbuser': CFG_DATABASE_USER,
           'dbpass': CFG_DATABASE_PASS,
           'webhost': CFG_DATABASE_HOST == 'localhost' and 'localhost' or os.popen('hostname -f', 'r').read().strip(),
           }
    sys.exit(1)

## execute test query:
try:
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    row = cursor.fetchone()
except MySQLdb.Error, e:
    print """
    ******************************************************
    ** DATABASE QUERY ERROR %(errcode)d: %(errmsg)s.
    ******************************************************
    ** Please inspect the above error message and       **
    ** please fix the problem before continuing.        **
    ******************************************************
    """ % {'errcode': e.args[0],
           'errmsg': e.args[1],
           }
    sys.exit(1)

## test insert/select of a Unicode string to detect possible
## Python/MySQL/MySQLdb mis-setup:
try:
    db.close()
    db = MySQLdb.connect(host=CFG_DATABASE_HOST, db=CFG_DATABASE_NAME, user=CFG_DATABASE_USER, passwd=CFG_DATABASE_PASS,
                         use_unicode=False, charset='utf8')
    cursor = db.cursor()
    x = "β" # Greek beta in UTF-8 is 0xCEB2
    cursor.execute("CREATE TEMPORARY TABLE test__invenio__utf8 (x char(1), y varbinary(2)) DEFAULT CHARACTER SET utf8")
    cursor.execute("INSERT INTO test__invenio__utf8 VALUES (%s,%s)", (x, x))
    cursor.execute("SELECT x,y,HEX(x),HEX(y),LENGTH(x),LENGTH(y),CHAR_LENGTH(x),CHAR_LENGTH(y) FROM test__invenio__utf8")
    res = cursor.fetchone()
    assert res == ('\xce\xb2', '\xce\xb2', 'CEB2', 'CEB2', 2L, 2L, 1L, 2L)
    cursor.execute("DROP TEMPORARY TABLE test__invenio__utf8")
except Exception, e:
    print """
    ******************************************************
    ** DATABASE RELATED ERROR: %(errmsg)s
    ******************************************************
    ** A problem was detected with the UTF-8 treatment  **
    ** in the chain between the Python application,     **
    ** the MySQLdb connector, and the MySQL database.   **
    ** You may perhaps have installed older versions    **
    ** of some prerequisite packages?                   **
    **                                                  **
    ** Please inspect the above error message and       **
    ** please fix the problem before continuing.        **
    ******************************************************
    """ % { 'errmsg': e }
    sys.exit(1)

## close connection:
cursor.close()
db.close()

