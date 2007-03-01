## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

__revision__ = "$Id$"

import string
import os
import time
import types
import re
from mod_python import apache
import sys
from urllib import quote

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     cdslang, \
     cdsname, \
     images, \
     storage, \
     urlpath, \
     version, \
     weburl
from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_isRole
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, page_not_authorized
from invenio.websubmit_config import *
from invenio.file import *
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import make_canonical_urlargd, redirect_to_url
from invenio.messages import gettext_set_language

import invenio.template
websubmit_templates = invenio.template.load('websubmit')


class WebInterfaceFilesPages(WebInterfaceDirectory):

    def __init__(self,recid):
        self.recid = recid
        return
    
    def _lookup(self, component, path):
        # after /record/<recid>/files/ every part is used as the file
        # name (with possible path in the case of archives to be
        # uncompressed)
        filename = component

        def getfile(req, form):
            args = wash_urlargd(form, websubmit_templates.files_default_urlargd)            
            ln = args['ln']
            
            _ = gettext_set_language(ln)

            uid = getUid(req)
            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE > 1:
                return page_not_authorized(req, "../getfile.py/index")

            uid_email = get_email(uid)
            readonly = CFG_ACCESS_CONTROL_LEVEL_SITE == 1

            # From now on: either the user provided a specific file
            # name (and a possible version), or we return a list of
            # all the available files. In no case are the docids
            # visible.
            bibarchive = BibRecDocs(self.recid)

            if filename:
                # We know the complete file name, guess which docid it
                # refers to
		## TODO: Change the extension system according to ext.py from setlink
		##       and have a uniform extension mechanism...
		name = file_strip_ext(filename)
		format = filename[len(name):]
                if format and format[0] == '.':
                    format = format[1:]
                
                # search this filename in the complete list of files
                for doc in bibarchive.listBibDocs():
                    if filename in [f.fullname for f in doc.listAllFiles()]:
                        docfile=doc.getFile(name,format,args['version'])
                        if docfile is None:
                            return warningMsg(_("Unable to find file."), req, cdsname, ln)
                            
                        if docfile.isRestricted():
                            return warningMsg(_("This file is restricted!"), req, cdsname, ln)
			    
                        if not readonly:
                            ip = str(req.get_remote_host(apache.REMOTE_NOLOOKUP))
                            res = doc.registerDownload(ip, version, format, uid)
                            
                        return docfile.stream(req)
                else:
                    return warningMsg(_("Unable to find file."), req, cdsname, ln)

            filelist = bibarchive.display("", args['version'], ln=ln)

            t = websubmit_templates.tmpl_filelist(
                ln=ln,
                recid=self.recid,
                docid="",
                version=args['version'],
                filelist=filelist)
            
            return page(title="",
                        body=t,
                        navtrail=_("Access to Fulltext"),
                        description="",
                        keywords="keywords",
                        uid=uid,
                        language=ln,
                        req=req)

        return getfile, []

    def __call__(self, req, form):
        """Called in case of URLs like /record/123/files without
           trailing slash.
        """
        return redirect_to_url(req, '%s/record/%s/files/' % (weburl, self.recid))

def websubmit_legacy_getfile(req, form):
    """ Handle legacy /getfile.py URLs """

    # FIXME: this should _redirect_ to the proper
    # /record/.../files/... URL.
    
    args = wash_urlargd(form, {
        'c': (str, cdsname),
        'recid': (str, ''),
        'docid': (str, ''),
        'version': (str, ''),
        'name': (str, ''),
        'format': (str, '')
        })

    def _getfile_py(req,c=cdsname,ln=cdslang,recid="",docid="",version="",name="",format=""):
        _ = gettext_set_language(ln)

        # get user ID:
        try:
            uid = getUid(req)
            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
                return page_not_authorized(req, "../getfile.py/index")
            uid_email = get_email(uid)
        except Error, e:
            return errorMsg(e.value,req)

        filelist=""

        # redirect to a canonical URL as far as it is possible (what
        # if we only have a docid, and no file supplied?)
        if name!="":
            if docid=="":
                return errorMsg(_("Parameter docid missing"), req, c, ln)

            doc = BibDoc(bibdocid=docid)
            docfile=doc.getFile(name,format,version)
            
            if docfile is None:
                return warningMsg(_("Unable to find file."),req, c, ln)

            # redirect to this specific file, possibly dropping
            # the version if we are referring to the latest one.
            target = '%s/record/%d/files/%s.%s' % (
                weburl, doc.recid, quote(docfile.name), docfile.format)

            if version and int(version) == int(doc.getLatestVersion()):
                version = ''
                    
            target += make_canonical_urlargd({
                'version': version}, websubmit_templates.files_default_urlargd)

            return redirect_to_url(req, target)
        
        # all files attached to a record
        elif recid!="":
            return redirect_to_url(req, '%s/record/%s/files/' % (weburl, recid))

        # a precise filename
        elif docid!="":
            bibdoc = BibDoc(bibdocid=docid)
            recid = bibdoc.getRecid()
            filelist = bibdoc.display(version, ln=ln)
            
        t = websubmit_templates.tmpl_filelist(
              ln = ln,
              recid = recid,
              docid = docid,
              version = version,
              filelist = filelist,
            )
        p_navtrail = _("Access to Fulltext")
        return page(title="",
                    body=t,
                    navtrail = p_navtrail,
                    description="",
                    keywords="keywords",
                    uid=uid,
                    language=ln,
                    req=req)
    
    return _getfile_py(req, **args)


# --------------------------------------------------

from invenio.websubmit_engine import home, action, interface, endaction

class WebInterfaceSubmitPages(WebInterfaceDirectory):

    _exports = ['summary', 'sub', 'direct', '']


    def direct(self, req, form):

        args = wash_urlargd(form, {'sub': (str, '')})
        sub = args['sub']
        
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../direct.py/index")

        myQuery = req.args
        if sub == "":
            return errorMsg("Sorry parameter missing...",req)
        res = run_sql("select docname,actname from sbmIMPLEMENT where subname=%s", (sub,))
        if len(res)==0:
            return errorMsg("Sorry. Cannot analyse parameter",req)
        else:
            # get document type
            doctype = res[0][0]
            # get action name
            action = res[0][1]
        # retrieve other parameter values
        params = re.sub("sub=[^&]*","",myQuery)
        # find existing access number
        result = re.search("access=([^&]*)",params)
        if result is not None:
            access = result.group(1)
            params = re.sub("access=[^&]*","",params)
        else:
            # create 'unique' access number
            pid = os.getpid()
            now = time.time()
            access = "%i_%s" % (now,pid)
        # retrieve 'dir' value
        res = run_sql ("select dir from sbmACTION where sactname=%s",(action,))
        dir = res[0][0]
        try:
            mainmenu = req.headers_in['Referer']
        except:
            mainmenu = ""
        url = "/submit?doctype=%s&dir=%s&access=%s&act=%s&startPg=1%s&mainmenu=%s" % (
            doctype,dir,access,action,params,quote(mainmenu))
        req.err_headers_out.add("Location", url)
        raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
        return ""


    def sub(self, req, form):
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../sub/")

        myQuery = req.args
        if myQuery:
            if re.search("@",myQuery):
                param = re.sub("@.*","",myQuery)
                IN = re.sub(".*@","",myQuery)
            else:
                IN = myQuery
            url = "%s/submit/direct?sub=%s&%s" % (urlpath,IN,param)
            req.err_headers_out.add("Location", url)
            raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
            return ""
        else:
            return "<html>Illegal page access</html>"


    def summary(self, req, form):
        args = wash_urlargd(form, {
            'doctype': (str, ''),
            'act': (str, ''),
            'access': (str, ''),
            'indir': (str, '')})
        
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../summary.py/index")

        t=""
        curdir  = "%s/%s/%s/%s" % (storage,args['indir'],args['doctype'],args['access'])
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
                if os.path.exists("%s/%s" % (curdir,arr[1])):
                    fd = open("%s/%s" % (curdir,arr[1]),"r")
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
                 images = images,
               )

    def index(self, req, form):

        args = wash_urlargd(form, {
            'c': (str, cdsname),
            'doctype': (str, ''),
            'act': (str, ''),
            'startPg': (str, "1"),
            'indir': (str, ''),
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

        def _index(req, c, ln, doctype, act, startPg, indir, access,
                   mainmenu, fromdir, file, nextPg, nbPg, curpage, step,
                   mode):

            uid = getUid(req)
            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
                return page_not_authorized(req, "../submit")

            if doctype=="":
                return home(req,c,ln)
            elif act=="":
                return action(req,c,ln,doctype)
            elif int(step)==0:
                return interface(req,c,ln, doctype, act, startPg, indir,
                                 access, mainmenu, fromdir, file, nextPg,
                                 nbPg, curpage)
            else:
                return endaction(req,c,ln, doctype, act, startPg, indir,
                                 access,mainmenu, fromdir, file, nextPg,
                                 nbPg, curpage, step, mode)

        return _index(req, **args)

    # Answer to both /submit/ and /submit
    __call__ = index


def errorMsg(title,req,c=cdsname,ln=cdslang):
    _ = gettext_set_language(ln)
    return page(title=_("Error"),
                    body = create_error_box(req, title=title,verbose=0, ln=ln),
                    description=_("Internal Error"),
                    keywords="CDS Invenio, Internal Error",
                    language=ln,
                    req=req)

def warningMsg(title,req,c=cdsname,ln=cdslang):
    _ = gettext_set_language(ln)
    return page(title=_("Warning"),
                    body = title,
                    description=_("Internal Error"),
                    keywords="CDS Invenio, Internal Error",
                    language=ln,
                    req=req)

