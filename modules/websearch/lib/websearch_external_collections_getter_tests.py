# -*- coding: utf-8 -*-
##
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

"""Testing functions for the page getter module.
"""

__revision__ = "$Id$"

import unittest

from invenio.websearch_external_collections_getter import HTTPAsyncPageGetter, async_download

class AsyncDownloadTest(unittest.TestCase):
    """Test suite for websearch_external_collections_*"""

    def test_async_download(self):
        """websearch_external_collections_getter - asynchronous download"""

        ## Test varius cases for the async_download function:
        ##   - test 2 workings pages : google, kernel.org
        ##   - test 1 unresolvable name : rjfreijoiregjreoijgoirg.fr
        ##   - test 1 bad ip : 1.2.3.4
        ## Return the list of errors.

        checks = [  {'url': 'http://public.web.cern.ch/public/', 'content': "<title>CERN - The world's largest particle physics laboratory</title>"}, 
                    {'url': 'http://cdsware.cern.ch/invenio/index.html', 'content': '<title>CDS Invenio: Overview</title>'},
                    {'url': 'http://rjfreijoiregjreoijgoirg.fr'},
                    {'url': 'http://1.2.3.4/'} ] 

        def finished(pagegetter, check, current_time):
            """Function called when a page is received."""
            is_ok = pagegetter.status is not None

            if check.has_key('content') and is_ok:
                is_ok = pagegetter.data.find(check['content']) > 0

            check['result'] = is_ok == check.has_key('content')

        pagegetters = [HTTPAsyncPageGetter(check['url']) for check in checks]
        finished_list = async_download(pagegetters, finished, checks, 20)

        for (finished, check) in zip(finished_list, checks):
            if not finished:
                check['result'] = not check.has_key('content')

        errors = [check for check in checks if not check['result']]

        self.assertEqual(errors, [])

def create_test_suite():
    """Return test suite for the external collection tests."""
    return unittest.TestSuite((unittest.makeSuite(AsyncDownloadTest, 'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())

