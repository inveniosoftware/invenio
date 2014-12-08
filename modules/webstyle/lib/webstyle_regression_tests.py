# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebStyle Regression Test Suite."""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase
import httplib
import os
import urlparse
import mechanize
from urllib2 import urlopen, HTTPError

from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_PREFIX, CFG_DEVEL_SITE
from invenio.bibdocfile import calculate_md5
from invenio.testutils import make_test_suite, run_test_suite, nottest
from invenio.goto_engine import CFG_GOTO_PLUGINS, register_redirection, drop_redirection, update_redirection

def get_final_url(url):
    """Perform a GET request to the given URL, discarding the result and return
    the final one in case of redirections"""
    response = urlopen(url)
    response.read()
    return response.url

class WebStyleWSGIUtilsTests(InvenioTestCase):
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


class WebStyleGotoTests(InvenioTestCase):
    """Test the goto framework"""
    def tearDown(self):
        drop_redirection('first_record')
        drop_redirection('invalid_external')
        drop_redirection('latest_article')
        drop_redirection('latest_pdf_article')

    def test_plugin_availability(self):
        """webstyle - test GOTO plugin availability"""
        self.failUnless('goto_plugin_simple' in CFG_GOTO_PLUGINS)
        self.failUnless('goto_plugin_latest_record' in CFG_GOTO_PLUGINS)
        self.failUnless('goto_plugin_cern_hr_documents' in CFG_GOTO_PLUGINS)
        self.failIf(CFG_GOTO_PLUGINS.get_broken_plugins())

    def test_simple_relative_redirection(self):
        """webstyle - test simple relative redirection via goto_plugin_simple"""
        register_redirection('first_record', 'goto_plugin_simple', parameters={'url': '/record/1'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/first_record'), CFG_SITE_URL + '/record/1')

    def test_simple_absolute_redirection(self):
        """webstyle - test simple absolute redirection via goto_plugin_simple"""
        register_redirection('first_record', 'goto_plugin_simple', parameters={'url': CFG_SITE_URL + '/record/1'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/first_record'), CFG_SITE_URL + '/record/1')

    def test_simple_absolute_redirection_https(self):
        """webstyle - test simple absolute redirection to https via goto_plugin_simple"""
        register_redirection('first_record', 'goto_plugin_simple', parameters={'url': CFG_SITE_SECURE_URL + '/record/1'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/first_record'), CFG_SITE_SECURE_URL + '/record/1')

    def test_invalid_external_redirection(self):
        """webstyle - test simple absolute redirection to https via goto_plugin_simple"""
        register_redirection('invalid_external', 'goto_plugin_simple', parameters={'url': 'http://www.google.com'})
        self.assertRaises(HTTPError, get_final_url, CFG_SITE_URL + '/goto/google')

    def test_latest_article_redirection(self):
        """webstyle - test redirecting to latest article via goto_plugin_latest_record"""
        register_redirection('latest_article', 'goto_plugin_latest_record', parameters={'cc': 'Articles'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/latest_article'), CFG_SITE_URL + '/record/145')

    @nottest
    def FIXME_TICKET_1293_test_latest_pdf_article_redirection(self):
        """webstyle - test redirecting to latest article via goto_plugin_latest_record"""
        register_redirection('latest_pdf_article', 'goto_plugin_latest_record', parameters={'cc': 'Articles', 'format': '.pdf'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/latest_pdf_article'), CFG_SITE_URL + '/record/97/files/0002060.pdf')

    @nottest
    def FIXME_TICKET_1293_test_URL_argument_in_redirection(self):
        """webstyle - test redirecting while passing arguments on the URL"""
        register_redirection('latest_article', 'goto_plugin_latest_record', parameters={'cc': 'Articles'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/latest_article?format=.pdf'), CFG_SITE_URL + '/record/97/files/0002060.pdf')

    def test_updating_redirection(self):
        """webstyle - test updating redirection"""
        register_redirection('first_record', 'goto_plugin_simple', parameters={'url': '/record/1'})
        update_redirection('first_record', 'goto_plugin_simple', parameters={'url': '/record/2'})
        self.assertEqual(get_final_url(CFG_SITE_URL + '/goto/first_record'), CFG_SITE_URL + '/record/2')


TEST_SUITE = make_test_suite(WebStyleWSGIUtilsTests, WebStyleGotoTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
