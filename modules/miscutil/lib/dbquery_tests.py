# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""Unit tests for dbquery library."""

__revision__ = "$Id$"

import unittest

from invenio import dbquery

class TableUpdateTimesTest(unittest.TestCase):
    """Test functions related to the update_times of MySQL tables."""

    def test_single_table_update_time(self):
        """dbquery - single table update time detection"""
        test_table = "collection"
        # detect MySQL version number:
        res = dbquery.run_sql("SELECT VERSION()")
        mysql_server_version = res[0][0]
        if mysql_server_version.startswith("5."):
            # MySQL-5 provides INFORMATION_SCHEMA:
            query = """SELECT UPDATE_TIME FROM INFORMATION_SCHEMA.TABLES
                        WHERE table_name='%s'""" % test_table
            test_table_update_time = str(dbquery.run_sql(query)[0][0])
        elif mysql_server_version.startswith("4.1"):
            # MySQL-4.1 has it on 12th position:
            query = """SHOW TABLE STATUS LIKE '%s'""" % test_table
            test_table_update_time = str(dbquery.run_sql(query)[0][12])
        elif mysql_server_version.startswith("4.0"):
            # MySQL-4.0 has it on 11th position:
            query = """SHOW TABLE STATUS LIKE '%s'""" % test_table
            test_table_update_time = str(dbquery.run_sql(query)[0][11])
        else:
            test_table_update_time = "MYSQL SERVER VERSION NOT DETECTED"
        # compare it with the one detected by the function:
        self.assertEqual(test_table_update_time,
                         dbquery.get_table_update_time("collection"))
        
def create_test_suite():
    """Return test suite for the user handling."""
    return unittest.TestSuite((
        unittest.makeSuite(TableUpdateTimesTest,'test'),
        ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())


