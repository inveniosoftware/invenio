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

from invenio.testutils import InvenioTestCase
from datetime import datetime

from invenio.testutils import make_test_suite, run_test_suite
from invenio.intbitset import intbitset
from invenio.dbquery import run_sql
from invenio.docextract_task import fetch_last_updated, store_last_updated
from invenio.bibauthorid_affiliations import (process_affiliations,
                                              process_chunk,
                                              get_current_aff)

EXPECTED_AFF = {512L: {'aff': [u'Comenius University'], 'last_recid': 59}, 588L: {'aff': [u'New York University'], 'last_recid': 89}, 514L: {'aff': [u'California State University'], 'last_recid': 60}, 516L: {'aff': [u'Northwest University, China'], 'last_recid': 61}, 598L: {'aff': [u'Princeton University'], 'last_recid': 94}, 519L: {'aff': [u'Los Alamos Sci. Lab.'], 'last_recid': 62}, 520L: {'aff': [u'The University of Melbourne'], 'last_recid': 63}, 522L: {'aff': [u'Aichi Shukutoku Univ'], 'last_recid': 64}, 12L: {'aff': [u'Cambridge University'], 'last_recid': 8}, 527L: {'aff': [u'University of Athens'], 'last_recid': 66}, 17L: {'aff': [u'CERN'], 'last_recid': 18}, 530L: {'aff': [u'University of British Columbia'], 'last_recid': 67}, 531L: {'aff': [u'Princeton University'], 'last_recid': 68}, 533L: {'aff': [u'Institut fur Physic, Universitat Mainz'], 'last_recid': 69}, 542L: {'aff': [u'National University of Singapore'], 'last_recid': 70}, 34L: {'aff': [u'Aachen, Tech. Hochsch.'], 'last_recid': 10}, 549L: {'aff': [u'KEK'], 'last_recid': 71}, 559L: {'aff': [u'University of Osijek'], 'last_recid': 72}, 561L: {'aff': [u'Uppsala University'], 'last_recid': 73}, 499L: {'aff': [u'University of Coimbra'], 'last_recid': 54}, 567L: {'aff': [u'Princeton University'], 'last_recid': 77}, 568L: {'aff': [u'Princeton University'], 'last_recid': 95}, 569L: {'aff': [u'INFN', u'Universita di Napoli'], 'last_recid': 78}, 570L: {'aff': [u'University of London'], 'last_recid': 79}, 571L: {'aff': [u'Brown University'], 'last_recid': 80}, 572L: {'aff': [u'Stanford University'], 'last_recid': 81}, 447L: {'aff': [u'CERN'], 'last_recid': 17}, 578L: {'aff': [u'INFN'], 'last_recid': 83}, 579L: {'aff': [u'Princeton University'], 'last_recid': 84}, 580L: {'aff': [u'INFN', u'Universita di Milano-Bicocca'], 'last_recid': 85}, 584L: {'aff': [u'Kyoto University'], 'last_recid': 86}, 457L: {'aff': [u'Stanford University'], 'last_recid': 19}, 586L: {'aff': [u'Lebedev Physics Institute'], 'last_recid': 87}, 459L: {'aff': [u'University of Jyvaskyla'], 'last_recid': 20}, 460L: {'aff': [u'University College London'], 'last_recid': 21}, 462L: {'aff': [u'MIT'], 'last_recid': 22}, 335L: {'aff': [u'Cambridge University'], 'last_recid': 11}, 594L: {'aff': [u'National Technical University of Athens'], 'last_recid': 92}, 483L: {'aff': [u'Minnesota Univ.'], 'last_recid': 47}, 468L: {'aff': [u'University of Wisconsin'], 'last_recid': 29}, 590L: {'aff': [u'LPTHE'], 'last_recid': 90}, 563L: {'aff': [u'Fudan University'], 'last_recid': 74}, 471L: {'aff': [u'Indiana University'], 'last_recid': 31}, 591L: {'aff': [u'DESY'], 'last_recid': 91}, 475L: {'aff': [u'L D Landau Institute for Theoretical Physics of Russian Academy of Sciences'], 'last_recid': 43}, 477L: {'aff': [u'CERN'], 'last_recid': 44}, 479L: {'aff': [u'King Fadh University'], 'last_recid': 45}, 480L: {'aff': [u'Columbia Univ.'], 'last_recid': 46}, 587L: {'aff': [u'Princeton University'], 'last_recid': 88}, 355L: {'aff': [u'CERN'], 'last_recid': 12}, 356L: {'aff': [u'Brookhaven Nat. Lab.'], 'last_recid': 13}, 614L: {'aff': [u'Gaziantep U.'], 'last_recid': 108}, 486L: {'aff': [u'CFIF'], 'last_recid': 48}, 359L: {'aff': [u'Delhi University'], 'last_recid': 15}, 488L: {'aff': [u'University of New South Wales'], 'last_recid': 49}, 490L: {'aff': [u'Universite Blaise Pascal'], 'last_recid': 50}, 615L: {'aff': [u'Gaziantep U.'], 'last_recid': 108}, 493L: {'aff': [u'FCIF'], 'last_recid': 51}, 366L: {'aff': [u'Washington U. Seattle'], 'last_recid': 16}, 496L: {'aff': [u'Univ. Dortmund'], 'last_recid': 53}, 616L: {'aff': [u'Gaziantep U.'], 'last_recid': 108}, 467L: {'aff': [u'Bell Teleph Labs'], 'last_recid': 28}, 501L: {'aff': [u'CERN'], 'last_recid': 55}, 596L: {'aff': [u'The Pennsylvania State University'], 'last_recid': 93}, 503L: {'aff': [u'Yale University'], 'last_recid': 56}, 575L: {'aff': [u'The Weizmann Inst. of Science'], 'last_recid': 82}, 506L: {'aff': [u'University of California, Berkeley'], 'last_recid': 57}, 507L: {'aff': [u'University of California, Berkeley'], 'last_recid': 58}, 524L: {'aff': [u'Institute of Nuclear Physics, Cracow, Poland'], 'last_recid': 65}}


def compare_aff_dicts(test, aff, expected):
    for pid, aff_info in aff.iteritems():
        test.assertEqual((pid, aff_info), (pid, expected[pid]))
    test.assertEqual(sorted(aff.keys()), sorted(expected.keys()))



class TaskTests(InvenioTestCase):
    def setUp(self):
        run_sql("TRUNCATE aidAFFILIATIONS")

    @classmethod
    def tearDownClass(cls):
        run_sql("TRUNCATE aidAFFILIATIONS")
        process_affiliations(all_records=True)

    def test_all_records(self):
        all_recids = intbitset(run_sql("SELECT id FROM bibrec"))
        aff = process_chunk(all_recids)
        for value in aff.itervalues():
            del value['last_occurence']
        compare_aff_dicts(self, aff, EXPECTED_AFF)

    def test_get_current_aff(self):
        process_affiliations(all_records=True)
        pids = intbitset(run_sql("SELECT personid FROM aidPERSONIDDATA where tag = 'canonical_name'"))
        aff = get_current_aff(pids)
        for value in aff.itervalues():
            del value['last_occurence']
        compare_aff_dicts(self, aff, EXPECTED_AFF)

    def test_latest_records(self):
        name = 'affiliations'
        dummy_last_recid, last_date = fetch_last_updated(name)
        run_sql('UPDATE xtrJOB SET last_updated = %s WHERE name = %s', (datetime(year=1900, month=1, day=1), name))
        process_affiliations()
        pids = intbitset(run_sql("SELECT personid FROM aidPERSONIDDATA where tag = 'canonical_name'"))
        aff = get_current_aff(pids)
        for value in aff.itervalues():
            del value['last_occurence']
        compare_aff_dicts(self, aff, EXPECTED_AFF)
        run_sql("TRUNCATE aidAFFILIATIONS")
        self.assertEqual(get_current_aff(pids), {})
        store_last_updated(None, last_date, name)

    def test_process_affiliations(self):
        recid = 108
        process_affiliations([recid])
        rows = run_sql("SELECT personid, affiliation, last_recid FROM aidAFFILIATIONS ORDER BY personid")
        self.assertEqual(rows, ((614L, 'Gaziantep U.', 108),
                                (615L, 'Gaziantep U.', 108),
                                (616L, 'Gaziantep U.', 108)))

    def test_adding_author(self):
        recid = 65
        pid = 524
        process_affiliations([recid])
        run_sql("DELETE FROM aidAFFILIATIONS WHERE personid = %s", [pid])
        process_affiliations([recid])
        rows = run_sql("SELECT personid, affiliation, last_recid FROM aidAFFILIATIONS ORDER BY personid")
        self.assertEqual(rows, ((524L, 'Institute of Nuclear Physics, Cracow, Poland', 65),))

    def test_removing_recompute_author(self):
        recid = 1
        run_sql("""INSERT INTO aidAFFILIATIONS (personid, affiliation, last_recid, last_occurence)
                   VALUES (%s,%s,%s,%s)""", (524, 'Hello', 1, datetime.now()))
        process_affiliations([recid])
        rows = run_sql("SELECT personid, affiliation, last_recid FROM aidAFFILIATIONS ORDER BY personid")
        self.assertEqual(rows, ((524L, 'Institute of Nuclear Physics, Cracow, Poland', 65),))


TEST_SUITE = make_test_suite(TaskTests)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
