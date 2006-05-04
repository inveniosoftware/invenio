# -*- coding: utf-8 -*-
## $Id$
## CDS Invenio ErrorLib unit tests.
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
""" Test unit for the miscutil/errorlib module. """
__lastupdated__ = """$Date$"""


from invenio.errorlib import get_msg_associated_to_code, get_msgs_for_code_list
import unittest

class TestInternalErrorlibErrors(unittest.TestCase):
    """
    Class for testing!
    """
    messages = []
    
    def test_correct_association(self):
        """errorlib - code association: correct code"""
        # correct input
        input_err_code = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error') 
        self.assertEqual(output_err_code, input_err_code)

    def test_no_module(self):
        """errorlib - code association: no <module>_config"""
        # no file module_config
        input_err_code ='ERR_BADMODULEIDENTIFIER_WITH_BAD_ERRORNAME'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error')
        expected_output_err_code = 'ERR_MISCUTIL_IMPORT_ERROR'
        self.assertEqual(output_err_code, expected_output_err_code)

    def test_no_dictionary(self):
        """errorlib - code association: no error dictionary"""
        # file exists, but no dictionary
        input_err_code ='ERR_MISCUTIL_NODICTIONARY'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'nodict')
        expected_output_err_code = 'ERR_MISCUTIL_NO_DICT'
        self.assertEqual(output_err_code, expected_output_err_code)

    def test_no_identifier(self):
        """errorlib - code association: no identifier"""
        # identifier not in dictionary
        input_err_code ='ERR_MISCUTIL_IDENTIFIER_WONT_BE_FOUND_IN_DICTIONNARY'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error')
        expected_output_err_code = 'ERR_MISCUTIL_NO_MESSAGE_IN_DICT'
        self.assertEqual(output_err_code, expected_output_err_code)
        
    def test_not_an_error(self):
        """errorlib - code association: badly named error"""
        # identifier does not begin with ERR or WRN
        input_err_code = 'STRANGEERROR'
        (output_err_code, err_msg) = get_msg_associated_to_code(input_err_code, 'error')
        expected_output_err_code = 'ERR_MISCUTIL_UNDEFINED_ERROR'
        self.assertEqual(output_err_code, expected_output_err_code)
        
    def test_correct_argument_validation(self):
        """errorlib - single argument"""
        # displayable error
        error = 'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED'
        output_list = get_msgs_for_code_list((error, 'junk'))
        self.assertEqual(1, len(output_list))
        self.assertEqual(2, len(output_list[0]))
        self.assertEqual(error, output_list[0][0])
        self.messages.append(output_list[0][1])

    def test_correct_arguments_validation(self):
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

    # z because this function must execute lately for more interesting results
    def test_zsubstitution(self):
        """errorlib - arguments: every argument substituted"""
        # string replacement
        testmessages = reduce(lambda x, y: str(x) + str(y), self.messages)
        self.assertEqual(0, testmessages.count('%') - testmessages.count('%%'))

    # z because this function must also execute lately for more interesting results
    def test_zinternationalization(self):
        """errorlib - internationalization"""
        # string internationalization
        testmessages = reduce(lambda x, y: str(x) + str(y), self.messages)
        self.assertEqual(0, testmessages.count('_('))
        
def create_test_suite():
    """
    Return test suite for the search engine.
    """
    return unittest.TestSuite((unittest.makeSuite(TestInternalErrorlibErrors, 'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
