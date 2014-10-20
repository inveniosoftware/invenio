# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""
Invenio mail sending utilities.  send_email() is the main API function
people should be using; just check out its docstring.
"""

__revision__ = "$Id$"

import sys
from time import sleep
import smtplib
import socket
import re
import os

from email.Header import Header
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from email.MIMEImage import MIMEImage
from email.Utils import formatdate
from cStringIO import StringIO
from formatter import DumbWriter, AbstractFormatter
from invenio.access_control_config import CFG_TEMP_EMAIL_ADDRESS

from invenio.config import \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_NAME, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_MISCUTIL_SMTP_HOST, \
     CFG_MISCUTIL_SMTP_PORT, \
     CFG_VERSION, \
     CFG_DEVEL_SITE

try:
    from invenio.config import \
         CFG_MISCUTIL_SMTP_USER,\
         CFG_MISCUTIL_SMTP_PASS,\
         CFG_MISCUTIL_SMTP_TLS
except ImportError:
    CFG_MISCUTIL_SMTP_USER = ''
    CFG_MISCUTIL_SMTP_PASS = ''
    CFG_MISCUTIL_SMTP_TLS = False

from invenio.messages import wash_language, gettext_set_language
from invenio.textutils import guess_minimum_encoding
from invenio.errorlib import register_exception
from invenio.miscutil_config import InvenioMiscUtilError


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
    @param bccaddr: [string or list-of-strings] to be used for BCC header of the email
                    (if string, then receivers are separated by ',')
    @return: the scheduled bibtasklet
    """
    from invenio.bibtask import task_low_level_submission
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
               ln=CFG_SITE_LANG,
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

    if html_images is None:
        html_images = {}

    if type(toaddr) is str:
        toaddr = toaddr.strip().split(',')
    toaddr = remove_temporary_emails(toaddr)

    if type(bccaddr) is str:
        bccaddr = bccaddr.strip().split(',')

    usebcc = len(toaddr) > 1  # More than one address, let's use Bcc in place of To

    if copy_to_admin:
        if CFG_SITE_ADMIN_EMAIL not in toaddr:
            toaddr.append(CFG_SITE_ADMIN_EMAIL)
    if CFG_DEVEL_SITE:  # if we are on a development site, we don't want to send external e-mails
        content = """
--------------------------------------------------------------
This message would have been sent to the following recipients:
%s
--------------------------------------------------------------
%s""" % (toaddr, content)
        toaddr = CFG_SITE_ADMIN_EMAIL
        usebcc = False
    body = forge_email(fromaddr, toaddr, subject, content, html_content,
                       html_images, usebcc, header, footer, html_header,
                       html_footer, ln, charset, replytoaddr, attachments,
                       bccaddr)

    _ = gettext_set_language(CFG_SITE_LANG)

    if attempt_times < 1 or not toaddr:
        try:
            raise InvenioMiscUtilError(_('The system is not attempting to send an email from %s, to %s, with body %s.') % (fromaddr, toaddr, body))
        except InvenioMiscUtilError, exc:
            register_exception()
#        log('ERR_MISCUTIL_NOT_ATTEMPTING_SEND_EMAIL', fromaddr, toaddr, body)
        return False
    sent = False
    failure_reason = ''
    failure_details = ''
    while not sent and attempt_times > 0:
        try:
            server = smtplib.SMTP(CFG_MISCUTIL_SMTP_HOST, CFG_MISCUTIL_SMTP_PORT)
            if debug_level > 2:
                server.set_debuglevel(1)
            else:
                server.set_debuglevel(0)

            if CFG_MISCUTIL_SMTP_TLS:
                server.ehlo()
                server.starttls()
                server.ehlo()
            if CFG_MISCUTIL_SMTP_USER and CFG_MISCUTIL_SMTP_PASS:
                server.login(CFG_MISCUTIL_SMTP_USER, CFG_MISCUTIL_SMTP_PASS)
            if isinstance(toaddr, basestring):
                toaddr = [toaddr]
            server.sendmail(fromaddr, toaddr + bccaddr, body)
            server.quit()
            sent = True
        except (smtplib.SMTPException, socket.error) as e:
            failure_reason = type(e).__name__
            failure_details = str(e)
            register_exception()
            if debug_level > 1:
                try:
                    raise InvenioMiscUtilError(_('Error in connecting to the SMPT server waiting %s seconds. Exception is %s, while sending email from %s to %s with body %s.') % (attempt_sleeptime, sys.exc_info()[0], fromaddr, toaddr, body))
                except InvenioMiscUtilError, exc:
                    register_exception()
#                log('ERR_MISCUTIL_CONNECTION_SMTP', attempt_sleeptime,
#                    sys.exc_info()[0], fromaddr, toaddr, body)
        if not sent:
            attempt_times -= 1
            if attempt_times > 0:  # sleep only if we shall retry again
                sleep(attempt_sleeptime)
    if not sent:
        # report failure to the admin with the intended message, its
        # sender and recipients
        if forward_failures_to_admin:
            # prepend '> ' to every line of the original message
            quoted_body = '> ' + '> '.join(body.splitlines(True))

            # define and fill in the report template
            admin_report_subject = _('Error while sending an email: %s') % (subject)
            admin_report_body = _("\nError while sending an email.\n"
                                  "Reason: %s\n"
                                  "Details: %s\n"
                                  "Sender: \"%s\"\n"
                                  "Recipient(s): \"%s\"\n\n"
                                  "The content of the mail was as follows:\n"
                                  "%s") % (failure_reason, failure_details,
                                           fromaddr, ', '.join(toaddr),
                                           quoted_body)

            send_email(CFG_SITE_ADMIN_EMAIL, CFG_SITE_ADMIN_EMAIL,
                       admin_report_subject, admin_report_body,
                       forward_failures_to_admin=False)

        try:
            raise InvenioMiscUtilError(_('Error in sending email from %s to %s with body %s.') % (fromaddr, toaddr, body))
        except InvenioMiscUtilError, exc:
            register_exception()
#        log('ERR_MISCUTIL_SENDING_EMAIL', fromaddr, toaddr, body)
    return sent


def email_header(ln=CFG_SITE_LANG):
    """The header of the email
    @param ln: language
    @return: header as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard header
    out = """%(hello)s
        """ % {
            'hello':  _("Hello:")
            }
    return out


def email_html_header(ln=CFG_SITE_LANG):
    """The header of the email
    @param ln: language
    @return: header as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard header
    out = """%(hello)s<br />
        """ % {
            'hello':  _("Hello:")
            }
    return out


def email_footer(ln=CFG_SITE_LANG):
    """The footer of the email
    @param ln: language
    @return: footer as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard footer
    out = """\n\n%(best_regards)s
--
%(sitename)s <%(siteurl)s>
%(need_intervention_please_contact)s <%(sitesupportemail)s>
        """ % {
            'sitename': CFG_SITE_NAME_INTL[ln],
            'best_regards': _("Best regards"),
            'siteurl': CFG_SITE_URL,
            'need_intervention_please_contact': _("Need human intervention?  Contact"),
            'sitesupportemail': CFG_SITE_SUPPORT_EMAIL
            }
    return out


def email_html_footer(ln=CFG_SITE_LANG):
    """The html footer of the email
    @param ln: language
    @return: footer as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard footer
    out = """<br /><br /><em>%(best_regards)s</em>
    <hr />
<a href="%(siteurl)s"><strong>%(sitename)s</strong></a><br />
%(need_intervention_please_contact)s <a href="mailto:%(sitesupportemail)s">%(sitesupportemail)s</a>
        """ % {
            'sitename': CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME),
            'best_regards': _("Best regards"),
            'siteurl': CFG_SITE_URL,
            'need_intervention_please_contact': _("Need human intervention?  Contact"),
            'sitesupportemail': CFG_SITE_SUPPORT_EMAIL
            }
    return out


def forge_email(fromaddr, toaddr, subject, content, html_content='',
                html_images=None, usebcc=False, header=None, footer=None,
                html_header=None, html_footer=None, ln=CFG_SITE_LANG,
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
    @return: forged email as a string"""
    if html_images is None:
        html_images = {}

    if header is None:
        content = email_header(ln) + content
    else:
        content = header + content
    if footer is None:
        content += email_footer(ln)
    else:
        content += footer

    if charset is None:
        (content, content_charset) = guess_minimum_encoding(content)
    else:
        content_charset = charset

    subject = get_mail_header(subject)
    fromaddr = get_mail_header(fromaddr)
    toaddr = get_mail_header(toaddr)
    replytoaddr = get_mail_header(replytoaddr)
    bccaddr = get_mail_header(bccaddr)

    toaddr = remove_temporary_emails(toaddr)

    if html_content:
        if html_header is None:
            html_content = email_html_header(ln) + html_content
        else:
            html_content = html_header + html_content
        if html_footer is None:
            html_content += email_html_footer(ln)
        else:
            html_content += html_footer

        if charset is None:
            (html_content, html_content_charset) = guess_minimum_encoding(html_content)
        else:
            html_content_charset = charset

        msg_root = MIMEMultipart('alternative')
        msg_root.preamble = 'This is a multi-part message in MIME format.'

        msg_text = MIMEText(content, _charset=content_charset)
        msg_root.attach(msg_text)

        msg_text = MIMEText(html_content, 'html', _charset=html_content_charset)
        if not html_images:
            # No image? Attach the HTML to the root
            msg_root.attach(msg_text)
        else:
            # Image(s)? Attach the HTML and image(s) as children of a
            # "related" block
            msg_related = MIMEMultipart('related')
            msg_related.attach(msg_text)
            for image_id, image_path in html_images.iteritems():
                msg_image = MIMEImage(open(image_path, 'rb').read())
                msg_image.add_header('Content-ID', '<%s>' % image_id)
                msg_image.add_header('Content-Disposition', 'attachment', filename=os.path.split(image_path)[1])
                msg_related.attach(msg_image)
            msg_root.attach(msg_related)
    else:
        msg_root = MIMEText(content, _charset=content_charset)

    if attachments:
        from invenio.bibdocfile import _mimes, guess_format_from_url
        old_msg_root = msg_root
        msg_root = MIMEMultipart()
        msg_root.attach(old_msg_root)
        for attachment in attachments:
            try:
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
                register_exception(alert_admin=True, prefix="Can't attach %s" % attachment)

    msg_root['From'] = fromaddr
    if replytoaddr:
        msg_root['Reply-To'] = replytoaddr
    if usebcc:
        msg_root['Bcc'] = toaddr
        msg_root['To'] = 'Undisclosed.Recipients:'
        if bccaddr:
            msg_root['Bcc'] += ",%s" % (bccaddr,)
    else:
        msg_root['To'] = toaddr
        if bccaddr:
            msg_root['Bcc'] = bccaddr
    msg_root['Date'] = formatdate(localtime=True)
    msg_root['Subject'] = subject
    msg_root['User-Agent'] = 'Invenio %s at %s' % (CFG_VERSION, CFG_SITE_URL)
    return msg_root.as_string()

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

_RE_TEMPORARY_EMAIL = re.compile(CFG_TEMP_EMAIL_ADDRESS % r'.+?', re.I)
def remove_temporary_emails(emails):
    """
    Removes the temporary emails (which are constructed randomly when user logs in
    with an external authentication provider which doesn't supply an email
    address) from an email list.

    @param emails: email list (if string, then receivers are separated by ',')
    @type emails: [str]|str

    @rtype: list|str
    """

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
    if type(value) is not str:
        value = ','.join(value)
    try:
        value = value.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        value = Header(value, 'utf-8')
    return value
