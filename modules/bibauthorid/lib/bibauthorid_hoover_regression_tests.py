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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from unittest import *
from mock import *
import os
from sys import exit

from invenio.testutils import make_test_suite
from invenio.testutils import run_test_suite

from invenio.bibauthorid_testutils import *

from invenio.bibtask import setup_loggers
from invenio.bibtask import task_set_task_param
from invenio.bibtask import task_low_level_submission

from invenio.bibupload_regression_tests import wipe_out_record_from_all_tables
from invenio.dbquery import run_sql

import invenio.bibauthorid_rabbit
from invenio.bibauthorid_rabbit import rabbit

import invenio.bibauthorid_hoover
from invenio.bibauthorid_hoover import hoover

from invenio.bibauthorid_dbinterface import get_inspire_id_of_author
from invenio.bibauthorid_dbinterface import _delete_from_aidpersonidpapers_where
from invenio.bibauthorid_dbinterface import get_papers_of_author

from invenio.search_engine import get_record

from invenio.bibindex_regression_tests import reindex_for_type_with_bibsched

from invenio.config import CFG_BINDIR


def index_hepnames_authors():
    """runs bibindex for the index '_type' and returns the task_id"""
    program = os.path.join(CFG_BINDIR, 'bibindex')
    # Add hepnames collection
    task_id = task_low_level_submission(
        'bibindex',
        'hoover_regression_tests',
        '-w',
        'author',
        '-u',
        'admin',
    )
    COMMAND = "%s %s > /dev/null 2> /dev/null" % (program, str(task_id))
    os.system(COMMAND)
    return task_id


def clean_up_the_database(inspireID):
    if inspireID:
        run_sql("delete from aidPERSONIDDATA where data=%s", (inspireID,))

dupl = 0
pid = -1


def mock_add():
    global dupl
    dupl += 1


class BibAuthorIDHooverTestCase(TestCase):

    run_exec = False

    @classmethod
    def setUpClass(cls):

        if cls.run_exec:
            return
        cls.run_exec = True
        cls.verbose = 0
        cls.logger = setup_loggers()
        cls.logger.info('Setting up regression tests...')
        task_set_task_param('verbose', cls.verbose)

        cls.authors = {'author1': {
            'name': 'authoraaaaa authoraaaab',
            'inspireID': 'INSPIRE-FAKE_ID1'},
            'author2': {
            'name': 'authorbbbba authorbbbbb',
            'inspireID': 'INSPIRE-FAKE_ID2'},
            'author3': {
            'name': 'authorcccca authorccccb',
            'inspireID': 'INSPIRE-FAKE_ID3'},
            'author4': {
            'name': 'authordddda authorddddb',
            'inspireID': 'INSPIRE-FAKE_ID4'},
            'author5': {
            'name': 'authoreeeea authoreeeeb',
            'inspireID': 'INSPIRE-FAKE_ID5'},
            'author6': {
            'name': 'authorffffa authorffffb',
            'inspireID': 'INSPIRE-FAKE_ID6'},
            'author7': {
            'name': 'authorgggga authorggggb',
            'inspireID': 'INSPIRE-FAKE_ID7'},
            'author8': {
            'name': 'authorhhhha authorhhhhb',
            'inspireID': 'INSPIRE-FAKE_ID8'},
            'author9': {
            'name': 'authoriiiia authoriiiib',
            'inspireID': 'INSPIRE-FAKE_ID9'},
            'author10': {
            'name': 'authorjjjja authorjjjjb',
            'inspireID': 'INSPIRE-FAKE_ID10'},
            'author11': {
            'name': 'authorkkkka authorkkkkb',
            'inspireID': 'INSPIRE-FAKE_ID11'},
            'author12': {
            'name': 'authorlllla authorllllb',
            'inspireID': 'INSPIRE-FAKE_ID12'},
            'author13': {
            'name': 'authormmmma authormmmmb',
            'inspireID': 'INSPIRE-FAKE_ID13'},
            'author14': {
            'name': 'authornnnna authornnnnb',
            'inspireID': 'INSPIRE-FAKE_ID14'},
            'author15': {
            'name': 'authorooooa authoroooob',
            'inspireID': 'INSPIRE-FAKE_ID15'},
            'author16': {
            'name': 'authorppppa authorppppb',
            'inspireID': 'INSPIRE-FAKE_ID16'},
            'author17': {
            'name': 'authorqqqqa authorqqqqb',
            'inspireID': 'INSPIRE-FAKE_ID17'},
            'author18': {
            'name': 'authorrrrra authorrrrrb',
            'inspireID': 'INSPIRE-FAKE_ID18'},
            'author19': {
            'name': 'authorssssa authorssssb',
            'inspireID': 'INSPIRE-FAKE_ID19'}
        }
        cls.marc_xmls = dict()
        cls.bibrecs = dict()
        cls.pids = dict()
        cls.bibrefs = dict()

        def set_up_test_hoover_inertia():
            cls.marc_xmls['paper1'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author1']['name'], limit_to_collections=True)
            cls.bibrecs['paper1'] = get_bibrec_for_record(
                cls.marc_xmls['paper1'],
                opt_mode='insert')
            cls.marc_xmls['paper1'] = add_001_field(
                cls.marc_xmls['paper1'],
                cls.bibrecs['paper1'])

        def set_up_test_hoover_duplication():
            cls.marc_xmls['paper2'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author2']['name'],
                None,
                ((cls.authors['author2']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper2'] = get_bibrec_for_record(
                cls.marc_xmls['paper2'],
                opt_mode='insert')
            cls.marc_xmls['paper2'] = add_001_field(
                cls.marc_xmls['paper2'],
                cls.bibrecs['paper2'])

        def set_up_test_hoover_assign_one_inspire_id_from_an_unclaimed_paper():
            cls.marc_xmls['paper3'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author3']['name'],
                None,
                ((cls.authors['author3']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper3'] = get_bibrec_for_record(
                cls.marc_xmls['paper3'],
                opt_mode='insert')
            cls.marc_xmls['paper3'] = add_001_field(
                cls.marc_xmls['paper3'],
                cls.bibrecs['paper3'])

        def set_up_test_hoover_assign_one_inspire_id_from_a_claimed_paper():
            cls.marc_xmls['paper4'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author4']['name'],
                None,
                ((cls.authors['author4']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper4'] = get_bibrec_for_record(
                cls.marc_xmls['paper4'],
                opt_mode='insert')
            cls.marc_xmls['paper4'] = add_001_field(
                cls.marc_xmls['paper4'],
                cls.bibrecs['paper4'])

        def set_up_test_hoover_assign_one_inspire_id_from_unclaimed_papers_with_different_inspireID(
        ):
            cls.marc_xmls['paper5'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author5']['name'],
                None,
                ((cls.authors['author5']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper5'] = get_bibrec_for_record(
                cls.marc_xmls['paper5'],
                opt_mode='insert')
            cls.marc_xmls['paper5'] = add_001_field(
                cls.marc_xmls['paper5'],
                cls.bibrecs['paper5'])

            cls.marc_xmls['paper6'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author5']['name'],
                None,
                ((cls.authors['author6']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper6'] = get_bibrec_for_record(
                cls.marc_xmls['paper6'],
                opt_mode='insert')
            cls.marc_xmls['paper6'] = add_001_field(
                cls.marc_xmls['paper6'],
                cls.bibrecs['paper6'])

        def set_up_test_hoover_assign_one_inspire_id_from_a_claimed_paper_and_unclaimed_paper_with_different_inspireID(
        ):
            cls.marc_xmls['paper7'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author7']['name'],
                None,
                ((cls.authors['author7']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper7'] = get_bibrec_for_record(
                cls.marc_xmls['paper7'],
                opt_mode='insert')
            cls.marc_xmls['paper7'] = add_001_field(
                cls.marc_xmls['paper7'],
                cls.bibrecs['paper7'])

            cls.marc_xmls['paper8'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author7']['name'],
                None,
                ((cls.authors['author8']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper8'] = get_bibrec_for_record(
                cls.marc_xmls['paper8'],
                opt_mode='insert')
            cls.marc_xmls['paper8'] = add_001_field(
                cls.marc_xmls['paper8'],
                cls.bibrecs['paper8'])

        def set_up_test_hoover_assign_one_inspire_id_from_claimed_papers_with_different_inspireID(
        ):
            cls.marc_xmls['paper9'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author9']['name'],
                None,
                ((cls.authors['author2']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper9'] = get_bibrec_for_record(
                cls.marc_xmls['paper9'],
                opt_mode='insert')
            cls.marc_xmls['paper9'] = add_001_field(
                cls.marc_xmls['paper9'],
                cls.bibrecs['paper9'])

            cls.marc_xmls['paper10'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author9']['name'],
                None,
                ((cls.authors['author10']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper10'] = get_bibrec_for_record(
                cls.marc_xmls['paper10'],
                opt_mode='insert')
            cls.marc_xmls['paper10'] = add_001_field(
                cls.marc_xmls['paper10'],
                cls.bibrecs['paper10'])

        def set_up_test_hoover_vacuum_an_unclaimed_paper_with_an_inspire_id_from_a_claimed_paper(
        ):
            cls.marc_xmls['paper11'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author11']['name'],
                None,
                ((cls.authors['author11']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper11'] = get_bibrec_for_record(
                cls.marc_xmls['paper11'],
                opt_mode='insert')
            cls.marc_xmls['paper11'] = add_001_field(
                cls.marc_xmls['paper11'],
                cls.bibrecs['paper11'])

            cls.marc_xmls['paper12'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author12']['name'],
                None,
                ((cls.authors['author11']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper12'] = get_bibrec_for_record(
                cls.marc_xmls['paper12'],
                opt_mode='insert')
            cls.marc_xmls['paper12'] = add_001_field(
                cls.marc_xmls['paper12'],
                cls.bibrecs['paper12'])

        def set_up_test_hoover_vacuum_a_claimed_paper_with_an_inspire_id_from_a_claimed_paper(
        ):
            cls.marc_xmls['paper13'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author13']['name'],
                None,
                ((cls.authors['author13']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper13'] = get_bibrec_for_record(
                cls.marc_xmls['paper13'],
                opt_mode='insert')
            cls.marc_xmls['paper13'] = add_001_field(
                cls.marc_xmls['paper13'],
                cls.bibrecs['paper13'])

            cls.marc_xmls['paper14'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author14']['name'],
                None,
                ((cls.authors['author13']['inspireID'],
                  'i'),
                 ), limit_to_collections=True)

            cls.bibrecs['paper14'] = get_bibrec_for_record(
                cls.marc_xmls['paper14'],
                opt_mode='insert')
            cls.marc_xmls['paper14'] = add_001_field(
                cls.marc_xmls['paper14'],
                cls.bibrecs['paper14'])

        def set_up_test_hoover_assign_one_inspire_id_from_hepnames_record():
            cls.marc_xmls['paper15'] = get_new_hepnames_marc_for_test(
                cls.authors['author15']['name'], ((cls.authors['author15']['inspireID'], 'i'),))

            cls.bibrecs['paper15'] = get_bibrec_for_record(
                cls.marc_xmls['paper15'],
                opt_mode='insert')
            cls.marc_xmls['paper15'] = add_001_field(
                cls.marc_xmls['paper15'],
                cls.bibrecs['paper15'])

        def set_up_duplicated_unclaimed_signature():
            cls.marc_xmls['paper16'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author16']['name'],
                (cls.authors['author17']['name'],
                 ),
                ((cls.authors['author16']['inspireID'],
                  'i'),
                 (cls.authors['author16']['inspireID'],
                  'i')), limit_to_collections=True)

            cls.bibrecs['paper16'] = get_bibrec_for_record(
                cls.marc_xmls['paper16'],
                opt_mode='insert')
            cls.marc_xmls['paper16'] = add_001_field(
                cls.marc_xmls['paper16'],
                cls.bibrecs['paper16'])

        def set_up_duplicated_claimed_signature():
            cls.marc_xmls['paper18'] = get_new_marc_for_test(
                'Test Paper',
                cls.authors['author18']['name'],
                (cls.authors['author19']['name'],
                 ),
                ((cls.authors['author18']['inspireID'],
                  'i'),
                 (cls.authors['author18']['inspireID'],
                  'i')), limit_to_collections=True)

            cls.bibrecs['paper18'] = get_bibrec_for_record(
                cls.marc_xmls['paper18'],
                opt_mode='insert')
            cls.marc_xmls['paper18'] = add_001_field(
                cls.marc_xmls['paper18'],
                cls.bibrecs['paper18'])

        set_up_test_hoover_inertia()
        set_up_test_hoover_duplication()
        set_up_test_hoover_assign_one_inspire_id_from_an_unclaimed_paper()
        set_up_test_hoover_assign_one_inspire_id_from_a_claimed_paper()
        set_up_test_hoover_assign_one_inspire_id_from_unclaimed_papers_with_different_inspireID()
        set_up_test_hoover_assign_one_inspire_id_from_a_claimed_paper_and_unclaimed_paper_with_different_inspireID()
        set_up_test_hoover_assign_one_inspire_id_from_claimed_papers_with_different_inspireID()
        set_up_test_hoover_vacuum_an_unclaimed_paper_with_an_inspire_id_from_a_claimed_paper()
        set_up_test_hoover_vacuum_a_claimed_paper_with_an_inspire_id_from_a_claimed_paper()
        set_up_test_hoover_assign_one_inspire_id_from_hepnames_record()
        set_up_duplicated_unclaimed_signature()
        set_up_duplicated_claimed_signature()

        cls.bibrecs_to_clean = [cls.bibrecs[key] for key in cls.bibrecs]
        rabbit(sorted([cls.bibrecs[key]
                       for key in cls.bibrecs]), verbose=False)

        for key in cls.authors:
            try:
                temp = set()
                cls.bibrefs[key] = get_bibref_value_for_name(
                    cls.authors[key]['name'])
                temp = run_sql(
                    "select personid from aidPERSONIDPAPERS where bibref_value=%s and bibrec=%s and name=%s",
                    (cls.bibrefs[key],
                     cls.bibrecs[
                        key.replace(
                            'author',
                            'paper')],
                        cls.authors[key]['name']))
                cls.pids[key] = temp[0][0] if temp else ()
            except KeyError as e:
                print e

        claim_test_paper(cls.bibrecs['paper4'])
        claim_test_paper(cls.bibrecs['paper7'])
        claim_test_paper(cls.bibrecs['paper9'])
        claim_test_paper(cls.bibrecs['paper10'])
        claim_test_paper(cls.bibrecs['paper11'])
        claim_test_paper(cls.bibrecs['paper13'])
        claim_test_paper(cls.bibrecs['paper14'])
        claim_test_paper(cls.bibrecs['paper18'])
        tmp_claimed_exception = invenio.bibauthorid_hoover.DuplicateClaimedPaperException
        tmp_unclaimed_exception = invenio.bibauthorid_hoover.DuplicateUnclaimedPaperException

        class MockClaimedException(
                invenio.bibauthorid_hoover.DuplicateClaimedPaperException):

            def __init__(self, message, pid, signature, present_signatures):
                global dupl
                super(MockClaimedException, self).__init__(message, pid, signature, present_signatures)
                dupl += 1

        class MockUnclaimedException(
                invenio.bibauthorid_hoover.DuplicateUnclaimedPaperException):

            def __init__(self, message, _pid, signature, present_signatures):
                global pid
                super(MockUnclaimedException, self).__init__(message, _pid, signature, present_signatures)
                pid = _pid

        invenio.bibauthorid_hoover.DuplicateClaimedPaperException = MockClaimedException
        invenio.bibauthorid_hoover.DuplicateUnclaimedPaperException = MockUnclaimedException
        hoover(list(set(cls.pids[key] for key in cls.pids if cls.pids[key])))
        invenio.bibauthorid_hoover.DuplicateClaimedPaperException = tmp_claimed_exception
        invenio.bibauthorid_hoover.DuplicateUnclaimedPaperException = tmp_unclaimed_exception
        print "dupl", dupl

    @classmethod
    def tearDownClass(cls):

        # All records are wiped out for consistency.
        for key in cls.authors:
            clean_up_the_database(cls.authors[key]['inspireID'])

        for key in cls.pids:
            if cls.pids[key]:
                _delete_from_aidpersonidpapers_where(cls.pids[key])

        for bibrec in cls.bibrecs_to_clean:
            wipe_out_record_from_all_tables(bibrec)
            clean_authors_tables(bibrec)


class OneAuthorOnePaperHooverTestCase(BibAuthorIDHooverTestCase):

    @classmethod
    def setUpClass(self):
        BibAuthorIDHooverTestCase.setUpClass()

    @classmethod
    def tearDownClass(self):
        pass

    def test_hoover_one_author_one_paper(self):

        def test_hoover_inertia():
            '''If nothing should change then nothing changes'''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author1'])
            self.assertEquals(inspireID, tuple())

        def test_hoover_for_duplication():
            '''No duplicated information in the database'''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author2'])
            self.assertEquals(inspireID, 'INSPIRE-FAKE_ID2')

        def test_hoover_assign_one_inspire_id_from_an_unclaimed_paper():
            '''
            Preconditions:
                *This is the only paper that the author has
                *No other author has a claim on the paper
            Postconditions:
                *connect author with inspireID taken from the unclaimed paper
            '''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author3'])
            self.assertEquals(
                inspireID,
                BibAuthorIDHooverTestCase.authors['author3']['inspireID'])

        def test_hoover_assign_one_inspire_id_from_a_claimed_paper():
            '''
            Preconditions:
                *This is the only paper that the author has
                *No other author has a claim on the paper
            Postconditions:
                *connect author with inspireID taken from the claimed paper
            '''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author4'])
            self.assertEquals(
                inspireID,
                BibAuthorIDHooverTestCase.authors['author4']['inspireID'])

        test_hoover_inertia()
        test_hoover_for_duplication()
        test_hoover_assign_one_inspire_id_from_an_unclaimed_paper()
        test_hoover_assign_one_inspire_id_from_a_claimed_paper()


class OneAuthorManyPapersHooverTestCase(BibAuthorIDHooverTestCase):

    @classmethod
    def setUpClass(self):
        BibAuthorIDHooverTestCase.setUpClass()

    @classmethod
    def tearDownClass(self):
        pass

    def test_hoover_one_author_many_papers(self):

        def test_hoover_assign_one_inspire_id_from_unclaimed_papers_with_different_inspireID(
        ):
            '''
            Preconditions:
                *One unclaimed paper of the author with inspireID: INSPIRE-FAKE_ID1
                *One unclaimed paper of the author with inspireID: INSPIRE-FAKE_ID2
                *The author has no inspireID connected to him
                *No other author has a claim on the papers

            Postconditions:
                *Nothing has changed
            '''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author5'])
            self.assertEquals(inspireID, ())

        def test_hoover_assign_one_inspire_id_from_a_claimed_paper_and_unclaimed_paper_with_different_inspireID(
        ):
            '''
            Preconditions:
                *One claimed paper of the author with inspireID: INSPIRE-FAKE_ID1
                *One unclaimed paper of the author with inspireID: INSPIRE-FAKE_ID2
                *The author has no inspireID connected to him
                *No other author has a claim on the papers

            Postconditions:
                *connect author with inspireID taken from the claimed paper(INSPIRE-FAKE_ID1)
            '''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author7'])
            self.assertEquals(
                inspireID,
                BibAuthorIDHooverTestCase.authors['author7']['inspireID'])

        def test_hoover_assign_one_inspire_id_from_claimed_papers_with_different_inspireID():
            '''
            Preconditions:
                *One claimed paper of the author with inspireID: INSPIRE-FAKE_ID1
                *One claimed paper of the author with inspireID: INSPIRE-FAKE_ID2
                *The author has no inspireID connected to him
                *No other author has a claim on the papers

            Postconditions:
                *Nothing has changed
            '''

            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author9'])
            self.assertEquals(inspireID, ())

        test_hoover_assign_one_inspire_id_from_unclaimed_papers_with_different_inspireID()
        test_hoover_assign_one_inspire_id_from_a_claimed_paper_and_unclaimed_paper_with_different_inspireID()
        test_hoover_assign_one_inspire_id_from_claimed_papers_with_different_inspireID()


class ManyAuthorsHooverTestCase(BibAuthorIDHooverTestCase):

    @classmethod
    def setUpClass(self):
        BibAuthorIDHooverTestCase.setUpClass()

    @classmethod
    def tearDownClass(self):
        pass

    def test_many_authors(self):

        def test_hoover_vacuum_an_unclaimed_paper_with_an_inspire_id_from_a_claimed_paper():
            '''
            Preconditions:
                *One claimed paper of the author1 with inspireID: INSPIRE-FAKE_ID1
                *One unclaimed paper of the author2 with inspireID: INSPIRE-FAKE_ID1
                *The authors has no inspireIDs connected to them
                *No other authors has a claim on the papers

            Postconditions:
                *Author1 is connected to the inspireID: INSPIRE-FAKE_ID1
                *The unclaimed paper of author2 is now moved to author1
            '''

            first_author_papers = get_papers_of_author(
                BibAuthorIDHooverTestCase.pids['author11'])
            second_author_papers = get_papers_of_author(
                BibAuthorIDHooverTestCase.pids['author12'])

            inspireID1 = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author11'])
            self.assertEquals(
                inspireID1,
                BibAuthorIDHooverTestCase.authors['author11']['inspireID'])
            inspireID2 = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author12'])
            self.assertEquals(inspireID2, ())

            self.assertEquals(len(first_author_papers), 2)
            self.assertEquals(len(second_author_papers), 0)

        def test_hoover_vacuum_a_claimed_paper_with_an_inspire_id_from_a_claimed_paper():
            '''
            Preconditions:
                *One claimed paper of the author1 with inspireID: INSPIRE-FAKE_ID1
                *One claimed paper of the author2 with inspireID: INSPIRE-FAKE_ID1
                *The authors has no inspireIDs connected to them
                *No other authors has a claim on the papers

            Postconditions:
                *Author1 is connected to the inspireID: INSPIRE-FAKE_ID1
                *Nothing else changes
            '''

            first_author_papers = get_papers_of_author(
                BibAuthorIDHooverTestCase.pids['author13'])
            second_author_papers = get_papers_of_author(
                BibAuthorIDHooverTestCase.pids['author14'])

            inspireID1 = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author13'])
            self.assertEquals(inspireID1, ())
            inspireID2 = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author14'])
            self.assertEquals(inspireID2, ())

            self.assertEquals(len(first_author_papers), 1)
            self.assertEquals(len(second_author_papers), 1)

        test_hoover_vacuum_an_unclaimed_paper_with_an_inspire_id_from_a_claimed_paper()
        test_hoover_vacuum_a_claimed_paper_with_an_inspire_id_from_a_claimed_paper()


class HepnamesHooverTestCase(BibAuthorIDHooverTestCase):

    @classmethod
    def setUpClass(self):
        BibAuthorIDHooverTestCase.setUpClass()

    @classmethod
    def tearDownClass(self):
        pass

    def test_hepnames(self):
        def test_hoover_assign_one_inspire_id_from_hepnames_record():
            print BibAuthorIDHooverTestCase.pids['author15']
            inspireID = get_inspire_id_of_author(
                BibAuthorIDHooverTestCase.pids['author15'])
            self.assertEquals(
                inspireID,
                BibAuthorIDHooverTestCase.authors['author15']['inspireID'])

        test_hoover_assign_one_inspire_id_from_hepnames_record()


class DuplicatedSignaturesTestCase(BibAuthorIDHooverTestCase):

    @classmethod
    def setUpClass(self):
        BibAuthorIDHooverTestCase.setUpClass()

    @classmethod
    def tearDownClass(self):
        pass

    def test_duplicated_signatures(self):
        def duplicated_claimed_signature():
            self.assertEquals(dupl, 1)

        def duplicated_unclaimed_signature():
            inspireID = get_inspire_id_of_author(pid)
            author_papers = get_papers_of_author(pid)
            self.assertEquals(len(author_papers), 1)

        duplicated_claimed_signature()
        duplicated_unclaimed_signature()


TEST_SUITE = make_test_suite(
    OneAuthorOnePaperHooverTestCase,
    OneAuthorManyPapersHooverTestCase,
    ManyAuthorsHooverTestCase,
    DuplicatedSignaturesTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=False)
    BibAuthorIDHooverTestCase.tearDownClass()
