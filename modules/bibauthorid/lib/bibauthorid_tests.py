# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

import unittest
import bibauthorid_utils as baidu
import bibauthorid_authorname_utils as bau
from invenio.testutils import make_test_suite, run_test_suite

class TestSplitNameParts(unittest.TestCase):
    """Test for the functionality of splitting name strings in parts"""

    def test_split_name_parts(self):
        """bibauthorid - test split name parts"""

        self.assertEqual(['This', ['I', 'F'], ['Isacorrect', 'Fullname'], [0, 1]],
         baidu.split_name_parts('This, Isacorrect Fullname'))

        self.assertEqual(['', [], []], baidu.split_name_parts(''))

        self.assertEqual(['name', ['F', 'I'], ['Full', 'Inverted'], [0, 1]],
         baidu.split_name_parts('full inverted name'))

        self.assertEqual(['Two Words', ['S', 'N'], ['Surname', 'Name'], [0, 1]],
         baidu.split_name_parts('Two Words, Surname Name'))

        self.assertEqual(['Strange+)*{ (=]&-$Char', ['N'], ['Name'], [0]],
         baidu.split_name_parts('Strange+)*{ (=]&-$Char, Name'))

class TestCreateUnifiedNames(unittest.TestCase):
    """Test for the functionality of creation of unified names strings"""

    def test_create_unified_name(self):
        """bibauthorid - test creation of unified name strings"""

        self.assertEqual('this, I. F. ',
            baidu.create_unified_name('this, isa fullname'))

        self.assertEqual('fullname, T. I. ',
            baidu.create_unified_name('this isa fullname'))

        self.assertEqual(', ',
            baidu.create_unified_name(''))

        self.assertEqual('Strange$![+{&]+)= Chars, T. ',
            baidu.create_unified_name('Strange$![+{&]+)= Chars, Twonames'))


class TestCreateNormalizedName(unittest.TestCase):
    """Test for the functionality of creation of normalized names strings"""

    def test_create_normalized_name(self):
        """bibauthorid - test creation of normalized name strings"""

        self.assertEqual('this, Isa Fullname',
            baidu.create_normalized_name(
            baidu.split_name_parts('this, isa fullname')))

        self.assertEqual('fullname, This Isa',
            baidu.create_normalized_name(
            baidu.split_name_parts('this isa fullname')))

        self.assertEqual('Strange&][{}) ==}{$*]!, Name',
            baidu.create_normalized_name(
            baidu.split_name_parts('Strange&][{}) ==}{$*]!, Name')))

        self.assertEqual(',',
            baidu.create_normalized_name(
            baidu.split_name_parts('')))

class TestCleanNameString(unittest.TestCase):
    """Test for the functionality of creation of cleaned names strings"""

    def test_clean_name_string(self):
        """bibauthorid - test cleaning of name strings"""

        self.assertEqual('this is a full name',
           baidu.clean_name_string('this is a full name'))

        self.assertEqual('this is a full ,. pz',
            baidu.clean_name_string('this is a full ;,.$&[{{}}(=*)+]pz'))

        self.assertEqual('',
            baidu.clean_name_string(''))

class TestCompareNames(unittest.TestCase):
    """Test for the functionality of comparison of names strings"""

    def test_compare_names(self):
        """bibauthorid - test names comparison funcions"""

        self.assertEqual(0.94999999999999996,
            bau.compare_names('Ellis, j.', 'Ellis, j.'))

        self.assertEqual(1.0,
            bau.compare_names('Ellis, john', 'Ellis, john'))

        self.assertEqual(1.0,
            bau.compare_names('John Ellis', 'John Ellis'))

#        self.assertEqual(0.94999999999999996,
#            bau.compare_names('J. Ellis','J. Ellis'))

        self.assertEqual(0.0,
            bau.compare_names('John Ellis', 'John Mark'))

        self.assertEqual(0.0,
            bau.compare_names('Ellis, John', 'Mark, John'))

        self.assertEqual(0.0,
            bau.compare_names('', ''))


TEST_SUITE = make_test_suite(TestSplitNameParts,
                             TestCreateUnifiedNames,
                             TestCreateNormalizedName,
                             TestCleanNameString,
                             TestCompareNames,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
