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

"""Unit tests for the inveniomanage script."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class ViewsTest(InvenioTestCase):

    """Test base views."""

    def test_ping_view(self):
        """Test /ping endpoint."""
        response = self.client.get("/ping")

        assert 'OK' == response.data


TEST_SUITE = make_test_suite(ViewsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
