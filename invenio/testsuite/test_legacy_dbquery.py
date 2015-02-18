# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013, 2015 CERN.
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

"""Unit tests for dbquery library."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite

__revision__ = "$Id$"

dbquery = lazy_import('invenio.legacy.dbquery')


class TableUpdateTimesTest(InvenioTestCase):

    """Test functions related to the update_times of MySQL tables."""

    def _check_table_update_time(self, tablename):
        """Helper function to check update time of TABLENAME."""
        from invenio.base.globals import cfg
        # detect MySQL version number:
        res = dbquery.run_sql("SELECT VERSION()")
        mysql_server_version = res[0][0]
        if mysql_server_version.startswith("5."):
            # MySQL-5 provides INFORMATION_SCHEMA:
            query = """SELECT UPDATE_TIME FROM INFORMATION_SCHEMA.TABLES
                        WHERE table_name='%s' AND table_schema='%s' """ \
                        % (tablename, cfg['CFG_DATABASE_NAME'])
            tablename_update_time = str(dbquery.run_sql(query)[0][0])
        elif mysql_server_version.startswith("4.1"):
            # MySQL-4.1 has it on 12th position:
            query = """SHOW TABLE STATUS LIKE "%s" """ % tablename
            tablename_update_time = str(dbquery.run_sql(query)[0][12])
        elif mysql_server_version.startswith("4.0"):
            # MySQL-4.0 has it on 11th position:
            query = """SHOW TABLE STATUS LIKE "%s" """ % tablename
            tablename_update_time = str(dbquery.run_sql(query)[0][11])
        else:
            tablename_update_time = "MYSQL SERVER VERSION NOT DETECTED"
        # compare it with the one detected by the function:
        self.assertEqual(tablename_update_time,
                         dbquery.get_table_update_time(tablename))

    def test_single_table_update_time(self):
        """dbquery - single table (with indexes) update time detection."""
        # NOTE: this tests usual "long" branch of
        # get_table_update_time()
        self._check_table_update_time("collection")

    def test_empty_table_update_time(self):
        """dbquery - empty table (no indexes) update time detection."""
        # NOTE: this tests unusual "None" branch of
        # get_table_update_time()
        # create empty test table
        test_table = "tmpTESTTABLE123"
        dbquery.run_sql("CREATE TABLE IF NOT EXISTS %s (a INT)" % test_table)
        # run the test:
        self._check_table_update_time(test_table)
        # drop empty test table
        dbquery.run_sql("DROP TABLE %s" % test_table)

    def test_utf8_python_mysqldb_mysql_storage_chain(self):
        """dbquery - UTF-8 in Python<->MySQLdb<->MySQL storage chain."""
        # NOTE: This test test creates, uses and destroys a temporary
        # table called "test__invenio__utf8".
        beta_in_utf8 = "β"  # Greek beta in UTF-8 is 0xCEB2
        dbquery.run_sql(
            "CREATE TEMPORARY TABLE test__invenio__utf8 "
            "(x char(1), y varbinary(2)) DEFAULT CHARACTER SET utf8")
        dbquery.run_sql(
            "INSERT INTO test__invenio__utf8 (x, y) VALUES (%s, %s)",
            (beta_in_utf8, beta_in_utf8))
        res = dbquery.run_sql(
            "SELECT x,y,HEX(x),HEX(y),LENGTH(x),LENGTH(y),"
            "CHAR_LENGTH(x),CHAR_LENGTH(y) FROM test__invenio__utf8")
        self.assertEqual(
            res[0],
            ('\xce\xb2', '\xce\xb2', 'CEB2', 'CEB2', 2L, 2L, 1L, 2L))
        dbquery.run_sql("DROP TEMPORARY TABLE test__invenio__utf8")


class WashTableColumnNameTest(InvenioTestCase):

    """Test evaluation of wash_table_column_name and real_escape_string."""

    def test_wash_table_column_name(self):
        """dbquery - wash table column name."""
        testcase_error = "foo ; bar"
        testcase_ok = "foo_bar"
        self.assertRaises(Exception, dbquery.wash_table_column_name,
                          testcase_error)
        self.assertEqual(testcase_ok,
                         dbquery.wash_table_column_name(testcase_ok))

    def test_real_escape_string(self):
        """dbquery - real escape string."""
        testcase_ok = "Programmer"
        testcase_injection = "' OR ''='"
        self.assertEqual(dbquery.real_escape_string(testcase_ok), testcase_ok)
        self.assertNotEqual(dbquery.real_escape_string(testcase_injection),
                            testcase_injection)


TEST_SUITE = make_test_suite(TableUpdateTimesTest, WashTableColumnNameTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
