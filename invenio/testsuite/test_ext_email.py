# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""
Test unit for the miscutil/mailutils module.
"""

import os
import sys
import pkg_resources
from base64 import encodestring
from six import iteritems, StringIO
from flask import current_app

from invenio.ext.email import send_email
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class MailTestCase(InvenioTestCase):

    EMAIL_BACKEND = 'flask_email.backends.console.Mail'

    def setUp(self):
        super(MailTestCase, self).setUp()
        current_app.config['EMAIL_BACKEND'] = self.EMAIL_BACKEND
        self.__stdout = sys.stdout
        self.stream = sys.stdout = StringIO()

    def tearDown(self):
        del self.stream
        sys.stdout = self.__stdout
        del self.__stdout
        super(MailTestCase, self).tearDown()

    def flush_mailbox(self):
        self.stream = sys.stdout = StringIO()

    #def get_mailbox_content(self):
    #    messages = self.stream.getvalue().split('\n' + ('-' * 79) + '\n')
    #    return [message_from_string(m) for m in messages if m]


class TestMailUtils(MailTestCase):
    """
    mailutils TestSuite.
    """

    def test_console_send_email(self):
        """
        Test that the console backend can be pointed at an arbitrary stream.
        """
        msg_content = """Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Subject
From: from@example.com
To: to@example.com"""

        send_email('from@example.com', ['to@example.com'], subject='Subject',
                   content='Content')
        self.assertIn(msg_content, sys.stdout.getvalue())
        self.flush_mailbox()

        send_email('from@example.com', 'to@example.com', subject='Subject',
                   content='Content')
        self.assertIn(msg_content, sys.stdout.getvalue())
        self.flush_mailbox()


    def test_email_text_template(self):
        """
        Test email text template engine.
        """
        from invenio.ext.template import render_template_to_string

        contexts = {
            'ctx1': {'content': 'Content 1'},
            'ctx2': {'content': 'Content 2', 'header': 'Header 2'},
            'ctx3': {'content': 'Content 3', 'footer': 'Footer 3'},
            'ctx4': {'content': 'Content 4', 'header': 'Header 4', 'footer': 'Footer 4'}
        }

        msg_content = """Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: %s
From: from@example.com
To: to@example.com"""

        for name, ctx in iteritems(contexts):
            msg = render_template_to_string('mail_text.tpl', **ctx)
            send_email('from@example.com', ['to@example.com'], subject=name,
                       **ctx)
            email = sys.stdout.getvalue()
            self.assertIn(msg_content % name, email)
            self.assertIn(msg, email)
            self.flush_mailbox()

    def test_email_html_template(self):
        """
        Test email html template engine.
        """
        from invenio.ext.template import render_template_to_string

        contexts = {
            'ctx1': {'html_content': '<b>Content 1</b>'},
            'ctx2': {'html_content': '<b>Content 2</b>',
                     'html_header': '<h1>Header 2</h1>'},
            'ctx3': {'html_content': '<b>Content 3</b>',
                     'html_footer': '<i>Footer 3</i>'},
            'ctx4': {'html_content': '<b>Content 4</b>',
                     'html_header': '<h1>Header 4</h1>',
                     'html_footer': '<i>Footer 4</i>'}
        }

        def strip_html_key(ctx):
            return dict(map(lambda (k, v): (k[5:], v), iteritems(ctx)))

        for name, ctx in iteritems(contexts):
            msg = render_template_to_string('mail_html.tpl',
                                            **strip_html_key(ctx))
            send_email('from@example.com', ['to@example.com'], subject=name,
                       content='Content Text', **ctx)
            email = sys.stdout.getvalue()
            self.assertIn('Content-Type: multipart/alternative;', email)
            self.assertIn('Content Text', email)
            self.assertIn(msg, email)
            self.flush_mailbox()

    def test_email_html_image(self):
        """
        Test sending html message with an image.
        """
        html_images = {
            'img1': pkg_resources.resource_filename(
                'invenio.base',
                os.path.join('static', 'img', 'journal_water_dog.gif')
            )
        }
        send_email('from@example.com', ['to@example.com'],
                   subject='Subject', content='Content Text',
                   html_content='<img src="cid:img1"/>',
                   html_images=html_images)
        email = sys.stdout.getvalue()
        self.assertIn('Content Text', email)
        self.assertIn('<img src="cid:img1"/>', email)
        with open(html_images['img1'], 'r') as f:
            self.assertIn(encodestring(f.read()), email)
        self.flush_mailbox()

    def test_sending_attachment(self):
        """
        Test sending email with an attachment.
        """
        attachments = [
            pkg_resources.resource_filename(
                'invenio.base',
                os.path.join('static', 'img', 'journal_header.png')
            )
        ]
        send_email('from@example.com', ['to@example.com'],
                   subject='Subject', content='Content Text',
                   attachments=attachments)
        email = sys.stdout.getvalue()
        self.assertIn('Content Text', email)
        # First attachemnt is image/png
        self.assertIn('Content-Type: image/png', email)
        for attachment in attachments:
            with open(attachment, 'r') as f:
                self.assertIn(encodestring(f.read()), email)
        self.flush_mailbox()

    def test_single_recipient(self):
        """
        Test that the email receivers are hidden.
        """
        msg_content = """Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Subject
From: from@example.com
To: to@example.com"""

        send_email('from@example.com', ['to@example.com'],
                   subject='Subject', content='Content')
        email = sys.stdout.getvalue()
        self.assertIn(msg_content, email)
        self.flush_mailbox()

        send_email('from@example.com', 'to@example.com',
                   subject='Subject', content='Content')
        email = sys.stdout.getvalue()
        self.assertIn(msg_content, email)
        self.flush_mailbox()

    def test_bbc_undisclosed_recipients(self):
        """
        Test that the email receivers are hidden.
        """
        msg_content = """Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Subject
From: from@example.com
To: Undisclosed.Recipients:"""

        send_email('from@example.com', ['to@example.com', 'too@example.com'],
                   subject='Subject', content='Content')
        email = sys.stdout.getvalue()
        self.assertIn(msg_content, email)
        self.assertNotIn('Bcc: to@example.com,too@example.com', email)
        self.flush_mailbox()

        send_email('from@example.com', 'to@example.com, too@example.com',
                   subject='Subject', content='Content')
        email = sys.stdout.getvalue()
        self.assertIn(msg_content, email)
        self.assertNotIn('Bcc: to@example.com,too@example.com', email)
        self.flush_mailbox()


class TestAdminMailBackend(MailTestCase):

    EMAIL_BACKEND = 'invenio.ext.email.backends.console_adminonly.Mail'
    ADMIN_MESSAGE = "This message would have been sent to the following recipients"

    def test_simple_email_header(self):
        """
        Test simple email header.
        """
        from invenio.config import CFG_SITE_ADMIN_EMAIL
        from invenio.ext.template import render_template_to_string

        msg_content = """Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Subject
From: from@example.com
To: %s""" % (CFG_SITE_ADMIN_EMAIL, )

        msg = render_template_to_string('mail_text.tpl', content='Content')

        self.flush_mailbox()
        send_email('from@example.com', ['to@example.com'], subject='Subject',
                   content='Content')
        email = self.stream.getvalue()
        self.assertIn(msg_content, email)
        self.assertIn(self.ADMIN_MESSAGE, email)
        self.assertNotIn('Bcc:', email)
        self.assertIn(msg, email)
        self.flush_mailbox()

        send_email('from@example.com', 'to@example.com', subject='Subject',
                   content='Content')
        email = self.stream.getvalue()
        self.assertIn(msg_content, email)
        self.assertIn(self.ADMIN_MESSAGE, email)
        self.assertNotIn('Bcc:', email)
        self.assertIn(msg, email)
        self.flush_mailbox()


    def test_cc_bcc_headers(self):
        """
        Test that no Cc and Bcc headers are sent.
        """
        from invenio.config import CFG_SITE_ADMIN_EMAIL
        msg_content = """Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Subject
From: from@example.com
To: %s""" % (CFG_SITE_ADMIN_EMAIL, )

        send_email('from@example.com', ['to@example.com', 'too@example.com'],
                   subject='Subject', content='Content')
        email = self.stream.getvalue()
        self.assertIn(msg_content, email)
        self.assertIn(self.ADMIN_MESSAGE, email)
        self.assertIn('to@example.com,too@example.com', email)
        self.assertNotIn('Bcc: to@example.com,too@example.com', email)
        self.flush_mailbox()

        send_email('from@example.com', 'to@example.com, too@example.com',
                   subject='Subject', content='Content')
        email = self.stream.getvalue()
        self.assertIn(msg_content, email)
        self.assertIn(self.ADMIN_MESSAGE, email)
        self.assertIn('to@example.com,too@example.com', email)
        self.assertNotIn('Bcc: to@example.com,too@example.com', email)
        self.flush_mailbox()


TEST_SUITE = make_test_suite(TestMailUtils, TestAdminMailBackend)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
