# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013, 2014 CERN.
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

"""Testing functions for the page getter module.
"""

import sys

from StringIO import StringIO

from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
HTTPAsyncPageGetter = lazy_import('invenio.legacy.websearch_external_collections.getter:HTTPAsyncPageGetter')
async_download = lazy_import('invenio.legacy.websearch_external_collections.getter:async_download')


class AsyncDownloadTest(InvenioTestCase):
    """Test suite for websearch_external_collections_*"""

    def setUp(self):
        # We redirect stderr because the test for an invalid logs
        # a warning on stderr and xunit does not like it.
        # This only happens with python2.6.
        self.old_stderr = sys.stderr
        sys.stderr = StringIO()

    def tearDown(self):
        sys.stderr = self.old_stderr

    def test_async_download(self):
        """websearch_external_collections_getter - asynchronous download"""

        ## Test various cases for the async_download function:
        ##   - test 1 working page: invenio-software.org
        ##   - test 1 unresolvable name: rjfreijoiregjreoijgoirg.fr
        ##   - test 1 bad IP: 1.2.3.4
        ## Return the list of errors.
        checks = [
            {'url': 'http://invenio-software.org', 'content': 'About Invenio'},
            {'url': 'http://rjfreijoiregjreoijgoirg.fr'},
            {'url': 'http://1.2.3.4/'}]

        def cb_finished(pagegetter, check, current_time):
            """Function called when a page is received."""
            is_ok = pagegetter.status is not None

            if 'content' in check and is_ok:
                is_ok = pagegetter.data.find(check['content']) > 0

            check['result'] = is_ok == ('content' in check)

        pagegetters = [HTTPAsyncPageGetter(check['url']) for check in checks]
        finished_list = async_download(pagegetters, cb_finished, checks, 20)

        for (finished, check) in zip(finished_list, checks):
            if not finished:
                check['result'] = 'content' not in check

        errors = [check for check in checks if not check['result']]

        self.assertEqual(errors, [])

TEST_SUITE = make_test_suite(AsyncDownloadTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
