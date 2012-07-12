# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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
The Refextract task tests suite for tasks

It requires a fully functional invenio installation.
"""

import unittest

from invenio.testutils import make_test_suite, run_test_suite
from invenio.refextract_api import update_references, \
                                   RecordHasReferences, \
                                   FullTextNotAvailable


class RefextractApiTest(unittest.TestCase):
    def test_no_fulltext(self):
        try:
            update_references(1000000000000)
            self.fail()
        except FullTextNotAvailable:
            # As expected
            pass

    def test_no_overwrite(self):
        try:
            update_references(1, overwrite=False)
            self.fail()
        except RecordHasReferences:
            # As expected
            pass


if __name__ == '__main__':
    test_suite = make_test_suite(RefextractApiTest)
    run_test_suite(test_suite, warn_user=True)
