# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
Invenio Admin mail backend.  send_email() will send emails only to
CFG_SITE_ADMIN_EMAIL.
"""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_ADMIN_EMAIL


def adminonly_class(Backend):
    """Admin only mail backend class factory."""

    class _Mail(Backend):

        def send_messages(self, email_messages):
            def process_message(m):
                m.body = """
#--------------------------------------------------------------
#This message would have been sent to the following recipients:
#%s
#--------------------------------------------------------------
#%s""" % (','.join(m.recipients()), m.body)
                m.to = [CFG_SITE_ADMIN_EMAIL]
                m.cc = []
                m.bcc = []
                if 'Cc' in m.extra_headers:
                    del m.extra_headers['Cc']
                if 'Bcc' in m.extra_headers:
                    del m.extra_headers['Bcc']
                return m
            return super(_Mail, self).send_messages(
                map(process_message, email_messages))

    return _Mail
