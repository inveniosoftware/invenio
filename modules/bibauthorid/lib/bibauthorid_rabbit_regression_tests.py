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

"""This module contains regression tests for rabbit."""

__revision__ = "$Id$"

from invenio.bibtask import setup_loggers
from invenio.bibtask import task_set_task_param
from invenio.bibupload_regression_tests import wipe_out_record_from_all_tables
from invenio.dbquery import run_sql
from invenio.bibauthorid_rabbit import rabbit


from invenio.bibauthorid_testutils import get_new_marc_for_test
from invenio.bibauthorid_testutils import get_modified_marc_for_test
from invenio.bibauthorid_testutils import clean_authors_tables
from invenio.bibauthorid_testutils import get_bibrec_for_record
from invenio.bibauthorid_testutils import get_bibref_value_for_name
from invenio.bibauthorid_testutils import get_count_of_pids
from invenio.bibauthorid_testutils import claim_test_paper
from invenio.bibauthorid_testutils import person_in_aidpersonidpapers
from invenio.bibauthorid_testutils import person_in_aidpersoniddata
from invenio.bibauthorid_testutils import add_001_field
from invenio.bibauthorid_testutils import is_test_paper_claimed

from invenio.bibauthorid_dbinterface import get_authors_by_name
from invenio.bibauthorid_dbinterface import _add_external_id_to_author
from invenio.bibauthorid_dbinterface import _remove_external_id_from_author
from invenio.bibauthorid_name_utils import create_matchable_name
from invenio.testutils import InvenioTestCase, run_test_suite, make_test_suite
import invenio.config as config

from copy import deepcopy
from mock import patch


class BibAuthorIDRabbitTestCase(InvenioTestCase):

    '''
    Class with helper method for rabbit regression tests.
    '''

    def setUp(self):
        '''
        Setting up the regression test for rabbit.Notice that most rabbit test cases
        should reuse this setUp method.
        '''
        self.verbose = 0
        task_set_task_param('verbose', self.verbose)

        self.author_name = 'TestSurname, TestName'  # The original name.

        # A two-letter change to the original name. Notice unicode characters
        self.slightly_modified_author_name = u"TéstSurname, TestName"

        # A rather large change of the original name.
        self.heavily_modified_name = 'TestSarname, TostName'

        # The same for. coauthors
        self.co_authors_names = ['Coauthor, SomeCoauthor',
                                 'SomeCoauthor, DifferentCoauthor',
                                 'Queen, Elizabeth',
                                 'SomeBody, John']

        # This is a greek r!
        self.slightly_mod_co_authors_names = [u'Coauthoρ, SomeCoauthoρ',
                                              u'SomeCoauthoρ, DifferentCoauthoρ',
                                              u'Queen, Elizabeth',
                                              u'SomeBody, John']
        self.heavily_mod_co_authors_names = ['Coeuthara, SomeCithor',
                                             'SomiCythore, Difn',
                                             'Quiin, d\'Elezebath',
                                             'Samebedi, Johnathan']
        self.ext_id = 'FAKE_EXT_ID'

    def tearDown(self):
        # All records are wiped out for consistency.
        for bibrec in self.bibrecs_to_clean:
            wipe_out_record_from_all_tables(bibrec)
            clean_authors_tables(bibrec)


class OneAuthorRabbitTestCase(BibAuthorIDRabbitTestCase):

    def setUp(self):
        super(OneAuthorRabbitTestCase, self).setUp()
        self.main_marcxml_record = get_new_marc_for_test('Rabbit Test Paper', author_name=self.author_name,
                                                         ext_id=self.ext_id)
        self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record, opt_mode='insert')
        self.main_marcxml_record = add_001_field(self.main_marcxml_record, self.main_bibrec)
        self.bibrecs_to_clean = [self.main_bibrec]

    def test_rabbit_one_author_only(self):
        '''
        Rabbit tests for one author cases.
        '''
        def test_rabbit_add_new_paper_with_one_author():
            '''
            Rabbit gets a record with a new author.
            Tests whether the author-related tables are populated with
            the author's name.
            '''
            rabbit([self.main_bibrec], verbose=True)
            self.current_bibref_value = get_bibref_value_for_name(self.author_name)  # saved for following tests
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))

        def test_rabbit_remove_author_from_paper():
            '''
            The author field of the record is removed.
            Tests whether the author is actually removed by rabbit.
            '''
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            number_of_personids_after = get_count_of_pids()
            self.assertEquals(number_of_personids_before,
                              number_of_personids_after + 1)
            self.assertFalse(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertFalse(person_in_aidpersoniddata(self.author_name))

        def test_rabbit_add_author_again():
            '''
            The author field of the record is re-added.
            Tests whether the author is added again to aidPERSONIDPAPERS and aidPERSONIDDATA.
            '''
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            previous_bibref_value = self.current_bibref_value
            self.current_bibref_value = get_bibref_value_for_name(self.author_name)
            number_of_personids_after = get_count_of_pids()
            self.assertEquals(previous_bibref_value,
                              self.current_bibref_value)
            self.assertEquals(number_of_personids_after,
                              number_of_personids_before + 1)
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))

        def test_rabbit_slightly_modify_author():
            '''
            The author's name is modified slightly. This means, that the modified string is still similar
            to the original (much more than the current threshold). After the run of rabbit, the name in
            aidPERSONIDDATA should NOT change, since this is a slight modification.
            '''
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.slightly_modified_author_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            previous_bibref_value = self.current_bibref_value
            self.current_bibref_value = get_bibref_value_for_name(self.slightly_modified_author_name)
            number_of_personids_after = get_count_of_pids()

            self.assertTrue(person_in_aidpersonidpapers(
                self.slightly_modified_author_name, self.main_bibrec))
            self.assertNotEquals(previous_bibref_value,
                                 self.current_bibref_value)
            self.assertFalse(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))
            self.assertEquals(number_of_personids_before,
                              number_of_personids_after)

        def test_rabbit_heavily_modify_author():
            '''
            The author's name is modified heavily. This means, that the modified string is significantly
            different than the original.. After the run of rabbit, the name in
            aidPERSONIDDATA SHOULD change, since this is a heavy modification.
            '''
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.heavily_modified_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)

            previous_bibref_value = self.current_bibref_value
            self.current_bibref_value = get_bibref_value_for_name(self.heavily_modified_name)
            number_of_personids_after = get_count_of_pids()
            self.assertNotEquals(previous_bibref_value,
                                 self.current_bibref_value)
            self.assertTrue(person_in_aidpersonidpapers(
                self.heavily_modified_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.heavily_modified_name))
            self.assertFalse(person_in_aidpersoniddata(self.author_name))
            self.assertFalse(person_in_aidpersonidpapers(
                self.slightly_modified_author_name, self.main_bibrec))
            self.assertEquals(number_of_personids_before,
                              number_of_personids_after)

        def test_rabbit_claim_record():
            '''
            The test record is artificially being claimed. Then, the name of the author is being modified:
                i) slightly
                A slight modification of a claimed record should have the same behavior as before:
                    Name changes in aidPERSONIDPAPERS but not in aidPERSONIDDATA.
                ii) heavily
                Due to the fact that the paper is claimed the canonical name should NOT change in aidPERSONIDDATA.
            '''
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)

            claim_test_paper(self.main_bibrec)

            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.slightly_modified_author_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)

            number_of_personids_after = get_count_of_pids()
            self.assertEquals(number_of_personids_before,
                              number_of_personids_after)
            self.assertTrue(person_in_aidpersonidpapers(self.slightly_modified_author_name, self.main_bibrec))
            self.assertFalse(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(is_test_paper_claimed(self.main_bibrec, 100))

            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.heavily_modified_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)

            self.assertTrue(person_in_aidpersonidpapers(self.heavily_modified_name, self.main_bibrec))
            self.assertFalse(person_in_aidpersonidpapers(self.slightly_modified_author_name, self.main_bibrec))
            self.assertFalse(is_test_paper_claimed(self.main_bibrec, 100))

        def test_rabbit_add_inspireID():
            '''
            An inspire id is added to to an author artificially. Then, a record is uploaded with a
            heavily modifield name of the person + the same inspire ID. Despite the fact that the name
            is totally different, due to the fact that there is an inspire ID in place,
            the entry shall not change.
            '''
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            personid_to_test = get_authors_by_name(self.author_name)[0]

            _add_external_id_to_author(personid_to_test, 'INSPIREID', self.ext_id)

            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.heavily_modified_name,
                                                                  ext_id=self.ext_id)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            self.assertEquals(personid_to_test, get_authors_by_name(self.heavily_modified_name)[0])

            _remove_external_id_from_author(personid_to_test, 'INSPIREID', self.ext_id)

        def test_rabbit_mark_record_as_deleted():
            '''
            A record is deleted. Rabbit should understand that and remove the author from the aidPERSON* tables.
            '''
            number_of_personids_before = get_count_of_pids()
            if config.CFG_BIBAUTHORID_ENABLED:
                self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                      author_name=self.heavily_modified_author_name,
                                                                      ext_id=self.ext_id)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='delete')
            rabbit([self.main_bibrec], verbose=True)
            number_of_personids_after = get_count_of_pids()
            self.assertEquals(number_of_personids_before - 1,
                              number_of_personids_after)

        # Due to the nature of the tests, the order should be preserved.
        test_rabbit_add_new_paper_with_one_author()
        test_rabbit_remove_author_from_paper()
        test_rabbit_add_author_again()
        test_rabbit_slightly_modify_author()
        test_rabbit_heavily_modify_author()
        test_rabbit_claim_record()
        if config.CFG_INSPIRE_SITE:
            test_rabbit_add_inspireID()
        test_rabbit_mark_record_as_deleted()


class CoauthorsRabbitTestCase(BibAuthorIDRabbitTestCase):

    '''
    Rabbit test case with coauthors( otherwise identical to  OneAuthorRabbitTestCase
    '''

    def setUp(self):
        super(CoauthorsRabbitTestCase, self).setUp()
        self.main_marcxml_record = get_new_marc_for_test('Rabbit Test Paper', author_name=self.author_name,
                                                         co_authors_names=self.co_authors_names,
                                                         ext_id=self.ext_id)
        self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record, opt_mode='insert')
        self.main_marcxml_record = add_001_field(self.main_marcxml_record, self.main_bibrec)
        self.bibrecs_to_clean = list()
        self.bibrecs_to_clean.append(self.main_bibrec)

    def test_rabbit_with_coauthors(self):

        def test_rabbit_add_new_paper_with_four_coauthors():
            rabbit([self.main_bibrec], verbose=True)
            self.current_bibref_value_of_author = get_bibref_value_for_name(self.author_name)
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))

            self.current_bibref_values_of_coauthors = list()
            for coauthor_name in self.co_authors_names:
                bibref_value = get_bibref_value_for_name(coauthor_name)
                self.current_bibref_values_of_coauthors.append(bibref_value)
                self.assertTrue(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
                self.assertTrue(person_in_aidpersoniddata(coauthor_name))

        def test_rabbit_remove_coauthors_from_paper():

            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            number_of_personids_after = get_count_of_pids()
            self.assertEquals(number_of_personids_before,
                              number_of_personids_after + 4)

            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))

            for coauthor_name in self.co_authors_names:
                self.assertFalse(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
                self.assertFalse(person_in_aidpersoniddata(coauthor_name))

        def test_rabbit_add_coauthors_again():
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            previous_bibref_value_of_author = self.current_bibref_value_of_author
            self.current_bibref_value_of_author = get_bibref_value_for_name(self.author_name)

            previous_bibrefs_of_coauthors = deepcopy(self.current_bibref_values_of_coauthors)
            for index, _ in enumerate(self.current_bibref_values_of_coauthors):
                self.current_bibref_values_of_coauthors[index] = get_bibref_value_for_name(self.co_authors_names[index])
            number_of_personids_after = get_count_of_pids()

            self.assertEquals(previous_bibref_value_of_author,
                              self.current_bibref_value_of_author)
            self.assertEquals(set(previous_bibrefs_of_coauthors),
                              set(self.current_bibref_values_of_coauthors))
            self.assertEquals(number_of_personids_after,
                              number_of_personids_before + 4)

            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))

            for coauthor_name in self.co_authors_names:
                self.assertTrue(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
                self.assertTrue(person_in_aidpersoniddata(coauthor_name))

        def test_rabbit_slightly_modify_coauthors():
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.slightly_mod_co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            previous_bibref_value_of_author = self.current_bibref_value_of_author
            self.current_bibref_value_of_author = get_bibref_value_for_name(self.author_name)

            previous_bibrefs_of_coauthors = deepcopy(self.current_bibref_values_of_coauthors)
            for index, _ in enumerate(self.current_bibref_values_of_coauthors):
                self.current_bibref_values_of_coauthors[index] = get_bibref_value_for_name(
                    self.slightly_mod_co_authors_names[index])
            number_of_personids_after = get_count_of_pids()
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertEquals(previous_bibref_value_of_author,
                              self.current_bibref_value_of_author)
            self.assertNotEquals(set(previous_bibrefs_of_coauthors),
                                 set(self.current_bibref_values_of_coauthors))
            self.assertEquals(number_of_personids_after,
                              number_of_personids_before)
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))
            for coauthor_name in self.slightly_mod_co_authors_names:
                self.assertTrue(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
            for coauthor_name in self.co_authors_names:
                self.assertTrue(person_in_aidpersoniddata(coauthor_name))

        def test_rabbit_heavily_modify_coauthors():
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.heavily_mod_co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            previous_bibref_value_of_author = self.current_bibref_value_of_author
            previous_bibrefs_of_coauthors = deepcopy(self.current_bibref_values_of_coauthors)
            for index, _ in enumerate(self.current_bibref_values_of_coauthors):
                self.current_bibref_values_of_coauthors[index] = get_bibref_value_for_name(
                    self.heavily_mod_co_authors_names[index])
            number_of_personids_after = get_count_of_pids()
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertEquals(previous_bibref_value_of_author,
                              self.current_bibref_value_of_author)
            self.assertNotEquals(set(previous_bibrefs_of_coauthors),
                                 set(self.current_bibref_values_of_coauthors))
            self.assertEquals(number_of_personids_after,
                              number_of_personids_before)
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))
            for coauthor_name in self.heavily_mod_co_authors_names:
                self.assertTrue(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
                self.assertTrue(person_in_aidpersoniddata(coauthor_name))

        def test_rabbit_claim_record():
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            claim_test_paper(self.main_bibrec)
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.slightly_mod_co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)
            number_of_personids_after = get_count_of_pids()
            self.assertEquals(number_of_personids_before,
                              number_of_personids_after)
            self.assertTrue(is_test_paper_claimed(self.main_bibrec, 700))
            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))
            for coauthor_name in self.slightly_mod_co_authors_names:
                self.assertTrue(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
            for coauthor_name in self.co_authors_names:
                self.assertTrue(person_in_aidpersoniddata(coauthor_name))
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.heavily_mod_co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='replace')
            rabbit([self.main_bibrec], verbose=True)

            self.assertTrue(person_in_aidpersonidpapers(self.author_name, self.main_bibrec))
            self.assertTrue(person_in_aidpersoniddata(self.author_name))
            for coauthor_name in self.heavily_mod_co_authors_names:
                self.assertTrue(person_in_aidpersonidpapers(coauthor_name, self.main_bibrec))
                self.assertTrue(person_in_aidpersoniddata(coauthor_name))
            self.assertFalse(is_test_paper_claimed(self.main_bibrec, 700))


        def test_rabbit_add_inspireID_to_coauthors():
            pass
            # TODO this needs a bit of work

        def test_rabbit_mark_record_as_deleted():
            number_of_personids_before = get_count_of_pids()
            self.main_marcxml_record = get_modified_marc_for_test(self.main_marcxml_record,
                                                                  author_name=self.author_name,
                                                                  co_authors_names=self.heavily_mod_co_authors_names)
            self.main_bibrec = get_bibrec_for_record(self.main_marcxml_record,
                                                     opt_mode='delete')
            rabbit([self.main_bibrec], verbose=True)

            number_of_personids_after = get_count_of_pids()
            self.assertEquals(number_of_personids_before - 5,
                              number_of_personids_after)

        test_rabbit_add_new_paper_with_four_coauthors()
        test_rabbit_remove_coauthors_from_paper()
        test_rabbit_add_coauthors_again()
        test_rabbit_slightly_modify_coauthors()
        test_rabbit_heavily_modify_coauthors()
        test_rabbit_claim_record()
        if config.CFG_INSPIRE_SITE:
            test_rabbit_add_inspireID_to_coauthors()
        test_rabbit_mark_record_as_deleted()


class MatchableNameRabbitTestCase(BibAuthorIDRabbitTestCase):

    '''
    Test that checks that rabbit actually DOES compare by the defined matchable name.
    '''

    def setUp(self):
        super(MatchableNameRabbitTestCase, self).setUp()
        main_marcxml_record = get_new_marc_for_test('Rabbit Test Paper', author_name=self.author_name)
        self.main_bibrec = get_bibrec_for_record(main_marcxml_record, opt_mode='insert')
        self.bibrecs_to_clean = list()
        self.bibrecs_to_clean.append(self.main_bibrec)

    @patch('invenio.bibauthorid_rabbit.create_matchable_name')
    @patch('invenio.bibauthorid_dbinterface.create_matchable_name')
    def test_rabbit_matchable_name(self, mocked_func1, mocked_func2):
        '''
        The return value of the function that creates the matchable name is being mocked.
        With this test we ensure that the function create_matchable_name is actually being used.
        '''
        mocked_func1.return_value = 'Fake Name'
        mocked_func2.return_value = mocked_func1.return_value

        rabbit([self.main_bibrec], verbose=True)

        first_pid = run_sql("select personid from aidPERSONIDPAPERS where bibrec=%s", (self.main_bibrec,))[0][0]

        second_marcxml_record = get_new_marc_for_test('Rabbit Test Paper', author_name=self.heavily_modified_name)
        second_bibrec = get_bibrec_for_record(second_marcxml_record, opt_mode='insert')
        self.bibrecs_to_clean.append(second_bibrec)

        rabbit([second_bibrec], verbose=True)

        second_pid = run_sql("select personid from aidPERSONIDPAPERS where bibrec=%s", (second_bibrec,))[0][0]
        self.assertEquals(first_pid, second_pid)


import invenio.bibauthorid_rabbit


class MnamesCacheConsistencyTestCase(BibAuthorIDRabbitTestCase):

    '''
    Test to ensure that the cache for matchable names and pids works consistenly.
    '''

    def setUp(self):
        super(MnamesCacheConsistencyTestCase, self).setUp()
        main_marcxml_record = get_new_marc_for_test('Rabbit Test Paper', author_name=self.author_name)
        self.main_bibrec = get_bibrec_for_record(main_marcxml_record, opt_mode='insert')
        self.bibrecs_to_clean = list()
        self.bibrecs_to_clean.append(self.main_bibrec)

    @patch('invenio.bibauthorid_rabbit.destroy_mnames_pids_cache')
    @patch('invenio.bibauthorid_rabbit.get_authors_by_name')
    def test_m_names_cache(self, mocked_func, mocked_destroy):
        '''
        For this test we check whether a value is in the cache.
        '''

        def do_nothing():
            '''
            A function that does nothing. It substitutes the destroy_mnames_pids_cache,
            so that we can actually take a snapshot of the cache for our test.
            '''
            pass

        mocked_func.return_value = [9999]
        mocked_destroy.side_effect = do_nothing()
        rabbit([self.main_bibrec], verbose=True)
        m_name = create_matchable_name(self.author_name)
        self.assertTrue(invenio.bibauthorid_rabbit.M_NAME_PIDS_CACHE[m_name])


class MnamesFunctionsTest(BibAuthorIDRabbitTestCase):

    '''
    Test to understand whether the functions that are called to transform
    name to matchable names are functioning correctly.
    '''

    def setUp(self):
        super(MnamesFunctionsTest, self).setUp()
        main_marcxml_record = get_new_marc_for_test('Rabbit Test Paper', author_name=self.author_name)
        self.main_bibrec = get_bibrec_for_record(main_marcxml_record,
                                                 opt_mode='insert')
        self.bibrecs_to_clean = list()
        self.bibrecs_to_clean.append(self.main_bibrec)

    def test_m_names_transformations(self):
        '''
        In this test we define three functions and then use them
        as the functions that generate mnames.
        '''

        def m_name_func_1(name):
            m_name_func_1.has_been_called = True
            return invenio.bibauthorid_rabbit.M_NAME_FUNCTIONS[0](name)

        m_name_func_1.has_been_called = False

        def m_name_func_2(name):
            m_name_func_2.has_been_called = True
            return invenio.bibauthorid_rabbit.M_NAME_FUNCTIONS[0](name)

        m_name_func_2.has_been_called = False

        invenio.bibauthorid_rabbit.M_NAME_FUNCTIONS[1:] = [m_name_func_1,
                                                           m_name_func_2]
        rabbit([self.main_bibrec], verbose=True)
        self.assertTrue(m_name_func_1.has_been_called)
        self.assertTrue(m_name_func_2.has_been_called)

TEST_SUITE = make_test_suite(BibAuthorIDRabbitTestCase,
                             OneAuthorRabbitTestCase,
                             CoauthorsRabbitTestCase,
                             MatchableNameRabbitTestCase,
                             MnamesCacheConsistencyTestCase,
                             MnamesFunctionsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=False)
