# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Unit tests for search views."""

from intbitset import intbitset
from flask import url_for, current_app
from invenio.testsuite import InvenioTestCase, make_test_suite, \
    run_test_suite


class SearchViewTest(InvenioTestCase):
    """ Test search view functions. """

    def test_home_collection_page_availability(self):
        response = self.client.get(url_for('collections.index'))
        self.assert200(response)

        response = self.client.get(url_for(
            'collections.collection', name=current_app.config['CFG_SITE_NAME']))
        self.assert200(response)

    def test_search_page_availability(self):
        response = self.client.get(url_for('search.search'))
        self.assert200(response)


TEST_SUITE = make_test_suite(SearchViewTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
