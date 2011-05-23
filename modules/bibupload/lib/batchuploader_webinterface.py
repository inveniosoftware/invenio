# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""WebUpload web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.webinterface_handler_wsgi_utils import Field
from invenio.config import CFG_SITE_URL
from invenio.urlutils import redirect_to_url
from invenio.messages import gettext_set_language
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.webuser import getUid, page_not_authorized
from invenio.webpage import page

from invenio.batchuploader_engine import metadata_upload, cli_upload, \
     get_user_metadata_uploads, get_user_document_uploads, document_upload, \
     get_daemon_doc_files, get_daemon_meta_files, cli_allocate_record, \
     check_date, check_time, user_authorization

try:
    import invenio.template
    batchuploader_templates = invenio.template.load('batchuploader')
except:
    pass


class WebInterfaceBatchUploaderPages(WebInterfaceDirectory):
    """Defines the set of /batchuploader pages."""

    _exports = ['', 'metadata', 'robotupload', 'metasubmit', 'history', 'documents', 'docsubmit', 'daemon', 'allocaterecord']

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/batchuploader/metadata" % (CFG_SITE_URL))

    def metadata(self, req, form):
        """ Display Metadata file upload form """
        argd = wash_urlargd(form, {'error': (int, 0),
                                    'filetype': (str, ""),
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
                argd['error'], argd['filetype'], argd['mode'], argd['submit_date'],
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
                                   'submit_time': (str, ""),
                                   'priority': (str, "")})
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

        errors, info = document_upload(req, argd['docfolder'], argd['matching'],
                                       argd['mode'], date, time, argd['ln'], argd['priority'])

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

    def allocaterecord(self, req, form):
        """
        Interface for robots to allocate a record and obtain a record identifier
        """
        return cli_allocate_record(req)

    def metasubmit(self, req, form):
        """ Function called after submitting the metadata upload form.
            Checks if input fields are correct before uploading.
        """
        argd = wash_urlargd(form, {'metafile': (Field, None),
                                   'filetype': (str, None),
                                   'mode': (str, None),
                                   'submit_date': (str, None),
                                   'submit_time': (str, None),
                                   'filename': (str, None),
                                   'priority': (str, None)})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        #Check if input fields are correct, if not, redirect to upload form
        correct_date = check_date(argd['submit_date'])
        correct_time = check_time(argd['submit_time'])
        if correct_time != 0:
            redirect_to_url(req,
            "%s/batchuploader/metadata?error=1&filetype=%s&mode=%s&submit_date=%s"
            % (CFG_SITE_URL, argd['filetype'], argd['mode'], argd['submit_date']))
        if not argd['metafile'].value: # Empty file
            redirect_to_url(req,
            "%s/batchuploader/metadata?error=2&filetype=%s&mode=%s&submit_date=%s&submit_time=%s"
            % (CFG_SITE_URL, argd['filetype'], argd['mode'], argd['submit_date'],
            argd['submit_time']))
        if correct_date != 0:
            redirect_to_url(req,
            "%s/batchuploader/metadata?error=%s&filetype=%s&mode=%s&submit_time=%s"
            % (CFG_SITE_URL, correct_date, argd['filetype'], argd['mode'], argd['submit_time']))

        date = argd['submit_date'] not in ['yyyy-mm-dd', ''] \
                and argd['submit_date'] or ''
        time = argd['submit_time'] not in ['hh:mm:ss', ''] \
                and argd['submit_time'] or ''

        if date != '' and time == '':
            redirect_to_url(req, "%s/batchuploader/metadata?error=1&filetype=%s&mode=%s&submit_date=%s"
            % (CFG_SITE_URL, argd['filetype'], argd['mode'], argd['submit_date']))
        elif date == '' and time != '':
            redirect_to_url(req, "%s/batchuploader/metadata?error=4&filetype=%s&mode=%s&submit_time=%s"
            % (CFG_SITE_URL, argd['filetype'], argd['mode'], argd['submit_time']))

        #Function where bibupload queues the file
        auth_code, auth_message = metadata_upload(req,
                                  argd['metafile'], argd['filetype'], argd['mode'].split()[0],
                                  date, time, argd['filename'], argd['ln'],
                                  argd['priority'])

        if auth_code == 1: # not authorized
            referer = '/batchuploader/'
            return page_not_authorized(req=req, referer=referer,
                        text=auth_message, navmenuid="batchuploader")
        else:
            uid = getUid(req)
            body = batchuploader_templates.tmpl_display_menu(argd['ln'])
            if auth_code == 2: # invalid MARCXML
                body += batchuploader_templates.tmpl_invalid_marcxml(argd['ln'])
                title = _("Invalid MARCXML")
            else:
                body += batchuploader_templates.tmpl_upload_successful(argd['ln'])
                title = _("Upload successful")
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
