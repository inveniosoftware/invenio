# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013 CERN.
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

"""WebUpload web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from invenio.legacy.wsgi.utils import Field
from invenio.config import CFG_SITE_SECURE_URL
from invenio.utils.url import redirect_to_url
from invenio.base.i18n import gettext_set_language
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.utils.apache import SERVER_RETURN, HTTP_NOT_FOUND
from invenio.legacy.wsgi.utils import handle_file_post
from invenio.legacy.webuser import getUid, page_not_authorized, get_email
from invenio.legacy.webpage import page

from invenio.legacy.batchuploader.engine import metadata_upload, cli_upload, \
     get_user_metadata_uploads, get_user_document_uploads, document_upload, \
     get_daemon_doc_files, get_daemon_meta_files, cli_allocate_record, \
     user_authorization, perform_upload_check, _transform_input_to_marcxml

try:
    import invenio.legacy.template
    batchuploader_templates = invenio.legacy.template.load('batchuploader')
except:
    pass


class WebInterfaceBatchUploaderPages(WebInterfaceDirectory):
    """Defines the set of /batchuploader pages."""

    _exports = ['', 'metadata', 'metasubmit', 'history', 'documents',
        'docsubmit', 'daemon', 'allocaterecord', 'confirm']

    def _lookup(self, component, path):
        def restupload(req, form):
            """Interface for robots used like this:
                $ curl --data-binary '@localfile.xml' http://cds.cern.ch/batchuploader/robotupload/[insert|replace|correct|append]?[callback_url=http://...]&nonce=1234 -A invenio_webupload
            """
            filepath, mimetype = handle_file_post(req)
            argd = wash_urlargd(form, {'callback_url': (str, None), 'nonce': (str, None), 'special_treatment': (str, None)})
            return cli_upload(req, open(filepath), '--' + path[0], argd['callback_url'], argd['nonce'], argd['special_treatment'])

        def legacyrobotupload(req, form):
            """Interface for robots used like this:
                $ curl -F 'file=@localfile.xml' -F 'mode=-i' [-F 'callback_url=http://...'] [-F 'nonce=1234'] http://cds.cern.ch/batchuploader/robotupload -A invenio_webupload
            """
            argd = wash_urlargd(form, {'mode': (str, None), 'callback_url': (str, None), 'nonce': (str, None), 'special_treatment': (str, None)})
            return cli_upload(req, form.get('file', None), argd['mode'], argd['callback_url'], argd['nonce'], argd['special_treatment'])

        if component == 'robotupload':
            if path and path[0] in ('insert', 'replace', 'correct', 'append', 'insertorreplace'):
                return restupload, None
            else:
                return legacyrobotupload, None
        else:
            return None, path

    def index(self, req, form):
        """ The function called by default
        """
        redirect_to_url(req, "%s/batchuploader/metadata" % (CFG_SITE_SECURE_URL))

    def metadata(self, req, form):
        """ Display Metadata file upload form """
        argd = wash_urlargd(form, { 'filetype': (str, ""),
                                    'mode': (str, ""),
                                    'submit_date': (str, "yyyy-mm-dd"),
                                    'submit_time': (str, "hh:mm:ss"),
                                    'email_logs_to': (str, None)})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized
        uid = getUid(req)
        if argd['email_logs_to'] is None:
            argd['email_logs_to'] = get_email(uid)
        body = batchuploader_templates.tmpl_display_menu(argd['ln'], ref="metadata")
        body += batchuploader_templates.tmpl_display_web_metaupload_form(argd['ln'],
                argd['filetype'], argd['mode'], argd['submit_date'],
                argd['submit_time'], argd['email_logs_to'])

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
        email_logs_to = get_email(uid)
        body = batchuploader_templates.tmpl_display_menu(argd['ln'], ref="documents")
        body += batchuploader_templates.tmpl_display_web_docupload_form(argd['ln'], email_logs_to=email_logs_to)

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
                                   'priority': (str, ""),
                                   'email_logs_to': (str, "")})
        _ = gettext_set_language(argd['ln'])

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized

        date = argd['submit_date'] not in ['yyyy-mm-dd', ''] \
                                and argd['submit_date'] or ''
        time = argd['submit_time'] not in ['hh:mm:ss', ''] \
                                and argd['submit_time'] or ''

        errors, info = document_upload(req, argd['docfolder'], argd['matching'],
                                       argd['mode'], date, time, argd['ln'], argd['priority'], argd['email_logs_to'])

        body = batchuploader_templates.tmpl_display_menu(argd['ln'])
        uid = getUid(req)
        navtrail = '''<a class="navtrail" href="%s/batchuploader/documents">%s</a>''' % \
                    (CFG_SITE_SECURE_URL, _("Document batch upload"))

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

    def allocaterecord(self, req, form):
        """
        Interface for robots to allocate a record and obtain a record identifier
        """
        return cli_allocate_record(req)

    def metasubmit(self, req, form):
        """ Function called after submitting the metadata upload form.
            Checks if input fields are correct before uploading.
        """
        argd = wash_urlargd(form, {'metafile': (str, None),
                                   'filetype': (str, None),
                                   'mode': (str, None),
                                   'submit_date': (str, None),
                                   'submit_time': (str, None),
                                   'filename': (str, None),
                                   'priority': (str, None),
                                   'email_logs_to': (str, None)})
        _ = gettext_set_language(argd['ln'])

        # Check if the page is directly accessed
        if argd['metafile']  == None:
            redirect_to_url(req, "%s/batchuploader/metadata"
            % (CFG_SITE_SECURE_URL))

        not_authorized = user_authorization(req, argd['ln'])
        if not_authorized:
            return not_authorized

        date = argd['submit_date'] not in ['yyyy-mm-dd', ''] \
                and argd['submit_date'] or ''
        time = argd['submit_time'] not in ['hh:mm:ss', ''] \
                and argd['submit_time'] or ''

        auth_code, auth_message = metadata_upload(req,
                                  argd['metafile'], argd['filetype'],
                                  argd['mode'].split()[0],
                                  date, time, argd['filename'], argd['ln'],
                                  argd['priority'], argd['email_logs_to'])

        if auth_code == 1: # not authorized
            referer = '/batchuploader/'
            return page_not_authorized(req=req, referer=referer,
                        text=auth_message, navmenuid="batchuploader")
        else:
            uid = getUid(req)
            body = batchuploader_templates.tmpl_display_menu(argd['ln'])
            body += batchuploader_templates.tmpl_upload_successful(argd['ln'])
            title = _("Upload successful")
            navtrail = '''<a class="navtrail" href="%s/batchuploader/metadata">%s</a>''' % \
                            (CFG_SITE_SECURE_URL, _("Metadata batch upload"))
            return page(title = title,
                        body = body,
                        uid = uid,
                        navtrail = navtrail,
                        lastupdated = __lastupdated__,
                        req = req,
                        language = argd['ln'],
                        navmenuid = "batchuploader")

    def confirm(self, req, form):
        """ Function called after submitting the metadata upload form.
            Shows a summary of actions to be performed and possible errors
        """
        argd = wash_urlargd(form, {'metafile': (Field, None),
                                   'filetype': (str, None),
                                   'mode': (str, None),
                                   'submit_date': (str, None),
                                   'submit_time': (str, None),
                                   'filename': (str, None),
                                   'priority': (str, None),
                                   'skip_simulation': (str, None),
                                   'email_logs_to': (str, None)})
        _ = gettext_set_language(argd['ln'])

        # Check if the page is directly accessed or no file selected
        if not argd['metafile']:
            redirect_to_url(req, "%s/batchuploader/metadata"
            % (CFG_SITE_SECURE_URL))

        metafile = argd['metafile'].value
        if argd['filetype'] != 'marcxml':
            metafile = _transform_input_to_marcxml(file_input=metafile)


        date = argd['submit_date'] not in ['yyyy-mm-dd', ''] \
                and argd['submit_date'] or ''
        time = argd['submit_time'] not in ['hh:mm:ss', ''] \
                and argd['submit_time'] or ''

        errors_upload = ''

        skip_simulation = argd['skip_simulation'] == "skip"
        if not skip_simulation:
            errors_upload = perform_upload_check(metafile, argd['mode'])

        body = batchuploader_templates.tmpl_display_confirm_page(argd['ln'],
                                                                 metafile, argd['filetype'], argd['mode'], date,
                                                                 time, argd['filename'], argd['priority'], errors_upload,
                                                                 skip_simulation, argd['email_logs_to'])

        uid = getUid(req)
        navtrail = '''<a class="navtrail" href="%s/batchuploader/metadata">%s</a>''' % \
                    (CFG_SITE_SECURE_URL, _("Metadata batch upload"))
        title = 'Confirm your actions'
        return page(title = title,
                    body = body,
                    metaheaderadd = batchuploader_templates.tmpl_styles(),
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
        body = batchuploader_templates.tmpl_display_menu(argd['ln'],
                                                         ref="history")
        body += batchuploader_templates.tmpl_upload_history(argd['ln'],
                                                            uploaded_meta_files,
                                                            uploaded_doc_files)
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
        body = batchuploader_templates.tmpl_display_menu(argd['ln'],
                                                         ref="daemon")
        body += batchuploader_templates.tmpl_daemon_content(argd['ln'], docs,
                                                            metadata)
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
        redirect_to_url(req, '%s/batchuploader/metadata' % CFG_SITE_SECURE_URL)
