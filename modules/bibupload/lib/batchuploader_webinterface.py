# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""WebUpload web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.webinterface_handler_wsgi_utils import Field
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_URL
from invenio.urlutils import redirect_to_url
from invenio.messages import gettext_set_language
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.webuser import getUid, page_not_authorized, collect_user_info
from invenio.webpage import page

from invenio.batchuploader_engine import metadata_upload, cli_upload, \
     get_user_metadata_uploads, get_user_document_uploads, document_upload, \
     get_daemon_doc_files, get_daemon_meta_files

import re
import calendar

try:
    import invenio.template
    batchuploader_templates = invenio.template.load('batchuploader')
except:
    pass

def check_date(date):
    """ Check if date is correct
        @return:
            0 - Default or correct date
            3 - Incorrect format
            4 - Date does not exist
    """
    if not date or date == "yyyy-mm-dd":
        return 0
    correct_format = re.match("2[01]\d\d-[01]?\d-[0-3]?\d", date)
    if not correct_format:
        return 3
    #separate year, month, day
    date = correct_format.group(0).split("-")
    try:
        calendar.weekday(int(date[0]), int(date[1]), int(date[2]))
    except ValueError:
        return 4
    return 0

def check_time(time):
    """ Check if time is correct
        @return:
            0 - Default or correct time
            1 - Incorrect format
    """
    if not time or time == "hh:mm:ss":
        return 0
    correct_format = re.match("[0-2]\d:[0-5]\d:[0-5]\d", time)
    if not correct_format:
        return 1
    return 0

def check_file(name):
    """ Simple check to avoid blank filename and bad extensions
        @return:
            0 - Correct file name
            1 - File name not correct
    """
    if not name.endswith('.xml'):
        return 1
    return 0

def user_authorization(req, ln):
    """ Check user authorization to visit page """
    _ = gettext_set_language(ln)
    user_info = collect_user_info(req)
    if user_info['email'] == 'guest':
        auth_code, auth_message = acc_authorize_action(req, 'runbatchuploader')
        referer = '/batchuploader/'
        error_msg = _("Guests are not authorized to run batchuploader")
        return page_not_authorized(req=req, referer=referer,
                                   text=error_msg, navmenuid="batchuploader")
    else:
        auth_code, auth_message = acc_authorize_action(req, 'runbatchuploader')
        if auth_code != 0:
            referer = '/batchuploader/'
            error_msg = _("The user '%s' is not authorized to run batchuploader" % (user_info['nickname']))
            return page_not_authorized(req=req, referer=referer,
                                       text=error_msg, navmenuid="batchuploader")


class WebInterfaceBatchUploaderPages(WebInterfaceDirectory):
    """Defines the set of /batchuploader pages."""

    _exports = ['', 'metadata', 'robotupload', 'metasubmit', 'history', 'documents', 'docsubmit', 'daemon']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/batchuploader/metadata" % (CFG_SITE_URL))

    def metadata(self, req, form):
        """ Display Metadata file upload form """
        argd = wash_urlargd(form, {'error': (int, 0),
                                    'mode': (str, ""),
                                    'submit_date': (str, "yyyy-mm-dd"),
                                    'submit_time': (str, "hh:mm:ss")})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        uid = getUid(req)
        body = batchuploader_templates.tmpl_display_menu(argd['ln'], ref="metadata")
        body += batchuploader_templates.tmpl_display_web_metaupload_form(argd['ln'],
                argd['error'], argd['mode'], argd['submit_date'],
                argd['submit_time'])

        title = _("Metadata batch upload")
        return page(title = title,
                    body = body,
                    metaheaderadd = batchuploader_templates.tmpl_styles(),
                    uid = uid,
                    lastupdated = __lastupdated__,
                    req = req,
                    language = argd['ln'],
                    navmenuid = "batchuploader")

    def documents(self, req, form):
        """ Display document upload form """
        argd = wash_urlargd(form, {
                                    })
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        uid = getUid(req)
        body = batchuploader_templates.tmpl_display_menu(argd['ln'], ref="documents")
        body += batchuploader_templates.tmpl_display_web_docupload_form(argd['ln'])

        title = _("Document batch upload")
        return page(title = title,
                    body = body,
                    metaheaderadd = batchuploader_templates.tmpl_styles(),
                    uid = uid,
                    lastupdated = __lastupdated__,
                    req = req,
                    language = argd['ln'],
                    navmenuid = "batchuploader")

    def docsubmit(self, req, form):
        """ Function called after submitting the document upload form.
            Performs the appropiate action depending on the input parameters
        """
        argd = wash_urlargd(form, {'docfolder': (str, ""),
                                   'matching': (str, ""),
                                   'mode': (str, ""),
                                   'submit_date': (str, ""),
                                   'submit_time': (str, "")})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        #Check if input fields are correct, if not, redirect to upload form
        correct_date = check_date(argd['submit_date'])
        correct_time = check_time(argd['submit_time'])
        if correct_time != 0:
            redirect_to_url(req,
            "%s/batchuploader/documents?error=1&mode=%s&docfolder=%s&matching=%s&submit_date=%s"
            % (CFG_SITE_URL, argd['mode'], argd['docfolder'], argd['matching'], argd['submit_date']))
        if correct_date != 0:
            redirect_to_url(req,
            "%s/batchuploader/documents?error=%s&mode=%s&docfolder=%s&matching=%s&submit_time=%s"
            % (CFG_SITE_URL, correct_date, argd['mode'], argd['docfolder'], argd['matching'], argd['submit_time']))

        date = argd['submit_date'] not in ['yyyy-mm-dd', ''] \
                                and argd['submit_date'] or ''
        time = argd['submit_time'] not in ['hh:mm:ss', ''] \
                                and argd['submit_time'] or ''

        if date != '' and time == '':
            redirect_to_url(req, "%s/batchuploader/documents?error=1&mode=%s&docfolder=%s&matching=%s&submit_date=%s"
                            % (CFG_SITE_URL, argd['mode'], argd['docfolder'], argd['matching'], argd['submit_date']))
        elif date == '' and time != '':
            redirect_to_url(req, "%s/batchuploader/documents?error=4&mode=%s&docfolder=%s&matching=%s&submit_time=%s"
                            % (CFG_SITE_URL, argd['mode'], argd['docfolder'], argd['matching'], argd['submit_time']))

        errors, info = document_upload(req, argd['docfolder'], argd['matching'], argd['mode'], date, time, argd['ln'])

        body = batchuploader_templates.tmpl_display_menu(argd['ln'])
        uid = getUid(req)
        navtrail = '''<a class="navtrail" href="%s/batchuploader/documents">%s</a>''' % \
                    (CFG_SITE_URL, _("Document batch upload"))

        body += batchuploader_templates.tmpl_display_web_docupload_result(argd['ln'], errors, info)
        title = _("Document batch upload result")

        return page(title = title,
                    body = body,
                    metaheaderadd = batchuploader_templates.tmpl_styles(),
                    uid = uid,
                    navtrail = navtrail,
                    lastupdated = __lastupdated__,
                    req = req,
                    language = argd['ln'],
                    navmenuid = "batchuploader")

    def robotupload(self, req, form):
        """Interface for robots used like this:
            $ curl -F 'file=@localfile.xml' -F 'mode=-i' http://cdsweb.cern.ch/batchuploader/robotupload -A invenio_webupload
        """
        argd = wash_urlargd(form, {'file': (Field, None),
                                   'mode': (str,None)})
        cli_upload(req, argd['file'], argd['mode'])

    def metasubmit(self, req, form):
        """ Function called after submitting the metadata upload form.
            Checks if input fields are correct before uploading.
        """
        argd = wash_urlargd(form, {'metafile': (Field, None),
                                   'mode': (str,None),
                                   'submit_date': (str, None),
                                   'submit_time': (str, None),
                                   'filename': (str, None)})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        #Check if input fields are correct, if not, redirect to upload form
        correct_date = check_date(argd['submit_date'])
        correct_time = check_time(argd['submit_time'])
        correct_file = check_file(argd['filename'])
        if correct_time != 0:
            redirect_to_url(req,
            "%s/batchuploader/metadata?error=1&mode=%s&submit_date=%s"
            % (CFG_SITE_URL, argd['mode'], argd['submit_date']))
        if correct_file != 0:
            redirect_to_url(req,
            "%s/batchuploader/metadata?error=2&mode=%s&submit_date=%s&submit_time=%s"
            % (CFG_SITE_URL, argd['mode'], argd['submit_date'],
            argd['submit_time']))
        if correct_date != 0:
            redirect_to_url(req,
            "%s/batchuploader/metadata?error=%s&mode=%s&submit_time=%s"
            % (CFG_SITE_URL, correct_date, argd['mode'], argd['submit_time']))

        date = argd['submit_date'] not in ['yyyy-mm-dd', ''] \
                and argd['submit_date'] or ''
        time = argd['submit_time'] not in ['hh:mm:ss', ''] \
                and argd['submit_time'] or ''

        if date != '' and time == '':
            redirect_to_url(req, "%s/batchuploader/metadata?error=1&mode=%s&submit_date=%s"
            % (CFG_SITE_URL, argd['mode'], argd['submit_date']))
        elif date == '' and time != '':
            redirect_to_url(req, "%s/batchuploader/metadata?error=4&mode=%s&submit_time=%s"
            % (CFG_SITE_URL, argd['mode'], argd['submit_time']))

        #Function where bibupload queues the file
        auth_code, auth_message = metadata_upload(req,
                                  argd['metafile'], argd['mode'].split()[0],
                                  date, time, argd['filename'], argd['ln'])

        if auth_code != 0:
            referer = '/batchuploader/'
            return page_not_authorized(req=req, referer=referer,
                        text=auth_message, navmenuid="batchuploader")
        else:
            uid = getUid(req)
            body = batchuploader_templates.tmpl_display_menu(argd['ln'])
            body += batchuploader_templates.tmpl_upload_succesful(argd['ln'])
            title = _("Upload succesful")
            navtrail = '''<a class="navtrail" href="%s/batchuploader/metadata">%s</a>''' % \
                            (CFG_SITE_URL, _("Metadata batch upload"))
            return page(title = title,
                        body = body,
                        uid = uid,
                        navtrail = navtrail,
                        lastupdated = __lastupdated__,
                        req = req,
                        language = argd['ln'],
                        navmenuid = "batchuploader")

    def history(self, req, form):
        """Display upload history of the current user"""
        argd = wash_urlargd(form, {})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        uploaded_meta_files = get_user_metadata_uploads(req)
        uploaded_doc_files = get_user_document_uploads(req)

        uid = getUid(req)
        body = batchuploader_templates.tmpl_display_menu(argd['ln'], ref="history")
        body += batchuploader_templates.tmpl_upload_history(argd['ln'], uploaded_meta_files, uploaded_doc_files)
        title = _("Upload history")
        return page(title = title,
                    body = body,
                    metaheaderadd = batchuploader_templates.tmpl_styles(),
                    uid = uid,
                    lastupdated = __lastupdated__,
                    req = req,
                    language = argd['ln'],
                    navmenuid = "batchuploader")

    def daemon(self, req, form):
        """ Display content of folders where the daemon will look into """
        argd = wash_urlargd(form, {})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        docs = get_daemon_doc_files()
        metadata = get_daemon_meta_files()

        uid = getUid(req)
        body = batchuploader_templates.tmpl_display_menu(argd['ln'], ref="daemon")
        body += batchuploader_templates.tmpl_daemon_content(argd['ln'], docs, metadata)
        title = _("Batch Uploader: Daemon monitor")
        return page(title = title,
                    body = body,
                    metaheaderadd = batchuploader_templates.tmpl_styles(),
                    uid = uid,
                    lastupdated = __lastupdated__,
                    req = req,
                    language = argd['ln'],
                    navmenuid = "batchuploader")

    def __call__(self, req, form):
        """Redirect calls without final slash."""
        redirect_to_url(req, '%s/batchuploader/metadata' % CFG_SITE_URL)
