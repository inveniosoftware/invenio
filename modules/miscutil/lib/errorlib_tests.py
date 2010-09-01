# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

""" Test unit for the miscutil/errorlib module. """

__revision__ = "$Id$"

from invenio.errorlib import get_msg_associated_to_code, \
                             get_msgs_for_code_list, \
                             get_emergency_recipients
from invenio.testutils import make_test_suite, run_test_suite

import unittest
import datetime
import time
import calendar

class TestInternalErrorlibErrors(unittest.TestCase):
    """
    Class for testing!
    """
    messages = []

    def test_correct_association(self):
        """errorlib - code association: correct code"""
        # correct input
        input_err_code = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        (output_err_code, dummy) = get_msg_associated_to_code(input_err_code,
                                                              'error')
        self.assertEqual(output_err_code, input_err_code)

    def test_no_module(self):
        """errorlib - code association: no <module>_config"""
        # no file module_config
        input_err_code ='ERR_BADMODULEIDENTIFIER_WITH_BAD_ERRORNAME'
        (output_err_code, dummy) = get_msg_associated_to_code(input_err_code,
                                                              'error')
        expected_output_err_code = 'ERR_MISCUTIL_IMPORT_ERROR'
        self.assertEqual(output_err_code, expected_output_err_code)

    def test_no_dictionary(self):
        """errorlib - code association: no error dictionary"""
        # file exists, but no dictionary
        input_err_code ='ERR_MISCUTIL_NODICTIONARY'
        (output_err_code, dummy) = get_msg_associated_to_code(input_err_code,
                                                              'nodict')
        expected_output_err_code = 'ERR_MISCUTIL_NO_DICT'
        self.assertEqual(output_err_code, expected_output_err_code)

    def test_no_identifier(self):
        """errorlib - code association: no identifier"""
        # identifier not in dictionary
        input_err_code ='ERR_MISCUTIL_IDENTIFIER_WONT_BE_FOUND_IN_DICTIONNARY'
        (output_err_code, dummy) = get_msg_associated_to_code(input_err_code,
                                                              'error')
        expected_output_err_code = 'ERR_MISCUTIL_NO_MESSAGE_IN_DICT'
        self.assertEqual(output_err_code, expected_output_err_code)

    def test_not_an_error(self):
        """errorlib - code association: badly named error"""
        # identifier does not begin with ERR or WRN
        input_err_code = 'STRANGEERROR'
        (output_err_code, dummy) = get_msg_associated_to_code(input_err_code,
                                                              'error')
        expected_output_err_code = 'ERR_MISCUTIL_UNDEFINED_ERROR'
        self.assertEqual(output_err_code, expected_output_err_code)

    def test_correct_arg_validation(self):
        """errorlib - single argument"""
        # displayable error
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        output_list = get_msgs_for_code_list((error, 'junk'))
        self.assertEqual(1, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(error, output_list[0][0])
        self.messages.append(output_list[0][1])

    def test_correct_args_validation(self):
        """errorlib - multiple errors"""
        # displayable errors
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        output_list = get_msgs_for_code_list([(error, 'junk'), (error, 'junk')])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(error, output_list[1][0])
        # store error message for further tests
        self.messages.append(output_list[0][1])
        self.messages.append(output_list[1][1])

    def test_undefined_error(self):
        """errorlib - no underscore in error"""
        # undefined error
        error = 'ERRMISCUTIL'
        expected_error = 'ERR_MISCUTIL_UNDEFINED_ERROR'
        output_list = get_msgs_for_code_list([(error)])
        self.assertEqual(1, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(expected_error, output_list[0][0])
        # store error messages for further tests
        self.messages.append(output_list[0][1])

    def test_too_many_arguments(self):
        """errorlib - arguments: too many arguments"""
        # too many arguments
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        other_error = 'ERR_MISCUTIL_TOO_MANY_ARGUMENT'
        output_list = get_msgs_for_code_list([(error, 'junk', 'junk', 'junk')])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(other_error, output_list[1][0])
        # store error messages for further tests
        self.messages.append(output_list[0][1])
        self.messages.append(output_list[1][1])

    def test_too_few_arguments(self):
        """errorlib - arguments: too few arguments"""
        # too few argument
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        other_error = 'ERR_MISCUTIL_TOO_FEW_ARGUMENT'
        output_list = get_msgs_for_code_list([(error)])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(other_error, output_list[1][0])
        # store error messages for further tests
        self.messages.append(output_list[0][1])
        self.messages.append(output_list[1][1])

    def test_bad_type(self):
        """errorlib - arguments: bad argument type"""
        # bad argument type
        error = 'ERR_MISCUTIL_DEBUG'
        other_error = 'ERR_MISCUTIL_BAD_ARGUMENT_TYPE'
        output_list = get_msgs_for_code_list([(error, 'should be an int')])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(other_error, output_list[1][0])

    # z because this function must execute lately for more interesting
    # results:
    def test_zsubstitution(self):
        """errorlib - arguments: every argument substituted"""
        # string replacement
        testmessages = reduce(lambda x, y: str(x) + str(y), self.messages)
        self.assertEqual(0, testmessages.count('%') - testmessages.count('%%'))

    # z because this function must also execute lately for more
    # interesting results:
    def test_zinternationalization(self):
        """errorlib - internationalization"""
        # string internationalization
        testmessages = reduce(lambda x, y: str(x) + str(y), self.messages)
        self.assertEqual(0, testmessages.count('_('))

class TestGetEmergencyRecipients(unittest.TestCase):
    def test_get_emergency_recipients(self):
        """errorlib - test return of proper set of recipients"""
        now = datetime.datetime.today()
        tomorrow = now + datetime.timedelta(days=1)
        diff_day = now + datetime.timedelta(days=4)
        later = now.replace(hour=now.hour + 1)
        earlier = now.replace(hour=now.hour - 1)
        constraint_now = "%s %s-%s" % (
                                    now.strftime("%a"),
                                    earlier.strftime("%H:00"),
                                    later.strftime("%H:00"),
                                    )
        constraint_tomorrow = "%s %s-%s" % (
                                    tomorrow.strftime("%a"),
                                    earlier.strftime("%H:00"),
                                    later.strftime("%H:00"),
                                    )
        constraint_time = "%s-%s" % (
                                    earlier.strftime("%H:00"),
                                    later.strftime("%H:00"),
                                    )
        constraint_near_miss = "%s-%s" % (
                                    earlier.strftime("%H:00"),
                                    now.replace(minute=now.minute - 3) \
                                        .strftime("%H:%M")
                                    )
        constraint_day = "%s" % now.strftime("%A")
        constraint_diff_day = "%s" % diff_day.strftime("%A")
        test_config = {
                       constraint_now:      'now@example.com',
                       constraint_tomorrow: 'tomorrow@example.com',
                       constraint_time:     'time@example.com',
                       constraint_day:      'day@example.com,day@foobar.com',
                       constraint_diff_day: 'diff_day@example.com',
                       constraint_near_miss:'near_miss@example.com',
                       '*':                 'fallback@example.com',
                       }
        result = get_emergency_recipients(recipient_cfg=test_config)
        expected = ['now@example.com', 'time@example.com',
                    'day@example.com,day@foobar.com', 'fallback@example.com']
        self.assertEqual(set(result), set(expected))

TEST_SUITE = make_test_suite(TestInternalErrorlibErrors,
                             TestGetEmergencyRecipients,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
