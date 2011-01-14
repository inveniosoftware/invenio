# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""OAI Repository Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import time

from invenio.config import CFG_SITE_URL, CFG_OAI_SLEEP
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages

class OAIRepositoryWebPagesAvailabilityTest(unittest.TestCase):
    """Check OAI Repository web pages whether they are up or not."""

    def test_your_baskets_pages_availability(self):
        """oairepository - availability of OAI server pages"""

        baseurl = CFG_SITE_URL + '/oai2d'

        _exports = [#fast commands first:
                    '?verb=Identify',
                    '?verb=ListMetadataFormats',
                    # sleepy commands now:
                    '?verb=ListSets',
                    '?verb=ListRecords',
                    '?verb=GetRecord']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            if url.endswith('Identify') or \
               url.endswith('ListMetadataFormats'):
                pass
            else:
                # some sleep required for verbs other than Identify
                # and ListMetadataFormats, since oai2d refuses too
                # frequent access:
                time.sleep(CFG_OAI_SLEEP)
            error_messages.extend(test_web_page_content(url,
                                                        expected_text=
                                                        '</OAI-PMH>'))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

TEST_SUITE = make_test_suite(OAIRepositoryWebPagesAvailabilityTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
