# -*- coding: utf-8 -*-
## $Id$
## CDSware ErrorLib unit tests.
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
""" Test unit for the miscutil/errorlib module. """
__lastupdated__ = """$Date$"""


from cdsware.errorlib import get_msg_associated_to_code, get_msgs_for_code_list
import unittest

class TestInternalErrorlibErrors(unittest.TestCase):
    """
    Class for testing!
    """
    def test_get_msg_associated_to_code(self):
        """ Test for error code to message association """
        # correct input
        input_err_code = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error') 
        self.assertEqual(output_err_code, input_err_code)

        # no file module_config
        input_err_code ='ERR_BADMODULEIDENTIFIER_WITH_BAD_ERRORNAME'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error')
        expected_output_err_code = 'ERR_MISCUTIL_IMPORT_ERROR'
        self.assertEqual(output_err_code, expected_output_err_code)

        # file exists, but no dictionary
        input_err_code ='ERR_MISCUTIL_NODICTIONARY'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'nodict')
        expected_output_err_code = 'ERR_MISCUTIL_NO_DICT'
        self.assertEqual(output_err_code, expected_output_err_code)

        # identifier not in dictionary
        input_err_code ='ERR_MISCUTIL_IDENTIFIER_WONT_BE_FOUND_IN_DICTIONNARY'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error')
        expected_output_err_code = 'ERR_MISCUTIL_NO_MESSAGE_IN_DICT'
        self.assertEqual(output_err_code, expected_output_err_code)

        # identifier does not begin with ERR or WRN
        input_err_code = 'STRANGEERROR'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error')
        expected_output_err_code = 'ERR_MISCUTIL_UNDEFINED_ERROR'
        self.assertEqual(output_err_code, expected_output_err_code)
        
    def test_get_msgs_for_code_list(self):
        """ Test error message output """
        messages = []
        # displayable error
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        output_list = get_msgs_for_code_list((error, 'junk'))
        self.assertEqual(1, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(error, output_list[0][0])
        messages.append(output_list[0][1])
        
        # displayable errors
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        output_list = get_msgs_for_code_list([(error, 'junk'), (error, 'junk')])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(error, output_list[1][0])
        messages.append(output_list[0][1])
        messages.append(output_list[1][1])

        # undefined error
        error = 'ERRMISCUTIL'
        expected_error = 'ERR_MISCUTIL_UNDEFINED_ERROR'
        output_list = get_msgs_for_code_list([(error)])
        self.assertEqual(1, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(expected_error, output_list[0][0])
        messages.append(output_list[0][1])               
        
        # too many arguments
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        other_error = 'ERR_MISCUTIL_TOO_MANY_ARGUMENT'
        output_list = get_msgs_for_code_list([(error, 'junk', 'junk', 'junk')])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(other_error, output_list[1][0])
        messages.append(output_list[0][1])
        messages.append(output_list[1][1])
        
        # too few argument
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        other_error = 'ERR_MISCUTIL_TOO_FEW_ARGUMENT'
        output_list = get_msgs_for_code_list([(error)])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(other_error, output_list[1][0])
        messages.append(output_list[0][1])
        messages.append(output_list[1][1])

        # bad argument type
        error = 'ERR_MISCUTIL_DEBUG'
        other_error = 'ERR_MISCUTIL_BAD_ARGUMENT_TYPE'
        output_list = get_msgs_for_code_list([(error, 'should be an int')])
        self.assertEqual(2, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(2, len(output_list[1]))
        self.assertEqual(error, output_list[0][0])
        self.assertEqual(other_error, output_list[1][0])
        
        # string replacement
        messages = reduce(lambda x, y: str(x) + str(y), messages)
        self.assertEqual(0, messages.count('%') - messages.count('%%'))

        # string internationalization
        self.assertEqual(0, messages.count('_('))
        
def create_test_suite():
    """
    Return test suite for the search engine.
    """
    return unittest.TestSuite((unittest.makeSuite(TestInternalErrorlibErrors, 'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
