# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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

"""Test cases for the BibSword module."""

__revision__ = "$Id$"

# pylint: disable-msg=C0301

import os
import sys
import time
import pkg_resources

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio.legacy.bibsword.client_formatter import format_marcxml_file, \
                                              format_submission_status, \
                                              ArXivFormat
from invenio.legacy.bibsword.client import format_metadata, \
                                    list_submitted_resources, \
                                    perform_submission_process

from invenio.legacy.bibsword.client_http import RemoteSwordServer
from invenio.legacy.bibsword.client_dblayer import get_remote_server_auth, \
                                            insert_into_swr_clientdata, \
                                            update_submission_status, \
                                            select_submitted_record_infos, \
                                            delete_from_swr_clientdata
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsword.config import CFG_SUBMISSION_STATUS_SUBMITTED, \
                                    CFG_SUBMISSION_STATUS_PUBLISHED, \
                                    CFG_SUBMISSION_STATUS_REMOVED
from xml.dom import minidom

TEST_DATA = pkg_resources.resource_filename('invenio.legacy.bibsword', 'data')


class Test_format_marcxml_file(InvenioTestCase):
    """ bibsword_format - test the parsing and extracting of marcxml nodes"""

    def test_extract_marcxml_1(self):
        """Test_format_marcxml_file - extract marcxml without id, report_nos and comment"""
        # Test with marcxml file 1
        marcxml = open("%s%sTest_marcxml_file_1.xml" % (TEST_DATA, os.sep)).read()
        metadata = format_marcxml_file(marcxml)
        self.assertEqual(metadata['id'], '')
        self.assertEqual(metadata['title'],  "Calorimetry triggering in ATLAS")
        self.assertEqual(metadata['contributors'][0]['name'], "Igonkina, O")
        self.assertEqual(metadata['contributors'][0]['affiliation'][0], "NIKHEF, Amsterdam")
        self.assertEqual(metadata['summary'], "The ATLAS experiment is preparing for data taking at 14 TeV collision energy. A rich discovery physics program is being prepared in addition to the detailed study of Standard Model processes which will be produced in abundance. The ATLAS multi-level trigger system is designed to accept one event in 2 105 to enable the selection of rare and unusual physics events. The ATLAS calorimeter system is a precise instrument, which includes liquid Argon electro-magnetic and hadronic components as well as a scintillator-tile hadronic calorimeter. All these components are used in the various levels of the trigger system. A wide physics coverage is ensured by inclusively selecting events with candidate electrons, photons, taus, jets or those with large missing transverse energy. The commissioning of the trigger system is being performed with cosmic ray events and by replaying simulated Monte Carlo events through the trigger and data acquisition system.")
        self.assertEqual(metadata['contributors'][1]['name'], "Achenbach, R")
        self.assertEqual(metadata['contributors'][1]['affiliation'][0], "Kirchhoff Inst. Phys.")
        self.assertEqual(metadata['contributors'][2]['name'], "Adragna, P")
        self.assertEqual(metadata['contributors'][2]['affiliation'][0], "Queen Mary, U. of London")
        nb_contributors = len(metadata['contributors'])
        self.assertEqual(nb_contributors, 205)
        self.assertEqual(metadata['contributors'][204]['name'], "Özcan, E")
        self.assertEqual(metadata['contributors'][204]['affiliation'][0], "University Coll. London")
        self.assertEqual(metadata['doi'], "10.1088/1742-6596/160/1/012061")
        self.assertEqual(metadata['journal_refs'][0], "J. Phys.: Conf. Ser.: 012061 (2009) pp. 160")
        self.assertEqual(len(metadata['journal_refs']), 1)
        self.assertEqual('report_nos' in metadata, True)
        self.assertEqual(metadata['comment'], '')


    def test_extract_marcxml_2(self):
        """Test_format_marcxml_file - extract marcxml without report_nos, doi"""

        #Test with marcxml file 2
        marcxml = open("%s%sTest_marcxml_file_2.xml" % (TEST_DATA, os.sep)).read()
        metadata = format_marcxml_file(marcxml)
        self.assertEqual(metadata['id'], "arXiv:1001.1674")
        self.assertEqual(metadata['title'],  "Persistent storage of non-event data in the CMS databases")
        self.assertEqual(metadata['contributors'][0]['name'], "De Gruttola, M")
        self.assertEqual(metadata['contributors'][0]['affiliation'][0], "CERN")
        self.assertEqual(metadata['contributors'][0]['affiliation'][1], "INFN, Naples")
        self.assertEqual(metadata['contributors'][0]['affiliation'][2], "Naples U.")
        self.assertEqual(metadata['summary'], "In the CMS experiment, the non event data needed to set up the detector, or being produced by it, and needed to calibrate the physical responses of the detector itself are stored in ORACLE databases. The large amount of data to be stored, the number of clients involved and the performance requirements make the database system an essential service for the experiment to run. This note describes the CMS condition database architecture, the data-flow and PopCon, the tool built in order to populate the offline databases. Finally, the first results obtained during the 2008 and 2009 cosmic data taking are presented.")
        self.assertEqual(metadata['contributors'][1]['name'], "Di Guida, S")
        self.assertEqual(metadata['contributors'][1]['affiliation'][0], "CERN")
        self.assertEqual(metadata['contributors'][2]['name'], "Futyan, D")
        self.assertEqual(metadata['contributors'][2]['affiliation'][0], "Imperial Coll., London")
        nb_contributors = len(metadata['contributors'])
        self.assertEqual(nb_contributors, 11)
        self.assertEqual(metadata['contributors'][10]['name'], "Xie, Z")
        self.assertEqual(metadata['contributors'][10]['affiliation'][0], "Princeton U.")
        self.assertEqual(metadata['doi'], '')
        self.assertEqual(metadata['journal_refs'][0], "JINST: P04003 (2010) pp. 5")
        self.assertEqual(len(metadata['journal_refs']), 1)
        self.assertEqual('report_nos' in metadata, True)
        self.assertEqual(metadata['comment'], "Comments: 20 pages, submitted to IOP")

    def test_extract_full_marcxml_3(self):
        """Test_format_marcxml_file - extract marcxml without doi"""

        #Test with marcxml file 3
        marcxml = open("%s%sTest_marcxml_file_3.xml" % (TEST_DATA, os.sep)).read()
        metadata = format_marcxml_file(marcxml)
        self.assertEqual(metadata['id'], "ATL-PHYS-CONF-2007-008")
        self.assertEqual(metadata['title'],  "Early Standard Model physics and early discovery strategy in ATLAS")
        self.assertEqual(metadata['contributors'][0]['name'], "Grosse-Knetter, J")
        self.assertEqual(metadata['contributors'][0]['affiliation'][0], "Bonn U.")
        self.assertEqual(metadata['summary'], "In 2008 the LHC will open a new energy domain for physics within the Standard Model and beyond. The physics channels which will be addressed by the ATLAS experiment in the initial period of operation will be discussed. These include Standard Model processes such as W/Z production and early top measurements. This will be followed by a description of the searches for a low-mass Higgs boson, new heavy di-lepton resonances, and Supersymmetry, for which a striking signal might be observed after only a few months of data taking.")
        self.assertEqual(len(metadata['contributors']), 1)
        self.assertEqual(metadata['doi'], '')
        self.assertEqual(metadata['journal_refs'][0], "Nucl. Phys. B, Proc. Suppl.: 55-59 (2008) pp. 177-178")
        self.assertEqual(len(metadata['journal_refs']), 1)
        self.assertEqual(len(metadata['report_nos']), 2)
        self.assertEqual(metadata['report_nos'][0], "ATL-COM-PHYS-2007-036")
        self.assertEqual(metadata['report_nos'][1], "CERN-ATL-COM-PHYS-2007-036")
        self.assertEqual(metadata['comment'], '')

    def test_extract_null_marcxml(self):
        """Test_format_marcxml_file - no metadata"""

        #Test without any marcxml file
        metadata = format_marcxml_file("")
        self.assertEqual(metadata["error"], "MARCXML string is empty !")

    def test_extract_wrong_file(self):
        """Test_format_marcxml_file - unexistant metadata file"""

        #Test with a unknown marcxml file
        metadata = format_marcxml_file("%s%sTest_marcxml_file_false.xml" % (TEST_DATA, os.sep), True)
        self.assertEqual(metadata["error"], "Unable to open marcxml file !")


class Test_format_metadata(InvenioTestCase):
    """ bibsword - test the collection of all metadata """

    def test_correct_metadata_collection(self):
        """Test_format_metadata - collection of metadata without errors"""

        marcxml = open("%s%sTest_marcxml_file_3.xml" % (TEST_DATA, os.sep)).read()

        metadata = {}
        metadata['primary_label'] = 'Test - Test Disruptive Networks'
        metadata['primary_url'] = 'http://arxiv.org/terms/arXiv/test.dis-nn'

        user_info = {}
        user_info['nickname'] = 'test_user'
        user_info['email'] = 'test@user.com'

        deposit_results = []
        deposit_results.append(open("%s%sTest_media_deposit.xml" % (TEST_DATA, os.sep)).read())
        metadata = format_metadata(marcxml, deposit_results, user_info, metadata)

        self.assertEqual(metadata['id'], "ATL-PHYS-CONF-2007-008")
        self.assertEqual(metadata['title'],  "Early Standard Model physics and early discovery strategy in ATLAS")
        self.assertEqual(metadata['contributors'][0]['name'], "Grosse-Knetter, J")
        self.assertEqual(metadata['contributors'][0]['affiliation'][0], "Bonn U.")
        self.assertEqual(metadata['summary'], "In 2008 the LHC will open a new energy domain for physics within the Standard Model and beyond. The physics channels which will be addressed by the ATLAS experiment in the initial period of operation will be discussed. These include Standard Model processes such as W/Z production and early top measurements. This will be followed by a description of the searches for a low-mass Higgs boson, new heavy di-lepton resonances, and Supersymmetry, for which a striking signal might be observed after only a few months of data taking.")
        nb_contributors = len(metadata['contributors'])
        self.assertEqual(nb_contributors, 1)
        self.assertEqual(metadata['doi'], "")
        self.assertEqual(len(metadata['journal_refs']), 1)
        self.assertEqual(metadata['journal_refs'][0], "Nucl. Phys. B, Proc. Suppl.: 55-59 (2008) pp. 177-178")
        self.assertEqual(len(metadata['report_nos']), 2)
        self.assertEqual(metadata['report_nos'][0], "ATL-COM-PHYS-2007-036")
        self.assertEqual(metadata['report_nos'][1], "CERN-ATL-COM-PHYS-2007-036")
        self.assertEqual(metadata['comment'], "")

        self.assertEqual(metadata['primary_label'], "Test - Test Disruptive Networks")
        self.assertEqual(metadata['primary_url'], "http://arxiv.org/terms/arXiv/test.dis-nn")

        self.assertEqual(metadata['author_name'], "test_user")
        self.assertEqual(metadata['author_email'], "test@user.com")

        self.assertEqual(metadata['links']['link'], "https://arxiv.org/sword-app/edit/10070072")
        self.assertEqual(metadata['links']['type'], "application/pdf")


    def test_metadata_collection_no_data(self):
        """Test_format_metadata - collection of metadata without any changes"""

        # Gives an empty marcxml file
        marcxml = ""
        # Gives no metadata
        metadata = {}
        # Gives no user informations
        user_info = {}
        # Gives no result where to find a link
        deposit_results = []

        metadata = format_metadata(marcxml, deposit_results, user_info, metadata)
        self.assertEquals(len(metadata['error']), 9)
        self.assertEquals(metadata['error'][0], "No submitter name given !")
        self.assertEquals(metadata['error'][1], "No submitter email given !")
        self.assertEquals(metadata['error'][2], "No primary category label given !")
        self.assertEquals(metadata['error'][3], "No primary category url given !")
        self.assertEquals(metadata['error'][4], "No links to the media deposit found !")
        self.assertEquals(metadata['error'][5], "No document id given !")
        self.assertEquals(metadata['error'][6], "No title given !")
        self.assertEquals(metadata['error'][7], "No author given !")
        self.assertEquals(metadata['error'][8], "No summary given !")


        self.assertEquals(metadata['id'], "")
        self.assertEquals(metadata['title'], "")
        self.assertEqual(len(metadata['contributors']), 0)
        self.assertEqual(metadata['summary'], "")
        self.assertEqual(metadata['doi'], "")
        self.assertEqual(len(metadata['journal_refs']), 0)
        self.assertEqual(len(metadata['report_nos']), 0)
        self.assertEqual(metadata['comment'], "")
        self.assertEqual(metadata['primary_label'], "")
        self.assertEqual(metadata['primary_url'], "")
        self.assertEqual(metadata['author_name'], "")
        self.assertEqual(metadata['author_email'], "")
        self.assertEqual(len(metadata['links']), 0)


class Test_get_submission_status(InvenioTestCase):
    """ bibsword_httpquery - test the get_submission_status method """

    def test_get_submission_status_ok(self):
        """Test_get_submission_status - connect to an existing url"""

        authentication_info = get_remote_server_auth(4)
        connection = RemoteSwordServer(authentication_info)
        result = connection.get_submission_status("http://arxiv.org/resolve/app/10070073")

        self.assertEqual(result != "", True)


    def test_get_submission_status_no_url(self):
        """Test_get_submission_status - connect to an existing url"""

        authentication_info = get_remote_server_auth(4)
        connection = RemoteSwordServer(authentication_info)
        result = connection.get_submission_status("")

        self.assertEqual(result != "", False)

    def test_get_submission_status_wrong_url(self):
        """Test_get_submission_status - connect to an existing url"""

        authentication_info = get_remote_server_auth(4)
        connection = RemoteSwordServer(authentication_info)
        result = connection.get_submission_status("http://arxiv.org/reso")

        self.assertEqual(result != "", False)


class Test_format_submission_status(InvenioTestCase):
    """bibsword_format - test the parsing of format_submission_status method"""

    def test_format_submission_status_submitted(self):
        """Test_format_submission_status_submitted"""

        status_xml = open("%s%sTest_submission_status_submitted.xml" % (TEST_DATA, os.sep)).read()
        response =  format_submission_status(status_xml)

        self.assertEqual(response['status'], "submitted")
        self.assertEqual(response['id_submission'], "")
        self.assertEqual(response['error'], "")


    def test_format_submission_status_published(self):
        """Test_format_submission_status_published"""

        status_xml = open("%s%sTest_submission_status_published.xml" % (TEST_DATA, os.sep)).read()
        response =  format_submission_status(status_xml)

        self.assertEqual(response['status'], "published")
        self.assertEqual(response['id_submission'], "1003.9876")
        self.assertEqual(response['error'], "")


    def test_format_submission_status_onhold(self):
        """Test_format_submission_status_onhold"""

        status_xml = open("%s%sTest_submission_status_onhold.xml" % (TEST_DATA, os.sep)).read()
        response = format_submission_status(status_xml)

        self.assertEqual(response['status'], "onhold")
        self.assertEqual(response['id_submission'], "")
        self.assertEqual(response['error'], "")


    def test_format_submission_status_removed(self):
        """Test_format_submission_status_removed"""

        status_xml = open("%s%sTest_submission_status_unknown.xml" % (TEST_DATA, os.sep)).read()
        response =  format_submission_status(status_xml)

        self.assertEqual(response['status'], CFG_SUBMISSION_STATUS_REMOVED)
        self.assertEqual(response['id_submission'], "")
        self.assertEqual(response['error'], "identifier does not correspond to a SWORD wrapper, it may belong to a media deposit")


class Test_swrCLIENTDATA_table(InvenioTestCase):
    '''
      This test check that the entire update process works fine. It insert some
      data into the swrCLIENTDATA table, then he get some xml status entry from
      ArXiv and Finally, it update those that have changed their status
    '''

    id_tests = []

    def test_insert_submission(self):
        '''Test_insert_submission - check insert submission rows in swrCLIENTDATA'''

        self.id_tests.append(insert_into_swr_clientdata(1, 97, 'TESLA-FEL-99-07', 10030148,
                               '6', 'test_username', 'juliet.capulet@cds.cern.ch',
                               'test_media_deposit', 'test_media_submit',
                               'https://arxiv.org/sword-app/edit/10030148',
                               'https://arxiv.org/sword-app/edit/10030148.atom',
                               'http://arxiv.org/resolve/app/10030148'))

        self.id_tests.append(insert_into_swr_clientdata(1, 92, 'hep-th/0606096', 10070221,
                               '5', 'test_username', 'romeo.montague@cds.cern.ch',
                               'test_media_deposit', 'test_media_submit',
                               'https://arxiv.org/sword-app/edit/10070221',
                               'https://arxiv.org/sword-app/edit/10070221.atom',
                               'http://arxiv.org/resolve/app/10070221'))

        self.id_tests.append(insert_into_swr_clientdata(1, 92, 'hep-th/0606096', 12340097,
                               '5', 'test_username', 'romeo.montague@cds.cern.ch',
                               'test_media_deposit', 'test_media_submit',
                               'https://arxiv.org/sword-app/edit/12340097',
                               'https://arxiv.org/sword-app/edit/12340097.atom',
                               'http://arxiv.org/resolve/app/12340097'))

        rows = run_sql('''SELECT id, id_swrREMOTESERVER, id_record, report_no,
                       id_remote, id_user, user_name, user_email, xml_media_deposit,
                       xml_metadata_submit, submission_date, publication_date, removal_date,
                       link_medias, link_metadata, link_status, status, last_update
                       FROM swrCLIENTDATA''')

        for row in rows:
            self.assertEqual(row[0] in self.id_tests, True)
            if row[0] == self.id_tests[0]:
                self.assertEqual(row[1], 1)
                self.assertEqual(row[2], 97)
                self.assertEqual(row[4], '10030148')
                self.assertEqual(row[8], 'test_media_deposit')
                self.assertEqual(row[13], "https://arxiv.org/sword-app/edit/10030148")
                self.assertEqual(row[14], 'https://arxiv.org/sword-app/edit/10030148.atom')
                self.assertEqual(row[15], 'http://arxiv.org/resolve/app/10030148')
                self.assertEqual(row[16], CFG_SUBMISSION_STATUS_SUBMITTED)

            if row[0] == self.id_tests[1]:
                self.assertEqual(row[1], 1)
                self.assertEqual(row[2], 92)
                self.assertEqual(row[4], '10070221')
                self.assertEqual(row[8], 'test_media_deposit')
                self.assertEqual(row[13], 'https://arxiv.org/sword-app/edit/10070221')
                self.assertEqual(row[14], 'https://arxiv.org/sword-app/edit/10070221.atom')
                self.assertEqual(row[15], 'http://arxiv.org/resolve/app/10070221')
                self.assertEqual(row[16], CFG_SUBMISSION_STATUS_SUBMITTED)

            if row[0] == self.id_tests[2]:
                self.assertEqual(row[1], 1)
                self.assertEqual(row[2], 92)
                self.assertEqual(row[4], '12340097')
                self.assertEqual(row[8], 'test_media_deposit')
                self.assertEqual(row[13], 'https://arxiv.org/sword-app/edit/12340097')
                self.assertEqual(row[14], 'https://arxiv.org/sword-app/edit/12340097.atom')
                self.assertEqual(row[15], 'http://arxiv.org/resolve/app/12340097')
                self.assertEqual(row[16], CFG_SUBMISSION_STATUS_SUBMITTED)


    def test_update_submission(self):
        '''Test_insert_submission - check update submission rows in swrCLIENTDATA'''

        update_submission_status(self.id_tests[0], CFG_SUBMISSION_STATUS_SUBMITTED)
        update_submission_status(self.id_tests[1], CFG_SUBMISSION_STATUS_PUBLISHED, '1007.0221')
        update_submission_status(self.id_tests[2], CFG_SUBMISSION_STATUS_REMOVED)

        rows = run_sql('''SELECT id, id_swrREMOTESERVER, id_record, report_no,
                       id_remote, id_user, user_name, user_email, xml_media_deposit,
                       xml_metadata_submit, submission_date, publication_date, removal_date,
                       link_medias, link_metadata, link_status, status, last_update
                       FROM swrCLIENTDATA''')
        for row in rows:
            self.assertEqual(row[0] in self.id_tests, True)
            if row[0] == self.id_tests[0]:
                self.assertEqual(row[1], 1)
                self.assertEqual(row[2], 97)
                self.assertEqual(row[4], '10030148')
                self.assertEqual(row[8], 'test_media_deposit')
                self.assertEqual(row[13], 'https://arxiv.org/sword-app/edit/10030148')
                self.assertEqual(row[14], 'https://arxiv.org/sword-app/edit/10030148.atom')
                self.assertEqual(row[15], 'http://arxiv.org/resolve/app/10030148')
                self.assertEqual(row[16], CFG_SUBMISSION_STATUS_SUBMITTED)

            if row[0] == self.id_tests[1]:
                self.assertEqual(row[1], 1)
                self.assertEqual(row[2], 92)
                self.assertEqual(row[4], '1007.0221')
                self.assertEqual(row[8], 'test_media_deposit')
                self.assertEqual(row[13], 'https://arxiv.org/sword-app/edit/10070221')
                self.assertEqual(row[14], 'https://arxiv.org/sword-app/edit/10070221.atom')
                self.assertEqual(row[15], 'http://arxiv.org/resolve/app/10070221')
                self.assertEqual(row[16], CFG_SUBMISSION_STATUS_PUBLISHED)

            if row[0] == self.id_tests[2]:
                self.assertEqual(row[1], 1)
                self.assertEqual(row[2], 92)
                self.assertEqual(row[4], '12340097')
                self.assertEqual(row[8], 'test_media_deposit')
                self.assertEqual(row[13], 'https://arxiv.org/sword-app/edit/12340097')
                self.assertEqual(row[14], 'https://arxiv.org/sword-app/edit/12340097.atom')
                self.assertEqual(row[15], 'http://arxiv.org/resolve/app/12340097')
                self.assertEqual(row[16], CFG_SUBMISSION_STATUS_REMOVED)


    def test_yread_submission(self):
        '''test_read_submission - check read submission rows in swrCLIENTDATA'''


        currentDate = time.strftime("%Y-%m-%d %H:%M:%S")

        results = select_submitted_record_infos()

        self.assertEqual(len(results), run_sql('''SELECT COUNT(*) FROM swrCLIENTDATA''')[0][0])
        for result in results:
            self.assertEqual(result['id'] in self.id_tests, True)
            if result['id'] == self.id_tests[0]:
                self.assertEqual(result['id_server'], 1)
                self.assertEqual(result['id_record'], 97)
                self.assertEqual(result['id_user'], 6)
                self.assertEqual(result['id_remote'], '10030148')
                self.assertEqual(result['submission_date'], currentDate)
                self.assertEqual(result['publication_date'], '')
                self.assertEqual(result['removal_date'], "")
                self.assertEqual(result['link_medias'], 'https://arxiv.org/sword-app/edit/10030148')
                self.assertEqual(result['link_metadata'], 'https://arxiv.org/sword-app/edit/10030148.atom')
                self.assertEqual(result['link_status'], 'http://arxiv.org/resolve/app/10030148')
                self.assertEqual(result['status'], CFG_SUBMISSION_STATUS_SUBMITTED)

        results = select_submitted_record_infos(4)

        self.assertEqual(len(results), run_sql('''SELECT COUNT(*) FROM swrCLIENTDATA WHERE id_swrREMOTESERVER=4''')[0][0])

        for result in results:
            self.assertEqual(result['id'] in self.id_tests, True)
            if result['id'] == self.id_tests[1]:
                self.assertEqual(result['id_server'], 4)
                self.assertEqual(result['id_record'], 92)
                self.assertEqual(result['id_user'], 5)
                self.assertEqual(result['id_remote'], '1007.0221')
                self.assertEqual(result['submission_date'], currentDate)
                self.assertEqual(result['publication_date'], currentDate)
                self.assertEqual(result['removal_date'], "")
                self.assertEqual(result['link_medias'], 'https://arxiv.org/sword-app/edit/10070221')
                self.assertEqual(result['link_metadata'], 'https://arxiv.org/sword-app/edit/10070221.atom')
                self.assertEqual(result['link_status'], 'http://arxiv.org/resolve/app/10070221')
                self.assertEqual(result['status'], CFG_SUBMISSION_STATUS_PUBLISHED)


        results = select_submitted_record_infos(row_id=self.id_tests[2])
        self.assertEqual(len(results), 1)

        for result in results:
            self.assertEqual(result['id'] in self.id_tests, True)
            if result['id'] == self.id_tests[2]:
                self.assertEqual(result['id_server'], 1)
                self.assertEqual(result['id_record'], 92)
                self.assertEqual(result['id_user'], 5)
                self.assertEqual(result['id_remote'], '12340097')
                self.assertEqual(result['submission_date'], currentDate)
                self.assertEqual(result['publication_date'], "")
                self.assertEqual(result['removal_date'], currentDate)
                self.assertEqual(result['link_medias'], 'https://arxiv.org/sword-app/edit/12340097')
                self.assertEqual(result['link_metadata'], 'https://arxiv.org/sword-app/edit/12340097.atom')
                self.assertEqual(result['link_status'], 'http://arxiv.org/resolve/app/12340097')
                self.assertEqual(result['status'], CFG_SUBMISSION_STATUS_REMOVED)


    def test_zdelete_submission(self):
        '''test_delete_submission - check delete submission rows in swrCLIENTDATA'''

        nb_rows_before = run_sql('''SELECT COUNT(*) FROM swrCLIENTDATA''')[0][0]

        for id_test in self.id_tests:
            delete_from_swr_clientdata(id_test)

        nb_rows_after = run_sql('''SELECT COUNT(*) FROM swrCLIENTDATA''')[0][0]

        nb_rows = nb_rows_before - nb_rows_after

        self.assertEqual(nb_rows, 3)


class Test_list_submitted_resources(InvenioTestCase):
    '''Test_list_submitted_resources - check the data selection and update for admin interface'''

    def test_list_submitted_resources(self):
        '''Test_list_submitted_resources - check the data selection and update for admin interface'''

        id_tests = []

        id_tests.append(insert_into_swr_clientdata(4, 97, 1, 'test', 'test', '10030148',
                               'https://arxiv.org/sword-app/edit/10030148',
                               'https://arxiv.org/sword-app/edit/10030148.atom',
                               'http://arxiv.org/resolve/app/10030148'))

        time.sleep(1)

        id_tests.append(insert_into_swr_clientdata(4, 97, 1, 'test', 'test', '10030148',
                               'https://arxiv.org/sword-app/edit/10030148',
                               'https://arxiv.org/sword-app/edit/10030148.atom',
                               'http://arxiv.org/resolve/app/10030148'))

        update_submission_status(id_tests[1], CFG_SUBMISSION_STATUS_PUBLISHED, '1003.0148')

        time.sleep(1)

        id_tests.append(insert_into_swr_clientdata(3, 92, 2, 'test', 'test', '12340097',
                               'https://arxiv.org/sword-app/edit/12340097',
                               'https://arxiv.org/sword-app/edit/12340097.atom',
                               'http://arxiv.org/resolve/app/12340097'))

        time.sleep(1)

        (submissions, modifications) = list_submitted_resources(0, 10, '')

        self.assertEqual(len(submissions), 3)
        self.assertEqual(len(modifications), 2)

        self.assertEqual(submissions[1]['id_remote'], '1003.3743')
        self.assertEqual(submissions[1]['status'], CFG_SUBMISSION_STATUS_PUBLISHED)
        self.assertEqual(submissions[1]['publication_date'] != '', True)

        self.assertEqual(submissions[2]['id_remote'], '1003.0148')
        self.assertEqual(submissions[2]['status'], CFG_SUBMISSION_STATUS_PUBLISHED)
        self.assertEqual(submissions[2]['publication_date'] != '', True)

        self.assertEqual(submissions[0]['id_remote'], '12340097')
        self.assertEqual(submissions[0]['status'], CFG_SUBMISSION_STATUS_REMOVED)
        self.assertEqual(submissions[0]['removal_date'] != '', True)

        self.assertEqual(modifications[1], submissions[0]['id'])
        self.assertEqual(modifications[0], submissions[1]['id'])


        for id_test in id_tests:
            delete_from_swr_clientdata(id_test)


class Test_format_metadata_atom(InvenioTestCase):
    ''' Test_format_metadata_atom - check the generation of the atom entry containing metadata'''

    def test_format_full_metadata(self):
        ''' test_format_full_metadata check that every metadata get its xml node'''

        contributors = []
        contributor = {'name'       : 'contributor_1_test',
                       'email'      : 'contributor_1@test.com',
                       'affiliation': 'affiliation_test'}
        contributors.append(contributor)

        contributor = {'name'       : 'contributor_2_test',
                       'email'      : 'contributor_2@test.com',
                       'affiliation': ''}
        contributors.append(contributor)

        contributor = {'name'       : 'contributor_3_test',
                       'email'       : '',
                       'affiliation' : ''}
        contributors.append(contributor)

        categories = []
        category = {'url'  : 'https://arxiv.org/test-categories-1',
                    'label': 'category_1_test'}
        categories.append(category)
        category = {'url'  : 'https://arxiv.org/test-categories-2',
                    'label': 'category_2_test'}
        categories.append(category)
        category = {'url'  : 'https://arxiv.org/test-categories-3',
                    'label': 'category_3_test'}
        categories.append(category)

        journal_refs = []
        journal_refs.append('journal_ref_test_1')
        journal_refs.append('journal_ref_test_2')

        report_nos = []
        report_nos.append('report_no_test_1')
        report_nos.append('report_no_test_2')

        links = []
        links.append({'link': 'http://arxiv.org/test_1',
                      'type': 'application/test_1'})
        links.append({'link': 'http://arxiv.org/test_2',
                      'type': 'application/test_2'})

        metadata = {'id'         : 'id_test',
                    'title'       : 'title_test',
                    'author_name' : 'author_test',
                    'author_email': 'author_email',
                    'contributors': contributors,
                    'summary'     : 'summary_test',
                    'categories'  : categories,
                    'primary_url' : 'https://arxiv.org/primary-test-categories',
                    'primary_label': 'primary_category_label_test',
                    'comment'     : '23 pages, 3 chapters 1 test',
                    'journal_refs': journal_refs,
                    'report_nos'  : report_nos,
                    'doi'         : '10.2349.test.209',
                    'links'       : links
                    }

        arXivFormat = ArXivFormat()
        metadata_atom = arXivFormat.format_metadata(metadata)

        entry_node = minidom.parseString(metadata_atom)


        self.assertEqual(metadata_atom != '', True)


class Test_submission_process(InvenioTestCase):
    '''Test_submission_process - test document submission'''

    def test_perform_submission_process(self):
        '''Test_perform_submission_process - test document submission'''

        metadata = {}
        metadata['primary_label'] = 'Test - Test Disruptive Networks'
        metadata['primary_url'] = 'http://arxiv.org/terms/arXiv/test.dis-nn'

        user_info = {}
        user_info['nickname'] = 'test_user'
        user_info['email'] = 'test@user.com'
        user_info['id'] = 1

        result = perform_submission_process(4, 'https://arxiv.org/sword-app/test-collection',
                                            97, user_info, metadata)

        self.assertEqual(open('/tmp/media.xml', 'r').read() != '', True)
        self.assertEqual(open('/tmp/metadata.xml', 'r').read() != '', True)
        self.assertEqual(open('/tmp/submit.xml', 'r').read() != '', True)



        if result['row_id'] != '':
            delete_from_swr_clientdata(result['row_id'])



TEST_SUITE = make_test_suite(Test_format_marcxml_file,
                             Test_format_metadata,
                             #Test_get_submission_status,
                             #Test_format_submission_status,
                             Test_swrCLIENTDATA_table)
                             #Test_format_metadata_atom)
                             #Test_list_submitted_resources)
                             #Test_submission_process)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

