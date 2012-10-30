# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
Invenio Bibliographic Tasklet send_email wrapper.
"""

from invenio.mailutils import send_email


def bst_send_email(fromaddr,
                   toaddr,
                   subject="",
                   content="",
                   header=None,
                   footer=None,
                   copy_to_admin=0,
                   attempt_times=1,
                   attempt_sleeptime=10,
                   replytoaddr="",
                   bccaddr="",
                  ):
    """
    Send a forged email to TOADDR from FROMADDR with message created from subjet, content and possibly
    header and footer.
    @param fromaddr: sender
    @type fromaddr: string
    @param toaddr: comma-separated list of receivers
    @type toaddr: string
    @param subject: subject of the email
    @type subject: string
    @param content: content of the email
    @type content: string
    @param header: header to add, None for the Default
    @type header: string
    @param footer: footer to add, None for the Default
    @type footer: string
    @param copy_to_admin: if 1 add CFG_SITE_ADMIN_EMAIL in receivers
    @type copy_to_admin: int
    @param attempt_times: number of tries
    @type attempt_times: int
    @param attempt_sleeptime: seconds in between tries
    @type attempt_sleeptime: int
    @param replytoaddr: comma-separated list of emails to add as reply-to header
    @type replytoaddr: string
    @param bccaddr: comma-separated list of emails to add as bcc header
    @type bccaddr: string

    If sending fails, try to send it ATTEMPT_TIMES, and wait for
    ATTEMPT_SLEEPTIME seconds in between tries.
    """
    copy_to_admin = int(copy_to_admin)
    attempt_times = int(attempt_times)
    attempt_sleeptime = int(attempt_sleeptime)
    return send_email(fromaddr=fromaddr,
                      toaddr=toaddr,
                      subject=subject,
                      content=content,
                      header=header,
                      footer=footer,
                      copy_to_admin=copy_to_admin,
                      attempt_times=attempt_times,
                      attempt_sleeptime=attempt_sleeptime,
                      replytoaddr=replytoaddr,
                      bccaddr=bccaddr,
                     )
