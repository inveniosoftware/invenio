# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""BibAuthorId regressions tests."""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase, \
    run_test_suite, make_test_suite, test_web_page_content

from invenio.config import CFG_SITE_URL, \
    CFG_INSPIRE_SITE, CFG_BIBAUTHORID_ENABLED

from invenio.dbquery import run_sql

import random
import string


class BibAuthorIdDisplayedPages(InvenioTestCase):

    """This regression test checks whether suitable pages are displayed
        based on the variables CFG_INSPIRE_SITE and CFG_BIBAUTHORID_ENABLED"""

    def setUp(self):
        """ Initialization before tests"""
        # This random, arbitrarily large string is obviously invalid.
        self.any_name = ''.join(random.choice(string.lowercase) for x in range(26))
        self.canonical_name = self._get_canonical_name()

    def test_content_of_manage_profile(self):
        """This test checks whether the 'manage profile' page
           is neutral of implementation (e.g. Inspire features) and
           there are no authorisation issues."""

        if CFG_INSPIRE_SITE or CFG_BIBAUTHORID_ENABLED:

            # Ensures the authorization issue for manage_profile
            # will not return.
            url = '%s/author/manage_profile/%s' % (CFG_SITE_URL,
                                                   self.canonical_name)
            text_not_there = 'This page is not accessible directly.'
            response = test_web_page_content(url, 'guest',
                                             unexpected_text=text_not_there)
            self.assertEqual(list(), response)

            # Ensures that the js (INSPIRE specific) login prompt box appears
            # Only for Inspire
            if self.canonical_name:
                url = '%s/author/claim/%s' % (CFG_SITE_URL,
                                              self.canonical_name)
                guest_prompt_value = 'false'
                if CFG_INSPIRE_SITE:
                    guest_prompt_value = 'true'

                text_to_check = 'guestPrompt: %s' % guest_prompt_value
                response = test_web_page_content(url, 'guest',
                                                 expected_text=text_to_check)
                self.assertEqual(list(), response)

    def test_content_of_profile_pages(self):
        """This test checks whether the profiles are displayed
            containing appropriate error messages and content
            and redirect to other appropriate."""

        # If we're on Inspire, BibAuthorId is always enabled.
        if CFG_INSPIRE_SITE or CFG_BIBAUTHORID_ENABLED:

            # A valid canonical name should lead to the author's profile page.
            if self.canonical_name:
                url = '%s/author/profile/%s' % (CFG_SITE_URL,
                                                self.canonical_name)
                text_to_check = 'Personal Details'
                response = test_web_page_content(url, 'guest',
                                                 expected_text=text_to_check)
                self.assertEqual(list(), response)

            # An invalid query for some profile, should lead to 'Person search'.
            url = '%s/author/profile/%s' % (CFG_SITE_URL, self.any_name)
            text_to_check = ['Person search',
                             'We do not have a publication list for \'%s\'.'
                             % self.any_name]
            response = test_web_page_content(url, 'guest',
                                             expected_text=text_to_check)
            self.assertEqual(list(), response)

            # author/%s searches are kept for backward compatibility.
            # Should theses pages become obsolete,
            # the regression test will not fail.
            if self._test_web_page_existence_no_robots('%s/author/%s'
                                                       % (CFG_SITE_URL,
                                                          self.canonical_name)):
                if self.canonical_name:
                    url = '%s/author/%s' % (CFG_SITE_URL,
                                            self.canonical_name)
                    text_to_check = 'Personal Details'
                    response = test_web_page_content(url, 'guest',
                                                     expected_text=text_to_check)
                    self.assertEqual(list(), response)

                url = '%s/author/%s' % (CFG_SITE_URL, self.any_name)
                text_to_check = ['Person search',
                                 'We do not have a publication list for \'%s\''
                                 % self.any_name]
                response = test_web_page_content(url, 'guest',
                                                 expected_text=text_to_check)
                self.assertEqual(list(), response)

        # Bibauthorid is disabled.
        else:
            # The navigation bar shouldn't be there.
            text_not_there = ['View Profile', 'Manage Profile']

            url = '%s/author/profile/Ellis,%%20J' % CFG_SITE_URL
            text_to_check = ['Ellis, J', 'Personal Details']
            response = test_web_page_content(url, 'guest',
                                             expected_text=text_to_check,
                                             unexpected_text=text_not_there)
            self.assertEqual(list(), response)

            # An invalid query for a profile, should lead to 'Person search'.
            url = '%s/author/profile/%s' % (CFG_SITE_URL, self.any_name)
            text_to_check = 'This doesn\'t look like a person ID!'
            response = test_web_page_content(url, 'guest',
                                             expected_text=text_to_check,
                                             unexpected_text=text_not_there)
            self.assertEqual(list(), response)

            if self._test_web_page_existence_no_robots('%s/author/Ellis, J'
                                                       % CFG_SITE_URL):
                url = '%s/author/Ellis,%%20J' % CFG_SITE_URL
                text_to_check = ['Ellis, J', 'Personal Details']
                response = test_web_page_content(url, 'guest',
                                                 expected_text=text_to_check,
                                                 unexpected_text=text_not_there)
                self.assertEqual(list(), response)

                url = '%s/author/%s' % (CFG_SITE_URL, self.any_name)
                text_to_check = 'This doesn\'t look like a person ID!'
                response = test_web_page_content(url, 'guest',
                                                 expected_text=text_to_check,
                                                 unexpected_text=text_not_there)
                self.assertEqual(list(), response)

    def _test_web_page_existence_no_robots(self, url):
        """Almost identical to testutils.test_web_page_existence(url) except
            that we need to ignore robots.txt in some cases
            (e.g. Invenio production) for this regression test."""
        import mechanize
        browser = mechanize.Browser()
        try:
            browser.set_handle_robots(False)  # ignore robots.txt.
            browser.open(url)
        except:
            raise
        return True

    def _get_canonical_name(self):
        """ Fetches a valid canonical name from the database.
            Returns None if it is empty."""

        result = run_sql("select data from aidPERSONIDDATA where tag ="
                         + "'canonical_name' LIMIT 1")
        if result:
            return result[0][0]


TEST_SUITE = make_test_suite(BibAuthorIdDisplayedPages)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=False)
