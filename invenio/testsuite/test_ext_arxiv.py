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

"""Test *ArXiv* integration."""

from __future__ import absolute_import

import httpretty
import pkg_resources

from invenio.ext.arxiv import Arxiv
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class ArxivMixin(InvenioTestCase):

    """Custom Arxiv configuration."""

    @property
    def config(self):
        """Remove Arxiv from extensions to get full control of the test."""
        from invenio.base.config import EXTENSIONS
        cfg = super(ArxivMixin, self).config
        cfg["EXTENSIONS"] = filter(
            lambda k: not k.startswith("invenio.ext.arxiv"),
            EXTENSIONS)
        cfg["ARXIV_API_URL"] = "http://export.example.org/oai2"
        cfg["CACHE_TYPE"] = "simple"
        return cfg


class TestArxiv(ArxivMixin):

    """Test of extension creation."""

    def test_creation(self):
        assert "arxiv" not in self.app.extensions
        Arxiv(app=self.app)
        assert isinstance(self.app.extensions["arxiv"], Arxiv)

    def test_creation_old_flask(self):
        # Simulate old Flask (pre 0.9)
        del self.app.extensions
        Arxiv(app=self.app)
        assert isinstance(self.app.extensions["arxiv"], Arxiv)

    def test_creation_init(self):
        assert "arxiv" not in self.app.extensions
        r = Arxiv()
        r.init_app(app=self.app)
        assert isinstance(self.app.extensions["arxiv"], Arxiv)

    def test_double_creation(self):
        Arxiv(app=self.app)
        self.assertRaises(RuntimeError, Arxiv, app=self.app)


class TestArxivQuery(ArxivMixin):

    """Test Arxiv query response parsing."""

    def setUp(self):
        self.arxiv = Arxiv(app=self.app)

    def tearDown(self):
        del self.arxiv

    @httpretty.activate
    def test_found_result(self):
        httpretty.register_uri(
            httpretty.GET,
            self.app.config["ARXIV_API_URL"] +
            "?verb=GetRecord&metadataPrefix=arXiv&identifier=oai:arXiv.org:1007.5048",
            body=pkg_resources.resource_string(
                "invenio.testsuite", "data/response_export_arxiv.xml"),
            status=200
        )

        response = self.app.extensions["arxiv"].search("1007.5048")
        self.assertEqual(response.status_code, 200)

    @httpretty.activate
    def test_zero_results_found(self):
        httpretty.register_uri(
            httpretty.GET,
            self.app.config["ARXIV_API_URL"] +
            "?verb=GetRecord&metadataPrefix=arXiv&identifier=oai:arXiv.org:dead.beef",
            body=pkg_resources.resource_string(
                "invenio.testsuite", "data/response_export_arxiv_zero.xml"),
            status=200
        )

        response = self.app.extensions["arxiv"].search("9999.9999")
        self.assertEqual(response.status_code, 404)

    @httpretty.activate
    def test_unsupported_versioning(self):
        httpretty.register_uri(
            httpretty.GET,
            self.app.config["ARXIV_API_URL"] +
            "?verb=GetRecord&metadataPrefix=arXiv&identifier=oai:arXiv.org:1007.5048v1",
            body=pkg_resources.resource_string(
                "invenio.testsuite", "data/response_export_arxiv_versioning.xml"),
            status=200
        )

        response = self.app.extensions["arxiv"].search("1007.5048v1")
        self.assertEqual(response.status_code, 415)

    @httpretty.activate
    def test_malformed_arxiv_id(self):
        httpretty.register_uri(
            httpretty.GET,
            self.app.config["ARXIV_API_URL"] +
            "?verb=GetRecord&metadataPrefix=arXiv&identifier=oai:arXiv.org:dead.beef",
            body=pkg_resources.resource_string(
                "invenio.testsuite", "data/response_export_arxiv_malformed.xml"),
            status=200
        )

        response = self.app.extensions["arxiv"].search("dead.beef")
        self.assertEqual(response.status_code, 422)

TEST_SUITE = make_test_suite(TestArxiv, TestArxivQuery)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
