# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebStyle Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import httplib
import os
import urlparse
import mechanize

from invenio.config import CFG_SITE_URL, CFG_PREFIX, CFG_DEVEL_SITE
from invenio.bibdocfile import calculate_md5
from invenio.testutils import make_test_suite, run_test_suite


class WebStyleWSGIUtilsTest(unittest.TestCase):
    """Test WSGI Utils."""

    if CFG_DEVEL_SITE:
        def test_iteration_over_posted_file(self):
            """webstyle - posting a file via form upload"""
            path = os.path.join(CFG_PREFIX, 'lib', 'webtest', 'invenio', 'test.gif')
            body = open(path).read()
            br = mechanize.Browser()
            br.open(CFG_SITE_URL + '/httptest/post1').read()
            br.select_form(nr=0)
            br.form.add_file(open(path))
            body2 = br.submit().read()
            self.assertEqual(body, body2, "Body sent differs from body received")
            pass

    if CFG_DEVEL_SITE:
        def test_posting_file(self):
            """webstyle - direct posting of a file"""
            path = os.path.join(CFG_PREFIX, 'lib', 'webtest', 'invenio', 'test.gif')
            body = open(path).read()
            md5 = calculate_md5(path)
            mimetype = 'image/gif'
            connection = httplib.HTTPConnection(urlparse.urlsplit(CFG_SITE_URL)[1])
            connection.request('POST', '/httptest/post2', body, {'Content-MD5': md5, 'Content-Type': mimetype, 'Content-Disposition': 'filename=test.gif'})
            response = connection.getresponse()
            body2 = response.read()
            self.assertEqual(body, body2, "Body sent differs from body received")


TEST_SUITE = make_test_suite(WebStyleWSGIUtilsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
