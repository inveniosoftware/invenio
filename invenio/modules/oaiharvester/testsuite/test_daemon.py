# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Unit tests for the OAI harvester."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class TestOAIUtils(InvenioTestCase):

    """Test for OAI utility functions."""

    def test_identifier_filter(self):
        """oaiharvest - testing identifier filter."""
        from invenio.legacy.oaiharvest.daemon import get_identifier_names
        self.assertEqual(get_identifier_names("oai:mysite.com:1234"),
                         ["oai:mysite.com:1234"])
        self.assertEqual(get_identifier_names("oai:mysite.com:1234, oai:example.com:2134"),
                         ["oai:mysite.com:1234", "oai:example.com:2134"])
        self.assertEqual(get_identifier_names("oai:mysite.com:1234/testing, oai:example.com:record/1234"),
                         ["oai:mysite.com:1234/testing", "oai:example.com:record/1234"])

    def test_identifier_filter_special_arXiv(self):
        """oaiharvest - testing identifier filter for arXiv."""
        from invenio.legacy.oaiharvest.daemon import get_identifier_names
        self.assertEqual(get_identifier_names("oai:arxiv.org:1234.1245"),
                         ["oai:arXiv.org:1234.1245"])
        self.assertEqual(get_identifier_names("oai:arXiv.org:1234.1245, arXiv:1234.1245"),
                         ["oai:arXiv.org:1234.1245", "oai:arXiv.org:1234.1245"])
        self.assertEqual(get_identifier_names("oai:arXiv.org:1234.12452"),
                         ["oai:arXiv.org:1234.12452"])


TEST_SUITE = make_test_suite(TestOAIUtils)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
