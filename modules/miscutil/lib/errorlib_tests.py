# -*- coding: utf-8 -*-
## $Id$
## CDSware Search Engine unit tests.

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


__version__ =  """FIXME: last updated"""

import errorlib
import unittest

class TestInternalErrorlibErrors(unittest.TestCase):
    """
    """
    def test_get_msgs_for_code_list(self):
        """
        """
        self.assertEqual([('ERR_WEBCOMMENT_FOR_TESTING_PURPOSES', ' THIS IS FOR TESTING PURPOSES ONLY var1=var1 var2=var2 var3=var3 var4=var4 var5=var5 var6=var6 ')], 
                         errorlib.get_msgs_for_code_list([('ERR_WEBCOMMENT_FOR_TESTING_PURPOSES', 'var1', 'var2', 'var3', 'var4', 'var5', 'var6')]))
        self.assertEqual([('ERR_WEBCOMMENT_FOR_TESTING_PURPOSES', ' THIS IS FOR TESTING PURPOSES ONLY var1=var1 var2=var2 var3=var3 var4=??? var5=??? var6=??? '),
                        ('ERR_MISUTIL_PROGRAMMING_ERROR', " Programming error: Too few arguments given for error ERR_WEBCOMMENT_FOR_TESTING_PURPOSES ")], 
                         errorlib.get_msgs_for_code_list([('ERR_WEBCOMMENT_FOR_TESTING_PURPOSES', 'var1', 'var2', 'var3')]))
        self.assertEqual([('ERR_WEBCOMMENT_FOR_TESTING_PURPOSES', ' THIS IS FOR TESTING PURPOSES ONLY var1=var1 var2=var2 var3=var3 var4=var4 var5=var5 var6=var6 '), 
                        ('ERR_MISUTIL_PROGRAMMING_ERROR', " Programming error: Too many arguments given for error ERR_WEBCOMMENT_FOR_TESTING_PURPOSES ")], 
                         errorlib.get_msgs_for_code_list([('ERR_WEBCOMMENT_FOR_TESTING_PURPOSES', 'var1', 'var2', 'var3', 'var4', 'var5', 'var6', 'var7')]))



def create_test_suite():
    """
    Return test suite for the search engine.
    """
    return unittest.TestSuite((unittest.makeSuite(TestInternalErrorlibErrors,'test'),))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
