# -*- coding:utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
"""bibindex_engine_tokenizer_tests - regression tests for tokenizers
"""

from datetime import datetime
from invenio.testutils import (
    InvenioTestCase, make_test_suite, run_test_suite, nottest
)
from invenio.bibindex_tokenizers.BibIndexAbstractParentTokenizer import (
    BibIndexAbstractParentTokenizer, get_recids_by_field_values
)
from invenio.bibindex_tokenizers.BibIndexParentAuthorTokenizer import (
    BibIndexParentAuthorTokenizer,
)
from invenio.bibindex_tokenizers.BibIndexExactParentAuthorTokenizer import (
    BibIndexExactParentAuthorTokenizer,
)
from invenio.bibindex_tokenizers.BibIndexCanonicalAuthorTokenizer import (
    BibIndexCanonicalAuthorTokenizer,
)
from invenio.bibindex_tokenizers.BibIndexParentCanonicalAuthorTokenizer import (
    BibIndexParentCanonicalAuthorTokenizer,
)
from invenio.bibindex_engine_config import CFG_BIBINDEX_INDEX_TABLE_TYPE
from invenio.intbitset import intbitset
from invenio.dbquery import run_sql


@nottest
def simulate_record_modification(recid, date):
    run_sql(
        """
        INSERT INTO hstRECORD
            (id_bibrec, marcxml, job_id, job_name, job_person,
                job_date, job_details, affected_fields)
        VALUES
            (%s,'',1,'__bibindex_tokenizer_regression_tests__','UNKNOWN',
                %s,'','')
        """,
        (recid, date)
    )


@nottest
def delete_simulated_record_modifications():
    run_sql("""
        DELETE FROM hstRECORD
        WHERE job_name = '__bibindex_tokenizer_regression_tests__'
    """)


class TestAbstractParentTokenizer(InvenioTestCase):

    """Test AbstractParentTokenizer"""

    @classmethod
    def setUp(self):
        self.tokenizer = BibIndexAbstractParentTokenizer()

    def test_get_parent_recids(self):
        """TestAbstractParentTokenizer - testing get_parent_recids"""
        test_pairs = [
            (1, []),
            (2, []),
            (3, []),
            (10, []),
            (20, []),
            (30, []),
            (40, []),
            (141, []),
            (142, [10]),
            (143, [20]),
            (144, [30]),
            (145, [40])
        ]

        for input_recids, expected_output in test_pairs:
            output = self.tokenizer.get_parent_recids(input_recids)
            self.assertEqual(
                expected_output,
                output,
                "get_parent_recids(%s): received %s instead of %s"
                % (input_recids, output, expected_output)
            )

    def test_get_modified_recids(self):
        """TestAbstractParentTokenizer - testing get_modified_recids"""
        test_pairs = [
            # Test no modification
            ([], []),
            # Test modification of some records
            ([1], [1]),
            ([2], [2]),
            ([3], [3]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 3, 4], [2, 3, 4]),
            ([3, 4, 5], [3, 4, 5]),
            ([10, 21, 32], [10, 21, 32]),
            ([20, 31, 42], [20, 31, 42]),
            ([30, 41, 52], [30, 41, 52])
        ]
        modification_date = datetime(3000, 2, 1)
        modification_range = (datetime(3000, 1, 1), None)

        for input_recids, expected_output in test_pairs:
            for recid in input_recids:
                simulate_record_modification(recid, modification_date)

            output = sorted(self.tokenizer.get_modified_recids(
                modification_range,
                '__fake_index_name__'
            ))
            delete_simulated_record_modifications()

            self.assertEqual(
                expected_output,
                output,
                "get_modified_recids(): received %s instead of %s"
                % (output, expected_output)
            )

    def test_get_dependent_recids(self):
        """TestAbstractParentTokenizer - testing get_dependent_recids"""
        test_pairs = [
            # Test no record
            ([], []),
            # Test "non child", "non parent" records
            ([1], [1]),
            ([2], [2]),
            ([3], [3]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 3, 4], [2, 3, 4]),
            ([3, 4, 5], [3, 4, 5]),
            ([11, 22, 33], [11, 22, 33]),
            ([21, 32, 43], [21, 32, 43]),
            ([31, 42, 53], [31, 42, 53]),
            # Test "child" records
            ([142], [142]),
            ([143], [143]),
            ([144], [144]),
            ([145], [145]),
            # Test "parent" records
            ([10], [10, 142]),
            ([20], [20, 143]),
            ([30], [30, 144]),
            ([40], [40, 145])
        ]

        for input_recids, expected_output in test_pairs:
            output = sorted(self.tokenizer.get_dependent_recids(
                intbitset(input_recids),
                '__fake_index_name__'
            ))
            self.assertEqual(
                expected_output,
                output,
                "get_dependent_recids(%s): received %s instead of %s"
                % (input_recids, output, expected_output)
            )

    def test_get_recids_by_field_values(self):
        """TestAbstractParentTokenizer - testing function get_recids_by_field_values"""
        test_pairs = [
            # Test no record
            ([], []),
            # Test records without dependent records
            ([1], []),
            ([2], []),
            ([3], []),
            ([1, 2, 3], []),
            ([2, 3, 4], []),
            ([3, 4, 5], []),
            ([11, 22, 33], []),
            ([21, 32, 43], []),
            ([31, 42, 53], []),
            # Test records with dependent records
            ([10], [142]),
            ([20], [143]),
            ([30], [144]),
            ([40], [145])
        ]

        for input_recids, expected_output in test_pairs:
            output = sorted(get_recids_by_field_values(
                self.tokenizer.parent_tag,
                input_recids
            ))
            self.assertEqual(
                expected_output,
                output,
                "get_recids_by_field_values('%s', %s): received %s instead of %s"
                % (self.tokenizer.parent_tag, input_recids, output, expected_output)
            )


class TestParentAuthorTokenizer(InvenioTestCase):

    """Test BibIndexParentAuthorTokenizer"""

    @classmethod
    def setUp(self):
        self.tokenizer = BibIndexParentAuthorTokenizer()

    def test_tokenize_phrases_10(self):
        """TestParentAuthorTokenizer - testing tokenize for phrases record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 10
        output = self.tokenizer.tokenize(input_recid, table_type)
        # The list must be empty because record 10 has no "parent records":
        # it is not a dataset used in other records (and it has no 786__w tag)
        self.assertEqual([], output)

    def test_tokenize_words_10(self):
        """TestParentAuthorTokenizer - testing tokenize for words record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 10
        output = self.tokenizer.tokenize(input_recid, table_type)
        # The list must be empty because record 10 has no "parent records":
        # it is not a dataset used in other records (and it has no 786__w tag)
        self.assertEqual([], output)

    def test_tokenize_phrases_142(self):
        """TestParentAuthorTokenizer - testing tokenize for phrases record 142
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 142
        output = self.tokenizer.tokenize(input_recid, table_type)

        self.assertEqual(974, len(output))
        # Test just a few phrases
        self.assertIn("G Ellis", output)
        self.assertIn("Ellis, G", output)
        self.assertIn("M Martinez", output)
        self.assertIn("Martinez, M", output)
        self.assertIn("P Laurelli", output)
        self.assertIn("Laurelli, P", output)

    def test_tokenize_words_142(self):
        """TestParentAuthorTokenizer - testing tokenize for words record 142
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 142
        output = self.tokenizer.tokenize(input_recid, table_type)

        self.assertEqual(344, len(output))
        # Test just a few of words
        self.assertIn("g", output)
        self.assertIn("ellis", output)
        self.assertIn("m", output)
        self.assertIn("martinez", output)
        self.assertIn("p", output)
        self.assertIn("laurelli", output)

    def test_get_modified_recids(self):
        """TestParentAuthorTokenizer - testing get_modified_recids"""
        test_pairs = [
            # Test no modification
            ([], []),
            # Test modification of "non parent" records
            ([1], [1]),
            ([2], [2]),
            ([3], [3]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 3, 4], [2, 3, 4]),
            ([3, 4, 5], [3, 4, 5]),
            ([11, 22, 33], [11, 22, 33]),
            ([21, 32, 43], [21, 32, 43]),
            ([31, 42, 53], [31, 42, 53]),
            # Test modification of "child" records
            ([142], [142]),
            ([143], [143]),
            ([144], [144]),
            ([145], [145]),
            # Test modification of "parent" records
            ([10], [10]),
            ([20], [20]),
            ([30], [30]),
            ([40], [40])
        ]
        modification_date = datetime(3000, 2, 1)
        modification_range = (datetime(3000, 1, 1), None)

        for input_recid, expected_output in test_pairs:
            for recid in input_recid:
                simulate_record_modification(recid, modification_date)
            output = sorted(self.tokenizer.get_modified_recids(
                modification_range,
                '__fake_index_name__'
            ))
            delete_simulated_record_modifications()
            self.assertEqual(
                expected_output,
                output,
                "get_modified_recids(): received %s instead of %s"
                % (output, expected_output)
            )

    def test_get_dependent_recids(self):
        """TestParentAuthorTokenizer - testing get_dependent_recids"""
        test_pairs = [
            # Test no record
            ([], []),
            # Test "non child", "non parent" records
            ([1], [1]),
            ([2], [2]),
            ([3], [3]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 3, 4], [2, 3, 4]),
            ([3, 4, 5], [3, 4, 5]),
            ([11, 22, 33], [11, 22, 33]),
            ([21, 32, 43], [21, 32, 43]),
            ([31, 42, 53], [31, 42, 53]),
            # Test "child" records
            ([142], [142]),
            ([143], [143]),
            ([144], [144]),
            ([145], [145]),
            # Test "parent" records
            ([10], [10, 142]),
            ([20], [20, 143]),
            ([30], [30, 144]),
            ([40], [40, 145])
        ]

        for input_recids, expected_output in test_pairs:
            output = sorted(self.tokenizer.get_dependent_recids(
                intbitset(input_recids),
                '__fake_index_name__'
            ))
            self.assertEqual(
                expected_output,
                output,
                "get_dependent_recids(%s): received %s instead of %s"
                % (input_recids, output, expected_output)
            )


class TestExactParentAuthorTokenizer(InvenioTestCase):

    """Test BibIndexExactParentAuthorTokenizer"""

    @classmethod
    def setUp(self):
        self.tokenizer = BibIndexExactParentAuthorTokenizer()

    def test_tokenize_phrases_10(self):
        """TestExactParentAuthorTokenizer - testing tokenize for phrases record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 10
        output = self.tokenizer.tokenize(input_recid, table_type)
        # The list must be empty because record 10 has no "parent records":
        # it is not a dataset used in other records (and it has no 786__w tag)
        self.assertEqual([], output)

    def test_tokenize_words_10(self):
        """TestExactParentAuthorTokenizer - testing tokenize for words record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 10
        output = self.tokenizer.tokenize(input_recid, table_type)
        # The list must be empty because record 10 has no "parent records":
        # it is not a dataset used in other records (and it has no 786__w tag)
        self.assertEqual([], output)

    def test_tokenize_phrases_142(self):
        """TestExactParentAuthorTokenizer - testing tokenize for phrases record 142
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 142
        output = self.tokenizer.tokenize(input_recid, table_type)

        self.assertEqual(315, len(output))
        # Test just a few phrases
        self.assertIn("O'Shea, V", output)
        self.assertIn("Awunor, O", output)
        self.assertIn("Armstrong, S R", output)
        self.assertIn("Nuzzo, S", output)
        self.assertIn("Renk, B", output)
        self.assertIn("Rothberg, J E", output)

    def test_tokenize_words_142(self):
        """TestExactParentAuthorTokenizer - testing tokenize for words record 142
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 142
        output = self.tokenizer.tokenize(input_recid, table_type)

        self.assertEqual(344, len(output))
        # Test just a few words
        self.assertIn("machefert", output)
        self.assertIn("tilquin", output)
        self.assertIn("pascolo", output)
        self.assertIn("martinez", output)
        self.assertIn("jost", output)
        self.assertIn("laurelli", output)

    def test_get_modified_recids(self):
        """TestExactParentAuthorTokenizer - testing get_modified_recids"""
        test_pairs = [
            # Test no modification
            ([], []),
            # Test modification of "non parent" records
            ([1], [1]),
            ([2], [2]),
            ([3], [3]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 3, 4], [2, 3, 4]),
            ([3, 4, 5], [3, 4, 5]),
            ([11, 22, 33], [11, 22, 33]),
            ([21, 32, 43], [21, 32, 43]),
            ([31, 42, 53], [31, 42, 53]),
            # Test modification of "child" records
            ([142], [142]),
            ([143], [143]),
            ([144], [144]),
            ([145], [145]),
            # Test modification of "parent" records
            ([10], [10]),
            ([20], [20]),
            ([30], [30]),
            ([40], [40])
        ]
        modification_date = datetime(3000, 2, 1)
        modification_range = (datetime(3000, 1, 1), None)

        for input_recid, expected_output in test_pairs:
            for recid in input_recid:
                simulate_record_modification(recid, modification_date)
            output = sorted(self.tokenizer.get_modified_recids(
                modification_range,
                '__fake_index_name__'
            ))
            delete_simulated_record_modifications()
            self.assertEqual(
                expected_output,
                output,
                "get_modified_recids(): received %s instead of %s"
                % (output, expected_output)
            )

    def test_get_dependent_recids(self):
        """TestExactParentAuthorTokenizer - testing get_dependent_recids"""
        test_pairs = [
            # Test no record
            ([], []),
            # Test "non child", "non parent" records
            ([1], [1]),
            ([2], [2]),
            ([3], [3]),
            ([1, 2, 3], [1, 2, 3]),
            ([2, 3, 4], [2, 3, 4]),
            ([3, 4, 5], [3, 4, 5]),
            ([11, 22, 33], [11, 22, 33]),
            ([21, 32, 43], [21, 32, 43]),
            ([31, 42, 53], [31, 42, 53]),
            # Test "child" records
            ([142], [142]),
            ([143], [143]),
            ([144], [144]),
            ([145], [145]),
            # Test "parent" records
            ([10], [10, 142]),
            ([20], [20, 143]),
            ([30], [30, 144]),
            ([40], [40, 145])
        ]

        for input_recids, expected_output in test_pairs:
            output = sorted(self.tokenizer.get_dependent_recids(
                intbitset(input_recids),
                '__fake_index_name__'
            ))
            self.assertEqual(
                expected_output,
                output,
                "get_dependent_recids(%s): received %s instead of %s"
                % (input_recids, output, expected_output)
            )


class TestCanonicalAuthorTokenizer(InvenioTestCase):

    """Test BibIndexCanonicalAuthorTokenizer"""

    @classmethod
    def setUp(self):
        self.tokenizer = BibIndexCanonicalAuthorTokenizer()

    def test_tokenize_phrases_10(self):
        """TestCanonicalAuthorTokenizer - test tokenize for phrases record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 10
        tokenize = self.tokenizer.get_tokenizing_function(table_type)
        output = tokenize(input_recid)

        self.assertEqual(315, len(output))
        # Test just a few phrases
        self.assertIn("G.Ellis.1", output)
        self.assertIn("H.G.Sander.1", output)
        self.assertIn("G.Leibenguth.1", output)

    def test_tokenize_words_10(self):
        """TestCanonicalAuthorTokenizer - test tokenize for words record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 10
        tokenize = self.tokenizer.get_tokenizing_function(table_type)
        output = tokenize(input_recid)

        self.assertEqual(315, len(output))
        # Test just a few phrases
        self.assertIn("G.Ellis.1", output)
        self.assertIn("H.G.Sander.1", output)
        self.assertIn("G.Leibenguth.1", output)

    def test_tokenize_phrases_30(self):
        """TestCanonicalAuthorTokenizer - test tokenize for phrases record 30
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 30
        tokenize = self.tokenizer.get_tokenizing_function(table_type)
        output = tokenize(input_recid)

        self.assertEqual(sorted(output), ['P.Pipe.1', 'R.J.Hughes.1'])

    def test_tokenize_words_30(self):
        """TestCanonicalAuthorTokenizer - test tokenize for words record 30
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 30
        tokenize = self.tokenizer.get_tokenizing_function(table_type)
        output = tokenize(input_recid)

        self.assertEqual(sorted(output), ['P.Pipe.1', 'R.J.Hughes.1'])


class TestParentCanonicalAuthorTokenizer(InvenioTestCase):

    """Test BibIndexParentCanonicalAuthorTokenizer"""

    @classmethod
    def setUp(self):
        self.tokenizer = BibIndexParentCanonicalAuthorTokenizer()

    def test_tokenize_phrases_10(self):
        """TestParentCanonicalAuthorTokenizer - testing tokenize for phrases record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 10
        output = self.tokenizer.tokenize(input_recid, table_type)
        # The list must be empty because record 10 has no "parent records":
        # it is not a dataset used in other records (and it has no 786__w tag)
        self.assertEqual([], output)

    def test_tokenize_words_10(self):
        """TestParentCanonicalAuthorTokenizer - testing tokenize for words record 10
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 10
        output = self.tokenizer.tokenize(input_recid, table_type)
        # The list must be empty because record 10 has no "parent records":
        # it is not a dataset used in other records (and it has no 786__w tag)
        self.assertEqual([], output)

    def test_tokenize_phrases_142(self):
        """TestParentCanonicalAuthorTokenizer - testing tokenize for phrases record 142
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]
        input_recid = 142
        output = self.tokenizer.tokenize(input_recid, table_type)

        self.assertEqual(315, len(output))
        # Test just a few phrases
        self.assertIn("G.Ellis.1", output)
        self.assertIn("H.G.Sander.1", output)
        self.assertIn("G.Leibenguth.1", output)

    def test_tokenize_words_142(self):
        """TestParentCanonicalAuthorTokenizer - testing tokenize for words record 142
        """
        table_type = CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]
        input_recid = 142
        output = self.tokenizer.tokenize(input_recid, table_type)

        self.assertEqual(315, len(output))
        # Test just a few words
        self.assertIn("G.Ellis.1", output)
        self.assertIn("H.G.Sander.1", output)
        self.assertIn("G.Leibenguth.1", output)


TEST_SUITE = make_test_suite(TestAbstractParentTokenizer,
                             TestParentAuthorTokenizer,
                             TestExactParentAuthorTokenizer,
                             TestCanonicalAuthorTokenizer,
                             TestParentCanonicalAuthorTokenizer,)

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
