# -*- coding: utf-8 -*-
#
# This file is part of Invenio
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
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Test UnAPI service hooks implementation."""

from __future__ import absolute_import

from flask import url_for

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class UnAPIMixin(InvenioTestCase):

    """Custom Arxiv configuration."""

    @property
    def config(self):
        """Set format mapping."""
        cfg = super(UnAPIMixin, self).config
        cfg["UNAPI_FORMAT_MAPPING"] = {
            'marcxml': 'xm',
            'dc': 'xd',
        }
        return cfg


class TestUnAPIEndpoint(UnAPIMixin):

    """Test Arxiv query response parsing."""

    def test_index(self):
        response = self.client.get(url_for('unapi.index'))
        assert 'marcxml' in response.data

    def test_redirection(self):
        response = self.client.get(
            url_for('unapi.index', id=1, format='marcxml'))
        assert response.status_code == 302

TEST_SUITE = make_test_suite(TestUnAPIEndpoint)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
