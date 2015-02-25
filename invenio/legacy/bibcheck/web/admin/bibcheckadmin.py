# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012 CERN.
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

"""Invenio BibCheck Administrator Interface."""

import cgi
import os
from invenio.legacy.bibrank.adminlib import check_user
from invenio.legacy.webpage import page, error_page
from invenio.legacy.webuser import getUid, page_not_authorized
from invenio.base.i18n import wash_language, gettext_set_language
#from invenio.utils.url import wash_url_argument, redirect_to_url
from invenio.config import CFG_SITE_LANG, CFG_SITE_SECURE_URL, \
                           CFG_SITE_NAME, CFG_ETCDIR, CFG_BINDIR

__lastupdated__ = """$Date$"""


def is_admin(req):
    """checks if the user has the rights (etc)"""
    # Check if user is authorized to administer
    uid = 0
    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)
    (auth_code, auth_msg) = check_user(req, 'cfgbibformat')
    if not auth_code:
        return (True, uid)
    else:
        return (False, uid)


def index(req, search="", ln=CFG_SITE_LANG):
    """
    Main BibCheck administration page.
    @param ln: language
    """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail = """<a class="navtrail" href="%s/help/admin">%s</a>""" % \
               (CFG_SITE_SECURE_URL, _("Admin Area"))
    (admin_ok, uid) = is_admin(req)
    if admin_ok:
        return page(title=_("BibCheck Admin"),
                body=_perform_request_index(ln, search),
                language=ln,
                uid=uid,
                navtrail = navtrail,
                lastupdated=__lastupdated__,
                req=req,
                warnings=[])
    else:
        #redirect to login
        return page_not_authorized(req=req, text=_("Not authorized"), navtrail=navtrail)


def _perform_request_index(ln, search=""):
    """ makes a listing of files that are found in etc/bibcheck.
        Include a delete button for each. """
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    mydir = CFG_ETCDIR+"/bibcheck"
    if not os.path.exists(mydir):
        return _("ERROR: %(x_name)s does not exist", x_name=mydir)
    if not os.path.isdir(mydir):
        return  _("ERROR: %(x_name)s is not a directory", x_name=mydir)
    if not os.access(mydir, os.W_OK):
        return  _("ERROR: %(x_name)s is not writable", x_name=mydir)
    myfiles = os.listdir(mydir)
    if search:
        #include only files that match
        matching = []
        for myfile in myfiles:
            if (myfile.count(search) > 0):
                matching.append(myfile)
            else: #see if the string is in the file
                mypath = CFG_ETCDIR+"/bibcheck/"+myfile
                infile = file(mypath, 'r')
                filelines = infile.readlines()
                for line in filelines:
                    if line.count(search) > 0:
                        matching.append(myfile)
                        break
                infile.close()
        myfiles = matching
    lines = ""
    #add a search box
    lines += """
        <!--make a search box-->
        <table class="admin_wvar" cellspacing="0">
        <tr><td>
        <form action="%(siteurl)s/admin/bibcheck/bibcheckadmin.py/index">
          %(searchforastr)s
          <input type="text" name="search" value="%(search)s" />
          <input type="hidden" name="ln" value="%(ln)s" />
          <input type="submit" class="adminbutton" value="Search">
          </form>
          </td></tr></table> """ % { 'siteurl': CFG_SITE_SECURE_URL,
                                     'search': search,
                                     'ln': ln,
                                      'searchforastr': _("Limit to knowledge bases containing string:") }
    if myfiles:
        #create a table..
        oddstripestyle = 'style="background-color: rgb(235, 247, 255);"' #for every other line
        lines += '<table class="admin_wvar">\n'
        isodd = True
        myfiles.sort()
        for myfile in myfiles:
            mystyle = ""
            if isodd:
                mystyle = oddstripestyle
            isodd = not isodd
            lines += "<tr "+mystyle+">"
            line = '<td>' + cgi.escape(myfile) + '</td>'
            line += '<td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>'
            line += '<td><a href="%s/admin/bibcheck/bibcheckadmin.py/edit?fname=' % CFG_SITE_SECURE_URL + \
                    myfile+'&ln='+ln+'">Edit</a></td>'
            line += '<td>&nbsp;&nbsp;&nbsp;</td>'
            reallydelq = _("Really delete")+" "+myfile+"?"
            line += '<td><a href="%s/admin/bibcheck/bibcheckadmin.py/delete?fname=' % CFG_SITE_SECURE_URL + \
                    myfile+'&ln='+ln+'" onclick="return confirm(\''+reallydelq+'\');">'+_("Delete")+'</a></td>'
            #verify syntax..
            line += '<td>&nbsp;&nbsp;&nbsp;</td>'
            line += '<td><a href="%s/admin/bibcheck/bibcheckadmin.py/verify?fname=' % CFG_SITE_SECURE_URL + \
                    myfile+'&ln='+ln+'">'+_("Verify syntax")+'</a></td>'
            lines += line+"</tr>\n"
        lines += "</table>\n"
    myout = lines
    myout += "<br/><br/><a href=\"%s/admin/bibcheck/bibcheckadmin.py/edit\">" % CFG_SITE_SECURE_URL + \
             _("Create new")+"</a>"
    return myout

def verify(req, fname, ln=CFG_SITE_LANG):
    """verify syntax by calling an external checking program"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    (admin_ok, uid) = is_admin(req)

    # sanity check for fname:
    fname = os.path.basename(fname)

    navtrail = """<a class="navtrail" href="%s/help/admin">%s</a>""" % \
               (CFG_SITE_SECURE_URL, _("Admin Area"))
    navtrail += """&gt; <a class="navtrail" href="%s/admin/bibcheck/bibcheckadmin.py/">BibCheck Admin</a> """ % CFG_SITE_SECURE_URL
    errors = ""
    outstr = ""
    errstr = ""
    path_to_bibcheck_cli = CFG_BINDIR + os.sep + 'bibcheck'
    if not os.path.exists(path_to_bibcheck_cli):
        errors = _("File %(x_name)s does not exist.", x_name=path_to_bibcheck_cli)
    if not errors:
        #first check where we have stderr now so that we can assign it back
        try:
            (handle, mystdout, mystderr) = os.popen3(path_to_bibcheck_cli + " --verify" + fname)
            outstr = str(mystdout.readlines())
            errstr = str(mystderr.readlines())
        except:
            #the call failed?
            errors = _("Calling bibcheck -verify failed.")
    if not errors:
        if not errstr:
            return "OK"
        else:
            return errstr
    else:
        return page(title=_("Verify BibCheck config file"),
                body= _("Verify problem")+":<br/>"+errors,
                language= ln,
                uid=uid,
                navtrail = navtrail,
                lastupdated=__lastupdated__,
                req=req,
                warnings=[])

def edit(req, ln=CFG_SITE_LANG, fname=""):
    """ creates an editor for the file. This is called also when the user wants to
        create a new file. In the case fname is empty"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    # sanity check for fname:
    fname = os.path.basename(fname)

    #check auth
    (admin_ok, uid) = is_admin(req)
    navtrail = """<a class="navtrail" href="%s/help/admin">%s</a>""" % \
               (CFG_SITE_SECURE_URL, _("Admin Area"))
    navtrail += """&gt; <a class="navtrail" href="%s/admin/bibcheck/bibcheckadmin.py/">BibCheck Admin</a> """ % CFG_SITE_SECURE_URL
    myout = _("File")+" " + cgi.escape(fname) + "<br/>"
    if admin_ok:
        #add a javascript checker so that the user cannot save a form with empty
        #fname
        myout += """<script language="JavaScript" type="text/javascript">
                    <!--
                     function checkform ( form ) { if (form.fname.value == "") {
                              alert( "Missing filename." ); form.fname.focus(); return false ;
                            }
                            return true ;
                      }
                     -->
                     </script>"""


        #read the file if there is one
        filelines = []
        if fname:
            myfile = CFG_ETCDIR+"/bibcheck/"+fname
            infile = file(myfile, 'r')
            filelines = infile.readlines()
            infile.close()
        myout += '<form method="post" action="save" onsubmit="return checkform(this);">'
        #create a filename dialog box if there is no fname, otherwise it's hidden
        if fname:
            myout += '<input type="hidden" name="fname" value="'+fname+'">'
        else:
            myout += '<input name="fname" value="'+fname+'"><br/>'
            myout += '<input type="hidden" name="wasnew" value="1">'
        myout += '<input type="hidden" name="ln" value="'+ln+'">'
        myout += '<textarea name="code" id="code" rows="25" style="width:100%">'
        for line in filelines:
            myout += line
        #create a save button
        myout += '</textarea><br/><input type="submit" name="save" value="'+_("Save Changes")+'"></form>'
        #create page
        return page(title=_("Edit BibCheck config file"),
                body= myout,
                language= ln,
                uid=uid,
                navtrail = navtrail,
                lastupdated=__lastupdated__,
                req=req,
                warnings=[])
    else: #not admin
        return page_not_authorized(req=req, text=_("Not authorized"), navtrail=navtrail)

def save(req, ln, fname, code, wasnew=0):
    """saves code into file fname. wasnew is 1 if this is a new file"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    # sanity check for fname:
    fname = os.path.basename(fname)

    #check auth
    (admin_ok, uid) = is_admin(req)
    navtrail = '''<a class="navtrail" href="%s/help/admin">%s</a>''' % \
               (CFG_SITE_SECURE_URL, _("Admin Area"))
    navtrail += """&gt; <a class="navtrail" href="%s/admin/bibcheck/bibcheckadmin.py/">BibCheck Admin</a> """ % CFG_SITE_SECURE_URL
    if admin_ok:
        myfile = CFG_ETCDIR+"/bibcheck/"+fname
        #check if the file exists if this was new
        if wasnew and os.path.exists(myfile):
            msg = _("File %(x_name)s already exists.", x_name=cgi.escape(fname))
        else:
            #write code into file
            msg = _("File %(x_name)s: written OK.", x_name=cgi.escape(fname))
            try:
                outfile = file(myfile, 'w')
                outfile.write(code)
                outfile.close()
            except IOError:
                msg = _("File %(x_name)s: write failed.", x_name=cgi.escape(fname))
        #print message
        return page(title=_("Save BibCheck config file"),
                body= msg,
                language= ln,
                uid=uid,
                navtrail = navtrail,
                lastupdated=__lastupdated__,
                req=req,
                warnings=[])
    else:
        return page_not_authorized(req=req, text=_("Not authorized"), navtrail=navtrail)

def delete(req, ln, fname):
    """delete file fname"""
    ln = wash_language(ln)
    _ = gettext_set_language(ln)

    # sanity check for fname:
    fname = os.path.basename(fname)

    #check auth
    (admin_ok, uid) = is_admin(req)
    navtrail = """<a class="navtrail" href="%s/help/admin">%s</a>""" % \
               (CFG_SITE_SECURE_URL, _("Admin Area"))
    navtrail += """&gt; <a class="navtrail" href="%s/admin/bibcheck/bibcheckadmin.py/">BibCheck Admin</a> """ % CFG_SITE_SECURE_URL
    if admin_ok:
        msg = ""
        myfile = CFG_ETCDIR+"/bibcheck/"+fname
        success = 1
        try:
            os.remove(myfile)
        except:
            success = 0
        if success:
            msg = _("File %(x_name)s deleted.", x_name=cgi.escape(fname))
        else:
            msg = _("File %(x_name)s: delete failed.", x_name=cgi.escape(fname))
        #print message
        return page(title=_("Delete BibCheck config file"),
                body= msg,
                language= ln,
                uid=uid,
                navtrail = navtrail,
                lastupdated=__lastupdated__,
                req=req,
                warnings=[])
    else:
        return page_not_authorized(req=req, text=_("Not authorized"), navtrail=navtrail)
