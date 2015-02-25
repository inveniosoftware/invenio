# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Unit tests for utility functions."""

from __future__ import absolute_import

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class HoldingPenUtilsTest(InvenioTestCase):

    """Test basic utility functions for Holding Pen."""

    def test_get_previous_next_objects_empty(self):
        """Test the getting of prev, next object ids from the list."""
        from invenio.modules.workflows.utils import get_previous_next_objects
        objects = []
        self.assertEqual(get_previous_next_objects(objects, 1), (None, None))

    def test_get_previous_next_objects_not_there(self):
        """Test the getting of prev, next object ids from the list."""
        from invenio.modules.workflows.utils import get_previous_next_objects
        objects = [3, 4]
        self.assertEqual(get_previous_next_objects(objects, 42), (None, None))

    def test_get_previous_next_objects_previous(self):
        """Test the getting of prev, next object ids from the list."""
        from invenio.modules.workflows.utils import get_previous_next_objects
        objects = [3, 4]
        self.assertEqual(get_previous_next_objects(objects, 4), (3, None))

    def test_get_previous_next_objects_next(self):
        """Test the getting of prev, next object ids from the list."""
        from invenio.modules.workflows.utils import get_previous_next_objects
        objects = [3, 4]
        self.assertEqual(get_previous_next_objects(objects, 3), (None, 4))

    def test_get_previous_next_objects_previous_next(self):
        """Test the getting of prev, next object ids from the list."""
        from invenio.modules.workflows.utils import get_previous_next_objects
        objects = [3, 4, 5]
        self.assertEqual(get_previous_next_objects(objects, 4), (3, 5))


TEST_SUITE = make_test_suite(HoldingPenUtilsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
