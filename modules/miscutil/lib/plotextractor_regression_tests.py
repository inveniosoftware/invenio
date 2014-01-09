# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2013 CERN.
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

"""Regression tests for the plotextract script."""

import os

from invenio.testutils import (InvenioTestCase,
                               make_test_suite,
                               run_test_suite)
from invenio.plotextractor import get_defaults
from invenio.config import CFG_TMPSHAREDDIR, CFG_SITE_URL
from invenio.shellutils import run_shell_command
from invenio.plotextractor_getter import harvest_single


class GetDefaultsTest(InvenioTestCase):
    """Test function to get default values."""
    def setUp(self):
        self.arXiv_id = "arXiv:astro-ph_0104076"
        self.tarball = "%s/2001/04/arXiv:astro-ph_0104076/arXiv:astro-ph_0104076" % CFG_TMPSHAREDDIR

    def test_get_defaults(self):
        """plotextractor - get defaults"""
        sdir_should_be = os.path.join(CFG_TMPSHAREDDIR, self.arXiv_id + '_plots')
        refno_should_be = "15" # Note: For ATLANTIS DEMO site
        sdir, refno = get_defaults(tarball=self.tarball, sdir=None, refno_url=CFG_SITE_URL)
        if sdir is not None:
            run_shell_command("rm -rf %s" % sdir)
        self.assertTrue(sdir == sdir_should_be,
                         "didn't get correct default scratch dir: expected %s found %s" % (sdir_should_be, sdir))
        self.assertTrue(refno == refno_should_be,
                         "didn't get correct default reference number")


class TestGetter(InvenioTestCase):

    def test_harvest_single(self):
        """plotextractor - check harvest_single"""
        tarball, pdf = harvest_single('arXiv:1204.6260', '/tmp', ('pdf', 'tarball'))
        self.assertTrue(pdf is not None, "PDF is of unknown type")
        self.assertTrue(tarball is not None, "Tarball is of unknown type")


# FIXME: TestGetter is querying arxiv!!!!
TEST_SUITE = make_test_suite(GetDefaultsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
