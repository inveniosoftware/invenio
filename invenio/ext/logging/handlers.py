# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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


from __future__ import absolute_import

import logging

from invenio.base.globals import cfg

from .wrappers import _get_filename_and_line
from .models import HstEXCEPTION


class InvenioLegacyHandler(logging.Handler):
    """
    Invenio log record handler. Use together with InvenioExceptionFormatter.
    """

    def emit(self, record):
        # Set by invenio.ext.logging.wrappers.register_exception
        if hasattr(record, 'invenio_register_exception'):
            extra = record.invenio_register_exception

            exc_info = record.exc_info
            exc_name = exc_info[0].__name__
            alert_admin = extra['alert_admin']
            subject = extra['subject']
            content = self.format(record)
            filename, line_no, function_name = _get_filename_and_line(exc_info)

            ## let's log the exception and see whether we should report it.
            log = HstEXCEPTION.get_or_create(exc_name, filename, line_no)
            if log.exception_should_be_notified and (
               cfg['CFG_SITE_ADMIN_EMAIL_EXCEPTIONS'] > 1 or
               (alert_admin and cfg['CFG_SITE_ADMIN_EMAIL_EXCEPTIONS'] > 0)):

                # Set subject of email
                if not subject:
                    subject = 'Exception (%s:%s:%s)' % (
                        filename, line_no, function_name
                    )
                subject = '%s at %s' % (subject, cfg['CFG_SITE_URL'])

                # Set content of email
                content = "\n%s\n%s" % (
                    log.pretty_notification_info,
                    content
                )

                # Send the email
                from invenio.ext.email import send_email
                send_email(
                    cfg['CFG_SITE_ADMIN_EMAIL'],
                    cfg['CFG_SITE_ADMIN_EMAIL'],
                    subject=subject,
                    content=content
                )
