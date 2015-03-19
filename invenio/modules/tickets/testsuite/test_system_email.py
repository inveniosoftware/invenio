# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013, 2015 CERN.
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


"""Unit tests for bibcatalog_system_email library."""

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.testsuite.test_ext_email import MailTestCase


class BibCatalogSystemEmailTest(MailTestCase):
    """Testing of BibCatalog."""

    EMAIL_BACKEND = 'flask_email.backends.console.Mail'

    def setUp(self):
        super(BibCatalogSystemEmailTest, self).setUp()
        from invenio.legacy.bibcatalog import system_email as bibcatalog_system_email
        from invenio.config import CFG_SITE_SUPPORT_EMAIL
        self.email = bibcatalog_system_email.BibCatalogSystemEmail()
        bibcatalog_system_email.CFG_BIBCATALOG_SYSTEM_TICKETS_EMAIL = CFG_SITE_SUPPORT_EMAIL
        bibcatalog_system_email.CFG_BIBCATALOG_SYSTEM = 'EMAIL'
        pass

    def test_email_ticket_search_exception_not_implemented(self):
        """bibcatalog_system_email - execution raises NotImplementedError exception"""

        self.assertRaises(NotImplementedError, self.email.ticket_search, 1)

    def test_ticket_submit_via_email(self):
        """bibcatalog_system_email - test creating ticket via email"""

        # TODO: our return values are ticket id or none; check both cases
        self.assertTrue(self.email.ticket_submit(subject="Issue with RT", text="The RT system is not as good as the email ticketing", owner='eduardo', priority=3, queue='TEST', requestor='Joeb', recordid=100))

    def test_ticket_comment_via_email(self):
        """bibcatalog_system_email - test commention on ticket via email"""

        self.assertTrue(self.email.ticket_comment(uid=1, ticketid='d834bnklca', comment='Eduardo is commenting on ticket blah, blah, blah'))

    def test_ticket_assign_via_email(self):
        """bibcatalog_system_email - test commention on ticket via email"""

        self.assertTrue(self.email.ticket_assign(uid=1, ticketid='d834bnklca', to_user='jrbl'))

    def test_ticket_set_attribute_via_email(self):
        """bibcatalog_system_email - test setting attribute on ticket via email"""

        self.assertTrue(self.email.ticket_set_attribute(uid=1, ticketid='d834bnklca', attribute='priority', new_value='1'))

    def test_ckeck_system(self):
        """bibcatalog_system_email - check_system returns true if successful, a message otherwise"""

        self.assertEqual(self.email.check_system(), '')

    def test_ticket_get_info(self):
        """bibcatalog_system_email - ticket_get_info raises NotImplementedError exception"""

        self.assertRaises(NotImplementedError, self.email.ticket_get_info, uid=1, ticketid=0)


TEST_SUITE = make_test_suite(BibCatalogSystemEmailTest)


if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
