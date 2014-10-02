# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""Unit tests for OrcidXmlExporter"""

__revision__ = "$Id$"

from invenio.testutils import InvenioTestCase, make_test_suite, run_test_suite
from invenio.orcid_xml_exporter import OrcidXmlExporter

from lxml import etree
import urllib2

# The URL to ORCID .xsd schema
XSD_URL = "https://raw.githubusercontent.com/ORCID/ORCID-Source/master" + \
          "/orcid-model/src/main/resources/orcid-message-1.1.xsd"

def is_valid_orcid_xml(xmlstring, schema):

    """Validates xmlstring using ORCID xsd schema.

    For the format definition and tutorials see:
    http://support.orcid.org/knowledgebase/articles/135422-xml-for-orcid-works

    :param xmlstring: xml in ORCID readable format.
    :type xmlstring: str
    :returns: bool -- indicates whether the validation passed or not
    """

    xmlparser = etree.XMLParser(schema=schema, encoding='utf-8')
    try:
        etree.fromstring(xmlstring.encode('utf-8'), xmlparser)
        return True
    except etree.XMLSyntaxError, exception_message:
        print exception_message
        return False

class TestWorkExporter(InvenioTestCase):

    """ A class with validation of ORCID work XMLs.

    It checks whether the XMLs produced by OrcidXmlExporter and works.xml
    are compatible with ORCID's XSD schema.
    """

    def setUp(self):
        self.exporter = OrcidXmlExporter()

        xsd_schema = urllib2.urlopen(XSD_URL)
        schema_root = etree.XML(xsd_schema.read())
        self.schema = etree.XMLSchema(schema_root)

    def _export_and_validate(self, worklist):

        '''Validates the XML made from records given in worklist dictionary.'''

        xmlstring = self.exporter.export(worklist, "works.xml")
        return is_valid_orcid_xml(xmlstring, self.schema)

    def test_empty_export(self):

        '''Tests XML with no works attached.'''

        assert self._export_and_validate([]) == True

    def test_orcid_example_export(self):

        '''Tests XML from the example from ORCID site.'''

        assert self._export_and_validate([{
            "work_title" : {
                "title" : "API Test Title",
                "subtitle" : "My Subtitle",
                "translated_titles" : [("fr", "API essai Titre")]
            },
            "journal_title" : "Journal Title",
            "short_description" : "My Abstract",
            "work_citation" : ("formatted-apa",
                               "My correctly formatted citation"),
            "work_type" : "journal-article",
            "publication_date" : {
                "year" : 2010,
                "month" : 11
            },
            "work_external_identifiers" : [("other-id", "1234")],
            "url" : "www.orcid.org",
            "contributors" : [{
                "name" : "LastName, FirstName",
                "attributes" : {
                    "role" : "author",
                    "sequence" : "first"
                }
            }],
            "language_code" : "en",
            "country" : ("US", "public")
        }]) == True

    def test_work_visibility(self):

        '''Tests XML with the visibility field in the record.'''

        assert self._export_and_validate([{
            "work_title" : {
                "title" : "Public work"
            },
            "short_description" : "Short description of public work",
            "work_type" : "test",
            "visibility" : "public"
        }]) == True

    def test_work_put_code(self):

        '''Tests XML with put code field in the record.'''

        assert self._export_and_validate([{
            "work_title" : {
                "title" : "A work"
            },
            "short_description" : "Very short description",
            "work_type" : "test",
            "put_code" : 1
        }]) == True

    def test_no_title(self):

        '''Tests XML with a record with no main title provided.

        If no title is provided, the xml will not be accepted by ORCID.
        '''

        assert self._export_and_validate([{
            "work_title" : {
                "subtitle" : "A work",
                "translated_titles" : [("fr", "Omlette du fromage")]
            },
            "short_description" : "Very short description",
            "work_type" : "test"
        }]) == False

    def test_many_works(self):

        '''Tests XML with multiple works.'''

        work_dict = {
            "work_title" : {
                "title" : "A work",
            },
            "short_description" : "Very short description",
            "work_type" : "test"
        }
        assert self._export_and_validate([work_dict, work_dict, work_dict]) == \
                True

    def test_incomplete_date(self):

        '''Test XML with wrong date in the record.

        The 'day' field in publication_date dictionary requires 'month' and
        'year' fields. Also, the 'month' field requires the 'year' field.
        '''

        assert self._export_and_validate([{
            "work_title" : {
                "title" : "A work"
            },
            "short_description" : "Very short description",
            "work_type" : "test",
            "publication_date" : {
                "month" : 10,
                "day" : 12
            }
        }]) == False

    def test_many_contributors(self):

        '''Test XML with many contributors in a single record.'''

        contributor = {
            "orcid" : "ContributorOrcid",
            "name" : "Contributor Contributowski",
            "email" : "contrib@ut.or",
            "attributes" : {
                "role" : "author",
                "sequence" : "first"
            }
        }
        assert self._export_and_validate([{
            "work_title" : {
                "title" : "A work"
            },
            "short_description" : "Very short description",
            "work_type" : "test",
            "contributors" : [contributor, contributor, contributor]
        }]) == True

    def test_wrong_year(self):

        '''Test XML with a record with wrong year set.

        Year should be a four digit number.
        '''
        assert self._export_and_validate([{
            "work_title" : {
                "title" : "A work"
            },
            "short_description" : "Very short description",
            "work_type" : "test",
            "publication_date" : {
                "year" : 10000
            }
        }]) == False

    def test_wrong_month(self):

        '''Test XML with a record with wrong monthset.

        Month should be a two digit number. In this particular case we should
        provide '08' as month.
        '''

        assert self._export_and_validate([{
            "work_title" : {
                "title" : "A work"
            },
            "short_description" : "Very short description",
            "work_type" : "test",
            "publication_date" : {
                "year" : 2014,
                "month" : 8
            }
        }]) == False

TEST_SUITE = make_test_suite(TestWorkExporter)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
