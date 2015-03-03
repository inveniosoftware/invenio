# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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
The BibRecord regression test suite.
"""

import unittest

from invenio.config import CFG_SITE_URL, \
     CFG_SITE_RECORD
from invenio import bibrecord
from invenio.testutils import make_test_suite, run_test_suite
from invenio.search_engine import get_record


class BibRecordFilterBibrecordTest(unittest.TestCase):
    """ bibrecord - testing for code filtering"""

    def setUp(self):
        self.rec = get_record(10)

    def test_empty_filter(self):
        """bibrecord - empty filter"""
        self.assertEqual(bibrecord.get_filtered_record(self.rec, []), self.rec)

    def test_filter_tag_only(self):
        """bibrecord - filtering only by MARC tag"""
        # Exist
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['001']), {'001': [([], ' ', ' ', '10', 1)]})
        # Do not exist
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['037']), {})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['856']), {})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['999']), {})
        # Sequence
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['001', '999']), {'001': [([], ' ', ' ', '10', 1)]})
        # Some tags do not exist
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['001', '260', '856', '400', '500', '999']), {'001': [([], ' ', ' ', '10', 1)]})

    def test_filter_subfields(self):
        """bibrecord - filtering subfields"""
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['65017a']), {'650': [([('a', 'Particle Physics - Experimental Results')], '1', '7', '', 1)],})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['65017a', '650172']), {'650': [([('a', 'Particle Physics - Experimental Results')], '1', '7', '', 1),
                                                                                                 ([('2', 'SzGeCERN')], '1', '7', '', 2)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['8560_f']), {'856': [([('f', 'valerie.brunner@cern.ch')], '0', ' ', '', 1)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['260__a']), {'260': [([('a', 'Geneva')], ' ', ' ', '', 1)],})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['595__a']), {'595': [([('a', 'CERN EDS')], ' ', ' ', '', 1),
                                                                                       ([('a', '20011220SLAC')], ' ', ' ', '', 2),
                                                                                       ([('a', 'giva')], ' ', ' ', '', 3),
                                                                                       ([('a', 'LANL EDS')], ' ', ' ', '', 4)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['8564_u']), {'856': [([('u', '%s/%s/10/files/ep-2001-094.ps.gz' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 1),
                                                                                       ([('u', '%s/%s/10/files/ep-2001-094.pdf' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 2)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['595__a', '8564_u']), {'595': [([('a', 'CERN EDS')], ' ', ' ', '', 1),
                                                                                                 ([('a', '20011220SLAC')], ' ', ' ', '', 2),
                                                                                                 ([('a', 'giva')], ' ', ' ', '', 3),
                                                                                                 ([('a', 'LANL EDS')], ' ', ' ', '', 4)],
                                                                                         '856': [([('u', '%s/%s/10/files/ep-2001-094.ps.gz' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 5),
                                                                                                 ([('u', '%s/%s/10/files/ep-2001-094.pdf' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 6)]})

    def test_filter_comprehensive(self):
        """bibrecord - comprehensive filtering"""
        tags = ['001', '035', '037__a', '65017a', '650']
        res = {}
        res['001'] = [([], ' ', ' ', '10', 1)]
        res['037'] = [([('a', 'hep-ex/0201013')], ' ', ' ', '', 2)]
        res['650'] = [([('a', 'Particle Physics - Experimental Results')], '1', '7', '', 3)]
        self.assertEqual(bibrecord.get_filtered_record(self.rec, tags), res)

    def test_filter_wildcards(self):
        """bibrecord - wildcards filtering"""
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['595__%']), {'595': [([('a', 'CERN EDS')], ' ', ' ', '', 1),
                                                                                       ([('a', '20011220SLAC')], ' ', ' ', '', 2),
                                                                                       ([('a', 'giva')], ' ', ' ', '', 3),
                                                                                       ([('a', 'LANL EDS')], ' ', ' ', '', 4)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['909CS%']), {'909': [([('s', 'n'), ('w', '200231')], 'C', 'S', '', 1)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['856%']), {})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['856%_u']), {'856': [([('u', '%s/%s/10/files/ep-2001-094.ps.gz' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 1),
                                                                                       ([('u', '%s/%s/10/files/ep-2001-094.pdf' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 2)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['909%5v']), {})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['909%5b']), {'909': [([('b', 'CER')], 'C', '5', '', 1)]})

    def test_filter_multi_wildcards(self):
        """bibrecord - multi wildcards filtering"""
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['909%%_']), {})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['856%_%']), {'856': [([('f', 'valerie.brunner@cern.ch')], '0', ' ', '', 1),
                                                                                       ([('s', '217223'), ('u', '%s/%s/10/files/ep-2001-094.ps.gz' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 2),
                                                                                       ([('s', '383040'), ('u', '%s/%s/10/files/ep-2001-094.pdf' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 3)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['909%%b']), {'909': [([('b', '11')], 'C', '0', '', 1),
                                                                                       ([('b', 'CER')], 'C', '5', '', 2)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['909%%%']), {'909': [([('y', '2002')], 'C', '0', '', 1),
                                                                                       ([('e', 'ALEPH')], 'C', '0', '', 2),
                                                                                       ([('b', '11')], 'C', '0', '', 3),
                                                                                       ([('p', 'EP')], 'C', '0', '', 4),
                                                                                       ([('a', 'CERN LEP')], 'C', '0', '', 5),
                                                                                       ([('c', '2001-12-19'), ('l', '50'), ('m', '2002-02-19'), ('o', 'BATCH')], 'C', '1', '', 6),
                                                                                       ([('u', 'CERN')], 'C', '1', '', 7),
                                                                                       ([('p', 'Eur. Phys. J., C')], 'C', '4', '', 8),
                                                                                       ([('b', 'CER')], 'C', '5', '', 9),
                                                                                       ([('s', 'n'), ('w', '200231')], 'C', 'S', '', 10),
                                                                                       ([('o', 'oai:cds.cern.ch:CERN-EP-2001-094'), ('p', 'cern:experiment')], 'C', 'O', '', 11)]})
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['980%%%']), bibrecord.get_filtered_record(self.rec, ['980_%%']))
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['980_%%']), bibrecord.get_filtered_record(self.rec, ['980%_%']))
        self.assertEqual(bibrecord.get_filtered_record(self.rec, ['980__%']), bibrecord.get_filtered_record(self.rec, ['980%%%']))

    def test_filter_wildcard_comprehensive(self):
        """bibrecord - comprehensive wildcard filtering"""
        tags = ['595__%', '909CS%', '856%', '856%_%', '909%5b', '980%%%']
        res = {}
        res['595'] = [([('a', 'CERN EDS')], ' ', ' ', '', 1),
                      ([('a', '20011220SLAC')], ' ', ' ', '', 2),
                      ([('a', 'giva')], ' ', ' ', '', 3),
                      ([('a', 'LANL EDS')], ' ', ' ', '', 4)]
        res['856'] = [([('f', 'valerie.brunner@cern.ch')], '0', ' ', '', 5),
                      ([('s', '217223'), ('u', '%s/%s/10/files/ep-2001-094.ps.gz' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 6),
                      ([('s', '383040'), ('u', '%s/%s/10/files/ep-2001-094.pdf' % (CFG_SITE_URL, CFG_SITE_RECORD))], '4', ' ', '', 7)]
        res['909'] = [([('s', 'n'), ('w', '200231')], 'C', 'S', '', 8),
                      ([('b', 'CER')], 'C', '5', '', 9)]
        res['980'] = [([('a', 'PREPRINT')], ' ', ' ', '', 10),
                      ([('a', 'ALEPHPAPER')], ' ', ' ', '', 11)]
        self.assertEqual(bibrecord.get_filtered_record(self.rec, tags), res)


TEST_SUITE = make_test_suite(
    BibRecordFilterBibrecordTest,
    )

if __name__ == '__main__':
    run_test_suite(TEST_SUITE, warn_user=True)
