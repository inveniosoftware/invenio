# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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
Invenio mail sending utilities.  send_email() is the main API function
people should be using; just check out its docstring.
"""

__revision__ = "$Id$"

import os
import re
import sys

from email import Encoders
from email.Header import Header
from email.MIMEBase import MIMEBase
from email.MIMEImage import MIMEImage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import formatdate
from flask import g
from flask_email.message import EmailMultiAlternatives, EmailMessage
from formatter import DumbWriter, AbstractFormatter
from six import iteritems, StringIO
from time import sleep

from invenio.base.globals import cfg
from invenio.base.helpers import unicodifier
from invenio.ext.template import render_template_to_string

from .errors import EmailError

default_ln = lambda ln: cfg.get('CFG_SITE_LANG') if ln is None else ln


def setup_app(app):
    """
    Prepare application config from Invenio configuration.

    @see: https://flask-email.readthedocs.org/en/latest/#configuration
    """
    cfg = app.config

    app.config.setdefault('EMAIL_BACKEND', cfg.get(
        'CFG_EMAIL_BACKEND', 'flask_email.backends.smtp.Mail'))
    app.config.setdefault('DEFAULT_FROM_EMAIL', cfg['CFG_SITE_SUPPORT_EMAIL'])
    app.config.setdefault('SERVER_EMAIL', cfg['CFG_SITE_ADMIN_EMAIL'])
    app.config.setdefault('ADMINS', (('', cfg['CFG_SITE_ADMIN_EMAIL']),))
    app.config.setdefault('MANAGERS', (cfg['CFG_SITE_SUPPORT_EMAIL'], ))

    CFG_MISCUTIL_SMTP_HOST = cfg.get('CFG_MISCUTIL_SMTP_HOST')
    CFG_MISCUTIL_SMTP_PORT = cfg.get('CFG_MISCUTIL_SMTP_PORT')
    CFG_MISCUTIL_SMTP_USER = cfg.get('CFG_MISCUTIL_SMTP_USER', '')
    CFG_MISCUTIL_SMTP_PASS = cfg.get('CFG_MISCUTIL_SMTP_PASS', '')
    CFG_MISCUTIL_SMTP_TLS = cfg.get('CFG_MISCUTIL_SMTP_TLS', False)

    app.config.setdefault('EMAIL_HOST', CFG_MISCUTIL_SMTP_HOST)
    app.config.setdefault('EMAIL_PORT', CFG_MISCUTIL_SMTP_PORT)
    app.config.setdefault('EMAIL_HOST_USER', CFG_MISCUTIL_SMTP_USER)
    app.config.setdefault('EMAIL_HOST_PASSWORD', CFG_MISCUTIL_SMTP_PASS)
    app.config.setdefault('EMAIL_USE_TLS', CFG_MISCUTIL_SMTP_TLS)
    # app.config['EMAIL_USE_SSL']: defaults to False

    app.config.setdefault('EMAIL_FILE_PATH', cfg['CFG_LOGDIR'])
    return app


def scheduled_send_email(fromaddr,
                         toaddr,
                         subject="",
                         content="",
                         header=None,
                         footer=None,
                         copy_to_admin=0,
                         attempt_times=1,
                         attempt_sleeptime=10,
                         user=None,
                         other_bibtasklet_arguments=None,
                         replytoaddr="",
                         bccaddr="",
                        ):
    """
    Like send_email, but send an email via the bibsched
    infrastructure.
    @param fromaddr: sender
    @type fromaddr: string
    @param toaddr: list of receivers
    @type toaddr: string (comma separated) or list of strings
    @param subject: the subject
    @param content: the body of the message
    @param header: optional header, otherwise default is used
    @param footer: optional footer, otherwise default is used
    @param copy_to_admin: set to 1 in order to send email the admins
    @param attempt_times: try at least n times before giving up sending
    @param attempt_sleeptime: number of seconds to sleep between two attempts
    @param user: the user name to user when scheduling the bibtasklet. If
        None, the sender will be used
    @param other_bibtasklet_arguments: other arguments to append to the list
        of arguments to the call of task_low_level_submission
    @param replytoaddr: [string or list-of-strings] to be used for the
                        reply-to header of the email (if string, then
                        receivers are separated by ',')
    @param bccaddr: [string or list-of-strings] to be used for BCC header
                     of the email
                    (if string, then receivers are separated by ',')
    @return: the scheduled bibtasklet
    """
    from invenio.legacy.bibsched.bibtask import task_low_level_submission
    if not isinstance(toaddr, (unicode, str)):
        toaddr = ','.join(toaddr)
    if not isinstance(replytoaddr, (unicode, str)):
        replytoaddr = ','.join(replytoaddr)

    toaddr = remove_temporary_emails(toaddr)

    if user is None:
        user = fromaddr
    if other_bibtasklet_arguments is None:
        other_bibtasklet_arguments = []
    else:
        other_bibtasklet_arguments = list(other_bibtasklet_arguments)
    if not header is None:
        other_bibtasklet_arguments.extend(("-a", "header=%s" % header))
    if not footer is None:
        other_bibtasklet_arguments.extend(("-a", "footer=%s" % footer))
    return task_low_level_submission(
        "bibtasklet", user, "-T", "bst_send_email",
        "-a", "fromaddr=%s" % fromaddr,
        "-a", "toaddr=%s" % toaddr,
        "-a", "replytoaddr=%s" % replytoaddr,
        "-a", "subject=%s" % subject,
        "-a", "content=%s" % content,
        "-a", "copy_to_admin=%s" % copy_to_admin,
        "-a", "attempt_times=%s" % attempt_times,
        "-a", "attempt_sleeptime=%s" % attempt_sleeptime,
        "-a", "bccaddr=%s" % bccaddr,
        *other_bibtasklet_arguments)


def send_email(fromaddr,
               toaddr,
               subject="",
               content="",
               html_content='',
               html_images=None,
               header=None,
               footer=None,
               html_header=None,
               html_footer=None,
               copy_to_admin=0,
               attempt_times=1,
               attempt_sleeptime=10,
               debug_level=0,
               ln=None,
               charset=None,
               replytoaddr="",
               attachments=None,
               bccaddr="",
               forward_failures_to_admin=True,
               ):
    """Send a forged email to TOADDR from FROMADDR with message created from subjet, content and possibly
    header and footer.
    @param fromaddr: [string] sender
    @param toaddr: [string or list-of-strings] list of receivers (if string, then
                   receivers are separated by ','). BEWARE: If more than once receiptiant is given,
                   the receivers are put in BCC and To will be "Undisclosed.Recipients:".
    @param subject: [string] subject of the email
    @param content: [string] content of the email
    @param html_content: [string] html version of the email
    @param html_images: [dict] dictionary of image id, image path
    @param header: [string] header to add, None for the Default
    @param footer: [string] footer to add, None for the Default
    @param html_header: [string] header to add to the html part, None for the Default
    @param html_footer: [string] footer to add to the html part, None for the Default
    @param copy_to_admin: [int] if 1 add CFG_SITE_ADMIN_EMAIL in receivers
    @param attempt_times: [int] number of tries
    @param attempt_sleeptime: [int] seconds in between tries
    @param debug_level: [int] debug level
    @param ln: [string] invenio language
    @param charset: [string] the content charset. By default is None which means
    to try to encode the email as ascii, then latin1 then utf-8.
    @param replytoaddr: [string or list-of-strings] to be used for the
                        reply-to header of the email (if string, then
                        receivers are separated by ',')
    @param attachments: list of paths of files to be attached. Alternatively,
        every element of the list could be a tuple: (filename, mimetype)
    @param bccaddr: [string or list-of-strings] to be used for BCC header of the email
                    (if string, then receivers are separated by ',')
    @param forward_failures_to_admin: [bool] prevents infinite recursion
                                             in case of admin reporting,
                                             when the problem is not in
                                             the e-mail address format,
                                             but rather in the network

    If sending fails, try to send it ATTEMPT_TIMES, and wait for
    ATTEMPT_SLEEPTIME seconds in between tries.

    e.g.:
    send_email('foo.bar@cern.ch', 'bar.foo@cern.ch', 'Let\'s try!'', 'check 1234', '<strong>check</strong> <em>1234</em><img src="cid:image1">', {'image1': '/tmp/quantum.jpg'})

    @return: [bool]: True if email was sent okay, False if it was not.
    """
    from invenio.ext.logging import register_exception
    ln = default_ln(ln)

    if html_images is None:
        html_images = {}

    if type(toaddr) is not list:
        toaddr = toaddr.strip().split(',')
    toaddr = remove_temporary_emails(toaddr)

    usebcc = len(toaddr) > 1  # More than one address, let's use Bcc in place of To

    if copy_to_admin:
        if cfg['CFG_SITE_ADMIN_EMAIL'] not in toaddr:
            toaddr.append(cfg['CFG_SITE_ADMIN_EMAIL'])

    if type(bccaddr) is not list:
        bccaddr = bccaddr.strip().split(',')

    msg = forge_email(fromaddr, toaddr, subject, content, html_content,
                       html_images, usebcc, header, footer, html_header,
                       html_footer, ln, charset, replytoaddr, attachments,
                       bccaddr)

    if attempt_times < 1 or not toaddr:
        try:
            raise EmailError(g._(
                'The system is not attempting to send an email from %(x_from)s'
                ', to %(x_to)s, with body %(x_body)s.', x_from=fromaddr,
                x_to=toaddr, x_body=content))
        except EmailError:
            register_exception()
        return False
    sent = False
    failure_reason = ''
    while not sent and attempt_times > 0:
        try:
            sent = msg.send()
        except Exception as e:
            failure_reason = str(e)
            register_exception()
            if debug_level > 1:
                try:
                    raise EmailError(g._('Error in sending message. \
                        Waiting %(sec)s seconds. Exception is %(exc)s, \
                        while sending email from %(sender)s to %(receipient)s \
                        with body %(email_body)s.', \
                        sec = attempt_sleeptime, \
                        exc = sys.exc_info()[0], \
                        sender = fromaddr, \
                        receipient = toaddr, \
                        email_body = content))
                except EmailError:
                    register_exception()
        if not sent:
            attempt_times -= 1
            if attempt_times > 0:  # sleep only if we shall retry again
                sleep(attempt_sleeptime)
    if not sent:
        # report failure to the admin with the intended message, its
        # sender and recipients
        if forward_failures_to_admin:
            # prepend '> ' to every line of the original message
            quoted_body = '> ' + '> '.join(content.splitlines(True))

            # define and fill in the report template
            admin_report_subject = g._('Error while sending an email: %(x_subject)s',
                                       x_subject=subject)
            admin_report_body = g._(
                "\nError while sending an email.\n"
                "Reason: %(x_reason)s\n"
                "Sender: \"%(x_sender)s\"\n"
                "Recipient(s): \"%(x_recipient)s\"\n\n"
                "The content of the mail was as follows:\n"
                "%(x_body)s",
                x_reason=failure_reason,
                x_sender=fromaddr,
                x_recipient=', '.join(toaddr),
                x_body=quoted_body)

            send_email(cfg['CFG_SITE_ADMIN_EMAIL'], cfg['CFG_SITE_ADMIN_EMAIL'],
                       admin_report_subject, admin_report_body,
                       forward_failures_to_admin=False)

        try:
            raise EmailError(g._(
                'Error in sending email from %(x_from)s to %(x_to)s with body'
                '%(x_body)s.', x_from=fromaddr, x_to=toaddr, x_body=content))
        except EmailError:
            register_exception()
    return sent


def attach_embed_image(email, image_id, image_path):
    """
    Attach an image to the email.
    """
    with open(image_path, 'rb') as image_data:
        img = MIMEImage(image_data.read())
        img.add_header('Content-ID', '<%s>' % image_id)
        img.add_header('Content-Disposition', 'attachment', filename=os.path.split(image_path)[1])
        email.attach(img)


def forge_email(fromaddr, toaddr, subject, content, html_content='',
                html_images=None, usebcc=False, header=None, footer=None,
                html_header=None, html_footer=None, ln=None,
                charset=None, replytoaddr="", attachments=None, bccaddr=""):
    """Prepare email. Add header and footer if needed.
    @param fromaddr: [string] sender
    @param toaddr: [string or list-of-strings] list of receivers (if string, then
                   receivers are separated by ',')
    @param usebcc: [bool] True for using Bcc in place of To
    @param subject: [string] subject of the email
    @param content: [string] content of the email
    @param html_content: [string] html version of the email
    @param html_images: [dict] dictionary of image id, image path
    @param header: [string] None for the default header
    @param footer: [string] None for the default footer
    @param ln: language
    @charset: [string] the content charset. By default is None which means
    to try to encode the email as ascii, then latin1 then utf-8.
    @param replytoaddr: [string or list-of-strings] to be used for the
                        reply-to header of the email (if string, then
                        receivers are separated by ',')
    @param attachments: list of paths of files to be attached. Alternatively,
        every element of the list could be a tuple: (filename, mimetype)
    @param bccaddr: [string or list-of-strings] to be used for BCC header of the email
                    (if string, then receivers are separated by ',')
    @return: forged email as an EmailMessage object"""
    ln = default_ln(ln)
    if html_images is None:
        html_images = {}

    content = render_template_to_string('mail_text.tpl',
                                        content=unicodifier(content),
                                        header=unicodifier(header),
                                        footer=unicodifier(footer)
                                        ).encode('utf8')

    if type(toaddr) is list:
        toaddr = ','.join(toaddr)

    if type(bccaddr) is list:
        bccaddr = ','.join(bccaddr)

    if type(replytoaddr) is list:
        replytoaddr = ','.join(replytoaddr)

    toaddr = remove_temporary_emails(toaddr)

    headers = {}
    kwargs = {'to': [], 'cc': [], 'bcc': []}

    if replytoaddr:
        headers['Reply-To'] = replytoaddr
    if usebcc:
        headers['Bcc'] = bccaddr
        kwargs['bcc'] = toaddr.split(',') + bccaddr.split(',')
        kwargs['to'] = ['Undisclosed.Recipients:']
    else:
        kwargs['to'] = toaddr.split(',')
    headers['From'] = fromaddr
    headers['Date'] = formatdate(localtime=True)
    headers['User-Agent'] = 'Invenio %s at %s' % (cfg['CFG_VERSION'],
                                                  cfg['CFG_SITE_URL'])

    if html_content:
        html_content = render_template_to_string(
            'mail_html.tpl',
            content=unicodifier(html_content),
            header=unicodifier(html_header),
            footer=unicodifier(html_footer)
            ).encode('utf8')

        msg_root = EmailMultiAlternatives(subject=subject, body=content,
                                          from_email=fromaddr,
                                          headers=headers, **kwargs)
        msg_root.attach_alternative(html_content, "text/html")

        #if not html_images:
        #    # No image? Attach the HTML to the root
        #    msg_root.attach(msg_text)
        #else:
        if html_images:
            # Image(s)? Attach the HTML and image(s) as children of a
            # "related" block
            msg_related = MIMEMultipart('related')
            #msg_related.attach(msg_text)
            for image_id, image_path in iteritems(html_images):
                attach_embed_image(msg_related, image_id, image_path)
            msg_root.attach(msg_related)
    else:
        msg_root = EmailMessage(subject=subject, body=content,
                                from_email=fromaddr, headers=headers, **kwargs)

    if attachments:
        from invenio.legacy.bibdocfile.api import _mimes, guess_format_from_url
        #old_msg_root = msg_root
        #msg_root = MIMEMultipart()
        #msg_root.attach(old_msg_root)
        for attachment in attachments:
            try:
                mime = None
                if type(attachment) in (list, tuple):
                    attachment, mime = attachment
                if mime is None:
                    ## Automatic guessing of mimetype
                    mime = _mimes.guess_type(attachment)[0]
                if mime is None:
                    ext = guess_format_from_url(attachment)
                    mime = _mimes.guess_type("foo" + ext)[0]
                if not mime:
                    mime = 'application/octet-stream'
                part = MIMEBase(*mime.split('/', 1))
                part.set_payload(open(attachment, 'rb').read())
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attachment))
                msg_root.attach(part)
            except:
                from invenio.ext.logging import register_exception
                register_exception(alert_admin=True, prefix="Can't attach %s" % attachment)

    return msg_root

RE_NEWLINES = re.compile(r'<br\s*/?>|</p>', re.I)
RE_SPACES = re.compile(r'\s+')
RE_HTML_TAGS = re.compile(r'<.+?>')


def email_strip_html(html_content):
    """Strip html tags from html_content, trying to respect formatting."""
    html_content = RE_SPACES.sub(' ', html_content)
    html_content = RE_NEWLINES.sub('\n', html_content)
    html_content = RE_HTML_TAGS.sub('', html_content)
    html_content = html_content.split('\n')
    out = StringIO()
    out_format = AbstractFormatter(DumbWriter(out))
    for row in html_content:
        out_format.add_flowing_data(row)
        out_format.end_paragraph(1)
    return out.getvalue()


def remove_temporary_emails(emails):
    """
    Removes the temporary emails (which are constructed randomly when user logs in
    with an external authentication provider which doesn't supply an email
    address) from an email list.

    @param emails: email list (if string, then receivers are separated by ',')
    @type emails: [str]|str

    @rtype: list|str
    """
    from invenio.modules.access.local_config import CFG_TEMP_EMAIL_ADDRESS
    _RE_TEMPORARY_EMAIL = re.compile(CFG_TEMP_EMAIL_ADDRESS % r'.+?', re.I)

    if type(emails) in (str, unicode):
        emails = [email.strip() for email in emails.split(',') if email.strip()]
        emails = [email for email in emails if not _RE_TEMPORARY_EMAIL.match(email)]
        return ','.join(emails)
    else:
        return [email for email in emails if not _RE_TEMPORARY_EMAIL.match(email)]


def get_mail_header(value):
    """
    Return a MIME-compliant header-string. Will join lists of strings
    into one string with comma (,) as separator.
    """
    if not isinstance(value, basestring):
        value = ','.join(value)
    try:
        value = value.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        value = Header(value, 'utf-8')
    return value
