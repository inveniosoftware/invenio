# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013 CERN.
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

"""
Test unit for the invenio.utils.mimetype module.
"""

from invenio.utils.mimetype import file_strip_ext
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestMimeTypeUtils(InvenioTestCase):
    """
    mimetypeutils TestSuite.
    """

    def test_file_strip_extension(self):
        """Tests striping the extension in the best way from a filename."""
        self.assertEqual(file_strip_ext("foo.tar.gz"), 'foo')
        self.assertEqual(file_strip_ext("foo.buz.gz"), 'foo.buz')
        self.assertEqual(file_strip_ext("foo.buz"), 'foo')
        self.assertEqual(file_strip_ext("foo.buz", only_known_extensions=True),
                         'foo.buz')
        self.assertEqual(file_strip_ext("foo.buz;1", skip_version=False,
                                        only_known_extensions=True),
                         'foo.buz;1')
        self.assertEqual(file_strip_ext("foo.gif;icon"), 'foo')
        self.assertEqual(file_strip_ext("foo.gif;icon",
                                        only_known_extensions=True),
                         'foo')
        self.assertEqual(file_strip_ext("foo.gif;icon",
                                        only_known_extensions=True,
                                        allow_subformat=False),
                         'foo.gif;icon')

    def test_version_and_subformat_strip(self):
        """Tests striping file with version and subformat."""
        self.assertEqual(file_strip_ext("foo.tar.gz;1;icon"), 'foo')
        self.assertEqual(file_strip_ext("foo.tar.gz;1;icon", only_known_extensions=True), 'foo.tar.gz;1')
        self.assertEqual(file_strip_ext("foo.tar.gz;1;icon", skip_version=True, only_known_extensions=True), 'foo')
        self.assertEqual(file_strip_ext("foo.buz;1;icon", only_known_extensions=True), 'foo.buz;1')
        self.assertEqual(file_strip_ext("foo.buz;1;icon", skip_version=True), 'foo')
        self.assertEqual(file_strip_ext("foo.buz;1;icon", skip_version=True, only_known_extensions=True), 'foo.buz')



TEST_SUITE = make_test_suite(TestMimeTypeUtils, )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
