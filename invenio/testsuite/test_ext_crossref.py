# -*- coding: utf-8 -*-
#
# This file is part of Invenio
# Copyright (C) 2014, 2015 CERN.
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
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Test *CrossRef* integration."""

from __future__ import absolute_import

import httpretty
import pkg_resources

from invenio.ext.crossref import CrossRef
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class CrossRefMixin(InvenioTestCase):

    """Custom CrossRef configuration."""

    @property
    def config(self):
        """Remove CrossRef from extensions to get full control of the test."""
        from invenio.base.config import EXTENSIONS
        cfg = super(CrossRefMixin, self).config
        cfg["EXTENSIONS"] = filter(
            lambda k: not k.startswith("invenio.ext.crossref"),
            EXTENSIONS)
        cfg["CROSSREF_API_URL"] = "http://api.example.org/works/"
        cfg["CACHE_TYPE"] = "simple"
        return cfg


class TestCrossRef(CrossRefMixin):

    """Test of extension creation."""

    def test_creation(self):
        assert "crossref" not in self.app.extensions
        CrossRef(app=self.app)
        assert isinstance(self.app.extensions["crossref"], CrossRef)

    def test_creation_old_flask(self):
        # Simulate old Flask (pre 0.9)
        del self.app.extensions
        CrossRef(app=self.app)
        assert isinstance(self.app.extensions["crossref"], CrossRef)

    def test_creation_init(self):
        assert "crossref" not in self.app.extensions
        r = CrossRef()
        r.init_app(app=self.app)
        assert isinstance(self.app.extensions["crossref"], CrossRef)

    def test_double_creation(self):
        CrossRef(app=self.app)
        self.assertRaises(RuntimeError, CrossRef, app=self.app)


class TestCrossRefQuery(CrossRefMixin):

    """Test CrossRef query response parsing."""

    def setUp(self):
        self.crossref = CrossRef(app=self.app)

    def tearDown(self):
        del self.crossref

    @httpretty.activate
    def test_found_result(self):
        httpretty.register_uri(
            httpretty.GET,
            self.app.config["CROSSREF_API_URL"] +
            "10.1103/PhysRevLett.19.1264",
            body=pkg_resources.resource_string(
                "invenio.testsuite", "data/response_export_crossref.json"),
            status=200
        )

        response = self.app.extensions["crossref"].search("10.1103/PhysRevLett.19.1264")
        self.assertEqual(response.status_code, 200)

    @httpretty.activate
    def test_zero_results_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.app.config["CROSSREF_API_URL"] +
            "10.1088/0067-0049/192/2/18a",
            body=pkg_resources.resource_string(
                "invenio.testsuite", "data/response_export_crossref_zero.json"),
            status=200
        )

TEST_SUITE = make_test_suite(TestCrossRef, TestCrossRefQuery)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
