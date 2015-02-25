# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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
"""WebSubmit interface for the management of referees."""

__revision__ = "$Id$"

# import interesting modules:
import types
import re

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_URL
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.access.control import \
     acc_delete_user_role, \
     acc_get_role_id, \
     acc_add_role, \
     acc_add_action,\
     acc_add_role_action_arguments, \
     acc_add_argument, \
     acc_get_user_roles, \
     acc_add_user_role, \
     acc_get_action_id, \
     acc_get_all_roles, \
     acc_get_role_users
from invenio.legacy.webpage import page, error_page
from invenio.legacy.webuser import getUid, list_registered_users, page_not_authorized
from invenio.base.i18n import wash_language

def index(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG, todo="", id="", doctype="",
          categ="", addusers="", warningText="", role=""):
    """Main entry point for the management of referees."""
    ln = wash_language(ln)
    # get user ID:
    uid = getUid(req)
    (auth_code, auth_message) = acc_authorize_action(req, "cfgwebsubmit", verbose=0)
    if auth_code != 0:
        ## user is not authorised to use WebSubmit Admin:
        return page_not_authorized(req=req, text=auth_message)

    # request for deleting a user
    if todo == "deleteuser":
        acc_delete_user_role(id, name_role=role)
    # request for adding user(s)
    if todo == "adduser":
        role = "referee_%s_%s" % (doctype, categ[1])
        roleId = acc_get_role_id(role)
        # if the role does not exists, we create it
        if roleId == 0:
            if acc_add_role(role, "referees for document type %s category %s" % (doctype, categ[1])) == 0:
                return error_page("Cannot create referee role", req, ln)
            else:
                roleId = acc_get_role_id(role)
            # if the action does not exist, we create it
            actionId = acc_get_action_id("referee")
            if actionId == 0:
                if acc_add_action("referee", "", "no", ("doctype","categ")) == 0:
                    return error_page("Cannot create action 'referee'", req, ln)
                else:
                    actionId = acc_get_action_id("referee")
            #create arguments
            arg1Id = acc_add_argument("doctype", doctype)
            arg2Id = acc_add_argument("categ", categ[1])
            # then link the role with the action
            if acc_add_role_action_arguments(roleId, actionId, -1, 0, 0, [arg1Id, arg2Id]) == 0:
                return error_page("Cannot link role with action", req, ln)
        roleId = acc_get_role_id(role)
        # For each id in the array
        if isinstance(addusers, types.ListType):
            for adduser in addusers:
                # First check  whether this id is not already associated with this rule
                myRoles = acc_get_user_roles(adduser)
                if not roleId in myRoles:
                    # Actually add the role to the user
                    acc_add_user_role(adduser, roleId)
                else:
                    warningText = '<span style="color:#f00">Sorry... This user is already a referee for this category.</span>'
        else:
            # First check  whether this id is not already associated with this rule
            myRoles = acc_get_user_roles(addusers)
            if not roleId in myRoles:
                # Actually add the role to the user
                acc_add_user_role(addusers, roleId)
            else:
                warningText = '<span style="color:#f00">Sorry... This user is already a referee for this category.</span>'
    return page(title="websubmit admin - referee selection",
                    body=displayRefereesPage(doctype, warningText),
                    description="",
                    keywords="",
                    uid=uid,
                    language=ln,
                    req=req)

def displayRefereesPage(doctype, warningText):
    """Output the list of refeeres as well as the controls to add/remove them"""
    t = ""
    if doctype in ['', '*']:
        doctype = '*'
        docname = "all catalogues"
    else:
        res = run_sql("SELECT * FROM sbmDOCTYPE WHERE sdocname=%s", (doctype,))
        docname = res[0][0]
    t += warningText
    t += """
<form action="referees.py" method="post">
<input type="hidden" name="todo" value="" />
<input type="hidden" name="id" value="" />
<input type="hidden" name="doctype" value="%s" />
<input type="hidden" name="categ" value="" />
<input type="hidden" name="role" value="" />
<!-- Role: referee -->
<table><tr><td valign="top">""" % doctype
    # call the function to display the table containing the list of associated emails
    t += displayUserTable(doctype)
    t += """
    </td>
    <td valign="top">"""
    # call the function to display the form allowing the manager to add new users
    t += displayAddUser(doctype)
    end_url = "%s/admin/websubmit/websubmitadmin.py/doctypeconfigure?doctype=%s" % (CFG_SITE_URL, doctype)
    if doctype in ['', '*']:
        end_url = "%s/admin/websubmit/websubmitadmin.py/" % CFG_SITE_URL
    t += """
    </td></tr></table>
<!-- End submissionuser rule -->
    <a href="%s">Finished</a>
    </form>""" % end_url
    return t

def displayUserTable(doctype):
    """Display the list of referees for the given doctype, as well as
    the control to remove them"""
    t = ""
    # start displaying the table which will contain the list of email addresses.
    t += """
    <table class="searchbox">
        <tr>
            <th class="portalboxheader" colspan="2">Referees</th>
        </tr>"""
    roles = acc_get_all_roles()
    referees = {}
    for role in roles:
        role_name = role[1]
        role_id = role[0]
        if re.match("^referee_%s_" % doctype, role_name):
            # Try to retrieve the referee's email from the referee's database
            if acc_get_role_users(role_id) is not None:
                referees[role_name] = acc_get_role_users(role_id)

    if len(referees) == 0:
        t += '<tr><td align="center" colspan="2"><img src="%s/img/noway.gif" height="16px" width="16px" alt="Empty"/></td></tr>' % CFG_SITE_URL
    i = 0
    for role in referees.keys():
        categ = re.match("referee_%s_(.*)" % doctype, role).group(1)
        res = run_sql("SELECT lname FROM sbmCATEGORIES WHERE sname=%s and doctype=%s", (categ, doctype,))
        if len(res) > 0:
            categname = "Referee(s) for category: %s" % res[0][0]
        else:
            categname = "General Referee(s)"
        t += '<tr><td colspan="2"><small><b>%s</b> </small></td></tr>' % categname
        for referee in referees[role]:
            if int(i/2) == i/2:
                bgcolor = "#eeeeee"
            else:
                bgcolor = "#dddddd"
            t += '<tr bgcolor="%s">' % bgcolor
            t += '<td align="right"><small>'
            t += referee[1]
            t += '</small></td>'
            t += '''<td><a href="" onclick="if (confirm('Are you sure you want to delete this referee?')){document.forms[0].todo.value='deleteuser';document.forms[0].id.value='%s';document.forms[0].role.value='%s';document.forms[0].submit();return false;}else{return false;}">''' % (referee[0], role)
            t += '<img src="%s/img/iconcross.gif" border="0" alt="Remove" /></a>' % CFG_SITE_URL
            t += '</td>'
            t += '</tr>'
            i += 1
    # close table
    t += "</table>"
    return t

def displayAddUser(doctype):
    """Display controls for adding users"""
    t = ""
    # start displaying the table which will contain the add form
    t += """
    <table class="searchbox" summary="">
        <tr>
            <th class="portalboxheader">Add</th>
        </tr>
        <tr>
            <td>
    User:<br/>"""
    users = list_registered_users()
    if len(users) < 20:
        numrows = len(users)
    else:
        numrows = 20
    t += '<select multiple="multiple" name="addusers" size="%s">' % numrows
    for user in users:
        if user[1] != "":
            t += '<option value="%s">%s</option>' % (user[0], user[1])
    t += '</select><br/>'
    t += '<select name="categ">'
    t += '<option value="*">All categories</option>'
    res = run_sql("select lname,sname FROM sbmCATEGORIES WHERE doctype=%s ORDER BY lname", (doctype,))
    for row in res:
        t += '<option value="%s">%s</option>' % (row[1], row[0])
    t += '</select><br/>'
    t += '''<input class="adminbutton" type="button" onclick="document.forms[0].todo.value='adduser';document.forms[0].submit();" value="ADD" />'''
    t += '</td></tr></table>'
    return t
