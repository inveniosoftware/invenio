# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Unit tests for pages."""

from flask import url_for

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from invenio.base.wrappers import lazy_import
from invenio.ext.sqlalchemy import db

Page = lazy_import('invenio.modules.pages.models:Page')


class PagesTestViews(InvenioTestCase):

    """ Test pages functionality."""

    def setUp(self):
        Page.query.delete()
        self.test_page = Page()
        self.test_page.id = 1
        self.test_page.url = "pages/test"
        self.test_page.title = "My test title"
        self.test_page.template_name = 'pages/default.html'
        self.test_page.content = "Testing pages"
        db.session.add(self.test_page)
        db.session.commit()

    def tearDown(self):
        db.session.delete(self.test_page)
        db.session.commit()

    def _get_test_page(self):
        p = Page.query.filter_by(id=self.test_page.id).first()
        return p

    def test_url_rule_added(self):
        p = self._get_test_page()
        self.assertEqual(url_for("pages.view"), p.url)

    def test_page_content(self):
        with self.app.test_client() as c:
            response = c.get("/pages/test")
            assert 'Testing pages' in response.data

    def test_trailing_slash_added(self):
        p = self._get_test_page()
        assert p.url.startswith("/")


TEST_SUITE = make_test_suite(PagesTestViews,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
