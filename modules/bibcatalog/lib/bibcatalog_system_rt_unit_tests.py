# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2015 CERN.
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
##
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


"""Unit tests for bibcatalog_system_rt library."""

from invenio.testutils import InvenioTestCase
from invenio.testutils import make_test_suite, run_test_suite

from invenio import bibcatalog_system_rt


class BibCatalogSystemRTTest(InvenioTestCase):

    """Testing of BibCatalog."""

    def setUp(self):
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER = 'testuser'
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD = 'testpass'
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_URL = 'http://testingdomainbadbad.invenio-software.org'
        self.rt = bibcatalog_system_rt.BibCatalogSystemRT()

    def tearDown(self):
        pass


TEST_SUITE = make_test_suite(BibCatalogSystemRTTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
