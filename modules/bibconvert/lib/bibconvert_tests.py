# -*- coding: utf-8 -*-

## $Id$
## CDS Invenio bibconvert unit tests.

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

"""Unit tests for the bibconvert."""

__revision__ = "$Id$"

import unittest

from invenio import bibconvert

class TestFormattingFunctions(unittest.TestCase):
    """Test bibconvert formatting functions."""

    def test_ff(self):
        """bibconvert - formatting functions"""
        
        self.assertEqual("Hello world!", bibconvert.FormatField("ello world", "ADD(H,!)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world", "ABR(11,!)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("xHello world!x", "CUT(x,x)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("He11o wor1d!", "REP(1,l)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "SUP(NUM)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "LIM(12,R)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "WORDS(2)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "MINL(5)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "MAXL(12)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world! @", "EXP(@,1)"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "IF(Hello world!,ORIG,)"))
        self.assertEqual("", bibconvert.FormatField("Hello world!", "NUM()"))
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!   ", "SHAPE()"))
        self.assertEqual("HELLO WORLD!", bibconvert.FormatField("Hello world!", "UP()"))
        self.assertEqual("hello world!", bibconvert.FormatField("Hello world!", "DOWN()"))
        self.assertEqual("Hello World!", bibconvert.FormatField("Hello world!", "CAP()"))


class TestGlobalFormattingFunctions(unittest.TestCase):
    """Test bibconvert global formatting functions."""

    def test_gff(self):
        """bibconvert - global formatting functions"""
    
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!","DEFP()"))

class TestGenerateValues(unittest.TestCase):
    """Test bibconvert value generation."""

    def test_gv(self):
        """bibconvert - value generation"""
        
        self.assertEqual("Hello world!", bibconvert.generate("VALUE(Hello world!)"))

class TestParseData(unittest.TestCase):
    """Test bibconvert input data parsing."""

    def test_idp(self):
        """bibconvert - input data parsing"""
        
        self.assertEqual(['A','B','C','D'], bibconvert.parse_field_definition("A---B---C---D"))

class TestRegExp(unittest.TestCase):
    """Test bibconvert regular expressions"""

    def test_regexp(self):
        """bibconvert - regular expressions"""
        
        self.assertEqual("Hello world!", bibconvert.FormatField("Hello world!", "RE([A-Z][a-z].*!)"))

class TestBCCL(unittest.TestCase):
    """Test bibconvert BCCL complinacy"""

    def xtest_bccl_09(self):
        """bibconvert - BCCL v.0.9 compliancy"""

        # FIXME: put proper tests here
        self.assertEqual(1, 1)

class TestKnowledgeBase(unittest.TestCase):
    """Test bibconvert knowledge base"""

    def xtest_enc(self):
        """bibconvert - knowledge base"""
        
        # FIXME: put proper tests here
        self.assertEqual(1, 1)

class TestErrorCodes(unittest.TestCase):
    """Test bibconvert error codes"""

    def xtest_enc(self):
        """bibconvert - error codes"""
        
        # FIXME: put proper tests here
        self.assertEqual(1, 1)

class TestEncodings(unittest.TestCase):
    """Test bibconvert encodings"""

    def xtest_enc(self):
        """bibconvert - encodings"""
        
        # FIXME: put proper tests here
        self.assertEqual(1, 1)


def create_test_suite():
    """Return test suite for the bibconvert module."""

    return unittest.TestSuite((unittest.makeSuite(TestFormattingFunctions, 'test'),
                               unittest.makeSuite(TestGlobalFormattingFunctions, 'test'),
                               unittest.makeSuite(TestGenerateValues, 'test'),
                               unittest.makeSuite(TestParseData, 'test'),
                               unittest.makeSuite(TestRegExp, 'test'),
                               unittest.makeSuite(TestBCCL, 'test'),
                               unittest.makeSuite(TestKnowledgeBase, 'test'),
                               unittest.makeSuite(TestErrorCodes, 'test'),
                               unittest.makeSuite(TestEncodings, 'test'),
                               ))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
