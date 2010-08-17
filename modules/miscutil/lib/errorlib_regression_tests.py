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

"""errorlib Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import os
import sys

from invenio.errorlib import register_exception, get_pretty_traceback
from invenio.config import CFG_SITE_URL, CFG_LOGDIR
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages

class ErrorlibWebPagesAvailabilityTest(unittest.TestCase):
    """Check errorlib web pages whether they are up or not."""

    def test_your_baskets_pages_availability(self):
        """errorlib - availability of error sending pages"""

        baseurl = CFG_SITE_URL + '/error/'

        _exports = ['', 'send']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class ErrorlibRegisterExceptionTest(unittest.TestCase):
    """Check errorlib register_exception functionality."""

    def test_simple_register_exception(self):
        """errorlib - simple usage of register_exception"""
        try:
            raise Exception('test-exception')
        except:
            result = register_exception()
        log_content = open(os.path.join(CFG_LOGDIR, 'invenio.err')).read()
        self.failUnless('test_simple_register_exception' in log_content)
        self.failUnless('test-exception' in log_content)
        self.assertEqual(1, result, "register_exception have not returned 1")

    def test_alert_admin_register_exception(self):
        """errorlib - alerting admin with register_exception"""
        text = 'test-exception that you should receive by email'
        try:
            raise Exception(text)
        except:
            result = register_exception(alert_admin=True)
        log_content = open(os.path.join(CFG_LOGDIR, 'invenio.err')).read()
        self.failUnless('test_alert_admin_register_exception' in log_content)
        self.failUnless(text in log_content)
        self.assertEqual(1, result, "register_exception have not returned 1")

    def test_password_hiding(self):
        """errorlib - hide password in frame analysis"""
        try:
            password = 'this password should not be visible'
            int('foo')
        except:
            output = get_pretty_traceback(exc_info=sys.exc_info(), force_stack=True)
        self.failIf(password in output, output)
        self.failUnless('<*****>' in output, output)

    def test_dbquery_password_hiding(self):
        """errorlib - hide dbquery password in frame analysis"""
        from invenio.dbquery import connect
        kwargs = {'host': 'foo', 'port': 999, 'db': 'baz', 'user': 'qoox', 'passwd': '123', 'use_unicode': False, 'charset': 'utf8'}
        try:
            connect(**kwargs)
        except:
            output = get_pretty_traceback(exc_info=sys.exc_info(), force_stack=True)
        self.failIf('123' in output, output)
        self.failUnless('<*****>' in output, output)

    def test_nested_password_hiding(self):
        """errorlib - hide password nested in dictionary in frame analysis"""
        try:
            foo = {
                'bar' : 'baz',
                'qoox' : {
                    'blibpwdblob' : '1234'
                }
            }
            int(foo)
        except:
            output = get_pretty_traceback(exc_info=sys.exc_info(), force_stack=True)
        self.failIf('1234' in output, output)
        self.failUnless('<*****>' in output, output)


TEST_SUITE = make_test_suite(ErrorlibWebPagesAvailabilityTest,
                             ErrorlibRegisterExceptionTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
