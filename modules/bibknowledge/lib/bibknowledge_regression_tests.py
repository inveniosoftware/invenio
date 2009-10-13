# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""Regression tests for BibKnowledge."""

import unittest
from invenio.config import CFG_SITE_URL
from invenio.bibknowledge import kb_exists, get_kba_values,\
     get_kbr_keys, get_kbd_values_for_bibedit, get_kbs_info, add_kb,\
     delete_kb, add_kb_mapping, remove_kb_mapping, get_kb_name, kb_mapping_exists
from invenio.testutils import make_test_suite, run_test_suite, test_web_page_content

class BibknowledgeTests(unittest.TestCase):
    """Test functions for bibknowledge."""

    def test_kb_pages_available(self):
        """bibknowledge - test /kb page availability"""
        kbpage = CFG_SITE_URL+"/kb"
        errs = test_web_page_content(kbpage)
        self.assertEqual([], errs)

    def test_kb_pages_curator_can_read(self):
        """bibknowledge - test that balthasar from the curator group can read page"""
        kbpage = CFG_SITE_URL+"/kb"
        errs = test_web_page_content(kbpage, username="balthasar",
                                     password="b123althasar",
                                     expected_text="BibKnowledge Admin")
        self.assertEqual([], errs)

    def test_EJOURNALS_exists(self):
        """bibknowledge - test that EJOURNALS kb is there"""
        isthere = kb_exists("EJOURNALS");
        self.assertEqual(True, isthere);

    def test_kbs_info(self):
        """bibknowledge - get_kbs_info returns EJOURNALS info"""
        myinfolist = get_kbs_info("", "EJOURNALS")
        myinfo = myinfolist[0]
        self.assertEqual(myinfo["name"],"EJOURNALS");

    def test_EJOURNALS_keys(self):
        """bibknowledge - test a left/right rule"""
        mykeys = get_kbr_keys("EJOURNALS", "Acta")
        self.assertEqual(2, len(mykeys))

    def test_get_kba_values(self):
        """bibknowledge - test recovering just values"""
        mylist = get_kba_values("EJOURNALS")
        self.assertEqual(327, len(mylist))

    def test_add_get_remove(self):
        """bibknowledge - test creating a kb, adding a mapping, removing it, removing kb"""
        new_kb_id = add_kb()
        new_name = get_kb_name(new_kb_id)
        add_kb_mapping(new_name, "foobar", "barfoo")
        fbexists = kb_mapping_exists(new_name, "foobar")
        self.assertEqual(True, fbexists)
        remove_kb_mapping(new_name, "foobar")
        fbexists = kb_mapping_exists(new_name, "foobar")
        self.assertEqual(False, fbexists)
        delete_kb(new_name)
        still_there = kb_exists(new_name)
        self.assertEqual(False, still_there)

    def test_kb_for_bibedit(self):
        """bibknowledge - test a dynamic db"""
        myvalues = get_kbd_values_for_bibedit("100__a", "", "Ellis")
        self.assertEqual(1, len(myvalues))

TEST_SUITE = make_test_suite(BibknowledgeTests)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)


