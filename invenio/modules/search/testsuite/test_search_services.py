# -*- coding: utf-8 -*-

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

"""WebSearch services unit tests."""

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class WebSearchServicesJournalHintService(InvenioTestCase):

    """Check JournalHintService plugin."""

    def setUp(self):
        """Load plugin."""
        from invenio.modules.search.searchext.services.JournalHintService import \
            JournalHintService
        self.plugin = JournalHintService()

    def test_seems_a_journal_reference(self):
        """Check function JournalHintService.seems_a_journal_reference."""
        test_pairs = [
            # Empty strings
            ("", False),
            (" ", False),
            ("\t", False),
            ("\t \t", False),
            # Invenio and Inspire queries
            ("author:Tom", False),
            ("find a John", False),
            ("find date after 2001", False),
            ("year:2001 OR year:2002", False),
            # Invalid journals with bad format
            ("Monkey", False),
            ("Monkey monkey", False),
            ("Monkey monkey (1)", False),
            ("Monkey monkey 1234", False),
            # Invalid journals with good format
            ("Monkey monkey, 1234", True),
            ("Monkey (2000)", True),
            # Invalid journals with good format, utf8
            (u"Capellà Pere (2000)".encode("utf8"), True),
            (u"País Valencià, 1234".encode("utf8"), True),
            # Valid journal with good format
            ("JHEP 9906:028 (1999)", True),
            ("Phys. Rev. Lett. 83 (1999) 3605", True),
            ("Nucl.Phys.,B75,(1974),461", True),
            ("  Nucl.  Phys.   B75   (1974)  461   ", True),
            ("D.S. Salopek, J.R.Bond and J.M.Bardeen,Phys.Rev.D40(1989)1753.",
             True),
        ]

        for test_input, expected in test_pairs:
            test_output = self.plugin.seems_a_journal_reference(test_input)
            self.assertEqual(
                test_output,
                expected,
                "JournalHintService.seems_a_journal_reference('%s') "
                "returned '%s' instead of '%s'"
                % (repr(test_input), repr(test_output), repr(expected))
            )


TEST_SUITE = make_test_suite()

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
