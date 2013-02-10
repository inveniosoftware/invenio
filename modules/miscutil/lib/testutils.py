## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2013 CERN.
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

# pylint: disable=E1102

"""
Helper functions for building and running test suites.
"""

__revision__ = "$Id$"

CFG_TESTUTILS_VERBOSE = 1

import os
import sys
import time
import unittest

from urllib import urlencode
from itertools import chain, repeat

import invenio
from invenio.config import CFG_PREFIX, \
     CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_LOGDIR
from invenio.w3c_validator import w3c_validate, w3c_errors_to_str, \
     CFG_TESTS_REQUIRE_HTML_VALIDATION

try:
    from nose.tools import nottest
except ImportError:
    def nottest(f):
        """Helper decorator to mark a function as not to be tested by nose."""
        f.__test__ = False
        return f

@nottest
def warn_user_about_tests(test_suite_type='regression'):
    """
    Display a standard warning about running tests that might modify
    user data, and wait for user confirmation, unless --yes-i-know
    was specified in the comman line.
    """

    # Provide a command line option to avoid having to type the
    # confirmation every time during development.
    if '--yes-i-know' in sys.argv:
        return

    if test_suite_type == 'web':
        sys.stderr.write("""\
**********************************************************************
**                                                                  **
**     A B O U T   T H E   W E B   T E S T   S U I T E              **
**                                                                  **
** The web test suite will be launched in Firefox.  You must have   **
** the Selenium IDE extension installed to be able to run the web   **
** test suite.  If you do, please check out the results of the web  **
** test suite in the Selenium IDE window.                           **
**                                                                  **
**********************************************************************

""")

    sys.stderr.write("""\
**********************************************************************
**                                                                  **
**     I M P O R T A N T   W A R N I N G                            **
**                                                                  **
** The %s test suite needs to be run on a clean demo site   **
** that you can obtain by doing:                                    **
**                                                                  **
**    $ inveniocfg --drop-demo-site \                               **
**                 --create-demo-site \                             **
**                 --load-demo-records                              **
**                                                                  **
** Note that DOING THE ABOVE WILL ERASE YOUR ENTIRE DATABASE.       **
**                                                                  **
** In addition, due to the write nature of some of the tests,       **
** the demo DATABASE will be ALTERED WITH JUNK DATA, so that        **
** it is recommended to rebuild the demo site anew afterwards.      **
**                                                                  **
**********************************************************************

Please confirm by typing 'Yes, I know!': """ % test_suite_type)

    answer = raw_input('')
    if answer != 'Yes, I know!':
        sys.stderr.write("Aborted.\n")
        raise SystemExit(0)

    return

@nottest
def make_test_suite(*test_cases):
    """ Build up a test suite given separate test cases"""
    return unittest.TestSuite([unittest.makeSuite(case, 'test')
                               for case in test_cases])

@nottest
def run_test_suite(testsuite, warn_user=False):
    """
    Convenience function to embed in test suites.  Run given testsuite
    and eventually ask for confirmation of warn_user is True.
    """
    if warn_user:
        warn_user_about_tests()
    unittest.TextTestRunner(verbosity=2).run(testsuite)

def make_url(path, **kargs):
    """ Helper to generate an absolute invenio URL with query
    arguments"""

    url = CFG_SITE_URL + path

    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

def make_surl(path, **kargs):
    """ Helper to generate an absolute invenio Secure URL with query
    arguments"""

    url = CFG_SITE_SECURE_URL + path

    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

class InvenioTestUtilsBrowserException(Exception):
    """Helper exception for the regression test suite browser."""
    pass

@nottest
def test_web_page_existence(url):
    """
    Test whether URL exists and is well accessible.
    Return True or raise exception in case of problems.
    """
    import mechanize
    browser = mechanize.Browser()
    try:
        browser.open(url)
    except:
        raise
    return True

def get_authenticated_mechanize_browser(username="guest", password=""):
    """
    Return an instance of a mechanize browser already authenticated
    to Invenio
    """
    try:
        import mechanize
    except ImportError:
        raise InvenioTestUtilsBrowserException('ERROR: Cannot import mechanize.')
    browser = mechanize.Browser()
    browser.set_handle_robots(False) # ignore robots.txt, since we test gently
    if username == "guest":
        return browser
    browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
    browser.select_form(nr=0)
    browser['p_un'] = username
    browser['p_pw'] = password
    browser.submit()
    username_account_page_body = browser.response().read()
    try:
        username_account_page_body.index("You are logged in as %s." % username)
    except ValueError:
        raise InvenioTestUtilsBrowserException('ERROR: Cannot login as %s.' % username)
    return browser

@nottest
def test_web_page_content(url,
                          username="guest",
                          password="",
                          expected_text="</html>",
                          unexpected_text="",
                          expected_link_target=None,
                          expected_link_label=None,
                          require_validate_p=CFG_TESTS_REQUIRE_HTML_VALIDATION):
    """Test whether web page URL as seen by user USERNAME contains
       text EXPECTED_TEXT and, eventually, contains a link to
       EXPECTED_LINK_TARGET (if set) labelled EXPECTED_LINK_LABEL (if
       set).  The EXPECTED_TEXT is checked via substring matching, the
       EXPECTED_LINK_TARGET and EXPECTED_LINK_LABEL via exact string
       matching.

       EXPECTED_TEXT, EXPECTED_LINK_LABEL and EXPECTED_LINK_TARGET can
       either be strings or list of strings (in order to check multiple
       values inside same page).

       Before doing the tests, login as USERNAME with password
       PASSWORD.  E.g. interesting values for USERNAME are "guest" or
       "admin".

       Return empty list in case of problems, otherwise list of error
       messages that may have been encountered during processing of
       page.
    """
    try:
        import mechanize
    except ImportError:
        raise InvenioTestUtilsBrowserException('ERROR: Cannot import mechanize.')
    if '--w3c-validate' in sys.argv:
        require_validate_p = True
        sys.stderr.write('Required validation\n')

    error_messages = []
    try:
        browser = get_authenticated_mechanize_browser(username, password)
        browser.open(url)
        url_body = browser.response().read()

        # now test for EXPECTED_TEXT:
        # first normalize expected_text
        if isinstance(expected_text, str):
            expected_texts = [expected_text]
        else:
            expected_texts = expected_text
        # then test
        for cur_expected_text in expected_texts:
            try:
                url_body.index(cur_expected_text)
            except ValueError:
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Page %s (login %s) does not contain %s.' % \
                      (url, username, cur_expected_text)

        # now test for UNEXPECTED_TEXT:
        # first normalize unexpected_text
        if isinstance(unexpected_text, str):
            if unexpected_text:
                unexpected_texts = [unexpected_text]
            else:
                unexpected_texts = []
        else:
            unexpected_texts = unexpected_text
        # then test
        for cur_unexpected_text in unexpected_texts:
            try:
                url_body.index(cur_unexpected_text)
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Page %s (login %s) contains %s.' % \
                      (url, username, cur_unexpected_text)
            except ValueError:
                pass

        # now test for EXPECTED_LINK_TARGET and EXPECTED_LINK_LABEL:
        if expected_link_target or expected_link_label:
            # first normalize expected_link_target and expected_link_label
            if isinstance(expected_link_target, str) or \
                   expected_link_target is None:
                expected_link_targets = [expected_link_target]
            else:
                expected_link_targets = expected_link_target
            if isinstance(expected_link_label, str) or \
                   expected_link_label is None:
                expected_link_labels = [expected_link_label]
            else:
                expected_link_labels = expected_link_label
            max_links = max(len(expected_link_targets), len(expected_link_labels))
            expected_link_labels = chain(expected_link_labels, repeat(None))
            expected_link_targets = chain(expected_link_targets, repeat(None))
            # then test
            for dummy in range(0, max_links):
                cur_expected_link_target = expected_link_targets.next()
                cur_expected_link_label = expected_link_labels.next()
                try:
                    browser.find_link(url=cur_expected_link_target,
                                      text=cur_expected_link_label)
                except mechanize.LinkNotFoundError:
                    raise InvenioTestUtilsBrowserException, \
                          'ERROR: Page %s (login %s) does not contain link to %s entitled %s.' % \
                          (url, username, cur_expected_link_target, cur_expected_link_label)

        # now test for validation if required
        if require_validate_p:
            valid_p, errors, warnings = w3c_validate(url_body)
            if not valid_p:
                error_text = 'ERROR: Page %s (login %s) does not validate:\n %s' % \
                                  (url, username, w3c_errors_to_str(errors, warnings))
                open('%s/w3c-markup-validator.log' % CFG_LOGDIR, 'a').write(error_text)
                raise InvenioTestUtilsBrowserException, error_text


    except mechanize.HTTPError, msg:
        error_messages.append('ERROR: Page %s (login %s) not accessible. %s' % \
                              (url, username, msg))
    except InvenioTestUtilsBrowserException, msg:
        error_messages.append('ERROR: Page %s (login %s) led to an error: %s.' % \
                              (url, username, msg))

    try:
        # logout after tests:
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/logout")
        browser.response().read()
        browser.close()
    except UnboundLocalError:
        pass

    if CFG_TESTUTILS_VERBOSE >= 9:
        print "%s test_web_page_content(), tested page `%s', login `%s', expected text `%s', errors `%s'." % \
              (time.strftime("%Y-%m-%d %H:%M:%S -->", time.localtime()),
               url, username, expected_text,
               ",".join(error_messages))

    return error_messages

def merge_error_messages(error_messages):
    """If the ERROR_MESSAGES list is non-empty, merge them and return nicely
       formatted string suitable for printing.  Otherwise return empty
       string.
    """
    out = ""
    if error_messages:
        out = "\n*** " + "\n*** ".join(error_messages)
    return out

@nottest
def build_and_run_unit_test_suite():
    """
    Detect all Invenio modules with names ending by '*_tests.py' (and
    not '_regression_tests.py'), build a complete test suite of them,
    and run it.  Called by 'inveniocfg --run-unit-tests'.
    """

    # We first import webinterface_tests in order to be sure to have
    # the fake Apache environment loaded among first things.  This is
    # needed for older OSes and mod_pythons such as on SLC4.
    from invenio import webinterface_tests

    test_modules = []

    for candidate in os.listdir(os.path.dirname(invenio.__file__)):
        base, ext = os.path.splitext(candidate)

        if ext != '.py' or not (base.endswith('_tests') and not \
                                base.endswith('_regression_tests')):
            continue

        module = __import__('invenio.' + base, globals(), locals(), ['TEST_SUITE'])
        test_modules.append(module.TEST_SUITE)

    complete_suite = unittest.TestSuite(test_modules)
    unittest.TextTestRunner(verbosity=2).run(complete_suite)

@nottest
def build_and_run_regression_test_suite():
    """
    Detect all Invenio modules with names ending by
    '*_regression_tests.py', build a complete test suite of them, and
    run it.  Called by 'inveniocfg --run-regression-tests'.
    """

    test_modules = []

    for candidate in os.listdir(os.path.dirname(invenio.__file__)):
        base, ext = os.path.splitext(candidate)

        if ext != '.py' or not base.endswith('_regression_tests'):
            continue

        module = __import__('invenio.' + base, globals(), locals(), ['TEST_SUITE'])
        test_modules.append(module.TEST_SUITE)

    warn_user_about_tests()

    complete_suite = unittest.TestSuite(test_modules)
    unittest.TextTestRunner(verbosity=2).run(complete_suite)

@nottest
def build_and_run_web_test_suite():
    """
    Detect all Selenium web test cases, build a complete test suite of
    them, and run it in a browser. (Requires Firefox with Selenium IDE
    extension.)  Called by 'inveniocfg --run-web-tests'.
    """
    # warn user first:
    warn_user_about_tests('web')
    # build test suite with all web tests:
    print ">>> Building complete web test suite..."
    webtestdir = CFG_PREFIX +  '/lib/webtest/invenio'
    fdesc = open(webtestdir + os.sep + "test_all.html", "w")
    fdesc.write('<table>\n')
    fdesc.write('<tr><td>Web test suite for the whole Invenio.</td></tr>\n')
    for candidate in sorted(os.listdir(webtestdir)):
        base, ext = os.path.splitext(candidate)
        if ext != '.html' or base == 'test_all':
            continue
        fdesc.write('<tr><td><a target="testFrame" href="%s">%s</a></td></tr>\n' % (candidate, base))
    fdesc.write('</table>\n')
    fdesc.close()
    # run this test suite:
    cmd = "firefox -chrome 'chrome://selenium-ide/content/selenium/TestRunner.html?baseURL=%s&test=file://%s/test_all.html&auto=true' -height 800 -width 1200 &" % \
          (CFG_SITE_URL, webtestdir)
    print ">>> Launching Firefox with Selenium IDE, please check the web test results there."
    os.system(cmd)
