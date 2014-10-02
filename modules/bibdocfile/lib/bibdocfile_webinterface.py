## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

import cgi
import os
import time
import shutil

from invenio.config import (CFG_ACCESS_CONTROL_LEVEL_SITE,
                            CFG_SITE_LANG,
                            CFG_TMPSHAREDDIR,
                            CFG_SITE_URL,
                            CFG_SITE_SECURE_URL,
                            CFG_WEBSUBMIT_STORAGEDIR,
                            CFG_SITE_RECORD,
                            CFG_INSPIRE_SITE,
                            CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_ICON_DOCTYPES,
                            CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_ICON_SIZE)
from invenio.bibdocfile_config import CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_DOCTYPES, \
     CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_MISC, \
     CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_RESTRICTIONS, \
     CFG_BIBDOCFILE_ICON_SUBFORMAT_RE
from invenio import webinterface_handler_config as apache
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_is_role
from invenio.webpage import page, pageheaderonly, \
    pagefooteronly, warning_page, write_warning
from invenio.webuser import getUid, page_not_authorized, collect_user_info, isUserSuperAdmin, \
                            isGuestUser
from invenio import webjournal_utils
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import make_canonical_urlargd, redirect_to_url
from invenio.messages import gettext_set_language
from invenio.search_engine import \
     guess_primary_collection_of_a_record, get_colID, record_exists, \
     create_navtrail_links, check_user_can_view_record, record_empty, \
     is_user_owner_of_record
from invenio.bibdocfile import BibRecDocs, normalize_format, file_strip_ext, \
    stream_restricted_icon, BibDoc, InvenioBibDocFileError, \
    get_subformat_from_format
from invenio.errorlib import register_exception
from invenio.websearchadminlib import get_detailed_page_tabs, get_detailed_page_tabs_counts
import invenio.template
bibdocfile_templates = invenio.template.load('bibdocfile')
webstyle_templates = invenio.template.load('webstyle')
websubmit_templates = invenio.template.load('websubmit')
websearch_templates = invenio.template.load('websearch')

from invenio.bibdocfile_managedocfiles import \
     create_file_upload_interface, \
     get_upload_file_interface_javascript, \
     get_upload_file_interface_css, \
     move_uploaded_files_to_storage

bibdocfile_templates = invenio.template.load('bibdocfile')


class WebInterfaceFilesPages(WebInterfaceDirectory):

    def __init__(self, recid):
        self.recid = recid

    def _lookup(self, component, path):
        # after /<CFG_SITE_RECORD>/<recid>/files/ every part is used as the file
        # name
        filename = component

        def getfile(req, form):
            args = wash_urlargd(form, bibdocfile_templates.files_default_urlargd)
            ln = args['ln']

            _ = gettext_set_language(ln)

            uid = getUid(req)
            user_info = collect_user_info(req)

            verbose = args['verbose']
            if verbose >= 1 and not isUserSuperAdmin(user_info):
                # Only SuperUser can see all the details!
                verbose = 0

            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE > 1:
                return page_not_authorized(req, "/%s/%s" % (CFG_SITE_RECORD, self.recid),
                                           navmenuid='submit')

            if record_exists(self.recid) < 1:
                msg = "<p>%s</p>" % _("Requested record does not seem to exist.")
                return warning_page(msg, req, ln)

            if record_empty(self.recid):
                msg = "<p>%s</p>" % _("Requested record does not seem to have been integrated.")
                return warning_page(msg, req, ln)

            (auth_code, auth_message) = check_user_can_view_record(user_info, self.recid)
            if auth_code and user_info['email'] == 'guest':
                if webjournal_utils.is_recid_in_released_issue(self.recid):
                    # We can serve the file
                    pass
                else:
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                             make_canonical_urlargd({'action': cookie, 'ln' : ln, 'referer' : \
                                                     CFG_SITE_SECURE_URL + user_info['uri']}, {})
                    return redirect_to_url(req, target, norobot=True)
            elif auth_code:
                if webjournal_utils.is_recid_in_released_issue(self.recid):
                    # We can serve the file
                    pass
                else:
                    return page_not_authorized(req, "../", \
                                               text = auth_message)


            readonly = CFG_ACCESS_CONTROL_LEVEL_SITE == 1

            # From now on: either the user provided a specific file
            # name (and a possible version), or we return a list of
            # all the available files. In no case are the docids
            # visible.
            try:
                bibarchive = BibRecDocs(self.recid)
            except InvenioBibDocFileError:
                register_exception(req=req, alert_admin=True)
                msg = "<p>%s</p><p>%s</p>" % (
                    _("The system has encountered an error in retrieving the list of files for this document."),
                    _("The error has been logged and will be taken in consideration as soon as possible."))
                return warning_page(msg, req, ln)

            if bibarchive.deleted_p():
                req.status = apache.HTTP_GONE
                return warning_page(_("Requested record does not seem to exist."), req, ln)

            docname = ''
            docformat = ''
            version = ''
            warn = ''

            if filename:
                # We know the complete file name, guess which docid it
                # refers to
                ## TODO: Change the extension system according to ext.py from setlink
                ##       and have a uniform extension mechanism...
                docname = file_strip_ext(filename)
                docformat = filename[len(docname):]
                if docformat and docformat[0] != '.':
                    docformat = '.' + docformat
                if args['subformat']:
                    docformat += ';%s' % args['subformat']
            else:
                docname = args['docname']

            if not docformat:
                docformat = args['format']
                if args['subformat']:
                    docformat += ';%s' % args['subformat']

            if not version:
                version = args['version']

            ## Download as attachment
            is_download = False
            if args['download']:
                is_download = True

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
                    if docname == bibarchive.get_docname(doc.id):
                        try:
                            try:
                                docfile = doc.get_file(docformat, version)
                            except InvenioBibDocFileError, msg:
                                req.status = apache.HTTP_NOT_FOUND
                                if not CFG_INSPIRE_SITE and req.headers_in.get('referer'):
                                    ## There must be a broken link somewhere.
                                    ## Maybe it's good to alert the admin
                                    register_exception(req=req, alert_admin=True)
                                warn += write_warning(_("The format %s does not exist for the given version: %s") % (cgi.escape(docformat), cgi.escape(str(msg))))
                                break
                            (auth_code, auth_message) = docfile.is_restricted(user_info)
                            if auth_code != 0 and not is_user_owner_of_record(user_info, self.recid):
                                if CFG_BIBDOCFILE_ICON_SUBFORMAT_RE.match(get_subformat_from_format(docformat)):
                                    return stream_restricted_icon(req)
                                if user_info['email'] == 'guest':
                                    cookie = mail_cookie_create_authorize_action('viewrestrdoc', {'status' : docfile.get_status()})
                                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                                    make_canonical_urlargd({'action': cookie, 'ln' : ln, 'referer' : \
                                        CFG_SITE_SECURE_URL + user_info['uri']}, {})
                                    redirect_to_url(req, target)
                                else:
                                    req.status = apache.HTTP_UNAUTHORIZED
                                    warn += write_warning(_("This file is restricted: ") + str(auth_message))
                                    break

                            if not docfile.hidden_p():
                                if not readonly:
                                    ip = str(req.remote_ip)
                                    doc.register_download(ip, docfile.get_version(), docformat, uid, self.recid)
                                try:
                                    return docfile.stream(req, download=is_download)
                                except InvenioBibDocFileError, msg:
                                    register_exception(req=req, alert_admin=True)
                                    req.status = apache.HTTP_INTERNAL_SERVER_ERROR
                                    warn += write_warning(_("An error has happened in trying to stream the request file."))
                            else:
                                req.status = apache.HTTP_UNAUTHORIZED
                                warn += write_warning(_("The requested file is hidden and can not be accessed."))

                        except InvenioBibDocFileError, msg:
                            register_exception(req=req, alert_admin=True)

            if docname and docformat and not warn:
                req.status = apache.HTTP_NOT_FOUND
                warn += write_warning(_("Requested file does not seem to exist."))
#            filelist = bibarchive.display("", version, ln=ln, verbose=verbose, display_hidden=display_hidden)
            filelist = bibdocfile_templates.tmpl_display_bibrecdocs(bibarchive, "", version, ln=ln, verbose=verbose, display_hidden=display_hidden)

            t = warn + bibdocfile_templates.tmpl_filelist(
                ln=ln,
                filelist=filelist)

            cc = guess_primary_collection_of_a_record(self.recid)
            unordered_tabs = get_detailed_page_tabs(get_colID(cc), self.recid, ln)
            ordered_tabs_id = [(tab_id, values['order']) for (tab_id, values) in unordered_tabs.iteritems()]
            ordered_tabs_id.sort(lambda x, y: cmp(x[1], y[1]))
            link_ln = ''
            if ln != CFG_SITE_LANG:
                link_ln = '?ln=%s' % ln
            tabs = [(unordered_tabs[tab_id]['label'],
                     '%s/%s/%s/%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, tab_id, link_ln),
                     tab_id == 'files',
                     unordered_tabs[tab_id]['enabled'])
                    for (tab_id, dummy_order) in ordered_tabs_id
                    if unordered_tabs[tab_id]['visible'] is True]

            tabs_counts = get_detailed_page_tabs_counts(self.recid)
            top = webstyle_templates.detailed_record_container_top(self.recid,
                                                                   tabs,
                                                                   args['ln'],
                                                                   citationnum=tabs_counts['Citations'],
                                                                   referencenum=tabs_counts['References'],
                                                                   discussionnum=tabs_counts['Discussions'])
            bottom = webstyle_templates.detailed_record_container_bottom(self.recid,
                                                                         tabs,
                                                                         args['ln'])
            title, description, keywords = websearch_templates.tmpl_record_page_header_content(req, self.recid, args['ln'])
            return pageheaderonly(title=title,
                        navtrail=create_navtrail_links(cc=cc, aas=0, ln=ln) + \
                                        ''' &gt; <a class="navtrail" href="%s/%s/%s">%s</a>
                                        &gt; %s''' % \
                        (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, title, _("Access to Fulltext")),

                        description=description,
                        keywords=keywords,
                        uid=uid,
                        language=ln,
                        req=req,
                        navmenuid='search',
                        navtrail_append_title_p=0) + \
                        websearch_templates.tmpl_search_pagestart(ln) + \
                        top + t + bottom + \
                        websearch_templates.tmpl_search_pageend(ln) + \
                        pagefooteronly(language=ln, req=req)
        return getfile, []

    def __call__(self, req, form):
        """Called in case of URLs like /CFG_SITE_RECORD/123/files without
           trailing slash.
        """
        args = wash_urlargd(form, bibdocfile_templates.files_default_urlargd)
        ln = args['ln']
        link_ln = ''
        if ln != CFG_SITE_LANG:
            link_ln = '?ln=%s' % ln

        return redirect_to_url(req, '%s/%s/%s/files/%s' % (CFG_SITE_URL, CFG_SITE_RECORD, self.recid, link_ln))

def bibdocfile_legacy_getfile(req, form):
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

    def _getfile_py(req, recid=0, docid=0, version="", name="", docformat="", ln=CFG_SITE_LANG):
        if not recid:
            ## Let's obtain the recid from the docid
            if docid:
                try:
                    bibdoc = BibDoc(docid=docid)
                    recid = bibdoc.bibrec_links[0]["recid"]
                except InvenioBibDocFileError:
                    return warning_page(_("An error has happened in trying to retrieve the requested file."), req, ln)
            else:
                return warning_page(_('Not enough information to retrieve the document'), req, ln)
        else:
            brd = BibRecDocs(recid)
            if not name and docid:
                ## Let's obtain the name from the docid
                try:
                    name = brd.get_docname(docid)
                except InvenioBibDocFileError:
                    return warning_page(_("An error has happened in trying to retrieving the requested file."), req, ln)

        docformat = normalize_format(docformat)

        redirect_to_url(req, '%s/%s/%s/files/%s%s?ln=%s%s' % (CFG_SITE_URL, CFG_SITE_RECORD, recid, name, docformat, ln, version and 'version=%s' % version or ''), apache.HTTP_MOVED_PERMANENTLY)

    return _getfile_py(req, **args)


# --------------------------------------------------

class WebInterfaceManageDocFilesPages(WebInterfaceDirectory):

    _exports = ['', 'managedocfiles', 'managedocfilesasync']

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
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                     make_canonical_urlargd({'ln' : argd['ln'],
                                             'referer' : CFG_SITE_SECURE_URL + user_info['uri']}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, referer="/%s/managedocfiles" % CFG_SITE_RECORD,
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
            working_dir = os.path.join(CFG_TMPSHAREDDIR,
                                       'websubmit_upload_interface_config_' + str(uid),
                                       argd['access'])
            if not os.path.isdir(working_dir):
                # We accessed the url without preliminary steps
                # (we did not upload a file)
                # Our working dir does not exist
                # Display the file manager
                argd['do'] = 0
            else:
                move_uploaded_files_to_storage(working_dir=working_dir,
                                               recid=argd['recid'],
                                               icon_sizes=CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_ICON_SIZE,
                                               create_icon_doctypes=CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_ICON_DOCTYPES,
                                               force_file_revision=False)
                # Clean temporary directory
                shutil.rmtree(working_dir)

                # Confirm modifications
                body += '<p style="color:#0f0">%s</p>' % \
                        (_('Your modifications to record #%i have been submitted') % argd['recid'])
        elif argd['cancel']:
            # Clean temporary directory
            working_dir = os.path.join(CFG_TMPSHAREDDIR,
                                       'websubmit_upload_interface_config_' + str(uid),
                                       argd['access'])
            shutil.rmtree(working_dir)
            body += '<p style="color:#c00">%s</p>' % \
                    (_('Your modifications to record #%i have been cancelled') % argd['recid'])

        if not argd['recid'] or argd['do'] != 0:
            body += '''
        <form method="post" action="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/managedocfiles">
        <label for="recid">%(edit_record)s:</label>
        <input type="text" name="recid" id="recid" />
        <input type="submit" value="%(edit)s" class="adminbutton" />
        </form>
        ''' % {'edit': _('Edit'),
               'edit_record': _('Edit record'),
               'CFG_SITE_URL': CFG_SITE_URL,
               'CFG_SITE_RECORD': CFG_SITE_RECORD}

        access = time.strftime('%Y%m%d_%H%M%S')
        if argd['recid'] and argd['do'] == 0:
            # Displaying interface to manage files
            # Prepare navtrail
            title, dummy_description, dummy_keywords = websearch_templates.tmpl_record_page_header_content(req, argd['recid'],
                                                                                               argd['ln'])
            navtrail = '''<a class="navtrail" href="%(CFG_SITE_URL)s/help/admin">Admin Area</a> &gt;
        <a class="navtrail" href="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/managedocfiles">%(manage_files)s</a> &gt;
        %(record)s: %(title)s
        ''' \
            % {'CFG_SITE_URL': CFG_SITE_URL,
               'title': title,
               'manage_files': _("Document File Manager"),
               'record': _("Record #%i") % argd['recid'],
               'CFG_SITE_RECORD': CFG_SITE_RECORD}

            body += create_file_upload_interface(\
                recid=argd['recid'],
                ln=argd['ln'],
                uid=uid,
                sbm_access=access,
                display_hidden_files=True,
                restrictions_and_desc=CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_RESTRICTIONS,
                doctypes_and_desc=CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_DOCTYPES,
                **CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_MISC)[1]

            body += '''<br />
            <form method="post" action="%(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/managedocfiles">
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
     'CFG_SITE_URL': CFG_SITE_URL,
     'CFG_SITE_RECORD': CFG_SITE_RECORD}

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
                raise apache.SERVER_RETURN(apache.HTTP_UNAUTHORIZED)
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
            auth_code = acc_authorize_action(user_info,
                "submit",
                authorized_if_no_roles=not isGuestUser(getUid(req)),
                doctype=argd['doctype'],
                act=action)[0]
            if auth_code and not acc_is_role("submit", doctype=argd['doctype'], act=action):
                # There is NO authorization plugged. User should have access
                auth_code = 0
        else:
            # User must be allowed to attach files
            auth_code = acc_authorize_action(user_info, 'runbibdocfile')[0]
            recid = argd['recid']

        if auth_code:
            raise apache.SERVER_RETURN(apache.HTTP_UNAUTHORIZED)

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

    __call__ = managedocfiles
