# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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


"""BibTask default plugins Test Suite."""

__revision__ = "$Id$"

import unittest
from invenio.testutils import make_test_suite, run_test_suite
from invenio.bibcheck_plugins import mandatory, \
    trailing_space, \
    regexp, \
    utf8, \
    enum, \
    dates, \
    texkey, \
    url
from invenio.bibcheck_task import AmendableRecord

MOCK_RECORD = {
    '001': [([], ' ', ' ', '1', 7)],
    '005': [([], ' ', ' ', '20130621172205.0', 7)],
    '100': [([('a', 'Photolab ')], ' ', ' ', '', 7)], # Trailing spaces
    '260': [([('c', '2000-06-14')], ' ', ' ', '', 7)],
    '261': [([('c', '14 Jun 2000')], ' ', ' ', '', 7)],
    '262': [([('c', '14 06 00')], ' ', ' ', '', 7)],
    '263': [([('c', '2000 06 14')], ' ', ' ', '', 7)],
    '264': [([('c', '1750 06 14')], ' ', ' ', '', 7)],
    '265': [([('c', '2100 06 14')], ' ', ' ', '', 7)],
    '340': [([('a', 'FI\xc3\x28LM')], ' ', ' ', '', 7)], # Invalid utf-8
    '595': [([('a', ' Press')], ' ', ' ', '', 7)], # Leading spaces
    '653': [([('a', 'LEP')], '1', ' ', '', 7)],
    '856': [([('f', 'neil.calder@cern.ch')], '0', ' ', '', 7)],
    '994': [([('u', 'http://httpstat.us/200')], '4', ' ', '', 7)], # Url that works
    '995': [([('u', 'www.google.com/favicon.ico')], '4', ' ', '', 7)],  # url without protocol
    '996': [([('u', 'httpstat.us/301')], '4', ' ', '', 7)],   # redirection without protocol
    '997': [([('u', 'http://httpstat.us/404')], '4', ' ', '', 7)], # Error 404
    '998': [([('u', 'http://httpstat.us/500')], '4', ' ', '', 7)], # Error 500
    '999': [([('u', 'http://httpstat.us/301')], '4', ' ', '', 7)], # Permanent redirect
}

RULE_MOCK = {
    "name": "test_rule",
    "holdingpen": True
}

class BibCheckPluginsTest(unittest.TestCase):
    """ Bibcheck default plugins test """

    def assertAmends(self, test, changes, **kwargs):
        """
        Assert that the plugin "test" amends the mock record when called with
        params kwargs.
        """
        record = AmendableRecord(MOCK_RECORD)
        record.set_rule(RULE_MOCK)
        test.check_record(record, **kwargs)
        self.assertTrue(record.amended)
        self.assertEqual(len(record.amendments), len(changes))
        for field, val in changes.iteritems():
            if val is not None:
                self.assertEqual(
                    [((field, 0, 0), val)],
                    list(record.iterfield(field))
                )
            else:
                self.assertEqual(len(list(record.iterfield(field))), 1)

    def assertFails(self, test, **kwargs):
        """
        Assert that the plugin test marks the record as invalid when called with
        params kwargs.
        """
        record = AmendableRecord(MOCK_RECORD)
        record.set_rule(RULE_MOCK)
        test.check_record(record, **kwargs)
        self.assertFalse(record.valid)
        self.assertTrue(len(record.errors) > 0)

    def assertOk(self, test, **kwargs):
        """
        Assert that the plugin test doesn't make any modification to the record
        when called with params kwargs.
        """
        record = AmendableRecord(MOCK_RECORD)
        record.set_rule(RULE_MOCK)
        test.check_record(record, **kwargs)
        self.assertTrue(record.valid)
        self.assertFalse(record.amended)
        self.assertEqual(len(record.amendments), 0)
        self.assertEqual(len(record.errors), 0)

    def test_mandatory(self):
        """ Mandatory fields plugin test """
        self.assertOk(mandatory, fields=["100%%a", "260%%c"])
        self.assertFails(mandatory, fields=["100%%b"])
        self.assertFails(mandatory, fields=["111%%%"])

    def test_trailing_space(self):
        """ Trailing space plugin test """
        self.assertAmends(trailing_space, {"100__a": "Photolab"}, fields=["100%%a"])
        self.assertAmends(trailing_space, {"100__a": "Photolab"}, fields=["595%%a", "100%%a"])
        self.assertOk(trailing_space, fields=["653%%a"])

    def test_regexp(self):
        """ Regexp plugin test """
        self.assertOk(regexp, regexps={
            "856%%f": "[^@]+@[^@]+$",
            "260%%c": r"\d{4}-\d\d-\d\d$"
        })
        self.assertFails(regexp, regexps={
            "340%%a": "foobar"
        })

    def test_utf8(self):
        """ Valid utf-8 plugin test """
        self.assertFails(utf8, fields=["%%%%%%"])
        self.assertOk(utf8, fields=["856%%%"])

    def test_enum(self):
        """ Enum plugin test """
        self.assertFails(enum, allowed_values={"100__a": ["Pepe", "Juan"]})
        self.assertOk(enum, allowed_values={"6531_a": ["LEP", "Other"]})

    def test_date(self):
        """ Date plugin test """
        self.assertOk(dates, fields=["260__c"])
        self.assertAmends(dates, {"261__c": "2000-06-14"}, fields=["261__c"])
        self.assertAmends(dates, {"262__c": "2000-06-14"}, fields=["262__c"])
        self.assertAmends(dates, {"263__c": "2000-06-14"}, fields=["263__c"])
        self.assertFails(dates, fields=["264__c"]) # Date in the far past
        self.assertFails(dates, fields=["265__c"], allow_future=False) # Date in the future
        self.assertFails(dates, fields=["100__a"]) # Invalid date

    def test_texkey(self):
        """ TexKey plugin test """
        self.assertAmends(texkey, {"035__a": None})

    # Test skipped by default because it involved making slow http requests
    #def test_url(self):
    #    """ Url checker plugin test. This plugin is disabled by default """
    #    self.assertOk(url, fields=["994%%u"])
    #    self.assertAmends(url, {"9954_u": "http://www.google.com/favicon.ico"}, fields=["995%%u"])
    #    self.assertAmends(url, {"9964_u": "http://httpstat.us"}, fields=["996%%u"])
    #    self.assertFails(url, fields=["997%%u"])
    #    self.assertFails(url, fields=["998%%u"])
    #    self.assertAmends(url, {"9994_u": "http://httpstat.us"}, fields=["999%%u"])


TEST_SUITE = make_test_suite(BibCheckPluginsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

