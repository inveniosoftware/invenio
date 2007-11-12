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

from email.Header import Header
from email.MIMEText import MIMEText

from invenio.config import \
     supportemail, \
     weburl, \
     cdslang, \
     cdsnameintl, \
     adminemail, \
     CFG_MISCUTIL_SMTP_HOST, \
     CFG_MISCUTIL_SMTP_PORT

from invenio.messages import wash_language, gettext_set_language
from invenio.errorlib import get_msgs_for_code_list, register_errors

def send_email(fromaddr,
               toaddr,
               subject,
               content,
               header=None,
               footer=None,
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
    @param header: [int] if 1 add header
    @param footer: [int] if 1 add footer
    @param copy_to_admin: [int] if 1 add emailamin in receivers
    @attempt_time: [int] number of tries
    @attempt_sleeptime: [int] seconds in between tries
    @debug_level: [int] debug level
    @ln: [string] invenio language

    If sending fails, try to send it ATTEMPT_TIMES, and wait for
    ATTEMPT_SLEEPTIME seconds in between tries.

    @return [int]: 0 if email was sent okay, 1 if it was not.
    """
    toaddr = toaddr.strip()
    usebcc = ',' in toaddr # More than one address, let's use Bcc in place of To
    if copy_to_admin:
        if len(toaddr) > 0:
            toaddr += ",%s" % (adminemail,)
        else:
            toaddr = adminemail
    body = forge_email(fromaddr, toaddr, subject, content, usebcc, header, footer, ln)
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
            raise e

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

def forge_email(fromaddr, toaddr, subject, content, usebcc=False, header=None, footer=None, ln=cdslang):
    """Prepare email. Add header and footer if needed.
    @param fromaddr: [string] sender
    @param toaddr: [string] receivers separated by ,
    @param usebcc: [bool] True for using Bcc in place of To
    @param subject: [string] subject of the email
    @param content: [string] content of the email
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
    msg = MIMEText(content, _charset='utf-8')
    msg['From'] = fromaddr
    if usebcc:
        msg['Bcc'] = toaddr
    else:
        msg['To'] = toaddr
    msg['Subject'] = Header(subject, 'utf-8')
    return msg.as_string()

def log(*error):
    """Register error
    @param error: tuple of the form(ERR_, arg1, arg2...)
    """
    _ = gettext_set_language(cdslang)
    errors = get_msgs_for_code_list([error], 'error', cdslang)
    register_errors(errors, 'error')

