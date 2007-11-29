# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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
from email.MIMEImage import MIMEImage
from cStringIO import StringIO
from formatter import DumbWriter, AbstractFormatter

from invenio.config import \
     supportemail, \
     weburl, \
     cdslang, \
     cdsnameintl, \
     cdsname, \
     adminemail, \
     CFG_MISCUTIL_SMTP_HOST, \
     CFG_MISCUTIL_SMTP_PORT, \
     version

from invenio.messages import wash_language, gettext_set_language
from invenio.errorlib import get_msgs_for_code_list, register_errors, register_exception

def send_email(fromaddr,
               toaddr,
               subject,
               content,
               html_content='',
               html_images={},
               header=None,
               footer=None,
               html_header=None,
               html_footer=None,
               copy_to_admin=0,
               attempt_times=1,
               attempt_sleeptime=10,
               debug_level=0,
               ln=cdslang
               ):
    """Send an forged email to TOADDR from FROMADDR with message created from subjet, content and possibly
    header and footer.
    @param fromaddr: [string] sender
    @param toaddr: [string] receivers separated by ,
    @param subject: [string] subject of the email
    @param content: [string] content of the email
    @param html_content: [string] html version of the email
    @param html_images: [dict] dictionary of image id, image path
    @param header: [string] header to add, None for the Default
    @param footer: [string] footer to add, None for the Default
    @param html_header: [string] header to add to the html part, None for the Default
    @param html_footer: [string] footer to add to the html part, None for the Default
    @param copy_to_admin: [int] if 1 add emailamin in receivers
    @attempt_time: [int] number of tries
    @attempt_sleeptime: [int] seconds in between tries
    @debug_level: [int] debug level
    @ln: [string] invenio language

    If sending fails, try to send it ATTEMPT_TIMES, and wait for
    ATTEMPT_SLEEPTIME seconds in between tries.

    e.g.:
    send_email('Samuele.Kaplun@cern.ch', 'Samuele.Kaplun@cern.ch', 'Proviamo un po\'', '123 prova', '<strong>123</strong> <em>prova</em><img src="cid:image1">', {'image1': '/home/sam/Desktop/Documenti/Foto/Labex/quantum.jpg'})

    @return [int]: 0 if email was sent okay, 1 if it was not.
    """
    toaddr = toaddr.strip()
    usebcc = ',' in toaddr # More than one address, let's use Bcc in place of To
    if copy_to_admin:
        if len(toaddr) > 0:
            toaddr += ",%s" % (adminemail,)
        else:
            toaddr = adminemail
    body = forge_email(fromaddr, toaddr, subject, content, html_content, html_images, usebcc, header, footer, html_header, html_footer, ln)
    toaddr = toaddr.split(",")
    if attempt_times < 1 or len(toaddr[0]) == 0:
        log('ERR_MISCUTIL_NOT_ATTEMPTING_SEND_EMAIL', fromaddr, toaddr, body)
        return False
    try:
        server = smtplib.SMTP(CFG_MISCUTIL_SMTP_HOST, CFG_MISCUTIL_SMTP_PORT)
        if debug_level > 2:
            server.set_debuglevel(1)
        else:
            server.set_debuglevel(0)
        server.sendmail(fromaddr, toaddr, body)
        server.quit()
    except (smtplib.SMTPException, socket.error), e:
        if attempt_times > 1:
            if (debug_level > 1):
                log('ERR_MISCUTIL_CONNECTION_SMTP', attempt_sleeptime, sys.exc_info()[0], fromaddr, toaddr, body)
            sleep(attempt_sleeptime)
            return send_email(fromaddr, toaddr, body, attempt_times-1, attempt_sleeptime)
        else:
            log('ERR_MISCUTIL_SENDING_EMAIL', fromaddr, toaddr, body)
            return False
    except Exception, e:
        register_exception()
        return False
    return True

def email_header(ln=cdslang):
    """The header of the email
    @param ln: language
    @return header as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard header
    out = """%(hello)s
        """ % {
            'hello':  _("Hello:")
            }
    return out

def email_html_header(ln=cdslang):
    """The header of the email
    @param ln: language
    @return header as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard header
    out = """%(hello)s<br />
        """ % {
            'hello':  _("Hello:")
            }
    return out


def email_footer(ln=cdslang):
    """The footer of the email
    @param ln: language
    @return footer as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard footer
    out = """\n\n%(best_regards)s
--
%(cdsnameintl)s <%(weburl)s>
%(need_intervention_please_contact)s <%(supportemail)s>
        """ % {
            'cdsnameintl': cdsnameintl[ln],
            'best_regards': _("Best regards"),
            'weburl': weburl,
            'need_intervention_please_contact': _("Need human intervention?  Contact"),
            'supportemail': supportemail
            }
    return out

def email_html_footer(ln=cdslang):
    """The html footer of the email
    @param ln: language
    @return footer as a string"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    #standard footer
    out = """<br /><br /><em>%(best_regards)s</em>
    <hr />
<a href="%(weburl)s"><strong>%(cdsnameintl)s</strong></a><br />
%(need_intervention_please_contact)s <a href="mailto:%(supportemail)s">%(supportemail)s</a>
        """ % {
            'cdsnameintl': cdsnameintl.get(ln, cdsname),
            'best_regards': _("Best regards"),
            'weburl': weburl,
            'need_intervention_please_contact': _("Need human intervention?  Contact"),
            'supportemail': supportemail
            }
    return out


def forge_email(fromaddr, toaddr, subject, content, html_content='', html_images={}, usebcc=False, header=None, footer=None, html_header=None, html_footer=None, ln=cdslang):
    """Prepare email. Add header and footer if needed.
    @param fromaddr: [string] sender
    @param toaddr: [string] receivers separated by ,
    @param usebcc: [bool] True for using Bcc in place of To
    @param subject: [string] subject of the email
    @param content: [string] content of the email
    @param html_content: [string] html version of the email
    @param html_images: [dict] dictionary of image id, image path
    @param header: [string] None for the default header
    @param footer: [string] None for the default footer
    @param ln: language
    @return forged email as a string"""
    if header is None:
        content = email_header(ln) + content
    else:
        content = header + content
    if footer is None:
        content += email_footer(ln)
    else:
        content += footer
    if html_content:
        if html_header is None:
            html_content = email_html_header(ln) + html_content
        else:
            html_content = html_header + content
        if html_footer is None:
            html_content += email_html_footer(ln)
        else:
            html_content += html_footer

        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = Header(subject, 'utf-8')
        msgRoot['From'] = fromaddr
        if usebcc:
            msgRoot['Bcc'] = toaddr
        else:
            msgRoot['To'] = toaddr
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        msgText = MIMEText(content, _charset='utf-8')
        msgAlternative.attach(msgText)

        msgText = MIMEText(html_content, 'html', _charset='utf-8')
        msgAlternative.attach(msgText)

        for image_id, image_path in html_images.iteritems():
            msgImage = MIMEImage(open(image_path, 'rb').read())
            msgImage.add_header('Content-ID', '<%s>' % image_id)
            msgImage.add_header('Content-Disposition', 'attachment', filename=os.path.split(image_path)[1])
            msgRoot.attach(msgImage)
    else:
        msgRoot = MIMEText(content, _charset='utf-8')
        msgRoot['From'] = fromaddr
        if usebcc:
            msgRoot['Bcc'] = toaddr
        else:
            msgRoot['To'] = toaddr
        msgRoot['Subject'] = Header(subject, 'utf-8')
    msgRoot.add_header('User-Agent', 'CDS Invenio %s' % version)
    return msgRoot.as_string()

newlines_re = re.compile(r'<br\s*/?>|</p>', re.I)
spaces_re = re.compile(r'\s+')
words_boundary_re = re.compile(r'\b')
html_tags_re = re.compile(r'<.+?>')

def email_strip_html(html_content):
    """Strip html tags from html_content, trying to respect formatting."""
    html_content = spaces_re.sub(' ', html_content)
    html_content = newlines_re.sub('\n', html_content)
    html_content = html_tags_re.sub('', html_content)
    html_content = html_content.split('\n')
    out = StringIO()
    out_format = AbstractFormatter(DumbWriter(out))
    for row in html_content:
        out_format.add_flowing_data(row)
        out_format.end_paragraph(1)
    return out.getvalue()


def log(*error):
    """Register error
    @param error: tuple of the form(ERR_, arg1, arg2...)
    """
    _ = gettext_set_language(cdslang)
    errors = get_msgs_for_code_list([error], 'error', cdslang)
    register_errors(errors, 'error')

