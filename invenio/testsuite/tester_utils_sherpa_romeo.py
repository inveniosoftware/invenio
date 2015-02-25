# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from __future__ import print_function

from six import iteritems

from invenio.utils.sherpa_romeo import SherpaRomeoSearch

"""
Test Cases

publishers search:
    - american
        127 numhits
    - American Academy of Audiology
        1 numhit - no policies
    - comput
        8 numhits
        all have conditions


title search:
    - american
        50 numhits(limit)
        first journal 'APS Legacy Content' issn = '0002-9513'
    - APS Legacy Content
        1 numhit
        name: American Physiological Society
        has conditions
    - comput
        50 numhits(limit)
        first journal
            name: ACM Communications in Computer Algebra
            issn: 1932-2232
    - computation
        50 numhits
        first journal
            name: ACM Transactions on Computation Theory
            issn: 1942-3454
    - Computational Intelligence
        16 numhits
    - Advances in Materials Physics and Chemistry
        2 numhits!!!
        the second has issn: 2162-531X

"""


class SherpaRomeoTesting:

    def __init__(self):
        self.sr = SherpaRomeoSearch()
        self.error_messages = []
        self.failed_tests = 0
        self.passed_tests = 0

    def test_publishers_search_numhits(self):
        publishers = self.sr.search_publisher("american")
        num_hits = self.sr.parser.xml['header']['numhits']
        try:
            assert len(publishers) == 127 == int(num_hits)
            self.passed_tests = +1
        except AssertionError:
            self.failed_tests += 1
            self.error_messages.append("Wrong number of numhits " + \
                                       "while searching term 'american'" + \
                                       "in publishers: " + \
                                       str(len(publishers)) + \
                                       "\ncorrect: " + num_hits)

        publishers = self.sr.search_publisher(\
                                "American Academy of Audiology")
        num_hits = self.sr.parser.xml['header']['numhits']
        try:
            assert len(publishers) == 1 == int(num_hits)
            self.passed_tests = +1
        except AssertionError:
            self.failed_tests += 1
            self.error_messages.append("Wrong number of numhits " + \
                                       "while searching term " + \
                                       "American Academy of Audiology' " + \
                                       "in publishers: " + num_hits + \
                                       "\ncorrect: 1")

        publishers = self.sr.search_publisher("comput")
        num_hits = self.sr.parser.xml['header']['numhits']
        try:
            assert len(publishers) == 8 == int(num_hits)
            self.passed_tests = +1
        except AssertionError:
            self.failed_tests += 1
            self.error_messages.append("Wrong number of numhits " + \
                                       "while searching term " + \
                                       "'American Academy of Audiology' " + \
                                       "in publishers: " + \
                                       str(len(publishers)) + \
                                       "\ncorrect: " + num_hits)

    def test_publishers_search_conditions(self):
        self.sr.search_publisher("comput")
        for publisher, conditions in iteritems(
                self.sr.parser.get_conditions()):
            try:
                assert conditions != None
                self.passed_tests = +1
            except AssertionError:
                self.failed_tests += 1
                self.error_messages.append("Conditions not found " + \
                                           "when they should be! " + \
                                           publisher)
                break

        self.sr.search_publisher("American Academy of Audiology")
        conditions = self.sr.parser.get_conditions()
        try:
            assert conditions == {}
            self.passed_tests = +1
        except AssertionError:
            self.failed_tests += 1
            self.error_messages.append("Conditions found " + \
                                       "when they shouldn't be! " + \
                                       "American Academy of Audiology")

    def run_all_tests(self):
        self.test_publishers_search_numhits()
        self.test_publishers_search_conditions()

    def print_test_results(self):
        for err_msg in self.error_messages:
            print(err_msg)
            print("-----------------")

        if self.failed_tests > 0:
            print("Failed Tests: ", self.failed_tests)
        if self.passed_tests > 0:
            print("Passed Tests: ", self.passed_tests)
