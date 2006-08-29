## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""
Helper functions for building and running test suites.
"""

__revision__ = "$Id$"

# if verbose level is set to 9, many debugging messages will be
# printed on stdout, so you may want to run:
#   $ regressiontestsuite > /tmp/z.log
# or even:
#   $ regressiontestsuite > /tmp/z.log 2> /tmp/z.err
cfg_testutils_verbose = 1

import string
import sys
import time
import unittest

from urllib import urlencode

from invenio.config import weburl, sweburl

def warn_user_about_tests():
    """ Put a standard warning about running tests that might modify
    user data"""
    
    # Provide a command line option to avoid having to type the
    # confirmation every time during development.
    if '--yes-i-know' in sys.argv:
        return

    sys.stderr.write("""\
**********************************************************************
**                                                                  **
**  ***  I M P O R T A N T   W A R N I N G  ***                     **
**                                                                  **
** The regression test suite needs to be run on a clean demo site   **
** that you can obtain by doing:                                    **
**                                                                  **
**    $ make drop-tables                                            **
**    $ make create-tables                                          **
**    $ make create-demo-site                                       **
**    $ make load-demo-records                                      **
**                                                                  **
** Note that DOING THE ABOVE WILL ERASE YOUR ENTIRE DATABASE.       **
**                                                                  **
** In addition, due to the write nature of some of the tests,       **
** the demo DATABASE will be ALTERED WITH JUNK DATA, so that        **
** it is recommended to rebuild the demo site anew afterwards.      **
**                                                                  **
**********************************************************************

Please confirm by typing "Yes, I know!": """)

    answer = raw_input('')
    if answer != 'Yes, I know!':
        sys.stderr.write("Aborted.\n")
        raise SystemExit(0)

    return

def warn_user_about_tests_and_run(testsuite):
    """ Convenience function to embed in test suites """
    warn_user_about_tests()
    unittest.TextTestRunner(verbosity=2).run(testsuite)
    

def make_test_suite(*test_cases):
    """ Build up a test suite given separate test cases"""
    
    return unittest.TestSuite([unittest.makeSuite(case, 'test')
                               for case in test_cases])

def make_url(path, **kargs):
    """ Helper to generate an absolute invenio URL with query
    arguments"""
    
    url = weburl + path
    
    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

def make_surl(path, **kargs):
    """ Helper to generate an absolute invenio Secure URL with query
    arguments"""
    
    url = sweburl + path
    
    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

class InvenioTestUtilsBrowserException(Exception):
    """Helper exception for the regression test suite browser."""
    pass

def test_web_page_content(url,
                          username="guest",
                          password="",
                          expected_text="</html>",
                          expected_link_target=None,
                          expected_link_label=None):
    """Test whether web page URL as seen by user USERNAME contains
       text EXPECTED_TEXT and, eventually, contains a link to
       EXPECTED_LINK_TARGET (if set) labelled EXPECTED_LINK_LABEL (if
       set).  The EXPECTED_TEXT is checked via substring matching, the
       EXPECTED_LINK_TARGET and EXPECTED_LINK_LABEL via exact string
       matching.

       Before doing the tests, login as USERNAME with password
       PASSWORD.  E.g. interesting values for USERNAME are "guest" or
       "admin".

       Return empty list in case of problems, otherwise list of error
       messages that may have been encountered during processing of
       page.
    """
    
    error_messages = []
    try:
        import mechanize
    except ImportError:
        return ['WARNING: Cannot import mechanize, test skipped.']
    browser = mechanize.Browser()
    try:
        # firstly login:
        if username == "guest":
            pass
        else:
            browser.open(sweburl + "/youraccount/login")
            browser.select_form(nr=0)
            browser['p_un'] = username
            browser['p_pw'] = password
            browser.submit()
            username_account_page_body = browser.response().read()
            try:
                string.index(username_account_page_body,
                             "You are logged in as %s." % username)
            except ValueError:
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Cannot login as %s, test skipped.' % username
        
        # secondly read page body:
        browser.open(url)
        url_body = browser.response().read()

        # now test for EXPECTED_TEXT:
        try:
            string.index(url_body, expected_text)
        except ValueError:
            raise InvenioTestUtilsBrowserException, \
                  'ERROR: Page %s (login %s) does not contain %s.' % \
                              (url, username, expected_text)

        # now test for EXPECTED_LINK_TARGET and EXPECTED_LINK_LABEL:
        if expected_link_target or expected_link_label:
            try:
                browser.find_link(url=expected_link_target,
                                  text=expected_link_label)
            except mechanize.LinkNotFoundError:
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Page %s (login %s) does not contain link to %s entitled %s.' % \
                                  (url, username, expected_link_target, expected_link_label)
                  
    except mechanize.HTTPError, msg:
        error_messages.append('ERROR: Page %s (login %s) not accessible. %s' % \
                              (url, username, msg))
    except InvenioTestUtilsBrowserException, msg:
        error_messages.append('ERROR: Page %s (login %s) led to an error: %s.' % \
                              (url, username, msg))

    # logout after tests:
    browser.open(sweburl + "/youraccount/logout")

    if cfg_testutils_verbose >= 9:
        print "%s test_web_page_content(), tested page `%s', login `%s', expected text `%s', errors `%s'." % \
              (time.strftime("%Y-%m-%d %H:%M:%S -->", time.localtime()),
               url, username, expected_text,
               string.join(error_messages, ","))

    return error_messages

def merge_error_messages(error_messages):
    """If the ERROR_MESSAGES list is non-empty, merge them and return nicely
       formatted string suitable for printing.  Otherwise return empty
       string.   
    """
    out = ""
    if error_messages:
        out = "\n*** " + string.join(error_messages, "\n*** ")
    return out
