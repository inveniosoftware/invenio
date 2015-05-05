# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Helper functions for building and running test suites."""

from __future__ import print_function, with_statement

# pylint: disable=E1102

CFG_TESTUTILS_VERBOSE = 1

import difflib
import os
import sys
import time
pyv = sys.version_info
if pyv[0] == 2 and pyv[1] < 7:
    import unittest2 as unittest
else:
    import unittest
import cgi
import subprocess
import binascii
import StringIO

from flask import url_for
from functools import wraps
from warnings import warn
from six import iteritems
from six.moves.urllib.parse import urlsplit, urlunsplit
from urllib import urlencode
from itertools import chain, repeat
from xml.dom.minidom import parseString

try:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    # web tests will not be available, but unit and regression tests will:
    pass

#try:
#    from nose.tools import nottest
#except ImportError:
#    def nottest(f):
#        """Helper decorator to mark a function as not to be tested by nose."""
#        f.__test__ = False
#        return f

nottest = unittest.skip('nottest')


#@nottest
def warn_user_about_tests(test_suite_type='regression'):
    """Display a standard warning.

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
**    $ inveniocfg --drop-demo-site                                 **
**    $ inveniocfg --create-demo-site                               **
**    $ inveniomanage demosite create                              **
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


#@nottest
def make_test_suite(*test_cases):
    """Build up a test suite given separate test cases."""
    return unittest.TestSuite([unittest.makeSuite(case, 'test')
                               for case in test_cases])

from invenio.base.factory import create_app
# pyparsing needed to import here before flask_testing in order to avoid
# pyparsing troubles due to twill
import pyparsing  # pylint: disable=W0611
from flask_testing import TestCase


class InvenioFixture(object):

    """Fixtures."""

    def __init__(self, fixture_builder=None):
        """Initialize the fixture."""
        self.fixture = None
        self.fixture_builder = fixture_builder

    def with_data(self, *datatypes):
        """FIXME: documentation is missing."""
        def dictate(func):
            @wraps(func)
            def patched(*args, **kwargs):
                if self.fixture is None:
                    self.fixture = self.fixture_builder()

                @self.fixture.with_data(*datatypes)
                def with_data_func(data):
                    return func(data, *args, **kwargs)
                return with_data_func()
            return patched
        return dictate


class InvenioTestCase(TestCase):

    """Base test case for invenio."""

    @property
    def config(self):
        """Configuration property."""
        cfg = {
            'engine': 'CFG_DATABASE_TYPE',
            'host': 'CFG_DATABASE_HOST',
            'port': 'CFG_DATABASE_PORT',
            'username': 'CFG_DATABASE_USER',
            'password': 'CFG_DATABASE_PASS',
            'database': 'CFG_DATABASE_NAME',
        }
        out = {}
        for (k, v) in iteritems(cfg):
            if hasattr(self, k):
                out[v] = getattr(self, k)
        return out

    def create_app(self):
        """Create the Flask application for testing."""
        app = create_app(**self.config)
        app.testing = True
        return app

    def login(self, username, password):
        """Log in as username and password."""
        from invenio.config import CFG_SITE_SECURE_URL
        #from invenio.utils.url import rewrite_to_secure_url
        return self.client.post(url_for('webaccount.login'),
                                base_url=CFG_SITE_SECURE_URL,
                                #rewrite_to_secure_url(request.base_url),
                                data=dict(nickname=username,
                                          password=password),
                                follow_redirects=True)

    def logout(self):
        """Log out."""
        from invenio.config import CFG_SITE_SECURE_URL
        return self.client.get(url_for('webaccount.logout'),
                               base_url=CFG_SITE_SECURE_URL,
                               follow_redirects=True)

    def shortDescription(self):
        """Return a short description of the test case."""
        return


class InvenioXmlTestCase(InvenioTestCase):
    def assertXmlEqual(self, got, want):
        xml_lines = parseString(got).toprettyxml(encoding='utf-8').split('\n')
        xml = '\n'.join(line for line in xml_lines if line.strip())
        xml2_lines = parseString(want).toprettyxml(encoding='utf-8').split('\n')
        xml2 = '\n'.join(line for line in xml2_lines if line.strip())
        try:
            self.assertEqual(xml, xml2)
        except AssertionError:
            for line in difflib.unified_diff(xml.split('\n'), xml2.split('\n')):
                print(line.strip('\n'))
            raise


class FlaskSQLAlchemyTest(InvenioTestCase):

    """Setting up and tearing down the database during tests."""

    def setUp(self):
        """Create the tables."""
        from invenio.ext.sqlalchemy import db
        db.create_all()

    def tearDown(self):
        """Drop the tables."""
        from invenio.ext.sqlalchemy import db
        db.session.expunge_all()
        db.session.rollback()
        db.drop_all()


#@nottest
def make_flask_test_suite(*test_cases):
    """Build up a Flask test suite given separate test cases."""
    from operator import add
    from invenio.config import CFG_DEVEL_TEST_DATABASE_ENGINES as engines
    create_type = lambda c: [type(k + c.__name__, (c,), d)
                             for k, d in iteritems(engines)]

    return unittest.TestSuite([unittest.makeSuite(case, 'test')
                              for case in reduce(add, map(create_type,
                                                          test_cases))])


@nottest
def run_test_suite(testsuite, warn_user=False):
    """"Run given testsuite and ask for confirmation if warn_user is True.

    Convenience function to embed in test suites.
    """
    if warn_user:
        warn_user_about_tests()
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    return runner.run(testsuite).wasSuccessful()


def make_url(path, **kargs):
    """Helper to generate an absolute invenio URL with query arguments."""
    from invenio.config import CFG_SITE_URL

    url = CFG_SITE_URL + path

    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url


def make_surl(path, **kargs):
    """Generate an absolute invenio Secure URL with query arguments."""
    from invenio.config import CFG_SITE_SECURE_URL
    url = CFG_SITE_SECURE_URL + path

    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url


def base64_to_file(base64_file, filepath):
    """Write a base64 encoded version of a file to disk."""
    with open(filepath, 'wb') as f:
        f.write(binascii.a2b_base64(base64_file))


def file_to_base64(filepath):
    """Get base64 encoded version of a file.

    Useful to encode a test file for inclusion in tests.
    """
    with open(filepath, 'rb') as f:
        return binascii.b2a_base64(f.read())


def stringio_to_base64(stringio_obj):
    """Get base64 encoded version of a StringIO object."""
    return binascii.b2a_base64(stringio_obj.getvalue())


def make_file_fixture(filename, base64_file):
    """
    Generate a file fixture suitable for use with the Flask test client.

    :param base64_file: A string encoding a file in base64. Use
        file_to_base64() to get the base64 encoding of a file. If not provided
        a PDF file be generated instead, including
    """
    fp = StringIO.StringIO(binascii.a2b_base64(base64_file))
    return fp, filename


def make_pdf_fixture(filename, text=None):
    """
    Generate a PDF fixture.

    It's suitable for use with Werkzeug test client and Flask test request
    context.

    Use of this function requires that reportlab have been installed.

    :param filename: Desired filename.
    :param text: Text to include in PDF. Defaults to "Filename: <filename>", if
        not specified.
    """
    if text is None:
        text = "Filename: %s" % filename

    # Generate simple PDF
    from reportlab.pdfgen import canvas
    output = StringIO.StringIO()
    c = canvas.Canvas(output)
    c.drawString(100, 100, text)
    c.showPage()
    c.save()

    return make_file_fixture(filename, stringio_to_base64(output))


class InvenioTestUtilsBrowserException(Exception):

    """Exception for the regression test suite browser."""

    pass


#@nottest
def test_web_page_existence(url):
    """
    Test whether URL exists and is well accessible.

    :return: True or raise exception in case of problems.
    """
    import mechanize
    browser = mechanize.Browser()
    try:
        browser.open(url)
    except:
        raise
    return True


def get_authenticated_mechanize_browser(username="guest", password=""):
    """Return an instance of an authenticated mechanize browser."""
    try:
        import mechanize
    except ImportError:
        raise InvenioTestUtilsBrowserException(
            'ERROR: Cannot import mechanize.')
    browser = mechanize.Browser()
    browser.set_handle_robots(False)  # ignore robots.txt, since we test gently
    if username == "guest":
        return browser
    from invenio.config import CFG_SITE_SECURE_URL
    browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
    browser.select_form(nr=0)
    browser['nickname'] = username
    browser['password'] = password
    browser.submit()
    username_account_page_body = browser.response().read()
    try:
        username_account_page_body.index("You are logged in as %s." % username)
    except ValueError:
        raise InvenioTestUtilsBrowserException(
            'ERROR: Cannot login as %s.' % username)
    return browser


#@nottest
def test_web_page_content(url,
                          username="guest",
                          password="",
                          expected_text="</html>",
                          unexpected_text="",
                          expected_link_target=None,
                          expected_link_label=None,
                          require_validate_p=None):
    """Test the content of a web page.

    Test whether web page URL as seen by user USERNAME contains
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

    :return: empty list in case of no problems, otherwise list of error
        messages that may have been encountered during processing of page.
    """
    from invenio.utils.w3c_validator import (w3c_validate, w3c_errors_to_str,
                                             CFG_TESTS_REQUIRE_HTML_VALIDATION)
    if require_validate_p is None:
        require_validate_p = CFG_TESTS_REQUIRE_HTML_VALIDATION
    try:
        import mechanize
    except ImportError:
        raise InvenioTestUtilsBrowserException(
            'ERROR: Cannot import mechanize.')
    if '--w3c-validate' in sys.argv:
        require_validate_p = True
        sys.stderr.write('Required validation\n')

    error_messages = []
    try:
        browser = get_authenticated_mechanize_browser(username, password)
        try:
            browser.open(url)
        except mechanize.HTTPError as msg:
            if msg.code != 401:
                raise msg
            error_messages.append('ERROR: Page %s (login %s) not accessible. '
                                  '%s' %
                                  (url, username, msg))
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
                raise InvenioTestUtilsBrowserException(
                    'ERROR: Page %s (login %s) does not contain %s, but '
                    'contains %s',
                    (url, username, cur_expected_text, url_body))

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
                raise InvenioTestUtilsBrowserException(
                    'ERROR: Page %s (login %s) contains %s.' %
                    (url, username, cur_unexpected_text))
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
            max_links = max(
                len(expected_link_targets), len(expected_link_labels))
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
                    raise InvenioTestUtilsBrowserException(
                        'ERROR: Page %s (login %s) does not contain link to %s'
                        'entitled %s.' %
                        (url, username, cur_expected_link_target,
                         cur_expected_link_label)
                    )

        # now test for validation if required
        if require_validate_p:
            valid_p, errors, warnings = w3c_validate(url_body)
            if not valid_p:
                error_text = 'ERROR: Page %s (login %s) does not ' \
                             'validate:\n %s' % \
                             (url, username, w3c_errors_to_str(
                              errors, warnings))
                from invenio.config import CFG_LOGDIR
                open('%s/w3c-markup-validator.log' %
                     CFG_LOGDIR, 'a').write(error_text)
                raise InvenioTestUtilsBrowserException(error_text)

    except InvenioTestUtilsBrowserException as msg:
        error_messages.append(
            'ERROR: Page %s (login %s) led to an error: %s.' %
            (url, username, msg))

    try:
        # logout after tests:
        from invenio.config import CFG_SITE_SECURE_URL
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/logout")
        browser.response().read()
        browser.close()
    except UnboundLocalError:
        pass
    except mechanize.HTTPError:
        # Raises 401 if you were not logged in before.
        pass

    if CFG_TESTUTILS_VERBOSE >= 9:
        print("%s test_web_page_content(), tested page `%s', login `%s', "
              "expected text `%s', errors `%s'." %
              (time.strftime("%Y-%m-%d %H:%M:%S -->", time.localtime()),
               url, username, expected_text,
               ",".join(error_messages)))

    return error_messages


def merge_error_messages(error_messages):
    """Merge the error messages into a print-friendly version.

    If the ERROR_MESSAGES list is non-empty, merge them and return nicely
    formatted string suitable for printing.  Otherwise return empty string.
    """
    out = ""
    if error_messages:
        out = "\n*** " + "\n*** ".join(error_messages)
    return out


#@nottest
def build_and_run_unit_test_suite():
    """Build and run the unit tests.

    Detect all Invenio modules with names ending by '*_unit_tests.py', build
    a complete test suite of them, and run it.
    Called by 'inveniocfg --run-unit-tests'.
    """
    from invenio.config import CFG_PYLIBDIR
    from invenio.pluginutils import PluginContainer
    test_modules_map = PluginContainer(
        os.path.join(CFG_PYLIBDIR, 'invenio', '*_unit_tests.py'),
        lambda plugin_name, plugin_code: getattr(plugin_code, "TEST_SUITE"))
    test_modules = [test_modules_map[name] for name in test_modules_map]

    broken_tests = test_modules_map.get_broken_plugins()

    broken_unit_tests = ['%s (reason: %s)' % (name, broken_tests[name][1])
                         for name in broken_tests]
    if broken_unit_tests:
        warn("Broken unit tests suites found: %s" %
             ', '.join(broken_unit_tests))

    complete_suite = unittest.TestSuite(test_modules)
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    return runner.run(complete_suite).wasSuccessful()


#@nottest
def build_and_run_js_unit_test_suite():
    """Build and run the JavaScript unit tests.

    Init the JsTestDriver server, detect all Invenio JavaScript files with
    names ending by '*_tests.js' and run them.
    Called by 'inveniocfg --run-js-unit-tests'.
    """
    from invenio.config import CFG_PREFIX, CFG_WEBDIR, CFG_JSTESTDRIVER_PORT

    def _server_init(server_process):
        """Init JsTestDriver server and check if it succedeed."""
        output_success = "Finished action run"
        output_error = "Server failed"
        read_timeout = 30

        start_time = time.time()
        elapsed_time = 0
        while 1:
            stdout_line = server_process.stdout.readline()
            if output_success in stdout_line:
                print('* JsTestDriver server ready\n')
                return True
            elif output_error in stdout_line or elapsed_time > read_timeout:
                print('* ! JsTestDriver server init failed\n')
                print(server_process.stdout.read())
                return False
            elapsed_time = time.time() - start_time

    def _find_and_run_js_test_files():
        """Find and run all the JavaScript files.

        Find all JS files installed in Invenio lib directory and run
        them on the JsTestDriver server
        """
        from invenio.utils.shell import run_shell_command
        errors_found = 0
        for candidate in os.listdir(CFG_WEBDIR + "/js"):
            base, ext = os.path.splitext(candidate)

            if ext != '.js' or not base.endswith('_tests'):
                continue

            print("Found test file %s. Running tests... " % (base + ext))
            exitcode_, stdout, stderr_ = run_shell_command(
                cmd="java -jar %s/JsTestDriver.jar --config %s --tests all" %
                (CFG_PREFIX + "/lib/java/js-test-driver",
                 CFG_WEBDIR + "/js/" + base + '.conf'))
            print(stdout)
            if "Fails: 0" not in stdout:
                errors_found += 1
        print(errors_found)
        return errors_found

    print("Going to start JsTestDriver server...")
    server_process = subprocess.Popen([
        "java",
        "-jar",
        "%s/JsTestDriver.jar" % (CFG_PREFIX + "/lib/java/js-test-driver"),
        "--runnerMode", "INFO",
        "--port",
        "%d" % CFG_JSTESTDRIVER_PORT],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    try:
        from invenio.config import CFG_SITE_URL
        if not _server_init(server_process):
            # There was an error initialising server
            return 1

        print("Now you can capture the browsers where you would "
              "like to run the tests by opening the following url:\n"
              "%s:%d/capture \n" % (CFG_SITE_URL, CFG_JSTESTDRIVER_PORT))

        print("Press enter when you are ready to run tests")
        raw_input()

        exitcode = _find_and_run_js_test_files()
    finally:
        server_process.kill()

    return exitcode


#@nottest
def build_and_run_regression_test_suite():
    """Build and run the regression tests.

    Detect all Invenio modules with names ending by
    '*_regression_tests.py', build a complete test suite of them, and
    run it.  Called by 'inveniocfg --run-regression-tests'.
    """
    from invenio.config import CFG_PYLIBDIR
    from invenio.pluginutils import PluginContainer
    test_modules_map = PluginContainer(
        os.path.join(CFG_PYLIBDIR, 'invenio', '*_regression_tests.py'),
        lambda plugin_name, plugin_code: getattr(plugin_code, "TEST_SUITE"))
    test_modules = test_modules_map.values()

    broken_tests = test_modules_map.get_broken_plugins()

    broken_regression_tests = ['%s (reason: %s)' % (name,
                                                    broken_tests[name][1])
                               for name in broken_tests]
    if broken_regression_tests:
        warn("Broken regression tests suites found: %s" %
             ', '.join(broken_regression_tests))

    warn_user_about_tests()

    complete_suite = unittest.TestSuite(test_modules)
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    return runner.run(complete_suite).wasSuccessful()


#@nottest
def build_and_run_web_test_suite():
    """Build and run the web tests.

    Detect all Invenio modules with names ending by
    '*_web_tests.py', build a complete test suite of them, and
    run it.  Called by 'inveniocfg --run-web-tests'.
    """
    from invenio.config import CFG_PYLIBDIR
    from invenio.pluginutils import PluginContainer
    test_modules_map = PluginContainer(
        os.path.join(CFG_PYLIBDIR, 'invenio', '*_web_tests.py'),
        lambda plugin_name, plugin_code: getattr(plugin_code, "TEST_SUITE"))
    test_modules = test_modules_map.values()

    broken_tests = test_modules_map.get_broken_plugins()

    broken_web_tests = ['%s (reason: %s)' % (name, broken_tests[name][1])
                        for name in broken_tests]
    if broken_web_tests:
        warn("Broken web tests suites found: %s" % ', '.join(broken_web_tests))

    warn_user_about_tests()

    complete_suite = unittest.TestSuite(test_modules)
    runner = unittest.TextTestRunner(descriptions=False, verbosity=2)
    return runner.run(complete_suite).wasSuccessful()


class InvenioWebTestCase(InvenioTestCase):

    """
    Base test case for the web environment.

    Helper library of useful web test functions for web tests creation.
    """

    def setUp(self):
        """Initialization before tests."""
        # Let's default to English locale
        profile = webdriver.FirefoxProfile()
        profile.set_preference('intl.accept_languages', 'en-us, en')
        profile.update_preferences()

        # the instance of Firefox WebDriver is created
        self.browser = webdriver.Firefox(profile)

        # list of errors
        self.errors = []

    def tearDown(self):
        """Cleanup actions after tests."""
        self.browser.quit()
        self.assertEqual([], self.errors)

    def find_element_by_name_with_timeout(self, element_name, timeout=30):
        """Find an element by name.

        This waits up to 'timeout' seconds before throwing an
        InvenioWebTestCaseException or if it finds the element will return it
        in 0 - timeout seconds.

        :param element_name: name of the element to find
        :type element_name: string
        :param timeout: time in seconds before throwing an exception if the
            element is not found
        :type timeout: int
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.find_element_by_name(element_name))
        except:
            raise InvenioWebTestCaseException(element=element_name)

    def find_element_by_link_text_with_timeout(self, element_link_text,
                                               timeout=30):
        """Find an element by link text.

        This waits up to 'timeout' seconds before throwing an
        InvenioWebTestCaseException or if it finds the element will return it
        in 0 - timeout seconds.

        :param element_link_text: link text of the element to find
        :type element_link_text: string
        :param timeout: time in seconds before throwing an exception if the
            element is not found
        :type timeout: int
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.find_element_by_link_text(
                    element_link_text))
        except:
            raise InvenioWebTestCaseException(element=element_link_text)

    def find_element_by_partial_link_text_with_timeout(
            self,
            element_partial_link_text,
            timeout=30):
        """Find an element by partial link text.

        This waits up to 'timeout' seconds before throwing an
        InvenioWebTestCaseException or if it finds the element will return it
        in 0 - timeout seconds.

        :param element_partial_link_text: partial link text of the element to
            find
        :type element_partial_link_text: string
        :param timeout: time in seconds before throwing an exception if the
            element is not found
        :type timeout: int
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.find_element_by_partial_link_text(
                    element_partial_link_text))
        except:
            raise InvenioWebTestCaseException(
                element=element_partial_link_text)

    def find_element_by_id_with_timeout(self, element_id, timeout=30, text=""):
        """Find an element by id.

        This waits up to 'timeout' seconds before throwing an
        InvenioWebTestCaseException or if it finds the element will return it
        in 0 - timeout seconds.

        If the parameter text is provided, the function waits until the element
        is found and its content is equal to the given text.

        If the element's text is not equal to the given text an exception will
        be raised and the result of this comparison will be stored in the
        errors list

        **NOTE:** Currently this is used to wait for an element's text to be
        refreshed using JavaScript

        :param element_id: id of the element to find
        :type element_id: string
        :param timeout: time in seconds before throwing an exception if the
            element is not found
        :type timeout: int
        :param text: expected text inside the given element.
        :type text: string
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.find_element_by_id(element_id))
        except:
            raise InvenioWebTestCaseException(element=element_id)

        if text:
            q = self.browser.find_element_by_id(element_id)
            try:
                # if the element's text is not equal to the given text, an
                # exception will be raised
                WebDriverWait(self.browser, timeout).until(
                    lambda driver: (driver.find_element_by_id(element_id) and
                                    q.text == text))
            except:
                # let's store the result of the comparison in the errors list
                try:
                    self.assertEqual(q.text, text)
                except AssertionError as e:
                    self.errors.append(str(e))

    def find_element_by_xpath_with_timeout(self, element_xpath, timeout=30):
        """Find an element by xpath.

        This waits up to 'timeout' seconds before throwing an
        InvenioWebTestCaseException or if it finds the element will return it
        in 0 - timeout seconds.

        :param element_xpath: xpath of the element to find
        :type element_xpath: string
        :param timeout: time in seconds before throwing an exception if the
            element is not found
        :type timeout: int
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.find_element_by_xpath(element_xpath))
        except:
            raise InvenioWebTestCaseException(element=element_xpath)

    def find_elements_by_class_name_with_timeout(self, element_class_name,
                                                 timeout=30):
        """Find an element by class name.

        This waits up to 'timeout' seconds before throwing an
        InvenioWebTestCaseException or if it finds the element  will return it
        in 0 - timeout seconds.

        :param element_class_name: class name of the element to find
        :type element_class_name: string
        :param timeout: time in seconds before throwing an exception if the
            element is not found
        :type timeout: int
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.find_element_by_class_name(
                    element_class_name))
        except:
            raise InvenioWebTestCaseException(element=element_class_name)

    def find_page_source_with_timeout(self, timeout=30):
        """Find the page source.

        This waits up to 'timeout' seconds  before throwing an
        InvenioWebTestCaseException or if the page source is loaded will return
        it in 0 - timeout seconds.

        :param timeout: time in seconds before throwing an exception if the
            page source is not found
        :type timeout: int
        """
        try:
            WebDriverWait(self.browser, timeout).until(
                lambda driver: driver.page_source)
        except:
            raise InvenioWebTestCaseException(element="page source")

    def login(self, username="guest", password="", force_ln='en',
              go_to_login_page=True):
        """Log in.

        :param username: the username (nickname or email)
        :type username: str
        :param password: the corresponding password
        :type password: str
        :param force_ln: if the arrival page doesn't use the corresponding
            language, then the browser will redirect to it.
        :type force_ln: str
        :param go_to_login_page: if True, look for login link on the
                                 page. Otherwise expect to be already
                                 on a page with the login form
        :type go_to_login_page: bool
        """
        if go_to_login_page:
            if ("You can use your nickname or your email address to login."
                    not in self.browser.page_source):

                if ("You are no longer recognized by our system"
                        in self.browser.page_source):

                    self.find_element_by_link_text_with_timeout("login here")
                    self.browser.find_element_by_link_text(
                        "login here").click()
                else:
                    self.find_element_by_link_text_with_timeout("login")
                    self.browser.find_element_by_link_text("login").click()

        self.find_element_by_name_with_timeout("nickname")
        self.browser.find_element_by_name("nickname").clear()
        self.fill_textbox(textbox_name="nickname", text=username)
        self.find_element_by_name_with_timeout("password")
        self.browser.find_element_by_name("password").clear()
        self.fill_textbox(textbox_name="password", text=password)
        self.find_element_by_name_with_timeout("action")
        self.browser.find_element_by_name("action").click()
        from invenio.config import CFG_SITE_NAME_INTL
        if force_ln and (CFG_SITE_NAME_INTL[force_ln]
                         not in self.browser.page_source):
            splitted_url = list(urlsplit(self.browser.current_url))
            query = cgi.parse_qs(splitted_url[3])
            query.update({u'ln': unicode(force_ln)})
            splitted_url[3] = urlencode(query)
            new_url = urlunsplit(splitted_url)
            self.browser.get(new_url)

    def logout(self):
        """Log out."""
        self.find_element_by_link_text_with_timeout("logout")
        self.browser.find_element_by_link_text("logout").click()

    @nottest
    def element_value_test(self,
                           element_name="",
                           element_id="",
                           expected_element_value="",
                           unexpected_element_value="",
                           in_form=True):
        """Check if the value in the given element is the expected value.

        :param element_name: name of the corresponding element in the form
        :type element_name: string
        :param element_id: id of the corresponding element in the form
        :type element_id: string
        :param expected_element_value: the expected element value
        :type expected_element_value: string
        :param unexpected_element_value: the unexpected element value
        :type unexpected_element_value: string
        :param in_form: depends on this parameter, the value of the given
            element is got in a different way. If it is True, the given element
            is a textbox or a textarea in a form.
        :type in_form: boolean
        """
        if element_name:
            self.find_element_by_name_with_timeout(element_name)
            q = self.browser.find_element_by_name(element_name)
        elif element_id:
            self.find_element_by_id_with_timeout(element_id)
            q = self.browser.find_element_by_id(element_id)

        if unexpected_element_value:
            try:
                if in_form:
                    self.assertNotEqual(
                        q.get_attribute('value'), unexpected_element_value)
                else:
                    self.assertNotEqual(q.text, unexpected_element_value)
            except AssertionError as e:
                self.errors.append(str(e))

        if expected_element_value:
            try:
                if in_form:
                    self.assertEqual(
                        q.get_attribute('value'), expected_element_value)
                else:
                    self.assertEqual(q.text, expected_element_value)
            except AssertionError as e:
                self.errors.append(str(e))

    @nottest
    def page_source_test(self, expected_text="", unexpected_text=""):
        """Check if the current page contains (or not) the expected text(s).

        The expected text (unexpected text) can also be a link.

        The expected text (unexpected text) can be a list of strings in order
        to check multiple values inside same page

        :param expected_text: the expected text
        :type expected_text: string or list of strings
        :param unexpected_text: the unexpected text
        :type unexpected_text: string or list of strings
        """
        self.find_page_source_with_timeout()
        if unexpected_text:
            if isinstance(unexpected_text, str):
                unexpected_texts = [unexpected_text]
            else:
                unexpected_texts = unexpected_text

            for unexpected_text in unexpected_texts:
                try:
                    self.assertEqual(
                        -1, self.browser.page_source.find(unexpected_text))
                except AssertionError as e:
                    self.errors.append(str(e))

        if expected_text:
            if isinstance(expected_text, str):
                expected_texts = [expected_text]
            else:
                expected_texts = expected_text

            for expected_text in expected_texts:
                try:
                    self.assertNotEqual(
                        -1, self.browser.page_source.find(expected_text))
                except AssertionError as e:
                    self.errors.append(str(e))

    def choose_selectbox_option_by_label(self,
                                         selectbox_name="",
                                         selectbox_id="",
                                         label=""):
        """Select the option at the given label in the select box.

        :param selectbox_name: the name of the corresponding select box in the
            form
        :type selectbox_name: string
        :param selectbox_id: the id of the corresponding select box in the form
        :type selectbox_id: string
        :param label: the option at this label will be selected
        :type label: string
        """
        if selectbox_name:
            self.find_element_by_name_with_timeout(selectbox_name)
            selectbox = self.browser.find_element_by_name(selectbox_name)
        elif selectbox_id:
            self.find_element_by_id_with_timeout(selectbox_id)
            selectbox = self.browser.find_element_by_id(selectbox_id)

        options = selectbox.find_elements_by_tag_name("option")
        for option in options:
            if option.text == label:
                option.click()
                break

    def choose_selectbox_option_by_index(self,
                                         selectbox_name="",
                                         selectbox_id="",
                                         index=""):
        """Select the option at the given index in the select box.

        :param selectbox_name: the name of the corresponding
            select box in the form
        :type selectbox_name: string
        :param selectbox_id: the id of the corresponding select box in the form
        :type selectbox_id: string
        :param index: the option at this index will be selected
        :type index: int
        """
        if selectbox_name:
            self.find_element_by_name_with_timeout(selectbox_name)
            selectbox = self.browser.find_element_by_name(selectbox_name)
        elif selectbox_id:
            self.find_element_by_id_with_timeout(selectbox_id)
            selectbox = self.browser.find_element_by_id(selectbox_id)

        options = selectbox.find_elements_by_tag_name("option")
        options[int(index)].click()

    def choose_selectbox_option_by_value(self,
                                         selectbox_name="",
                                         selectbox_id="",
                                         value=""):
        """Select the option at the given value in the select box.

        :param selectbox_name: the name of the corresponding
            select box in the form
        :type selectbox_id: string
        :param selectbox_id: the id of the corresponding select box in the form
        :type selectbox_id: string
        :param value: the option at this value will be selected
        :type value: string
        """
        if selectbox_name:
            self.find_element_by_name_with_timeout(selectbox_name)
            selectbox = self.browser.find_element_by_name(selectbox_name)
        elif selectbox_id:
            self.find_element_by_id_with_timeout(selectbox_id)
            selectbox = self.browser.find_element_by_id(selectbox_id)

        options = selectbox.find_elements_by_tag_name("option")
        for option in options:
            if option.get_attribute('value') == value:
                option.click()
                break

    def fill_textbox(self, textbox_name="", textbox_id="", text=""):
        """Fill in the input textbox or textarea with the given text.

        :param textbox_name: the name of the corresponding textbox
            or text area in the form
        :type textbox_name: string
        :param textbox_id: the id of the corresponding textbox
            or text area in the form
        :type textbox_id: string
        :param text: the information that the user wants to send
        :type text: string
        """
        if textbox_name:
            self.find_element_by_name_with_timeout(textbox_name)
            textbox = self.browser.find_element_by_name(textbox_name)
        elif textbox_id:
            self.find_element_by_id_with_timeout(textbox_id)
            textbox = self.browser.find_element_by_id(textbox_id)

        textbox.send_keys(text)

    def handle_popup_dialog(self):
        """Access the alert after triggering an action that opens a popup."""
        try:
            alert = self.browser.switch_to_alert()
            alert.accept()
        except:
            pass


class InvenioWebTestCaseException(Exception):

    """Exception for the web tests.

    This exception is thrown if the element we are looking for is not found
    after a set time period. The element is not found because the page needs
    more time to be fully loaded. To avoid this exception, we should increment
    the time period for that element in the corresponding function. See also:

    find_element_by_name_with_timeout()
    find_element_by_link_text_with_timeout()
    find_element_by_partial_link_text_with_timeout()
    find_element_by_id_with_timeout()
    find_element_by_xpath_with_timeout()
    find_elements_by_class_name_with_timeout()
    find_page_source_with_timeout()
    """

    def __init__(self, element):
        """Initialisation."""
        self.element = element
        self.message = "Time for finding the element '{0}' has expired".format(
            self.element)

    def __str__(self):
        """String representation."""
        return repr(self.message)


#@nottest
def build_and_run_flask_test_suite():
    """Build and run the flask tests.

    Detect all Invenio modules with names ending by
    '*_flask_tests.py', build a complete test suite of them, and
    run it.  Called by 'inveniocfg --run-flask-tests'.
    """
    test_modules = []
    import invenio
    for candidate in os.listdir(os.path.dirname(invenio.__file__)):
        base, ext = os.path.splitext(candidate)

        if ext != '.py' or not base.endswith('_flask_tests'):
            continue

        module = __import__(
            'invenio.' + base, globals(), locals(), ['TEST_SUITE'])
        test_modules.append(module.TEST_SUITE)

    # FIXME create warning about tested databases
    warn_user_about_tests()

    complete_suite = unittest.TestSuite(test_modules)
    run_test_suite(complete_suite)


def iter_suites(packages=None):
    """Yield all testsuites."""
    from werkzeug.utils import import_string, find_modules
    from flask_registry import ModuleAutoDiscoveryRegistry, \
        ImportPathRegistry

    app = create_app()

    if packages is None:
        testsuite = ModuleAutoDiscoveryRegistry('testsuite', app=app)
        from invenio import testsuite as testsuite_invenio
        from invenio.base import testsuite as testsuite_base
        from invenio.celery import testsuite as testsuite_celery
        testsuite.register(testsuite_invenio)
        testsuite.register(testsuite_base)
        testsuite.register(testsuite_celery)
    else:
        exclude = map(lambda x: x + '.testsuite',
                      app.config.get('PACKAGES_EXCLUDE', []))
        testsuite = ImportPathRegistry(initial=packages, exclude=exclude,
                                       load_modules=True)

    for package in testsuite:
        for name in find_modules(package.__name__):
            module = import_string(name)
            if not module.__name__.split('.')[-1].startswith('test_'):
                continue
            if hasattr(module, 'TEST_SUITE'):
                yield module.TEST_SUITE
            else:
                app.logger.warning(
                    "%s: No test suite defined." % module.__name__)


def suite():
    """Create the testsuite that has all the tests."""
    suite = unittest.TestSuite()
    for other_suite in iter_suites():
        suite.addTest(other_suite)
    return suite


def main():
    """Run the testsuite as command line application."""
    try:
        unittest.main(defaultTest='suite')
    except Exception as e:
        print(('Error: %s' % e))
