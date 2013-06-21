# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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


"""BibTask Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import datetime
from invenio.dbquery import run_sql
from invenio.bibtask import get_modified_records_since
from invenio.testutils import make_test_suite, run_test_suite

class BibTaskGetModifiedRecordsSiceTest(unittest.TestCase):

    def setUp(self):
        # Save old modification times to restore them later
        self.mod_times = run_sql("SELECT modification_date, id FROM bibrec")

        # Set most records modificated 2 months ago, 5 records one week ago and 3 records yesterday
        run_sql("UPDATE bibrec SET modification_date = DATE_ADD(NOW(), INTERVAL -2 MONTH)")
        run_sql("UPDATE bibrec SET modification_date = DATE_ADD(NOW(), INTERVAL -7 DAY) ORDER BY id DESC LIMIT 5")
        run_sql("UPDATE bibrec SET modification_date = DATE_ADD(NOW(), INTERVAL -1 DAY) ORDER BY id ASC LIMIT 3")

    def test_get_modified_records(self):
        self.assertEqual(len(get_modified_records_since(
            datetime.datetime.now() - datetime.timedelta(8)
        )), 8)
        self.assertEqual(len(get_modified_records_since(
            datetime.datetime.now() - datetime.timedelta(2)
        )), 3)
        self.assertEqual(len(get_modified_records_since(
            datetime.datetime.now() - datetime.timedelta(0)
        )), 0)

    def tearDown(self):
        # Restore modification times
        for row in self.mod_times:
            run_sql("UPDATE bibrec SET modification_date=%s WHERE id=%s", row)

TEST_SUITE = make_test_suite(BibTaskGetModifiedRecordsSiceTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)

