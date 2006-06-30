## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

## import interesting modules:
import string
import os
import sys
import time
import types
import re
import shutil
from invenio.config import cdsname,cdslang,weburl
from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import *
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email, list_registered_users
from invenio.messages import wash_language
from invenio.websubmit_config import *

def index(req,c=cdsname,ln=cdslang,todo="",id="",doctype="",categ="",addusers="",warningText="",role=""):
    ln = wash_language(ln)
    # get user ID:
    try:
        uid = getUid(req)
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value,req)
    (auth_code, auth_message) = acc_authorize_action(uid, "cfgwebsubmit",verbose=0)
    if auth_code != 0:
        return errorMsg(auth_message, req, uid)
    # request for deleting a user
    if todo == "deleteuser":
        acc_deleteUserRole(id,name_role=role)
    # request for adding user(s)
    if todo == "adduser":
        role = "referee_%s_%s" % (doctype,categ[1])
        roleId = acc_getRoleId(role)
        # if the role does not exists, we create it
        if roleId == 0:
            if acc_addRole(role,"referees for document type %s category %s" % (doctype,categ[1])) == 0:
                return errorMsg("Cannot create referee role",req)
            else:
                roleId = acc_getRoleId(role)
            # if the action does not exist, we create it
            actionId = acc_getActionId("referee")
            if actionId == 0:
                if acc_addAction("referee","","no",("doctype","categ")) == 0:
                    return errorMsg("Cannot create action 'referee'",req)
                else:
                    actionId = acc_getActionId("referee")
            #create arguments
            arg1Id = acc_addArgument("doctype",doctype)
            arg2Id = acc_addArgument("categ",categ[1])
            # then link the role with the action
            if acc_addRoleActionArguments(roleId,actionId,-1,0,0,[arg1Id,arg2Id]) == 0:
                return errorMsg("Cannot link role with action",req)
        roleId = acc_getRoleId(role)
        # For each id in the array
        if isinstance(addusers,types.ListType):
            for adduser in addusers:
                # First check  whether this id is not already associated with this rule
                myRoles = acc_getUserRoles(adduser)
                if not roleId in myRoles:
                    # Actually add the role to the user
                    acc_addUserRole(adduser,roleId)
                else:
                    warningText = "<font color=red>Sorry... This user is already a referee for this category.</font>"
        else:
            # First check  whether this id is not already associated with this rule
            myRoles = acc_getUserRoles(addusers)
            if not roleId in myRoles:
                # Actually add the role to the user
                acc_addUserRole(addusers,roleId)
            else:
                warningText = "<font color=red>Sorry... This user is already a referee for this category.</font>"
    return page(title="websubmit admin - referee selection",
                    body=displayRefereesPage(doctype,warningText),
                    description="",
                    keywords="",
                    uid=uid,
                    language=ln,
                    req=req)

def displayRefereesPage(doctype,warningText):
    t=""
    if doctype == "*":
        docname = "all catalogues"
    else:
        res = run_sql("SELECT * FROM sbmDOCTYPE WHERE sdocname=%s", (doctype,))
        docname = res[0][0]
    t+=warningText
    t+="""
<FORM ACTION='referees.py' METHOD='POST'>
<INPUT TYPE='hidden' NAME='todo' VALUE=''>
<INPUT TYPE='hidden' NAME='id' VALUE=''>
<INPUT TYPE='hidden' NAME='doctype' VALUE='%s'>
<INPUT TYPE='hidden' NAME='categ' VALUE=''>
<INPUT TYPE='hidden' NAME='role' VALUE=''>
<!-- Role: referee -->
<TABLE><TR><TD valign=top>""" %doctype
    # call the function to display the table containing the list of associated emails
    t+=displayUserTable(doctype)
    t+="""
    </TD>
    <TD valign=top>"""
    # call the function to display the form allowing the manager to add new users
    t+=displayAddUser(doctype)
    t+= """
    </TD></TR></TABLE>
<!-- End submissionuser rule -->
    <a href="%s/admin/websubmit/websubmitadmin.py/doctypeconfigure?doctype=%s">Finished</a>
    </FORM>""" % (weburl, doctype)
    return t
    
def displayUserTable(doctype):
    t=""
    # start displaying the table which will contain the list of email addresses.
    t+= """
    <table class="searchbox" summary="">
        <tr>
            <th class="portalboxheader" colspan="2">Referees</th>
        </tr>"""
    roles = acc_getAllRoles()
    referees = {}
    for role in roles:
        role_name = role[1]
        role_id = role[0]
        if re.match("^referee_%s_" % doctype,role_name):
            # Try to retrieve the referee's email from the referee's database
            if acc_getRoleUsers(role_id) != None:
                referees[role_name] = acc_getRoleUsers(role_id)

    if len(referees) == 0:
        t+= "<TR><TD align=center colspan=2><IMG SRC=\"%s/noway.gif\" height=16 width=16></TD></TR>" % images
    i=0
    for role in referees.keys():
        categ = re.match("referee_%s_(.*)" % doctype,role).group(1)
        res = run_sql("SELECT lname FROM sbmCATEGORIES WHERE sname=%s and doctype=%s", (categ,doctype,))
        if len(res) > 0:
            categname = "Referee(s) for category: %s" % res[0][0]
        else:
            categname = "General Referee(s)"
        t+= "<TR><TD colspan=2><small><b>%s</b> </small></TD></TR>" % categname
        for referee in referees[role]:
            if int(i/2) == i/2:
                bgcolor="#eeeeee"
            else:
                bgcolor="#dddddd"
            t+= "<TR bgcolor=%s>" % bgcolor
            t+= "<TD align=right><small>"
            t+= referee[1]
            t+= "</small></TD>"
            t+= "<TD><a href=\"\" onClick=\"if (confirm('Are you sure you want to delete this referee?')){document.forms[0].todo.value='deleteuser';document.forms[0].id.value='%s';document.forms[0].role.value='%s';document.forms[0].submit();return false;}else{return false;}\">" % (referee[0],role)
            t+= "<IMG SRC=\"%s/iconcross.gif\" border=0></a>" % images
            t+= "</TD>";
            t+= "</TR>";
            i+=1
    # close table
    t+="</TABLE>"
    return t

def displayAddUser(doctype):
    t=""
    # start displaying the table which will contain the add form
    t+= """
    <table class="searchbox" summary="">
        <tr>
            <th class="portalboxheader">Add</th>
        </tr>
        <tr>
            <td>
    User:<br>"""
    users = list_registered_users()
    if len(users) < 20:
        numrows = len(users)
    else:
        numrows = 20
    t+= "<SELECT multiple name=addusers size=%s>" % numrows
    for user in users:
        if user[1] != "":
            t+= "<OPTION value=%s>%s" % (user[0],user[1])
    t+= "</SELECT><br>"
    t+= "<SELECT name=categ>"
    t+= "<OPTION value='*'>All categories"
    res = run_sql("SELECT lname,sname FROM sbmCATEGORIES WHERE doctype=%s ORDER BY lname", (doctype,))
    for row in res:
        t+= "<OPTION value=%s>%s" % (row[1],row[0])
    t+= "</SELECT><br>"
    t+= "<INPUT class=\"adminbutton\" type=button onClick=\"document.forms[0].todo.value='adduser';document.forms[0].submit();\" VALUE=\"ADD\">"
    t+= "</small></TD></TR></TABLE>"
    return t


def errorMsg(title,req,uid,c=cdsname,ln=cdslang):
    return page(title="error",
                    body = create_error_box(req, title=title,verbose=0, ln=ln),
                    description="%s - Internal Error" % c, 
                    keywords="%s, CDS Invenio, Internal Error" % c,
                    language=ln,
                    uid=uid,
                    req=req)

