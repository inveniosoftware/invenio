# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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

# pylint: disable=C0301

"""ErrorLib web interface."""

__revision__ = "$Id$"

__lastupdated__ = "$Date$"

from invenio.config import CFG_SITE_URL
from invenio.legacy.webpage import page
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.utils.url import redirect_to_url
from invenio.base.i18n import gettext_set_language


def send_error_report_to_admin(header, url, time_msg,
                               browser, client, error,
                               sys_error, traceback_msg):
    """
    Sends an email to the admin with client info and tracestack
    """
    from invenio.base.globals import cfg
    from invenio.ext.email import send_email

    from_addr = '%s Alert Engine <%s>' % (
        cfg['CFG_SITE_NAME'], cfg['CFG_WEBALERT_ALERT_ENGINE_EMAIL'])
    to_addr = cfg['CFG_SITE_ADMIN_EMAIL']
    body = """
The following error was seen by a user and sent to you.
%(contact)s

%(header)s

%(url)s
%(time)s
%(browser)s
%(client)s
%(error)s
%(sys_error)s
%(traceback)s

Please see the %(logdir)s/invenio.err for traceback details.""" % {
        'header': header,
        'url': url,
        'time': time_msg,
        'browser': browser,
        'client': client,
        'error': error,
        'sys_error': sys_error,
        'traceback': traceback_msg,
        'logdir': cfg['CFG_LOGDIR'],
        'contact': "Please contact %s quoting the following information:" %
        (cfg['CFG_SITE_SUPPORT_EMAIL'], )}

    send_email(from_addr, to_addr, subject="Error notification", content=body)


class WebInterfaceErrorPages(WebInterfaceDirectory):

    """Defines the set of /error pages."""

    _exports = ['', 'send']

    def index(self, req, form):
        """Index page."""
        redirect_to_url(req, '%s/error/send' % CFG_SITE_URL)

    def send(self, req, form):
        """
        Confirmation page of error report sent the admin
        parameters are the same as used for the error box. See
        webstyle_templates.tmpl_error_box
        """

        argd = wash_urlargd(form, {'header': (str, "NA"),
                                   'url': (str, "NA"),
                                   'time': (str, "NA"),
                                   'browser': (str, "NA"),
                                   'client': (str, "NA"),
                                   'error': (str, "NA"),
                                   'sys_error': (str, "NA"),
                                   'traceback': (str, "NA"),
                                   'referer': (str, "NA"),
                                   })

        _ = gettext_set_language(argd['ln'])

        if argd['client'] == "NA":
            return page(title=_("Sorry"),
                        body=_(
                            "Cannot send error request, %(x_name)s parameter"
                            " missing.", x_name='client'),
                        lastupdated=__lastupdated__,
                        req=req)
        elif argd['url'] == "NA":
            return page(title=_("Sorry"),
                        body=_(
                            "Cannot send error request, %(x_name)s parameter"
                            " missing.", x_name='url'),
                        lastupdated=__lastupdated__,
                        req=req)
        elif argd['time'] == "NA":
            return page(title=_("Sorry"),
                        body=_(
                            "Cannot send error request, %(x_name)s parameter"
                            " missing.", x_name='time'),
                        lastupdated=__lastupdated__,
                        req=req)
        elif argd['error'] == "NA":
            return page(title=_("Sorry"),
                        body=_(
                            "Cannot send error request, %(x_name)s parameter"
                            " missing.", x_name='error'),
                        lastupdated=__lastupdated__,
                        req=req)
        else:
            send_error_report_to_admin(argd['header'],
                                       argd['url'],
                                       argd['time'],
                                       argd['browser'],
                                       argd['client'],
                                       argd['error'],
                                       argd['sys_error'],
                                       argd['traceback'])

            out = """
            <p><span class="exampleleader">%(title)s</span>
            <p>%(message)s
            <p>%(back)s
            """ % \
                {'title': _("The error report has been sent."),
                 'message': _(
                     "Many thanks for helping us to improve the service."),
                 'back': argd['referer'] != "NA" and
                 "<a href=\"%s\">back</a>" % (argd['referer'],) or
                 _("Use the back button of your browser to return to the "
                   "previous page.")
                 }
            return page(title=_("Thank you!"),
                        body=out,
                        lastupdated=__lastupdated__,
                        req=req)
