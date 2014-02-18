# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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

"""Unit tests for the citation indexer."""

from invenio.testutils import InvenioTestCase
import ConfigParser
import logging
import sys

from invenio.testutils import make_test_suite, run_test_suite
from invenio.config import CFG_ETCDIR
from invenio.dbquery import run_sql


def load_config():
    config_path = CFG_ETCDIR + "/bibrank/citation.cfg"
    config = ConfigParser.ConfigParser()
    config.readfp(open(config_path))
    return config

CONFIG = load_config()

EXPECTED_DICTS = {
    'refs': {77: [95], 79: [78], 80: [94], 82: [81], 83: [81], 85: [77, 84], 86: [77, 95], 87: [81], 88: [84], 89: [81], 91: [78, 79, 84], 92: [74, 91], 96: [18]},
    'cites': {18: [96], 74: [92], 77: [85, 86], 78: [79, 91], 79: [91], 81: [82, 83, 87, 89], 84: [85, 88, 91], 91: [92], 94: [80], 95: [77, 86]},
}


def compare_dicts(tester, dic, expected):
    # Clean out empty sets
    for k, v in dic.items():
        if not v:
            del dic[k]

    dic = dict([(k, sorted(list(v))) for k, v in dic.iteritems()])
    tester.assertEqual(dic, expected)


def remove_from_dicts(dicts, recid):
    for recid in dicts['cites'].keys():
        try:
            dicts['cites'][recid].remove(recid)
            dicts['cites_weight'] -= 1
        except ValueError:
            pass
        else:
            if not dicts['cites'][recid]:
                del dicts['cites'][recid]
                del dicts['cites_weight'][recid]

    for recid in dicts['refs'].keys():
        try:
            dicts['refs'][recid].remove(recid)
        except ValueError:
            pass
        else:
            if not dicts['refs'][recid]:
                del dicts['refs'][recid]


class TestCitationIndexer(InvenioTestCase):
    """Testing citation indexer."""
    def setUp(self):
        logger = logging.getLogger()
        for handler in logger.handlers:
            logger.removeHandler(handler)

        formatter = logging.Formatter('%(asctime)s --> %(message)s', '%Y-%m-%d %H:%M:%S')

        stdout_logger = logging.StreamHandler(sys.stdout)
        stdout_logger.setFormatter(formatter)
        # stdout_logger.setLevel(logging.DEBUG)
        stdout_logger.setLevel(logging.CRITICAL)
        stderr_logger = logging.StreamHandler(sys.stderr)
        stderr_logger.setFormatter(formatter)
        # stderr_logger.setLevel(logging.WARNING)
        stderr_logger.setLevel(logging.CRITICAL)
        logger.addHandler(stderr_logger)
        logger.addHandler(stdout_logger)
        logger.setLevel(logging.INFO)

    def test_basic(self):
        from invenio.bibrank_citation_indexer import process_chunk
        cites, refs = process_chunk(range(1, 100), CONFIG)
        compare_dicts(self, cites, EXPECTED_DICTS['cites'])
        compare_dicts(self, refs, EXPECTED_DICTS['refs'])

    def test_adding_record(self):
        "tests adding a record"
        from invenio.bibrank_citation_indexer import process_chunk
        cites, refs = process_chunk([92], CONFIG)
        expected_cites = {}
        compare_dicts(self, cites, expected_cites)
        expected_refs = {92: [74, 91]}
        compare_dicts(self, refs, expected_refs)

    def test_catchup(self):
        "tests adding a record (with catchup)"
        from invenio.bibrank_citation_indexer import process_chunk
        cites, refs = process_chunk([95], CONFIG)

        expected_cites = {95: [77, 86]}
        compare_dicts(self, cites, expected_cites)
        expected_refs = {}
        compare_dicts(self, refs, expected_refs)

    def test_db_adding_and_removing_records(self):
        from invenio.bibrank_citation_searcher import get_cited_by
        from invenio.bibrank_citation_indexer import store_dicts
        store_dicts([42222],
                    refs={42222: set([43333])},
                    cites={42222: set([40000, 40001])})
        cited_by_42222 = get_cited_by(42222)
        cited_by_43333 = get_cited_by(43333)
        store_dicts([42222],
                    refs={42222: set()},
                    cites={42222: set()})
        self.assertEqual(cited_by_42222, set([40000, 40001]))
        self.assertEqual(cited_by_43333, set([42222]))
        self.assertEqual(get_cited_by(42222), set())
        self.assertEqual(get_cited_by(43333), set())


class TestCitationIndexerWarnings(InvenioTestCase):
    def cleanup(self):
        run_sql("""DELETE FROM rnkCITATIONDATAERR
                   WHERE citinfo LIKE 'Test Ref %'""")

    def count(self):
        return run_sql("SELECT COUNT(*) FROM rnkCITATIONDATAERR")[0][0]

    def test_insert(self):
        from invenio.bibrank_citation_indexer import store_citation_warning
        self.cleanup()
        before = self.count()
        store_citation_warning('multiple-matches', 'Test Ref 1')
        store_citation_warning('not-well-formed', 'Test Ref 2')
        after = self.count()
        self.assertEqual(after - before, 2)
        store_citation_warning('not-well-formed', 'Test Ref 2')
        after2 = self.count()
        self.assertEqual(after2 - before, 2)
        self.cleanup()



class TestCitationLosses(unittest.TestCase):
    def test_abort_cites(self):
        from invenio.bibrank_citation_indexer import check_citations_losses
        # Hack for tests, the config is a pseudo dictionary.
        # check_citations_losses will look for citation_loss_per_record_limit
        # in the real config object.
        fake_config = {'rank_method': 'citation', 'citation': 2}
        try:
            check_citations_losses(fake_config,
                                   recids=[1, 2, 81],
                                   refs={1: set([]), 2: set([]), 81: set([])},
                                   cites={1: set([]), 2: set([]), 81: set([])})
        except Exception as e:  # pylint: disable=W0703
            if 'Lost too many references' not in str(e):
                raise
        else:
            self.fail()

    def test_abort_refs(self):
        from invenio.bibrank_citation_indexer import check_citations_losses
        # Hack for tests, the config is a pseudo dictionary.
        # check_citations_losses will look for citation_loss_per_record_limit
        # in the real config object.
        fake_config = {'rank_method': 'citation', 'citation': 2}
        try:
            check_citations_losses(fake_config,
                                   recids=[1, 2, 91],
                                   refs={1: set([]), 2: set([]), 91: set([])},
                                   cites={1: set([]), 2: set([]), 91: set([])})
        except Exception as e:  # pylint: disable=W0703
            if 'Lost too many references' not in str(e):
                raise
        else:
            self.fail()

    def test_no_abort(self):
        from invenio.bibrank_citation_indexer import check_citations_losses
        check_citations_losses(CONFIG, [1, 2, 81], {1: set([]), 2: set([]), 81: set([])}, {1: set([]), 2: set([]), 81: set([])})


TEST_SUITE = make_test_suite(TestCitationIndexer,
                             TestCitationIndexerWarnings,
                             TestCitationLosses)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
