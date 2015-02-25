# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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

"""Tests for downloadutils."""

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestDownloadUtils(InvenioTestCase):

    """Test simple download functionality."""

    def test_content_type(self):
        """Test simple calls to download_url."""
        from invenio.utils.filedownload import (download_url,
                                                InvenioFileDownloadError)
        tmpdoc = download_url("http://duckduckgo.com", content_type="html")
        self.assertTrue(tmpdoc)

        fun = lambda: download_url("http://google.com", content_type="pdf")
        self.assertRaises(InvenioFileDownloadError, fun)

    def test_is_url_local_file(self):
        """Test is_url_local_file() functionality."""
        from invenio.utils.filedownload import (safe_mkstemp,
                                                is_url_a_local_file)
        localpath = safe_mkstemp(".tmp")
        self.assertTrue(is_url_a_local_file(localpath))


TEST_SUITE = make_test_suite(TestDownloadUtils)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
