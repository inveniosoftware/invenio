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


"""BibTask Regression Test Suite."""

__revision__ = "$Id$"

import unittest
from ConfigParser import RawConfigParser
from invenio.testutils import make_test_suite, run_test_suite
from invenio.bibcheck_task import RulesParseError, \
        load_rule, \
        AmendableRecord
from invenio.bibcheck_plugins_unit_tests import MOCK_RECORD

PLUGINS_MOCK = {
    "valid_checker": {
        "check_record": lambda x: None,
        "all_args": set(
            "param_true param_number param_str param_obj param_arr".split()
        ),
        "mandatory_args": set()
    },
    "mandatory_args": {
        "check_record": lambda x: None,
        "all_args": set(["mandatory_arg"]),
        "mandatory_args": set(["mandatory_arg"])
    },
}
PLUGINS_MOCK["other_checker"] = PLUGINS_MOCK["valid_checker"]

RULE_MOCK = {
    "name": "test_rule",
    "holdingpen": True
}

INVALID_RULES = (
    ("empty_rule", {}, ""),
    ("invalid_checker", {
        "check": "non_existent_checker"
    }, "Invalid checker"),
    ("invalid_parameter", {
        "check": "valid_checker",
        "check.param": "Invalid JSON"
    }, "Invalid value"),
    ("invalid_option", {
        "check": "valid_checker",
        "non_existent_option": "true"
    }, "Invalid rule option"),
    ("no_checker", {
        "filter_collection": "CERN"
    }, "Doesn't have a checker"),
    ("unknown_parameter", {
        "check": "mandatory_args",
        "check.non_existent_arg": "true",
        "check.mandatory_arg": "true"
    }, "Unknown plugin argument"),
    ("mandatory_arg", {
        "check": "mandatory_args"
    }, "mandatory argument"),
)


class BibCheckRulesParseTest(unittest.TestCase):
    """ Tests the rule parse functionality """
    def test_invalid_rule(self):
        """ Makes sure the parser raises an error with invalid rules """
        config = RawConfigParser()

        # Create sections in the config file
        for rule_name, options, _ in INVALID_RULES:
            config.add_section(rule_name)
            for option_name, val in options.items():
                config.set(rule_name, option_name, val)

        # Test invalid sections that should fail to parse
        for rule_name, _, exception in INVALID_RULES:
            try:
                load_rule(config, PLUGINS_MOCK, rule_name)
                self.fail()
            except RulesParseError, ex:
                if str(ex).find(exception) < 0:
                    self.fail()

    def test_valid_rule(self):
        """ Checks that rules are parsed correctly """
        config = RawConfigParser()
        config.add_section("rule1")
        config.set("rule1", "check", "valid_checker")
        config.set("rule1", "check.param_true", "true")
        config.set("rule1", "check.param_number", "1337")
        config.set("rule1", "check.param_str", '"foobar"')
        config.set("rule1", "check.param_obj", '{"foo":"bar"}')
        config.set("rule1", "check.param_arr", '[true, 1337, ["foobar"]]')
        config.set("rule1", "filter_pattern", "foo")
        config.set("rule1", "filter_field", "bar")
        config.set("rule1", "filter_collection", "baz")
        config.set("rule1", "holdingpen", "true")

        config.add_section("rule2")
        config.set("rule2", "check", "other_checker")

        rule1 = load_rule(config, PLUGINS_MOCK, "rule1")
        rule2 = load_rule(config, PLUGINS_MOCK, "rule2")

        self.assertEqual(rule1["check"], "valid_checker")
        self.assertTrue(rule1["checker_params"]["param_true"])
        self.assertEqual(rule1["checker_params"]["param_number"], 1337)
        self.assertEqual(rule1["checker_params"]["param_str"], "foobar")
        self.assertEqual(rule1["checker_params"]["param_obj"], {"foo": "bar"})
        self.assertEqual(rule1["checker_params"]["param_arr"], [True, 1337, ["foobar"]])
        self.assertEqual(rule1["filter_pattern"], "foo")
        self.assertEqual(rule1["filter_field"], "bar")
        self.assertEqual(rule1["filter_collection"], "baz")
        self.assertEqual(rule1["holdingpen"], True)

        self.assertEqual(rule2["check"], "other_checker")


class BibCheckAmendableRecordTest(unittest.TestCase):
    """ Check the AmendableRecord class """

    def setUp(self):
        """ Create a mock amenda record to test with """
        self.record = AmendableRecord(MOCK_RECORD)
        self.record.set_rule(RULE_MOCK)

    def test_valid(self):
        """ Test the set_invalid method """
        self.assertTrue(self.record.valid)
        self.record.set_invalid("test message")
        self.assertFalse(self.record.valid)
        self.assertEqual(self.record.errors, ["Rule test_rule: test message"])

    def test_amend(self):
        """ Test the amend method """
        self.assertFalse(self.record.amendments)
        self.record.amend_field(("100__a", 0, 0), "Pepe", "Changed author")
        self.assertEqual(self.record["100"][0][0][0][1], "Pepe")
        self.assertTrue(self.record.amended)
        self.assertEqual(self.record.amendments, ["Rule test_rule: Changed author"])

    def test_itertags(self):
        """ Test the itertags method """
        self.assertEqual(
            set(self.record.keys()),
            set(self.record.itertags("%%%"))
        )
        self.assertEqual(set(['100']), set(self.record.itertags("100")))
        self.assertEqual(set(['001', '005']), set(self.record.itertags("00%")))
        self.assertEqual(set(), set(self.record.itertags("111")))

    def test_iterfields(self):
        """ Test the iterfields method """
        self.assertEqual(set(), set(self.record.iterfields(["111%%%"])))
        self.assertEqual(
            set([(("100__a", 0, 0), "Pepe")]),
            set(self.record.iterfields(["1%%%%%"]))
        )
        self.assertEqual(
            set([(("9944_u", 0, 0), self.record["994"][0][0][0][1]),
            (("9954_u", 0, 0), self.record["995"][0][0][0][1]),
            (("9964_u", 0, 0), self.record["996"][0][0][0][1]),
            (("9974_u", 0, 0), self.record["997"][0][0][0][1]),
            (("9984_u", 0, 0), self.record["998"][0][0][0][1]),
            (("9994_u", 0, 0), self.record["999"][0][0][0][1])]),
            set(self.record.iterfields(["9%%%%u"]))
        )

    def test_is_dummy(self):
        """ Test the is_dummy method """
        dummy_record = {
            '001': [([], ' ', ' ', '1', 1)]
        }
        record = AmendableRecord(dummy_record)
        self.assertTrue(record.is_dummy())

TEST_SUITE = make_test_suite(
        BibCheckRulesParseTest,
        BibCheckAmendableRecordTest
    )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

