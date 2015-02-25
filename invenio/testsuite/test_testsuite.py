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


from StringIO import StringIO
from invenio.testsuite import InvenioTestCase, make_test_suite, \
    run_test_suite, make_file_fixture, stringio_to_base64, make_pdf_fixture


class TestsuiteTest(InvenioTestCase):
    def test_make_file_fixture(self):
        res = make_file_fixture(
            "test.txt",
            stringio_to_base64(StringIO("content"))
        )
        assert isinstance(res, tuple)
        assert res[1] == "test.txt"
        assert hasattr(res[0], 'read')
        assert res[0].read() == "content"

    def test_make_make_pdf_fixture(self):
        res = make_pdf_fixture("test.pdf", text="Content")
        assert isinstance(res, tuple)
        assert res[1] == "test.pdf"
        assert hasattr(res[0], 'read')


TEST_SUITE = make_test_suite(InvenioTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
