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

"""Tests for communities views."""

from flask import url_for
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class CommunitiesViewTest(InvenioTestCase):

    """Test communities view functions."""

    def test_home_communities_page_availability(self):
        """communities - availability of main page"""
        response = self.client.get(url_for('communities.index'))
        self.assert200(response)

    def test_new_community_page_availability(self):
        """communities - availability of new community page"""
        self.login('admin', '')
        response = self.client.get(url_for('communities.new'))
        self.assert200(response)
        self.logout()

    def test_new_community_page_unauthorized(self):
        """communities - new communities restricted to logged in users"""
        response = self.client.get(url_for('communities.new'),
                                   follow_redirects=True)
        self.assert401(response)


TEST_SUITE = make_test_suite(CommunitiesViewTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
