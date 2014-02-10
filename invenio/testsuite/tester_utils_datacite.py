# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

"""
Unit tests for DataCite API wrapper

CFG_DATACITE_USERNAME and CFG_DATACITE_PASSWORD has to be set to be able to run
the tests.
"""

import string
import os

from invenio.base.factory import with_app_context
from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

dataciteutils = lazy_import('invenio.utils.datacite')


class DataCiteTestCase(InvenioTestCase):

    def setUp(self):
        # Force API in test mode
        self.d = dataciteutils.DataCite(test_mode=True)

    def tearDown(self):
        self.d = None

    def _random_doi(self):
        rand_string = ''.join(random.choice(string.lowercase + string.digits) for i in xrange(8)).upper()
        rand_string = "%s-%s" % (rand_string[0:4], rand_string[4:8])
        return "10.5072/INVENIO.TEST.%s" % rand_string

    def test_api(self):
        doi = self._random_doi()

        doc = '''<resource xmlns="http://datacite.org/schema/kernel-2.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://datacite.org/schema/kernel-2.2 http://schema.datacite.org/meta/kernel-2.2/metadata.xsd">
        <identifier identifierType="DOI">%s</identifier>
        <creators>
            <creator>
                <creatorName>Simko, T</creatorName>
            </creator>
        </creators>
        <titles>
            <title>Invenio Software at Ærø</title>
        </titles>
        <publisher>CERN</publisher>
        <publicationYear>2002</publicationYear>
        </resource>
        ''' % doi

        d = dataciteutils.DataCite(prefix="10.5072", test_mode=False)

        # Set metadata for DOI
        d.metadata_post(doc)

        # Mint new DOI
        url = "http://openaire.cern.ch/doi/%s" % doi
        d.doi_post(doi, url)

        # Get DOI location
        location = d.doi_get(doi)
        self.assertEqual(location, url)

        # Get metadata for DOI
        resdoc = d.metadata_get(doi)
        # Newlines are different in submitted and response, so process values
        # before comparing.
        submitted = filter(lambda x: x, [x.strip() for x in doc.splitlines()])
        received = filter(lambda x: x, [x.strip() for x in resdoc.splitlines()])
        self.assertEqual(submitted, received)

        # Set Media
        pdfurl = "http://openaire.cern.ch/pdf/doi/%s" % doi
        d.media_post(doi, {"application/pdf": pdfurl})

        # Get Media
        m = d.media_get(doi)
        self.assertTrue('application/pdf' in m)
        self.assertEqual(m['application/pdf'], pdfurl)

        # Make DOI inactive
        d.metadata_delete(doi)
        self.assertRaises(dataciteutils.DataCiteGoneError, d.metadata_get, doi)

    def test_unauthenticated(self):
        d = dataciteutils.DataCite(username="unknownuser", password="unknownpassword")
        self.assertRaises(dataciteutils.DataCiteUnauthorizedError, d.doi_get, "10.5072/INVENIO.TEST.22KX-LRQR")

    def test_not_found(self):
        self.assertRaises(dataciteutils.DataCiteNotFoundError, self.d.metadata_get, "10.5072/INVENIO.TEST.UNKNOWN-DOI")
        self.assertRaises(dataciteutils.DataCiteNotFoundError, self.d.metadata_delete, "10.5072/INVENIO.TEST.UNKNOWN-DOI")

    def test_forbidden(self):
        self.assertRaises(dataciteutils.DataCiteForbiddenError, self.d.metadata_get, "10.1594/WDCC/CCSRNIES_SRES_B2")
        self.assertRaises(dataciteutils.DataCiteForbiddenError, self.d.metadata_delete, "10.1594/WDCC/CCSRNIES_SRES_B2")
        self.assertRaises(dataciteutils.DataCiteForbiddenError, self.d.media_get, "10.1594/WDCC/CCSRNIES_SRES_B2")

    def test_badrequest(self):
        self.assertRaises(dataciteutils.DataCiteBadRequestError, self.d.metadata_post, "not an xml document")

    def test_precondition(self):
        self.assertRaises(dataciteutils.DataCitePreconditionError, self.d.doi_post, "10.5072/INVENIO.TEST.UNKNOWN-DOI", "http://invenio-software.org")


TEST_SUITE = make_test_suite(DataCiteTestCase)


@with_app_context()
def main():
    from invenio import config
    if not(hasattr(config, 'CFG_DATACITE_USERNAME') and hasattr(config, 'CFG_DATACITE_PASSWORD')):
        config.CFG_DATACITE_USERNAME = os.environ.get('CFG_DATACITE_USERNAME', '') or raw_input("DataCite username:")
        config.CFG_DATACITE_PASSWORD = os.environ.get('CFG_DATACITE_PASSWORD', '') or raw_input("DataCite password:")
    run_test_suite(TEST_SUITE)

if __name__ == "__main__":
    main()
