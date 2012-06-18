# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""Unit tests for datacite library."""

__revision__ = "$Id$"

import unittest
import dataciteutils

from invenio.config import CFG_SITE_LANGS
from invenio.testutils import make_test_suite, run_test_suite

# TODO examples

class CreateNameTest(unittest.TestCase):
    """
    Creating a new name...
    """

    def test_new_name(self):
        """datacite - creation of a new DOI name"""
        generate_doi('Test', 'Test', False)
        self.assertEqual('','')

class GetURLTest(unittest.TestCase):
    """
    Retrieving URLs from DOI names...
    """

    def test_get_URL_correct(self):
        """datacite - """
        get_url_by_doi(doi, endpoint, username, password)
        self.assertEqual('','')

    def test_get_URL_wrong(self):
        """datacite - """
        get_url_by_doi(doi, endpoint, username, password)
        self.assertEqual('','')

class GetMetadataTest(unittest.TestCase):
    """
    Retrieving URLs from DOI names...
    """

    def test_get_metadata_correct(self):
        """datacite - """
        get_url_by_doi(doi, endpoint, username, password)
        self.assertEqual('','')

    def test_get_metadata_wrong(self):
        """datacite - """
        get_url_by_doi(doi, endpoint, username, password)
        self.assertEqual('','')

class CreateDOITest(unittest.TestCase):
    """
    Setting DOI names...
    """

    def test_post_doi_correct(self):
        """datacite - """
        post_doi(new_doi, location, endpoint, username, password, testing)
        self.assertEqual('','')

    def test_post_doi_wrong(self):
        """datacite - """
        post_doi(new_doi, location, endpoint, username, password, testing)
        self.assertEqual('','')

class CreateMetadataTest(unittest.TestCase):
    """
    Setting DOI metadata...
    """

    def test_post_metadata_correct(self):
        """datacite - """
        post_metadata(metadata, endpoint, username, password, testing)
        self.assertEqual('','')

    def test_post_metadata_wrong(self):
        """datacite - """
        post_metadata(metadata, endpoint, username, password, testing)
        self.assertEqual('','')

class DeleteMetadataTest(unittest.TestCase):
    """
    Deleting DOI metadata...
    """

    def test_del_metadata_correct(self):
        """datacite - """
        delete_metadata (doi, endpoint, username, password)
        self.assertEqual('','')

    def test_del_metadata_wrong(self):
        """datacite - """
        delete_metadata (doi, endpoint, username, password)
        self.assertEqual('','')



class ExceptionTest(unittest.TestCase):
    """
    Exception raising...
    """

    def test_curl_exception(self):
        """datacite - """
        self.assertEqual('','')

    def test_servererror_exception(self):
        """datacite - """
        self.assertEqual('','')

    def test_requesterror_exception(self):
        """datacite - """
        self.assertEqual('','')

TEST_SUITE = make_test_suite(CreateNameTest,
                             GetURLTest,
                             GetMetadataTest,
                             CreateDOITest,
                             CreateMetadataTest,
                             DeleteMetadataTest,
                             ExceptionTest,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
