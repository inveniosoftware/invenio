# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

""" Test unit for the miscutil/sequtils module. """

from invenio.testutils import InvenioTestCase
try:
    from mock import patch
    HAS_MOCK = True
except ImportError:
    HAS_MOCK = False

from invenio.testutils import make_test_suite, run_test_suite
from invenio.dbquery import run_sql

from invenio.sequtils import SequenceGenerator
from invenio.sequtils_texkey import TexkeySeq, TexkeyNoAuthorError, \
                                    task_run_core


def get_bibrecord_mock(_):
    return {'001': [([], ' ', ' ', '1086086', 1)],
            '111': [([('a',
            'Mock conference'),
            ('d', '14-16 Sep 2011'),
            ('x', '2050-09-14'),
            ('c', 'xxxxx')],
            ' ',
            ' ',
            '',
            3)],
            '270': [([('m', 'dummy@dummy.com')], ' ', ' ', '', 5)],
            '856': [([('u', 'http://dummy.com/')], '4', ' ', '', 6)],
            '970': [([('a', 'CONF-XXXXXX')], ' ', ' ', '', 2)],
            '980': [([('a', 'CONFERENCES')], ' ', ' ', '', 7)]}


def get_sample_texkey(num_test=0):
    sample_records = []
    xml = """
    <record>
        <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Boyle, P.A.</subfield>
        </datafield>
        <datafield tag="700" ind1=" " ind2=" ">
            <subfield code="a">Christ, N.H.</subfield>
        </datafield>
        <datafield tag="269" ind1=" " ind2=" ">
            <subfield code="c">2012-12-06</subfield>
        </datafield>
    </record>
    """
    sample_records.append(xml)

    xml = """
    <record>
        <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Broekhoven-Fiene, Hannah</subfield>
        </datafield>
        <datafield tag="700" ind1=" " ind2=" ">
            <subfield code="a">Matthews, Brenda C.</subfield>
        </datafield>
            <datafield tag="269" ind1=" " ind2=" ">
        <subfield code="c">2012-12-06</subfield>
        </datafield>
    </record>
    """
    sample_records.append(xml)

    xml = """
    <record>
        <datafield tag="269" ind1=" " ind2=" ">
            <subfield code="b">CERN</subfield>
            <subfield code="a">Geneva</subfield>
            <subfield code="c">2012-11-06</subfield>
        </datafield>
        <datafield tag="300" ind1=" " ind2=" ">
            <subfield code="a">16</subfield>
        </datafield>
        <datafield tag="710" ind1=" " ind2=" ">
            <subfield code="g">ATLAS Collaboration</subfield>
        </datafield>
    </record>
    """
    sample_records.append(xml)

    xml = """
    <record>
        <datafield tag="269" ind1=" " ind2=" ">
            <subfield code="b">CERN</subfield>
            <subfield code="a">Geneva</subfield>
            <subfield code="c">2012-11-06</subfield>
        </datafield>
        <datafield tag="300" ind1=" " ind2=" ">
            <subfield code="a">16</subfield>
        </datafield>
    </record>
    """
    sample_records.append(xml)

    return sample_records[num_test]


class IntSeq(SequenceGenerator):
    seq_name = 'test_int'

    def _next_value(self, x):
        return x + 1


class TestIntSequenceGeneratorClass(InvenioTestCase):

    def test_sequence_next_int(self):
        int_seq = IntSeq()
        next_int = int_seq.next_value(1)
        self.assertEqual(next_int, 2)

        # Check if the value was stored in the DB
        res = run_sql("""SELECT seq_value FROM seqSTORE
                         WHERE seq_value=%s AND seq_name=%s""",
                         (2, int_seq.seq_name))
        self.assertEqual(int(res[0][0]), 2)

        # Clean DB entries
        run_sql(""" DELETE FROM seqSTORE WHERE seq_name="test_int" """)


class TestCnumSequenceGeneratorClass(InvenioTestCase):

    if HAS_MOCK:
        @patch('invenio.bibedit_utils.get_bibrecord',
            get_bibrecord_mock)
        def test_get_next_cnum(self):
            from invenio.sequtils_cnum import CnumSeq

            cnum_seq = CnumSeq()
            res = cnum_seq.next_value('xx')
            self.assertEqual(res, 'C50-09-14')
            res = cnum_seq.next_value('xx')
            self.assertEqual(res, 'C50-09-14.1')

            # Clean DB entries
            run_sql(""" DELETE FROM seqSTORE
                        WHERE seq_name="cnum"
                        AND seq_value IN ("C50-09-14", "C50-09-14.1") """)


class TestTexkeySequenceGeneratorClass(unittest.TestCase):

    def setUp(self):
        self.texkey1 = ""
        self.texkey2 = ""
        self.texkey3 = ""

    def test_get_next_texkey1(self):
        """ Generate the first texkey """

        texkey_seq = TexkeySeq()
        self.texkey1 = texkey_seq.next_value(xml_record=get_sample_texkey(0))
        self.assertEqual(self.texkey1[:-3], 'Boyle:2012')

    def test_get_next_texkey2(self):
        """ Generate the second texkey """

        texkey_seq = TexkeySeq()
        self.texkey2 = texkey_seq.next_value(xml_record=get_sample_texkey(1))
        self.assertEqual(self.texkey2[:-3], 'Broekhoven-Fiene:2012')

    def test_get_next_texkey3(self):
        """ Generate the third texkey """

        texkey_seq = TexkeySeq()
        self.texkey3 = texkey_seq.next_value(xml_record=get_sample_texkey(2))
        self.assertEqual(self.texkey3[:-3], 'ATLAS:2012')

    def test_get_next_texkey_error(self):
        """ Generate an error while getting a texkey """

        texkey_seq = TexkeySeq()
        self.assertRaises(TexkeyNoAuthorError,
            texkey_seq.next_value, xml_record=get_sample_texkey(3))

    def tearDown(self):
        # Clean DB entries
        run_sql(""" DELETE FROM seqSTORE
                    WHERE seq_name="texkey"
                    AND seq_value IN ("%s", "%s", "%s") """ % (self.texkey1,
                                                               self.texkey2,
                                                               self.texkey3))


class TestTexkeydaemonClass(unittest.TestCase):
    def test_task_run_core(self):
        """ Basic task_run_core check """
        task_run_core()


TEST_SUITE = make_test_suite(TestIntSequenceGeneratorClass,
                             TestCnumSequenceGeneratorClass,
                             TestTexkeySequenceGeneratorClass,
                             TestTexkeydaemonClass)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
