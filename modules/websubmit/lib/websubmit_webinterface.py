## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

import os
import time
import cgi
import sys
import shutil

from urllib import urlencode

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_TMPDIR, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_PREFIX, \
     CFG_CERN_SITE
from invenio import webinterface_handler_config as apache
from invenio.dbquery import run_sql
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_is_role
from invenio.webpage import page, create_error_box, pageheaderonly, \
    pagefooteronly
from invenio.webuser import getUid, page_not_authorized, collect_user_info, isGuestUser, isUserSuperAdmin
from invenio.websubmit_config import *
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import make_canonical_urlargd, redirect_to_url
from invenio.messages import gettext_set_language
from invenio.search_engine import \
     guess_primary_collection_of_a_record, get_colID, record_exists, \
     create_navtrail_links, check_user_can_view_record, record_empty
from invenio.bibdocfile import BibRecDocs, normalize_format, file_strip_ext, \
    stream_restricted_icon, BibDoc, InvenioWebSubmitFileError, stream_file, \
    decompose_file, propose_next_docname, get_subformat_from_format
from invenio.errorlib import register_exception
from invenio.websubmit_icon_creator import create_icon, InvenioWebSubmitIconCreatorError
import invenio.template
websubmit_templates = invenio.template.load('websubmit')
from invenio.websearchadminlib import get_detailed_page_tabs
from invenio.session import get_session
import invenio.template
webstyle_templates = invenio.template.load('webstyle')
websearch_templates = invenio.template.load('websearch')
try:
    from invenio.fckeditor_invenio_connector import FCKeditorConnectorInvenio
    fckeditor_available = True
except ImportError, e:
    fckeditor_available = False

from invenio.websubmit_managedocfiles import \
     create_file_upload_interface, \
     get_upload_file_interface_javascript, \
     get_upload_file_interface_css, \
     move_uploaded_files_to_storage

class WebInterfaceFilesPages(WebInterfaceDirectory):

    def __init__(self,recid):
        self.recid = recid

    def _lookup(self, component, path):
        # after /record/<recid>/files/ every part is used as the file
        # name
        filename = component

        def getfile(req, form):
            args = wash_urlargd(form, websubmit_templates.files_default_urlargd)
            ln = args['ln']

            _ = gettext_set_language(ln)

            uid = getUid(req)
            user_info = collect_user_info(req)

            verbose = args['verbose']
            if verbose >= 1 and not isUserSuperAdmin(user_info):
                # Only SuperUser can see all the details!
                verbose = 0

            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE > 1:
                return page_not_authorized(req, "/record/%s" % self.recid,
                                           navmenuid='submit')

            if record_exists(self.recid) < 1:
                msg = "<p>%s</p>" % _("Requested record does not seem to exist.")
                return warningMsg(msg, req, CFG_SITE_NAME, ln)

            if record_empty(self.recid):
                msg = "<p>%s</p>" % _("Requested record does not seem to have been integrated.")
                return warningMsg(msg, req, CFG_SITE_NAME, ln)

            (auth_code, auth_message) = check_user_can_view_record(user_info, self.recid)
            if auth_code and user_info['email'] == 'guest':
                cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
                target = '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln' : ln, 'referer' : \
                    CFG_SITE_URL + user_info['uri']}, {})
                return redirect_to_url(req, target, norobot=True)
            elif auth_code:
                return page_not_authorized(req, "../", \
                    text = auth_message)


            readonly = CFG_ACCESS_CONTROL_LEVEL_SITE == 1

            # From now on: either the user provided a specific file
            # name (and a possible version), or we return a list of
            # all the available files. In no case are the docids
            # visible.
            try:
                bibarchive = BibRecDocs(self.recid)
            except InvenioWebSubmitFileError, e:
                register_exception(req=req, alert_admin=True)
                msg = "<p>%s</p><p>%s</p>" % (
                    _("The system has encountered an error in retrieving the list of files for this document."),
                    _("The error has been logged and will be taken in consideration as soon as possible."))
                return warningMsg(msg, req, CFG_SITE_NAME, ln)

            if bibarchive.deleted_p():
                return print_warning(req, _("Requested record does not seem to exist."))

            docname = ''
            format = ''
            version = ''
            warn = ''

            if filename:
                # We know the complete file name, guess which docid it
                # refers to
                ## TODO: Change the extension system according to ext.py from setlink
                ##       and have a uniform extension mechanism...
                docname = file_strip_ext(filename)
                format = filename[len(docname):]
                if format and format[0] != '.':
                    format = '.' + format
                if args['subformat']:
                    format += ';%s' % args['subformat']
            else:
                docname = args['docname']

            if not format:
                format = args['format']
                if args['subformat']:
                    format += ';%s' % args['subformat']

            if not version:
                version = args['version']

            # version could be either empty, or all or an integer
            try:
                int(version)
            except ValueError:
                if version != 'all':
                    version = ''

            display_hidden = isUserSuperAdmin(user_info)

            if version != 'all':
                # search this filename in the complete list of files
                for doc in bibarchive.list_bibdocs():
                    if docname == doc.get_docname():
                        try:
                            docfile = doc.get_file(format, version)
                            (auth_code, auth_message) = docfile.is_restricted(user_info)
                            if auth_code != 0:
                                if CFG_WEBSUBMIT_ICON_SUBFORMAT_RE.match(get_subformat_from_format(format)):
                                    return stream_restricted_icon(req)
                                if user_info['email'] == 'guest':
                                    cookie = mail_cookie_create_authorize_action('viewrestrdoc', {'status' : docfile.get_status()})
                                    target = '/youraccount/login' + \
                                    make_canonical_urlargd({'action': cookie, 'ln' : ln, 'referer' : \
                                        CFG_SITE_URL + user_info['uri']}, {})
                                    redirect_to_url(req, target)
                                else:
                                    req.status = apache.HTTP_UNAUTHORIZED
                                    warn += print_warning(_("This file is restricted: ") + auth_message)
                                    break

                            if not docfile.hidden_p():
                                if not readonly:
                                    ip = str(req.remote_ip)
                                    res = doc.register_download(ip, version, format, uid)
                                try:
                                    return docfile.stream(req)
                                except InvenioWebSubmitFileError, msg:
                                    register_exception(req=req, alert_admin=True)
                                    req.status = apache.HTTP_INTERNAL_SERVER_ERROR
                                    return warningMsg(_("An error has happened in trying to stream the request file."), req, CFG_SITE_NAME, ln)
                            else:
                                req.status = apache.HTTP_UNAUTHORIZED
                                warn = print_warning(_("The requested file is hidden and can not be accessed."))

                        except InvenioWebSubmitFileError, msg:
                            register_exception(req=req, alert_admin=True)

            if docname and format and not warn:
                req.status = apache.HTTP_NOT_FOUND
                warn += print_warning(_("Requested file does not seem to exist."))
            filelist = bibarchive.display("", version, ln=ln, verbose=verbose, display_hidden=display_hidden)

            t = warn + websubmit_templates.tmpl_filelist(
                ln=ln,
                recid=self.recid,
                docname=args['docname'],
                version=version,
                filelist=filelist)

            cc = guess_primary_collection_of_a_record(self.recid)
            unordered_tabs = get_detailed_page_tabs(get_colID(cc), self.recid, ln)
            ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
            ordered_tabs_id.sort(lambda x,y: cmp(x[1],y[1]))
            link_ln = ''
            if ln != CFG_SITE_LANG:
                link_ln = '?ln=%s' % ln
            tabs = [(unordered_tabs[tab_id]['label'], \
                     '%s/record/%s/%s%s' % (CFG_SITE_URL, self.recid, tab_id, link_ln), \
                     tab_id == 'files',
                     unordered_tabs[tab_id]['enabled']) \
                    for (tab_id, order) in ordered_tabs_id
                    if unordered_tabs[tab_id]['visible'] == True]
            top = webstyle_templates.detailed_record_container_top(self.recid,
                                                                   tabs,
                                                                   args['ln'])
            bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                         tabs,
                                                                         args['ln'])
            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, args['ln'])
            return pageheaderonly(title=title,
                        navtrail=create_navtrail_links(cc=cc, aas=0, ln=ln) + \
                                        ''' &gt; <a class="navtrail" href="%s/record/%s">%s</a>
                                        &gt; %s''' % \
                        (CFG_SITE_URL, self.recid, title, _("Access to Fulltext")),

                        description="",
                        keywords="keywords",
                        uid=uid,
                        language=ln,
                        req=req,
                        navmenuid='search',
                        navtrail_append_title_p=0) + \
                        websearch_templates.tmpl_search_pagestart(ln) + \
                        top + t + bottom + \
                        websearch_templates.tmpl_search_pageend(ln) + \
                        pagefooteronly(lastupdated=__lastupdated__, language=ln, req=req)
        return getfile, []

    def __call__(self, req, form):
        """Called in case of URLs like /record/123/files without
           trailing slash.
        """
        args = wash_urlargd(form, websubmit_templates.files_default_urlargd)
        ln = args['ln']
        link_ln = ''
        if ln != CFG_SITE_LANG:
            link_ln = '?ln=%s' % ln

        return redirect_to_url(req, '%s/record/%s/files/%s' % (CFG_SITE_URL, self.recid, link_ln))

def websubmit_legacy_getfile(req, form):
    """ Handle legacy /getfile.py URLs """

    args = wash_urlargd(form, {
        'recid': (int, 0),
        'docid': (int, 0),
        'version': (str, ''),
        'name': (str, ''),
        'format': (str, ''),
        'ln' : (str, CFG_SITE_LANG)
        })

    _ = gettext_set_language(args['ln'])

    def _getfile_py(req, recid=0, docid=0, version="", name="", format="", ln=CFG_SITE_LANG):
        if not recid:
            ## Let's obtain the recid from the docid
            if docid:
                try:
                    bibdoc = BibDoc(docid=docid)
                    recid = bibdoc.get_recid()
                except InvenioWebSubmitFileError, e:
                    return warningMsg(_("An error has happened in trying to retrieve the requested file."), req, CFG_SITE_NAME, ln)
            else:
                return warningMsg(_('Not enough information to retrieve the document'), req, CFG_SITE_NAME, ln)
        else:
            if not name and docid:
                ## Let's obtain the name from the docid
                try:
                    bibdoc = BibDoc(docid)
                    name = bibdoc.get_docname()
                except InvenioWebSubmitFileError, e:
                    return warningMsg(_("An error has happened in trying to retrieving the requested file."), req, CFG_SITE_NAME, ln)

        format = normalize_format(format)

        redirect_to_url(req, '%s/record/%s/files/%s%s?ln=%s%s' % (CFG_SITE_URL, recid, name, format, ln, version and 'version=%s' % version or ''), apache.HTTP_MOVED_PERMANENTLY)

    return _getfile_py(req, **args)


# --------------------------------------------------

from invenio.websubmit_engine import home, action, interface, endaction

class WebInterfaceSubmitPages(WebInterfaceDirectory):

    _exports = ['summary', 'sub', 'direct', '', 'attachfile', 'uploadfile', \
                'getuploadedfile', 'managedocfiles', 'managedocfilesasync']

    def managedocfiles(self, req, form):
        """
        Display admin interface to manage files of a record
        """
        argd = wash_urlargd(form, {
            'ln': (str, ''),
            'access': (str, ''),
            'recid': (int, None),
            'do': (int, 0),
            'cancel': (str, None),
            })

        _ = gettext_set_language(argd['ln'])
        uid = getUid(req)
        user_info = collect_user_info(req)
        # Check authorization
        (auth_code, auth_msg) = acc_authorize_action(req,
                                                     'runbibdocfile')
        if auth_code and user_info['email'] == 'guest':
            # Ask to login
            target = '/youraccount/login' + \
                     make_canonical_urlargd({'ln' : argd['ln'],
                                             'referer' : CFG_SITE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, referer="/submit/managedocfiles",
                                       uid=uid, text=auth_msg,
                                       ln=argd['ln'],
                                       navmenuid="admin")

        # Prepare navtrail
        navtrail = '''<a class="navtrail" href="%(CFG_SITE_URL)s/help/admin">Admin Area</a> &gt; %(manage_files)s''' \
        % {'CFG_SITE_URL': CFG_SITE_URL,
           'manage_files': _("Manage Document Files")}

        body = ''
        if argd['do'] != 0 and not argd['cancel']:
            # Apply modifications
            working_dir = os.path.join(CFG_TMPDIR,
                                       'websubmit_upload_interface_config_' + str(uid),
                                       argd['access'])
            move_uploaded_files_to_storage(working_dir=working_dir,
                                           recid=argd['recid'],
                                           icon_sizes=['180>','700>'],
                                           create_icon_doctypes=['*'],
                                           force_file_revision=False)
            # Clean temporary directory
            shutil.rmtree(working_dir)

            # Confirm modifications
            body += '<p style="color:#0f0">%s</p>' % \
                    (_('Your modifications to record #%i have been submitted') % argd['recid'])
        elif argd['cancel']:
            # Clean temporary directory
            working_dir = os.path.join(CFG_TMPDIR,
                                       'websubmit_upload_interface_config_' + str(uid),
                                       argd['access'])
            shutil.rmtree(working_dir)
            body += '<p style="color:#c00">%s</p>' % \
                    (_('Your modifications to record #%i have been cancelled') % argd['recid'])

        if not argd['recid'] or argd['do'] != 0:
            body += '''
        <form method="post" action="%(CFG_SITE_URL)s/submit/managedocfiles">
        <label for="recid">%(edit_record)s:</label>
        <input type="text" name="recid" id="recid" />
        <input type="submit" value="%(edit)s" class="adminbutton" />
        </form>
        ''' % {'edit': _('Edit'),
               'edit_record': _('Edit record'),
               'CFG_SITE_URL': CFG_SITE_URL}

        access = time.strftime('%Y%m%d_%H%M%S')
        if argd['recid'] and argd['do'] == 0:
            # Displaying interface to manage files
            # Prepare navtrail
            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, argd['recid'],
                                                                                               argd['ln'])
            navtrail = '''<a class="navtrail" href="%(CFG_SITE_URL)s/help/admin">Admin Area</a> &gt;
        <a class="navtrail" href="%(CFG_SITE_URL)s/submit/managedocfiles">%(manage_files)s</a> &gt;
        %(record)s: %(title)s
        ''' \
            % {'CFG_SITE_URL': CFG_SITE_URL,
               'title': title,
               'manage_files': _("Document File Manager"),
               'record': _("Record #%i") % argd['recid']}

            # FIXME: add parameters to `runbibdocfile' in order to
            # configure the file editor based on role, or at least
            # move configuration below to some config file.
            body += create_file_upload_interface(\
                recid=argd['recid'],
                ln=argd['ln'],
                doctypes_and_desc=[('main', 'Main document'),
                                   ('latex', 'LaTeX'),
                                   ('source', 'Source'),
                                   ('additional', 'Additional File'),
                                   ('audio', 'Audio file'),
                                   ('video', 'Video file'),
                                   ('script', 'Script'),
                                   ('data', 'Data'),
                                   ('figure', 'Figure'),
                                   ('schema', 'Schema'),
                                   ('graph', 'Graph'),
                                   ('image', 'Image'),
                                   ('drawing', 'Drawing'),
                                   ('slides', 'Slides')],
                can_revise_doctypes=['*'],
                can_comment_doctypes=['*'],
                can_describe_doctypes=['*'],
                can_delete_doctypes=['*'],
                can_keep_doctypes=['*'],
                can_rename_doctypes=['*'],
                can_add_format_to_doctypes=['*'],
                can_restrict_doctypes=['*'],
                restrictions_and_desc=[('', 'Public'),
                                       ('restricted', 'Restricted')],
                uid=uid,
                sbm_access=access)[1]

            body += '''<br />
            <form method="post" action="%(CFG_SITE_URL)s/submit/managedocfiles">
            <input type="hidden" name="recid" value="%(recid)s" />
            <input type="hidden" name="do" value="1" />
            <input type="hidden" name="access" value="%(access)s" />
            <input type="hidden" name="ln" value="%(ln)s" />
            <div style="font-size:small">
    <input type="submit" name="cancel" value="%(cancel_changes)s" />
    <input type="submit" onclick="user_must_confirm_before_leaving_page=false;return true;" class="adminbutton" name="submit" id="applyChanges" value="%(apply_changes)s" />
    </div></form>''' % \
    {'apply_changes': _("Apply changes"),
     'cancel_changes': _("Cancel all changes"),
     'recid': argd['recid'],
     'access': access,
     'ln': argd['ln'],
     'CFG_SITE_URL': CFG_SITE_URL}

            body += websubmit_templates.tmpl_page_do_not_leave_submission_js(argd['ln'], enabled=True)

        return page(title = _("Document File Manager") + (argd['recid'] and (': ' + _("Record #%i") % argd['recid']) or ''),
                    navtrail=navtrail,
                    navtrail_append_title_p=0,
                    metaheaderadd = get_upload_file_interface_javascript(form_url_params='?access='+access) + \
                                    get_upload_file_interface_css(),
                    body = body,
                    uid = uid,
                    language=argd['ln'],
                    req=req,
                    navmenuid='admin')

    def managedocfilesasync(self, req, form):
        "Upload file and returns upload interface"

        argd = wash_urlargd(form, {
            'ln': (str, ''),
            'recid': (int, 1),
            'doctype': (str, ''),
            'access': (str, ''),
            'indir': (str, ''),
            })

        user_info = collect_user_info(req)
        include_headers = False
        # User submitted either through WebSubmit, or admin interface.
        if form.has_key('doctype') and form.has_key('indir') \
               and form.has_key('access'):
            # Submitted through WebSubmit. Check rights
            include_headers = True
            working_dir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                  argd['indir'], argd['doctype'],
                                  argd['access'])
            try:
                assert(working_dir == os.path.abspath(working_dir))
            except AssertionError:
                return apache.HTTP_UNAUTHORIZED
            try:
                # Retrieve recid from working_dir, safer.
                recid_fd = file(os.path.join(working_dir, 'SN'))
                recid = int(recid_fd.read())
                recid_fd.close()
            except:
                recid = ""
            try:
                act_fd = file(os.path.join(working_dir, 'act'))
                action = act_fd.read()
                act_fd.close()
            except:
                action = ""

            # Is user authorized to perform this action?
            (auth_code, auth_msg) = acc_authorize_action(user_info,
                                                         "submit",
                                                         doctype=argd['doctype'],
                                                         act=action)
        else:
            # User must be allowed to attach files
            (auth_code, auth_msg) = acc_authorize_action(user_info,
                                                         'runbibdocfile')
            recid = argd['recid']

        if auth_code:
            return apache.HTTP_UNAUTHORIZED

        return create_file_upload_interface(recid=recid,
                                            ln=argd['ln'],
                                            print_outside_form_tag=False,
                                            print_envelope=False,
                                            form=form,
                                            include_headers=include_headers,
                                            sbm_indir=argd['indir'],
                                            sbm_access=argd['access'],
                                            sbm_doctype=argd['doctype'],
                                            uid=user_info['uid'])[1]

    def uploadfile(self, req, form):
        """
        Similar to /submit, but only consider files. Nice for
        asynchronous Javascript uploads. Should be used to upload a
        single file.

        Also try to create an icon, and return URL to file(s) + icon(s)

        Authentication is performed based on session ID passed as
        parameter instead of cookie-based authentication, due to the
        use of this URL by the Flash plugin (to upload multiple files
        at once), which does not route cookies.

        FIXME: consider adding /deletefile and /modifyfile functions +
        parsing of additional parameters to rename files, add
        comments, restrictions, etc.
        """
        if sys.hexversion < 0x2060000:
            try:
                import simplejson as json
                simplejson_available = True
            except ImportError:
                # Okay, no Ajax app will be possible, but continue anyway,
                # since this package is only recommended, not mandatory.
                simplejson_available = False
        else:
            import json
            simplejson_available = True

        argd = wash_urlargd(form, {
            'doctype': (str, ''),
            'access': (str, ''),
            'indir': (str, ''),
            'session_id': (str, ''),
            'rename': (str, ''),
            })

        curdir = None
        if not form.has_key("indir") or \
               not form.has_key("doctype") or \
               not form.has_key("access"):
            return apache.HTTP_BAD_REQUEST
        else:
            curdir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                  argd['indir'],
                                  argd['doctype'],
                                  argd['access'])

        user_info = collect_user_info(req)
        if form.has_key("session_id"):
            # Are we uploading using Flash, which does not transmit
            # cookie? The expect to receive session_id as a form
            # parameter.  First check that IP addresses do not
            # mismatch. A ValueError will be raises if there is
            # something wrong
            session = get_session(req=req, sid=argd['session_id'])
            try:
                session = get_session(req=req, sid=argd['session_id'])
            except ValueError, e:
                return apache.HTTP_BAD_REQUEST

            # Retrieve user information. We cannot rely on the session here.
            res = run_sql("SELECT uid FROM session WHERE session_key=%s", (argd['session_id'],))
            if len(res):
                uid = res[0][0]
                user_info = collect_user_info(uid)
                try:
                    act_fd = file(os.path.join(curdir, 'act'))
                    action = act_fd.read()
                    act_fd.close()
                except:
                    act = ""

        # Is user authorized to perform this action?
        (auth_code, auth_message) = acc_authorize_action(uid, "submit",
                                                     verbose=0,
                                                     doctype=argd['doctype'],
                                                     act=action)
        if acc_is_role("submit", doctype=argd['doctype'], act=action) and auth_code != 0:
            # User cannot submit
            return apache.HTTP_UNAUTHORIZED
        else:
            # Process the upload and get the response
            added_files = {}
            for key, formfields in form.items():
                filename = key.replace("[]", "")
                file_to_open = os.path.join(curdir, filename)
                if hasattr(formfields, "filename") and formfields.filename:
                    dir_to_open = os.path.abspath(os.path.join(curdir,
                                                               'files',
                                                               str(user_info['uid']),
                                                               key))
                    try:
                        assert(dir_to_open.startswith(CFG_WEBSUBMIT_STORAGEDIR))
                    except AssertionError:
                        register_exception(req=req, prefix='curdir="%s", key="%s"' % (curdir, key))
                        return apache.HTTP_FORBIDDEN

                    if not os.path.exists(dir_to_open):
                        try:
                            os.makedirs(dir_to_open)
                        except:
                            register_exception(req=req, alert_admin=True)
                            return apache.HTTP_FORBIDDEN

                    filename = formfields.filename
                    ## Before saving the file to disc, wash the filename (in particular
                    ## washing away UNIX and Windows (e.g. DFS) paths):
                    filename = os.path.basename(filename.split('\\')[-1])
                    filename = filename.strip()
                    if filename != "":
                        # Check that file does not already exist
                        n = 1
                        while os.path.exists(os.path.join(dir_to_open, filename)):
                            #dirname, basename, extension = decompose_file(new_destination_path)
                            basedir, name, extension = decompose_file(filename)
                            new_name = propose_next_docname(name)
                            filename = new_name + extension
                        # This may be dangerous if the file size is bigger than the available memory
                        fp = open(os.path.join(dir_to_open, filename), "w")
                        fp.write(formfields.file.read())
                        fp.close()
                        fp = open(os.path.join(curdir, "lastuploadedfile"), "w")
                        fp.write(filename)
                        fp.close()
                        fp = open(file_to_open, "w")
                        fp.write(filename)
                        fp.close()
                        try:
                            # Create icon
                            (icon_path, icon_name) = create_icon(
                                { 'input-file'           : os.path.join(dir_to_open, filename),
                                  'icon-name'            : filename, # extension stripped automatically
                                  'icon-file-format'     : 'gif',
                                  'multipage-icon'       : False,
                                  'multipage-icon-delay' : 100,
                                  'icon-scale'           : "300>", # Resize only if width > 300
                                  'verbosity'            : 0,
                                  })

                            icons_dir = os.path.join(os.path.join(curdir,
                                                                  'icons',
                                                                  str(user_info['uid']),
                                                                  key))
                            if not os.path.exists(icons_dir):
                                # Create uid/icons dir if needed
                                os.makedirs(icons_dir)
                            os.rename(os.path.join(icon_path, icon_name),
                                      os.path.join(icons_dir, icon_name))
                            added_files[key] = {'name': filename,
                                                'iconName': icon_name}
                        except InvenioWebSubmitIconCreatorError, e:
                            # We could not create the icon
                            added_files[key] = {'name': filename}
                            continue
                    else:
                        return apache.HTTP_BAD_REQUEST

            # Send our response
            if simplejson_available:
                return json.dumps(added_files)

    def getuploadedfile(self, req, form):
        """
        Stream uploaded files.

        For the moment, restrict to files in ./curdir/files/uid or
        ./curdir/icons/uid directory, so that we are sure we stream
        files only to the user who uploaded them.
        """
        argd = wash_urlargd(form, {'indir': (str, None),
                                   'doctype': (str, None),
                                   'access': (str, None),
                                   'icon': (int, 0),
                                   'key': (str, None),
                                   'filename': (str, None)})

        if None in argd.values():
            return apache.HTTP_BAD_REQUEST

        uid = getUid(req)

        if argd['icon']:
            file_path = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                     argd['indir'],
                                     argd['doctype'],
                                     argd['access'],
                                     'icons',
                                     str(uid),
                                     argd['key'],
                                     argd['filename']
                                     )
        else:
            file_path = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                     argd['indir'],
                                     argd['doctype'],
                                     argd['access'],
                                     'files',
                                     str(uid),
                                     argd['key'],
                                     argd['filename']
                                     )

        abs_file_path = os.path.abspath(file_path)
        if abs_file_path.startswith(CFG_WEBSUBMIT_STORAGEDIR):
            # Check if file exist. Note that icon might not yet have
            # been created.
            for i in range(5):
                if os.path.exists(abs_file_path):
                    return stream_file(req, abs_file_path)
                time.sleep(1)

        # Send error 404 in all other cases
        return apache.HTTP_NOT_FOUND

    def attachfile(self, req, form):
        """
        Process requests received from FCKeditor to upload files.
        If the uploaded file is an image, create an icon version
        """
        if not fckeditor_available:
            return apache.HTTP_NOT_FOUND

        if not form.has_key('type'):
            form['type'] = 'File'

        if not form.has_key('NewFile') or \
               not form['type'] in \
               ['File', 'Image', 'Flash', 'Media']:
            return apache.HTTP_NOT_FOUND

        uid = getUid(req)

        # URL where the file can be fetched after upload
        user_files_path = '%(CFG_SITE_URL)s/submit/getattachedfile/%(uid)s' % \
                          {'uid': uid,
                           'CFG_SITE_URL': CFG_SITE_URL}

        # Path to directory where uploaded files are saved
        user_files_absolute_path = '%(CFG_PREFIX)s/var/tmp/attachfile/%(uid)s' % \
                                   {'uid': uid,
                                    'CFG_PREFIX': CFG_PREFIX}
        try:
            os.makedirs(user_files_absolute_path)
        except:
            pass

        # Create a Connector instance to handle the request
        conn = FCKeditorConnectorInvenio(form, recid=-1, uid=uid,
                                         allowed_commands=['QuickUpload'],
                                         allowed_types = ['File', 'Image', 'Flash', 'Media'],
                                         user_files_path = user_files_path,
                                         user_files_absolute_path = user_files_absolute_path)

        user_info = collect_user_info(req)
        (auth_code, auth_message) = acc_authorize_action(user_info, 'attachsubmissionfile')
        if user_info['email'] == 'guest':
            # User is guest: must login prior to upload
            data = conn.sendUploadResults(1, '', '', 'Please login before uploading file.')
        elif auth_code:
            # User cannot submit
            data = conn.sendUploadResults(1, '', '', 'Sorry, you are not allowed to submit files.')
        else:
            # Process the upload and get the response
            data = conn.doResponse()

            # At this point, the file has been uploaded. The FCKeditor
            # submit the image in form['NewFile']. However, the image
            # might have been renamed in between by the FCK connector on
            # the server side, by appending (%04d) at the end of the base
            # name. Retrieve that file
            uploaded_file_path = os.path.join(user_files_absolute_path,
                                              form['type'].lower(),
                                              form['NewFile'].filename)
            uploaded_file_path = retrieve_most_recent_attached_file(uploaded_file_path)
            uploaded_file_name = os.path.basename(uploaded_file_path)

            # Create an icon
            if form.get('type','') == 'Image':
                try:
                    (icon_path, icon_name) = create_icon(
                        { 'input-file'           : uploaded_file_path,
                          'icon-name'            : os.path.splitext(uploaded_file_name)[0],
                          'icon-file-format'     : os.path.splitext(uploaded_file_name)[1][1:] or 'gif',
                          'multipage-icon'       : False,
                          'multipage-icon-delay' : 100,
                          'icon-scale'           : "300>", # Resize only if width > 300
                          'verbosity'            : 0,
                          })

                    # Move original file to /original dir, and replace it with icon file
                    original_user_files_absolute_path = os.path.join(user_files_absolute_path,
                                                                     'image', 'original')
                    if not os.path.exists(original_user_files_absolute_path):
                        # Create /original dir if needed
                        os.mkdir(original_user_files_absolute_path)
                    os.rename(uploaded_file_path,
                              original_user_files_absolute_path + os.sep + uploaded_file_name)
                    os.rename(icon_path + os.sep + icon_name,
                              uploaded_file_path)
                except InvenioWebSubmitIconCreatorError, e:
                    pass

            # Transform the headers into something ok for mod_python
            for header in conn.headers:
                if not header is None:
                    if header[0] == 'Content-Type':
                        req.content_type = header[1]
                    else:
                        req.headers_out[header[0]] = header[1]

        # Send our response
        req.send_http_header()
        req.write(data)

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs (for getting
        and putting attachments) Eg:
        /submit/getattachedfile/41336978/image/myfigure.png
        /submit/attachfile/41336978/image/myfigure.png
        """
        if component == 'getattachedfile' and len(path) > 2:

            uid = path[0] # uid of the submitter
            file_type = path[1] # file, image, flash or media (as
                                # defined by FCKeditor)

            if file_type in ['file', 'image', 'flash', 'media']:
                file_name = '/'.join(path[2:]) # the filename

                def answer_get(req, form):
                    """Accessing files attached to submission."""
                    form['file'] = file_name
                    form['type'] = file_type
                    form['uid'] = uid
                    return self.getattachedfile(req, form)

                return answer_get, []

        # All other cases: file not found
        return None, []

    def getattachedfile(self, req, form):
        """
        Returns a file uploaded to the submission 'drop box' by the
        FCKeditor.
        """
        argd = wash_urlargd(form, {'file': (str, None),
                                   'type': (str, None),
                                   'uid': (int, 0)})

        # Can user view this record, i.e. can user access its
        # attachments?
        uid = getUid(req)
        user_info = collect_user_info(req)

        if not argd['file'] is None:
            # Prepare path to file on disk. Normalize the path so that
            # ../ and other dangerous components are removed.
            path = os.path.abspath(CFG_PREFIX + '/var/tmp/attachfile/' + \
                                   '/'  + str(argd['uid']) + \
                                   '/' + argd['type'] + '/' + argd['file'])

            # Check that we are really accessing attachements
            # directory, for the declared record.
            if path.startswith(CFG_PREFIX + '/var/tmp/attachfile/') and os.path.exists(path):
                return stream_file(req, path)

        # Send error 404 in all other cases
        return(apache.HTTP_NOT_FOUND)

    def direct(self, req, form):
        """Directly redirected to an initialized submission."""
        args = wash_urlargd(form, {'sub': (str, ''),
                                   'access' : (str, '')})

        sub = args['sub']
        access = args['access']
        ln = args['ln']

        _ = gettext_set_language(ln)

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "direct",
                                           navmenuid='submit')

        myQuery = req.args
        if not sub:
            return warningMsg(_("Sorry, 'sub' parameter missing..."), req, ln=ln)
        res = run_sql("SELECT docname,actname FROM sbmIMPLEMENT WHERE subname=%s", (sub,))
        if not res:
            return warningMsg(_("Sorry. Cannot analyse parameter"), req, ln=ln)
        else:
            # get document type
            doctype = res[0][0]
            # get action name
            action = res[0][1]
        # retrieve other parameter values
        params = dict(form)
        # find existing access number
        if not access:
            # create 'unique' access number
            pid = os.getpid()
            now = time.time()
            access = "%i_%s" % (now,pid)
        # retrieve 'dir' value
        res = run_sql ("SELECT dir FROM sbmACTION WHERE sactname=%s", (action,))
        dir = res[0][0]

        mainmenu = req.headers_in.get('referer')

        params['access'] = access
        params['act'] = action
        params['doctype'] = doctype
        params['startPg'] = '1'
        params['mainmenu'] = mainmenu
        params['ln'] = ln
        params['indir'] = dir

        url = "%s/submit?%s" % (CFG_SITE_URL, urlencode(params))
        redirect_to_url(req, url)

    def sub(self, req, form):
        """DEPRECATED: /submit/sub is deprecated now, so raise email to the admin (but allow submission to continue anyway)"""
        args = wash_urlargd(form, {'password': (str, '')})
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../sub/",
                                       navmenuid='submit')
        try:
            raise DeprecationWarning, 'submit/sub handler has been used. Please use submit/direct. e.g. "submit/sub?RN=123@SBIFOO" -> "submit/direct?RN=123&sub=SBIFOO"'
        except DeprecationWarning:
            register_exception(req=req, alert_admin=True)

        ln = args['ln']
        _ = gettext_set_language(ln)
        #DEMOBOO_RN=DEMO-BOOK-2008-001&ln=en&password=1223993532.26572%40APPDEMOBOO
        params = dict(form)
        password = args['password']
        if password:
            del params['password']
            if "@" in password:
                params['access'], params['sub'] = password.split('@', 1)
            else:
                params['sub'] = password
        else:
            args = str(req.args).split('@')
            if len(args) > 1:
                params = {'sub' : args[-1]}
                args = '@'.join(args[:-1])
                params.update(cgi.parse_qs(args))
            else:
                return warningMsg(_("Sorry, invalid URL..."), req, ln=ln)
        url = "%s/submit/direct?%s" % (CFG_SITE_URL, urlencode(params, doseq=True))
        redirect_to_url(req, url)


    def summary(self, req, form):
        args = wash_urlargd(form, {
            'doctype': (str, ''),
            'act': (str, ''),
            'access': (str, ''),
            'indir': (str, '')})

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../summary",
                                       navmenuid='submit')

        t=""
        curdir  = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, args['indir'], args['doctype'], args['access'])
        try:
            assert(curdir == os.path.abspath(curdir))
        except AssertionError:
            register_exception(req=req, alert_admin=True, prefix='Possible cracking tentative: indir="%s", doctype="%s", access="%s"' % (args['indir'], args['doctype'], args['access']))
            return warningMsg("Invalid parameters", req)

        subname = "%s%s" % (args['act'], args['doctype'])

        res = run_sql("select sdesc,fidesc,pagenb,level from sbmFIELD where subname=%s "
                      "order by pagenb,fieldnb", (subname,))
        nbFields = 0

        values = []
        for arr in res:
            if arr[0] != "":
                val = {
                       'mandatory' : (arr[3] == 'M'),
                       'value' : '',
                       'page' : arr[2],
                       'name' : arr[0],
                      }
                if os.path.exists(os.path.join(curdir, curdir,arr[1])):
                    fd = open(os.path.join(curdir, arr[1]),"r")
                    value = fd.read()
                    fd.close()
                    value = value.replace("\n"," ")
                    value = value.replace("Select:","")
                else:
                    value = ""
                val['value'] = value
                values.append(val)

        return websubmit_templates.tmpl_submit_summary(
                 ln = args['ln'],
                 values = values,
               )

    def index(self, req, form):

        args = wash_urlargd(form, {
            'c': (str, CFG_SITE_NAME),
            'doctype': (str, ''),
            'act': (str, ''),
            'startPg': (str, "1"),
            'access': (str, ''),
            'mainmenu': (str, ''),
            'fromdir': (str, ''),
            'nextPg': (str, ''),
            'nbPg': (str, ''),
            'curpage': (str, '1'),
            'step': (str, '0'),
            'mode': (str, 'U'),
            })

        ## Strip whitespace from beginning and end of doctype and action:
        args["doctype"] = args["doctype"].strip()
        args["act"] = args["act"].strip()

        def _index(req, c, ln, doctype, act, startPg, access,
                   mainmenu, fromdir, nextPg, nbPg, curpage, step,
                   mode):

            uid = getUid(req)
            if isGuestUser(uid):
                return redirect_to_url(req, "%s/youraccount/login%s" % (
                    CFG_SITE_SECURE_URL,
                        make_canonical_urlargd({
                    'referer' : CFG_SITE_URL + req.unparsed_uri, 'ln' : args['ln']}, {})), norobot=True)

            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
                return page_not_authorized(req, "../submit",
                                           navmenuid='submit')
            if CFG_CERN_SITE:
                ## HACK BEGIN: this is a hack for CMS and ATLAS draft
                from invenio.webuser import collect_user_info
                user_info = collect_user_info(req)
                if doctype == 'CMSPUB' and 'cds-admin [CERN]' not in user_info['group'] and not user_info['email'].lower() == 'cds.support@cern.ch':
                    if 'cms-publication-committee-chair [CERN]' not in user_info['group']:
                        return page_not_authorized(req, "../submit", text="In order to access this submission interface you need to be member of the CMS Publication Committee Chair.",
                                        navmenuid='submit')
                elif doctype == 'ATLPUB' and 'cds-admin [CERN]' not in user_info['group'] and not user_info['email'].lower() == 'cds.support@cern.ch':
                    if 'atlas-gen [CERN]' not in user_info['group']:
                        return page_not_authorized(req, "../submit", text="In order to access this submission interface you need to be member of ATLAS.",
                                        navmenuid='submit')
            ## HACK END

            if doctype=="":
                return home(req,c,ln)
            elif act=="":
                return action(req,c,ln,doctype)
            elif int(step)==0:
                return interface(req, c, ln, doctype, act, startPg, access, mainmenu, fromdir, nextPg, nbPg, curpage)
            else:
                return endaction(req, c, ln, doctype, act, startPg, access,mainmenu, fromdir, nextPg, nbPg, curpage, step, mode)

        return _index(req, **args)

    # Answer to both /submit/ and /submit
    __call__ = index

def errorMsg(title, req, c=None, ln=CFG_SITE_LANG):
    # load the right message language
    _ = gettext_set_language(ln)

    if c is None:
        c = CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)

    return page(title = _("Error"),
                body = create_error_box(req, title=str(title), verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                uid = getUid(req),
                language=ln,
                req=req,
                navmenuid='submit')

def warningMsg(title, req, c=None, ln=CFG_SITE_LANG):
    # load the right message language
    _ = gettext_set_language(ln)

    if c is None:
        c = CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)

    return page(title = _("Warning"),
                body = title,
                description="%s - Internal Error" % c,
                keywords="%s, Internal Error" % c,
                uid = getUid(req),
                language=ln,
                req=req,
                navmenuid='submit')

def print_warning(msg, type='', prologue='<br />', epilogue='<br />'):
    """Prints warning message and flushes output."""
    if msg:
        return websubmit_templates.tmpl_print_warning(
                   msg = msg,
                   type = type,
                   prologue = prologue,
                   epilogue = epilogue,
                 )
    else:
        return ''

def retrieve_most_recent_attached_file(file_path):
    """
    Retrieve the latest file that has been uploaded with the
    FCKeditor. This is the only way to retrieve files that the
    FCKeditor has renamed after the upload.

    Eg: 'prefix/image.jpg' was uploaded but did already
    exist. FCKeditor silently renamed it to 'prefix/image(1).jpg':
    >>> retrieve_most_recent_attached_file('prefix/image.jpg')
    'prefix/image(1).jpg'
    """
    (base_path, filename) = os.path.split(file_path)
    base_name = os.path.splitext(filename)[0]
    file_ext = os.path.splitext(filename)[1][1:]
    most_recent_filename = filename
    i = 0
    while True:
        i += 1
        possible_filename = "%s(%d).%s" % \
                            (base_name, i, file_ext)
        if os.path.exists(base_path + os.sep + possible_filename):
            most_recent_filename = possible_filename
        else:
            break

    return os.path.join(base_path, most_recent_filename)
