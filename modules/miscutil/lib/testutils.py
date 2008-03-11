## $Id$
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

# pylint: disable-msg=E1102

"""
Helper functions for building and running test suites.
"""

__revision__ = "$Id$"

# if verbose level is set to 9, many debugging messages will be
# printed on stdout, so you may want to run:
#   $ regressiontestsuite > /tmp/z.log
# or even:
#   $ regressiontestsuite > /tmp/z.log 2> /tmp/z.err

CFG_TESTUTILS_VERBOSE = 1

import string
import sys
import time
import unittest

from urllib import urlencode
from itertools import chain, repeat

from invenio.config import weburl, sweburl, CFG_LOGDIR
from invenio.w3c_validator import w3c_validate, w3c_errors_to_str, CFG_TESTS_REQUIRE_HTML_VALIDATION

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

def test_web_page_content(url,
                          username="guest",
                          password="",
                          expected_text="</html>",
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

    if '--w3c-validate' in sys.argv:
        require_validate_p = True
        sys.stderr.write('Required validation\n')

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
        # first normalize expected_text
        if isinstance(expected_text, str):
            expected_texts = [expected_text]
        else:
            expected_texts = expected_text
        # then test
        for cur_expected_text in expected_texts:
            try:
                string.index(url_body, cur_expected_text)
            except ValueError:
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Page %s (login %s) does not contain %s.' % \
                      (url, username, cur_expected_text)

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

    # logout after tests:
    browser.open(sweburl + "/youraccount/logout")

    if CFG_TESTUTILS_VERBOSE >= 9:
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
