# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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


"""Unit tests for bibcatalog_system_rt library."""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
bibcatalog_system_rt = lazy_import('invenio.legacy.bibcatalog.system_rt')


class BibCatalogSystemRTTest(InvenioTestCase):
    """Testing of BibCatalog."""

    def setUp(self):
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER = 'testuser'
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD = 'testpass'
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_URL = 'http://testingdomainbadbad.invenio-software.org'
        self.rt = bibcatalog_system_rt.BibCatalogSystemRT()

    def tearDown(self):
        pass

    def test_rt_run_command_fails_with_bum_environment(self):
        """bibcatalog_system_rt - _run_rt_command gives None for bad environment"""
        # A special kind of test requires a very weird environment
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_URL = None
        testobj = bibcatalog_system_rt.BibCatalogSystemRT()
        stdout = testobj._run_rt_command('/bin/ls /')
        bibcatalog_system_rt.CFG_BIBCATALOG_SYSTEM_RT_URL = 'http://testingdomainbadbad.invenio-software.org'
        self.assertEquals(stdout, None)

    def test_rt_run_command(self):
        """bibcatalog_system_rt - running simple command."""
        stdout = self.rt._run_rt_command('/bin/ls /')
        self.assertTrue(len(stdout) > 0)

    def test_rt_run_command_exception_bad_cmd(self):
        """bibcatalog_system_rt - bad command execution raises exception"""
        self.assertRaises(ValueError, self.rt._run_rt_command, '/etc/hosts')


TEST_SUITE = make_test_suite(BibCatalogSystemRTTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
