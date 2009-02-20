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

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

import string
import os
import time
import types
import re
try:
    from mod_python import apache
except ImportError:
    pass

import sys
from urllib import quote, unquote, urlencode

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_NAME_INTL, \
     CFG_SITE_URL, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_VERSION, \
     CFG_SITE_URL
from invenio.dbquery import run_sql, Error
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_is_role
from invenio.webpage import page, create_error_box, pageheaderonly, \
    pagefooteronly
from invenio.webuser import getUid, get_email, page_not_authorized, collect_user_info, isUserSuperAdmin
from invenio.websubmit_config import *
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import make_canonical_urlargd, redirect_to_url
from invenio.messages import gettext_set_language
from invenio.search_engine import \
     guess_primary_collection_of_a_record, \
     get_colID, \
     create_navtrail_links, check_user_can_view_record
from invenio.bibdocfile import BibRecDocs, normalize_format, file_strip_ext, \
    stream_restricted_icon, BibDoc, InvenioWebSubmitFileError
from invenio.errorlib import register_exception

import invenio.template
websubmit_templates = invenio.template.load('websubmit')
from invenio.websearchadminlib import get_detailed_page_tabs
import invenio.template
webstyle_templates = invenio.template.load('webstyle')
websearch_templates = invenio.template.load('websearch')

class WebInterfaceFilesPages(WebInterfaceDirectory):

    def __init__(self,recid):
        self.recid = recid

    def _lookup(self, component, path):
        # after /record/<recid>/files/ every part is used as the file
        # name
        filename = unquote(component)

        def getfile(req, form):
            args = wash_urlargd(form, websubmit_templates.files_default_urlargd)
            ln = args['ln']

            _ = gettext_set_language(ln)

            uid = getUid(req)
            user_info = collect_user_info(req)

            verbose = args['verbose']
            if verbose >= 1 and acc_authorize_action(user_info, 'fulltext')[0] != 0:
                # Only SuperUser can see all the details!
                verbose = 0

            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE > 1:
                return page_not_authorized(req, "/record/%s" % self.recid,
                                           navmenuid='submit')

            (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)
            if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
                cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
                target = '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln' : ln, 'referer' : \
                    CFG_SITE_URL + user_info['uri']}, {})
                return redirect_to_url(req, target)
            elif auth_code:
                return page_not_authorized(req, "../", \
                    text = auth_msg)


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
                return print_warning(msg)

            docname = ''
            format = ''
            version = ''

            if filename:
                # We know the complete file name, guess which docid it
                # refers to
                ## TODO: Change the extension system according to ext.py from setlink
                ##       and have a uniform extension mechanism...
                docname = file_strip_ext(filename)
                format = filename[len(docname):]
                if format and format[0] != '.':
                    format = '.' + format
            else:
                docname = args['docname']

            if not format:
                format = args['format']

            if not version:
                version = args['version']

            # version could be either empty, or all or an integer
            try:
                int(version)
            except ValueError:
                if version != 'all':
                    version = ''

            display_hidden = acc_authorize_action(user_info, 'fulltext')[0] == 0

            if version != 'all':
                # search this filename in the complete list of files
                for doc in bibarchive.list_bibdocs():
                    if docname == doc.get_docname():
                        try:
                            docfile = doc.get_file(format, version)
                        except InvenioWebSubmitFileError, msg:
                            register_exception(req=req, alert_admin=True)

                        if docfile.get_status() == '':
                            # The file is not resticted, let's check for
                            # collection restriction then.
                            (auth_code, auth_message) = check_user_can_view_record(user_info, self.recid)
                            if auth_code:
                                return warningMsg(_("The collection to which this file belong is restricted: ") + auth_message, req, CFG_SITE_NAME, ln)
                        else:
                            # The file is probably restricted on its own.
                            # Let's check for proper authorization then
                            (auth_code, auth_message) = docfile.is_restricted(req)
                            if auth_code != 0:
                                return warningMsg(_("This file is restricted: ") + auth_message, req, CFG_SITE_NAME, ln)

                        if display_hidden or not docfile.hidden_p():
                            if not readonly:
                                ip = str(req.get_remote_host(apache.REMOTE_NOLOOKUP))
                                res = doc.register_download(ip, version, format, uid)
                            try:
                                return docfile.stream(req)
                            except InvenioWebSubmitFileError, msg:
                                register_exception(req=req, alert_admin=True)
                                return warningMsg(_("An error has happened in trying to stream the request file."), req, CFG_SITE_NAME, ln)
                        else:
                            warn = print_warning(_("The requested file is hidden and you don't have the proper rights to access it."))

                    elif doc.get_icon() is not None and doc.get_icon().docname == file_strip_ext(filename):
                        icon = doc.get_icon()
                        try:
                            iconfile = icon.get_file(format, version)
                        except InvenioWebSubmitFileError, msg:
                            register_exception(req=req, alert_admin=True)
                            return warningMsg(_("An error has happened in trying to retrieve the corresponding icon."), req, CFG_SITE_NAME, ln)

                        if iconfile.get_status() == '':
                            # The file is not resticted, let's check for
                            # collection restriction then.
                            (auth_code, auth_message) = check_user_can_view_record(user_info, self.recid)
                            if auth_code:
                                return stream_restricted_icon(req)
                        else:
                            # The file is probably restricted on its own.
                            # Let's check for proper authorization then
                            (auth_code, auth_message) = iconfile.is_restricted(req)
                            if auth_code != 0:
                                return stream_restricted_icon(req)

                        if not readonly:
                            ip = str(req.get_remote_host(apache.REMOTE_NOLOOKUP))
                            res = doc.register_download(ip, version, format, uid)
                        try:
                            return iconfile.stream(req)
                        except InvenioWebSubmitFileError, msg:
                            register_exception(req=req, alert_admin=True)
                            return warningMsg(_("An error has happened in trying to stream the corresponding icon."), req, CFG_SITE_NAME, ln)

            if docname and format and display_hidden:
                req.status = apache.HTTP_NOT_FOUND
                warn = print_warning(_("Requested file does not seem to exist."))
            else:
                warn = ''
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
                        navtrail=create_navtrail_links(cc=cc, as=0, ln=ln) + \
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

    _exports = ['summary', 'sub', 'direct', '']


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
        args = wash_urlargd(form, {'password': (str, '')})
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../sub/",
                                       navmenuid='submit')

        #DEMOBOO_RN=DEMO-BOOK-2008-001&ln=en&password=1223993532.26572%40APPDEMOBOO
        params = dict(form)
        del params['password']
        password = args['password']
        if "@" in password:
            params['access'], params['sub'] = password.split('@', 1)
        else:
            params['sub'] = password
        url = "%s/submit/direct?%s" % (CFG_SITE_URL, urlencode(params))
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
            return warningMsg("Invalid parameters")

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
            'file': (str, ''),
            'nextPg': (str, ''),
            'nbPg': (str, ''),
            'curpage': (str, '1'),
            'step': (str, '0'),
            'mode': (str, 'U'),
            })

        req.form = form
        ## Strip whitespace from beginning and end of doctype and action:
        args["doctype"] = args["doctype"].strip()
        args["act"] = args["act"].strip()

        def _index(req, c, ln, doctype, act, startPg, access,
                   mainmenu, fromdir, file, nextPg, nbPg, curpage, step,
                   mode):

            uid = getUid(req)
            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
                return page_not_authorized(req, "../submit",
                                           navmenuid='submit')

            if doctype=="":
                return home(req,c,ln)
            elif act=="":
                return action(req,c,ln,doctype)
            elif int(step)==0:
                return interface(req, c, ln, doctype, act, startPg, access, mainmenu, fromdir, file, nextPg, nbPg, curpage)
            else:
                return endaction(req, c, ln, doctype, act, startPg, access,mainmenu, fromdir, file, nextPg, nbPg, curpage, step, mode)

        return _index(req, **args)

    # Answer to both /submit/ and /submit
    __call__ = index

def errorMsg(title, req, c=None, ln=CFG_SITE_LANG):
    # load the right message language
    _ = gettext_set_language(ln)

    if c is None:
        c = CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME)

    return page(title = _("Error"),
                body = create_error_box(req, title=title, verbose=0, ln=ln),
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
