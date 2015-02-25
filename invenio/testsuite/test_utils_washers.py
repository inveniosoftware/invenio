# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

"""Unit tests for the urlutils library."""

__revision__ = "$Id$"

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

WASH_HTML_ID = lazy_import('invenio.utils.washers:wash_html_id')


class TestWashUrlArgd(InvenioTestCase):
    # FIXME: test invenio.utils.washers.wash_urlargd
    pass


class TestWashHTMLId(InvenioTestCase):
    def test_clean_input(self):
        self.assert_(WASH_HTML_ID('abcd') == 'abcd')
        self.assert_(WASH_HTML_ID('a1b2') == 'a1b2')

    def test_dirty_input(self):
        self.assert_(WASH_HTML_ID('1234') == 'i1234')
        self.assert_(WASH_HTML_ID('1aaa') == 'i1aaa')
        self.assert_(WASH_HTML_ID('1`~!@#$%^&*()-_+=[{]};:\'"\\|,<.>/?a') ==
                     'i1_a')


TEST_SUITE = make_test_suite(TestWashHTMLId, TestWashUrlArgd)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
