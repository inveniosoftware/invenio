# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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

"""Invenio WebAccess Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

# fill config variables:

import re
import time

from six import iteritems

from invenio.config import \
    CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
    CFG_ACCESS_CONTROL_LEVEL_GUESTS, \
    CFG_ACCESS_CONTROL_LEVEL_SITE, \
    CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN, \
    CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS, \
    CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_ACTIVATION, \
    CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_DELETION, \
    CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT, \
    CFG_SITE_LANG, \
    CFG_SITE_NAME, \
    CFG_SITE_SUPPORT_EMAIL, \
    CFG_SITE_ADMIN_EMAIL, \
    CFG_SITE_SECURE_URL
import invenio.modules.access.engine as acce
import invenio.modules.access.control as acca
from invenio.ext.email import send_email
from invenio.legacy.bibrank.adminlib import addadminbox, tupletotable, \
        tupletotable_onlyselected, addcheckboxes, createhiddenform
from invenio.modules.access.firerole import compile_role_definition, \
    serialize
from invenio.base.i18n import gettext_set_language
from invenio.legacy.dbquery import run_sql, wash_table_column_name
from invenio.legacy.webpage import page
from invenio.legacy.webuser import getUid, isGuestUser, page_not_authorized, collect_user_info
from invenio.legacy.webuser import email_valid_p, get_user_preferences, \
    set_user_preferences, update_Uid
from invenio.utils.url import redirect_to_url, wash_url_argument
from invenio.modules.access.local_config import \
    WEBACCESSACTION, MAXPAGEUSERS, \
    SUPERADMINROLE, CFG_EXTERNAL_AUTHENTICATION, DELEGATEADDUSERROLE, \
    CFG_ACC_EMPTY_ROLE_DEFINITION_SRC, \
    MAXSELECTUSERS, CFG_EXTERNAL_AUTH_DEFAULT
from invenio.modules.access.errors import InvenioWebAccessFireroleError
from cgi import escape

from sqlalchemy.exc import OperationalError


def index(req, title='', body='', subtitle='', adminarea=2, authorized=0, ln=CFG_SITE_LANG):
    """main function to show pages for webaccessadmin.

    1. if user not logged in and administrator, show the mustlogin page

    2. if used without body argument, show the startpage

    3. show admin page with title, body, subtitle and navtrail.

    authorized - if 1, don't check if the user is allowed to be webadmin """
    navtrail_previous_links = '<a class="navtrail" href="%s/help/admin">Admin Area' \
        '</a>' % (CFG_SITE_SECURE_URL,)

    if body:
        if adminarea == 1:
            navtrail_previous_links += '&gt; <a class=navtrail ' \
            ' href=%s/admin/webaccess/webaccessadmin.py/delegate_startarea>' \
            'Delegate Rights</a> ' % (CFG_SITE_SECURE_URL, )
        if adminarea >= 2 and adminarea < 9:
            navtrail_previous_links += '&gt; ' \
            '<a class="navtrail" href=%s/admin/webaccess/webaccessadmin.py>' \
            'WebAccess Admin</a> ' % (CFG_SITE_SECURE_URL, )
        if adminarea == 3:
            navtrail_previous_links += '&gt; <a class=navtrail ' \
            'href=%s/admin/webaccess/webaccessadmin.py/rolearea>' \
            'Role Administration</a> ' % (CFG_SITE_SECURE_URL, )
        elif adminarea == 4:
            navtrail_previous_links += '&gt; ' \
            '<a class="navtrail" href=%s/admin/webaccess/webaccessadmin.py' \
            '/actionarea>Action Administration</a> ' % (CFG_SITE_SECURE_URL, )
        elif adminarea == 5:
            navtrail_previous_links += '&gt; ' \
            '<a class="navtrail" href=%s/admin/webaccess/webaccessadmin.py' \
            '/userarea>User Administration</a> ' % (CFG_SITE_SECURE_URL, )
        elif adminarea == 6:
            navtrail_previous_links += '&gt; ' \
            '<a class="navtrail" href=%s/admin/webaccess/webaccessadmin.py' \
            '/resetarea>Reset Authorizations</a> ' % (CFG_SITE_SECURE_URL, )
        elif adminarea == 7:
            navtrail_previous_links += '&gt; ' \
            '<a class="navtrail" href=%s/admin/webaccess/webaccessadmin.py' \
            '/manageaccounts>Manage Accounts</a> ' % (CFG_SITE_SECURE_URL, )
        elif adminarea == 8:
            navtrail_previous_links += '&gt; ' \
            '<a class="navtrail" href=%s/admin/webaccess/webaccessadmin.py' \
            '/listgroups>List Groups</a> ' % (CFG_SITE_SECURE_URL, )

    id_user = getUid(req)
    (auth_code, auth_message) = is_adminuser(req)
    if not authorized and auth_code != 0:
        return mustloginpage(req, auth_message)

    elif not body:
        title = 'WebAccess Admin'
        body = startpage()
    elif type(body) != str: body = addadminbox(subtitle, datalist=body)

    return page(title=title,
                uid=id_user,
                req=req,
                body=body,
                navtrail=navtrail_previous_links,
                lastupdated=__lastupdated__)

def mustloginpage(req, message):
    """show a page asking the user to login."""

    navtrail_previous_links = '<a class="navtrail" href="%s/admin/">' \
        'Admin Area</a> &gt; <a class="navtrail" href="%s/admin/webaccess/">' \
        'WebAccess Admin</a> ' % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL)

    return page_not_authorized(req=req, text=message,
        navtrail=navtrail_previous_links)

def is_adminuser(req):
    """check if user is a registered administrator. """

    return acce.acc_authorize_action(req, WEBACCESSACTION)


def perform_listgroups(req):
    """List all the existing groups."""
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    header = ['name']
    groups = run_sql('select name from usergroup')

    output = tupletotable(header, groups, highlight_rows_p=True,
                          alternate_row_colors_p=True)

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a></dt>
    <dd>go here to add a new role.</dd>
    </dl>
    """

    return index(req=req,
                title='Group list',
                subtitle='All the groups registered in the system',
                body=[output, extra],
                adminarea=2)

def perform_rolearea(req, grep=""):
    """create the role area menu page."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    header = ['id', 'name', 'description', 'firewall like role definition',
        'users', 'authorizations / actions', 'role', '']
    roles = acca.acc_get_all_roles()

    roles2 = []

    if grep:
        try:
            re_grep = re.compile(grep)
        except Exception as err:
            re_grep = None
            grep = ''
    else:
        re_grep = None

    for (id, name, desc, dummy, firerole_def_src) in roles:
        if not firerole_def_src:
            firerole_def_src = '' ## Workaround for None.
        if re_grep and not re_grep.search(name) and not re_grep.search(desc) and not re_grep.search(firerole_def_src):
            ## We're grepping for some word.
            ## Let's dig into the authorization then.
            all_actions = acca.acc_find_possible_actions_all(id)
            ## FIXME: the acc_find_possible_actions_all is really an ugly
            ## function, but is the closest to what it's needed in order
            ## to retrieve all the authorization of a role.
            for idx, row in enumerate(all_actions):
                grepped = False
                if idx % 2 == 0:
                    ## even lines contains headers like in:
                    ## ['role', 'action', '#', 'collection']
                    ## the only useful text to grep is from index 3 onwards
                    for keyword in row[3:]:
                        if re_grep.search(keyword):
                            grepped = True
                            break
                    if grepped:
                        break
                else:
                    ## odd lines contains content like in:
                    ## [1, 18L, 1, 'Theses']
                    ## the useful text to grep is indirectly index 1
                    ## which is indeed the id_action (needed to retrieve the
                    ## action name) and from column 3 onwards.
                    if re_grep.search(acca.acc_get_action_name(row[1])):
                        break
                    for value in row[3:]:
                        if re_grep.search(value):
                            grepped = True
                            break
                    if grepped:
                        break
            else:
                ## We haven't grepped anything!
                ## Let's skip to the next role then...
                continue
        if len(desc) > 30:
            desc = desc[:30] + '...'
        if firerole_def_src and len(firerole_def_src) > 30:
            firerole_def_src = firerole_def_src[:30] + '...'
        roles2.append([id, name, desc, firerole_def_src])
        for col in [(('add', 'adduserrole'),
                    ('delete', 'deleteuserrole'),),
                    (('add', 'addauthorization'),
                    ('modify', 'modifyauthorizations'),
                    ('remove', 'deleteroleaction')),
                    (('modify', 'modifyrole'),
                    ('delete', 'deleterole')),
                    (('show details', 'showroledetails'), )]:
            roles2[-1].append('<a href="%s?id_role=%s">%s</a>' %
                (col[0][1], id, col[0][0]))
            for (str, function) in col[1:]:
                roles2[-1][-1] += ' / <a href="%s?id_role=%s">%s</a>' % \
                    (function, id, str)

    output  = """
    <dl>
    <dt>Users:</dt>
    <dd>add or remove users from the access to a role and its priviliges.</dd>
    <dt>Authorizations/Actions:</dt>
    <dd>these terms means almost the same, but an authorization is a <br />
    connection between a role and an action (possibly) containing arguments.
    </dd>
    <dt>Roles:</dt>
    <dd>see all the information attached to a role and decide if you want
    to<br />delete it.</dd>
    </dl>
    <!--make a search box-->
    <table class="admin_wvar" cellspacing="0">
    <tr><td>
    <form>
    Show only roles having any detail matching the regular expression:
    <input type="text" name="grep" value="%s" />
    <input type="submit" class="adminbutton" value="Search">
    </form>
    </td></tr></table>
    """ % escape(grep)

    output += tupletotable(header=header, tuple=roles2, highlight_rows_p=True,
                           alternate_row_colors_p=True)

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a></dt>
    <dd>go here to add a new role.</dd>
    </dl>
    """

    return index(req=req,
                title='Role Administration',
                subtitle='administration with roles as access point',
                body=[output, extra],
                adminarea=2)


def perform_actionarea(req, grep=''):
    """create the action area menu page."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    if grep:
        try:
            re_grep = re.compile(grep)
        except Exception as err:
            re_grep = None
            grep = ''
    else:
        re_grep = None

    header = ['name', 'authorizations/roles', '']
    actions = acca.acc_get_all_actions()

    actions2 = []
    roles2 = []
    for (id, name, description) in actions:
        if re_grep and not re_grep.search(name) and not re_grep.search(description):
            grepped = False
            roles = acca.acc_get_action_roles(id)
            for id_role, role_name, role_description in roles:
                if re_grep.search(role_name) or re_grep.search(role_description):
                    grepped = True
                    break
                elif re_grep.search(acca.acc_get_role_details(id_role)[3] or ''):
                    ## Found in FireRole
                    grepped = True
                    break
                else:
                    details = acca.acc_find_possible_actions(id_role, id)
                    if details:
                        for argument in details[0][1:]:
                            if re_grep.search(argument):
                                grepped = True
                                break
                        for values in details[1:]:
                            for value in values[1:]:
                                if re_grep.search(value):
                                    grepped = True
                                    break
                            if grepped:
                                break
                if grepped:
                    break
            if not grepped:
                continue
        actions2.append([name, description])
        for col in [(('add', 'addauthorization'),
                    ('modify', 'modifyauthorizations'),
                    ('remove', 'deleteroleaction')),
                    (('show details', 'showactiondetails'), )]:
            actions2[-1].append('<a href="%s?id_action=%s&amp;reverse=1">%s'
                '</a>' % (col[0][1], id, col[0][0]))
            for (str, function) in col[1:]:
                actions2[-1][-1] += ' / <a href="%s?id_action=%s&amp;' \
                    'reverse=1">%s</a>' % (function, id, str)

    output  = """
    <dl>
    <dt>Authorizations/Roles:</dt>
    <dd>these terms means almost the same, but an authorization is a <br />
        connection between a role and an action (possibly) containing
        arguments.</dd>
    <dt>Actions:</dt>
    <dd>see all the information attached to an action.</dd>
    </dl>
    <!--make a search box-->
    <table class="admin_wvar" cellspacing="0">
    <tr><td>
    <form>
    Show only actions having any detail matching the regular expression:
    <input type="text" name="grep" value="%s" />
    <input type="submit" class="adminbutton" value="Search">
    </form>
    </td></tr></table>
    """ % escape(grep)

    output += tupletotable(header=header, tuple=actions2, highlight_rows_p=True,
                           alternate_row_colors_p=True)

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a>
    <dd>go here to add a new role.
    </dl>
    """

    return index(req=req,
                title='Action Administration',
                subtitle='administration with actions as access point',
                body=[output, extra],
                adminarea=2)


def perform_userarea(req, email_user_pattern=''):
    """create area to show info about users. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = 'step 1 - search for users'

    output = """
    <p>
    search for users to display.
    </p> """

    # remove letters not allowed in an email
    email_user_pattern = cleanstring_email(email_user_pattern)

    text  = ' <span class="adminlabel">1. search for user</span>\n'
    text += ' <input class="admin_wvar" type="text" name="email_user_pattern"'\
        ' value="%s" />\n' % (email_user_pattern, )

    output += createhiddenform(action="userarea",
                            text=text,
                            button="search for users")

    if email_user_pattern:
        try:
            users1 = run_sql("""SELECT id, email FROM user WHERE email<>'' AND email RLIKE %s
                ORDER BY email LIMIT %s""", (email_user_pattern, MAXPAGEUSERS+1))
        except OperationalError:
            users1 = ()

        if not users1:
            output += '<p>no matching users</p>'
        else:
            subtitle = 'step 2 - select what to do with user'

            users = []
            for (id, email) in users1[:MAXPAGEUSERS]:
                users.append([id, email])
                for col in [(('add', 'addroleuser'),
                            ('remove', 'deleteuserrole')),
                            (('show details', 'showuserdetails'), )]:
                    users[-1].append('<a href="%s?'
                        'id_user=%s">%s</a>' % (col[0][1], id, col[0][0]))
                    for (str, function) in col[1:]:
                        users[-1][-1] += ' / <a href="%s?' \
                            'id_user=%s&amp;reverse=1">%s</a>' % \
                            (function, id, str)

            output += '<p>found <strong>%s</strong> matching users:</p>' % \
                (len(users1), )
            output += tupletotable(header=['id', 'email', 'roles', ''],
                tuple=users, highlight_rows_p=True, alternate_row_colors_p=True)

            if len(users1) > MAXPAGEUSERS:
                output += '<p><strong>only showing the first %s users, ' \
                    'narrow your search...</strong></p>' % (MAXPAGEUSERS, )

    return index(req=req,
                title='User Administration',
                subtitle=subtitle,
                body=[output],
                adminarea=2)


def perform_resetarea(req):
    """create the reset area menu page."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    output = """
    <dl>
    <dt><a href="resetdefaultsettings">Reset to Default Authorizations</a>
    <dd>remove all changes that has been done to the roles and <br />
    add only the default authorization settings.
    <dt><a href="adddefaultsettings">Add Default Authorizations</a>
    <dd>keep all changes and add the default authorization settings.
    </dl>
    """

    return index(req=req,
                title='Reset Authorizations',
                subtitle='reseting to or adding default authorizations',
                body=[output],
                adminarea=2)


def perform_resetdefaultsettings(req, superusers=[], confirm=0):
    """delete all roles, actions and authorizations presently in the database
    and add only the default roles.
    only selected users will be added to superadmin, rest is blank """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    # cleaning input
    if type(superusers) == str: superusers = [superusers]

    # remove not valid e-mails
    for email in superusers:
        if not check_email(email): superusers.remove(email)

    # instructions
    output  = """
    <p>
    before you reset the settings, we need some users<br />
    to connect to <strong>%s</strong>.<br />
    enter as many e-mail addresses you want and press <strong>reset</strong>.<br />
    <strong>confirm reset settings</strong> when you have added enough e-mails.<br />
    <strong>%s</strong> is added as default.
    </p>""" % (SUPERADMINROLE, CFG_SITE_ADMIN_EMAIL)

    # add more superusers
    output += """
    <p>enter user e-mail addresses: </p>
    <form action="resetdefaultsettings" method="POST">"""

    for email in superusers:
        output += '      <input type="hidden" name="superusers" value="%s" />' % (email, )

    output += """
    <span class="adminlabel">e-mail</span>
    <input class="admin_wvar" type="text" name="superusers" />
    <input class="adminbutton" type="submit" value="add e-mail" />
    </form>"""


    if superusers:
        # remove emails
        output += """
        <form action="resetdefaultsettings" method="POST">
        have you entered wrong data?
        <input class="adminbutton" type="submit" value="remove all e-mails" />
        </form>
        """

        # superusers confirm table
        start = '<form action="resetdefaultsettings" method="POST">'

        extra  = ' <input type="hidden" name="confirm" value="1" />'
        for email in superusers:
            extra += '<input type="hidden" name="superusers" value="%s" />' % (email, )
        extra += ' <input class="adminbutton" type="submit" value="confirm to reset settings" />'

        end    = '</form>'

        output += '<p><strong>reset default settings</strong> with the users below? </p>'
        output += tupletotable(header=['e-mail address'],
                               tuple=superusers,
                               start=start,
                               extracolumn=extra,
                               end=end,
                               highlight_rows_p=True,
                               alternate_row_colors_p=True)

        if confirm in [1, "1"]:
            res = acca.acc_reset_default_settings(superusers)
            if res:
                output += '<p>successfully reset default settings</p>'
            else:
                output += '<p>sorry, could not reset default settings</p>'

    return index(req=req,
                title='Reset Default Settings',
                subtitle='reset settings',
                body=[output],
                adminarea=6)


def perform_adddefaultsettings(req, superusers=[], confirm=0):
    """add the default settings, and keep everything else.
    probably nothing will be deleted, except if there has been made changes to the defaults."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    # cleaning input
    if type(superusers) == str: superusers = [superusers]

    # remove not valid e-mails
    for email in superusers:
        if not check_email(email): superusers.remove(email)

    # instructions
    output  = """
    <p>
    before you add the settings, we need some users<br />
    to connect to <strong>%s</strong>.<br />
    enter as many e-mail addresses you want and press <strong>add</strong>.<br />
    <strong>confirm add settings</strong> when you have added enough e-mails.<br />
    <strong>%s</strong> is added as default.
    </p>""" % (SUPERADMINROLE, CFG_SITE_ADMIN_EMAIL)

    # add more superusers
    output += """
    <p>enter user e-mail addresses: </p>
    <form action="adddefaultsettings" method="POST">"""

    for email in superusers:
        output += '      <input type="hidden" name="superusers" value="%s" />' % (email, )

    output += """
    <span class="adminlabel">e-mail</span>
    <input class="admin_wvar" type="text" name="superusers" />
    <input class="adminbutton" type="submit" value="add e-mail" />
    </form>
    """

    if superusers:
        # remove emails
        output += """
        <form action="adddefaultsettings" method="POST">
        have you entered wrong data?
        <input class="adminbutton" type="submit" value="remove all e-mails" />
        </form>
        """

        # superusers confirm table
        start = '<form action="adddefaultsettings" method="POST">'

        extra  = ' <input type="hidden" name="confirm" value="1" />'
        for email in superusers:
            extra += '<input type="hidden" name="superusers" value="%s" />' % (email, )
        extra += ' <input class="adminbutton" type="submit" value="confirm to add settings" />'

        end    = '</form>'

        output += '<p><strong>add default settings</strong> with the users below? </p>'
        output += tupletotable(header=['e-mail address'],
                            tuple=superusers,
                            start=start,
                            extracolumn=extra,
                            end=end)

        if confirm in [1, "1"]:
            res = acca.acc_add_default_settings(superusers)
            if res:
                output += '<p>successfully added default settings</p>'
            else:
                output += '<p>sorry, could not add default settings</p>'

    return index(req=req,
                title='Add Default Settings',
                subtitle='add settings',
                body=[output],
                adminarea=6)

def perform_manageaccounts(req, mtype='', content='', confirm=0):
    """start area for managing accounts."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = 'Overview'

    fin_output = ''

    fin_output += """
    <table>
    <tr>
    <td><b>Menu</b></td>
    </tr>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/manageaccounts?mtype=perform_showall">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/manageaccounts?mtype=perform_accesspolicy#1">Access policy</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/manageaccounts?mtype=perform_accountoverview#2">Account overview</a></small></td>
    <td>3.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/manageaccounts?mtype=perform_createaccount#3">Create account</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/manageaccounts?mtype=perform_modifyaccounts#4">Edit accounts</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL, CFG_SITE_SECURE_URL)

    if mtype == "perform_accesspolicy" and content:
        fin_output += content
    elif mtype == "perform_accesspolicy" or mtype == "perform_showall":
        fin_output += perform_accesspolicy(req, callback='')
        fin_output += "<br />"

    if mtype == "perform_accountoverview" and content:
        fin_output += content
    elif mtype == "perform_accountoverview" or mtype == "perform_showall":
        fin_output += perform_accountoverview(req, callback='')
        fin_output += "<br />"

    if mtype == "perform_createaccount" and content:
        fin_output += content
    elif mtype == "perform_createaccount" or mtype == "perform_showall":
        fin_output += perform_createaccount(req, callback='')
        fin_output += "<br />"

    if mtype == "perform_modifyaccounts" and content:
        fin_output += content
    elif mtype == "perform_modifyaccounts" or mtype == "perform_showall":
        fin_output += perform_modifyaccounts(req, callback='')
        fin_output += "<br />"

    if mtype == "perform_becomeuser" and content:
        fin_output += content
    elif mtype == "perform_becomeuser" or mtype == "perform_showall":
        fin_output += perform_becomeuser(req, callback='')
        fin_output += "<br />"

    return index(req=req,
                title='Manage Accounts',
                subtitle=subtitle,
                body=[fin_output],
                adminarea=7,
                authorized=1)

def perform_accesspolicy(req, callback='yes', confirm=0):
    """Modify default behaviour of a guest user or if new accounts should automatically/manually be modified."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="1"></a>1. Access policy.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    account_policy = {}
    account_policy[0] = "Users can register new accounts. New accounts automatically activated."
    account_policy[1] = "Users can register new accounts. Admin users must activate the accounts."
    account_policy[2] = "Only admin can register new accounts. User cannot edit email address."
    account_policy[3] = "Only admin can register new accounts. User cannot edit email address or password."
    account_policy[4] = "Only admin can register new accounts. User cannot edit email address, password or login method."
    account_policy[5] = "Only admin can register new accounts. User cannot edit email address, password or login method and information about how to get an account is hidden from the login page."
    site_policy = {}
    site_policy[0] = "Normal operation of the site."
    site_policy[1] = "Read-only site, all write operations temporarily closed."
    site_policy[2] = "Site fully closed."
    site_policy[3] = "Site fully closed. Database connection disabled."

    output = "(Modifications must be done in access_control_config.py)<br />"
    output += "<br /><b>Current settings:</b><br />"
    output += "Site status: %s<br />" % (site_policy[CFG_ACCESS_CONTROL_LEVEL_SITE])
    output += "Guest accounts allowed: %s<br />" % (CFG_ACCESS_CONTROL_LEVEL_GUESTS == 0 and "Yes" or "No")
    output += "Account policy: %s<br />" % (account_policy[CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS])
    output += "Allowed email addresses limited: %s<br />" % (CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN and CFG_ACCESS_CONTROL_LIMIT_REGISTRATION_TO_DOMAIN or "Not limited")
    output += "Send email to admin when new account: %s<br />" % (CFG_ACCESS_CONTROL_NOTIFY_ADMIN_ABOUT_NEW_ACCOUNTS == 1 and "Yes" or "No")
    output += "Send email to user after creating new account: %s<br />" % (CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1 and "Yes" or "No")
    output += "Send email to user when account is activated: %s<br />" % (CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_ACTIVATION == 1 and "Yes" or "No")
    output += "Send email to user when account is deleted/rejected: %s<br />" % (CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_DELETION == 1 and "Yes" or "No")

    output += "<br />"
    output += "<b>Available 'login via' methods:</b><br />"
    methods = CFG_EXTERNAL_AUTHENTICATION.keys()
    methods.sort()
    for system in methods:
        output += """%s %s<br />""" % (system, (CFG_EXTERNAL_AUTH_DEFAULT == system and "(Default)" or ""))

    output += "<br /><b>Changing the settings:</b><br />"
    output += "Currently, all changes must be done using your favourite editor, and the webserver restarted for changes to take effect. For the settings to change, either look in the guide or in access_control_config.py ."

    body = [output]

    if callback:
        return perform_manageaccounts(req, "perform_accesspolicy", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_accountoverview(req, callback='yes', confirm=0):
    """Modify default behaviour of a guest user or if new accounts should automatically/manually be modified."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="2"></a>2. Account overview.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL
    output = ""
    res = run_sql("SELECT COUNT(*) FROM user WHERE email=''")
    output += "Guest accounts: %s<br />" % res[0][0]
    res = run_sql("SELECT COUNT(*) FROM user WHERE email!=''")
    output += "Registered accounts: %s<br />" % res[0][0]
    res = run_sql("SELECT COUNT(*) FROM user WHERE email!='' AND note='0' OR note IS NULL")
    output += "Inactive accounts: %s " % res[0][0]
    if res[0][0] > 0:
        output += ' [<a href="modifyaccounts?email_user_pattern=&amp;limit_to=disabled&amp;maxpage=25&amp;page=1">Activate/Reject accounts</a>]'
    res = run_sql("SELECT COUNT(*) FROM user")
    output += "<br />Total nr of accounts: %s<br />" % res[0][0]

    body = [output]

    if callback:
        return perform_manageaccounts(req, "perform_accountoverview", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_createaccount(req, email='', password='', callback='yes', confirm=0):
    """Modify default behaviour of a guest user or if new accounts should automatically/manually be modified."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="3"></a>3. Create account.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    output = ""

    text = ' <span class="adminlabel">Email:</span>\n'
    text += ' <input class="admin_wvar" type="text" name="email" value="%s" /><br />' % (email, )
    text += ' <span class="adminlabel">Password:</span>\n'
    text += ' <input class="admin_wvar" type="text" name="password" value="%s" /><br />' % (password, )

    output += createhiddenform(action="createaccount",
                                text=text,
                                confirm=1,
                                button="Create")

    if confirm in [1, "1"] and email and email_valid_p(email):
        res = run_sql("SELECT email FROM user WHERE email=%s", (email,))
        if not res:
            from invenio.modules.accounts.models import User
            from invenio.ext.sqlalchemy import db
            User.query.filter_by(id=1).delete()
            u = User(email=email, password=password, note=1)
            db.session.add(u)
            db.session.commit()

            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1:
                emailsent = send_new_user_account_warning(email, email, password) == 0
            if password:
                output += '<b><span class="info">Account created with password and activated.</span></b>'
            else:
                output += '<b><span class="info">Account created without password and activated.</span></b>'
            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_NEW_ACCOUNT == 1:
                if emailsent:
                    output += '<br /><b><span class="info">An email has been sent to the owner of the account.</span></b>'
                else:
                    output += '<br /><b><span class="important">Could not send an email to the owner of the account.</span></b>'

        else:
            output += '<b><span class="info">An account with the same email already exists.</span></b>'

    elif confirm in [1, "1"]:
        output += '<b><span class="info">Please specify an valid email-address.</span></b>'

    body = [output]

    if callback:
        return perform_manageaccounts(req, "perform_createaccount", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)


def perform_modifyaccountstatus(req, userID, email_user_pattern, limit_to, maxpage, page, callback='yes', confirm=0):
    """set a disabled account to enabled and opposite"""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    res = run_sql("SELECT id, email, note FROM user WHERE id=%s", (userID, ))
    subtitle = ""
    output = ""
    if res:
        if res[0][2] in [0, "0", None]:
            res2 = run_sql("UPDATE user SET note=1 WHERE id=%s", (userID, ))
            output += """<b><span class="info">The account '%s' has been activated.</span></b>""" % res[0][1]
            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_ACTIVATION == 1:
                emailsent = send_account_activated_message(res[0][1], res[0][1], '*****')
                if emailsent:
                    output += """<br /><b><span class="info">An email has been sent to the owner of the account.</span></b>"""
                else:
                    output += """<br /><b><span class="info">Could not send an email to the owner of the account.</span></b>"""

        elif res[0][2] in [1, "1"]:
            res2 = run_sql("UPDATE user SET note=0 WHERE id=%s", (userID, ))
            output += """<b><span class="info">The account '%s' has been set inactive.</span></b>""" % res[0][1]
    else:
        output += '<b><span class="info">The account id given does not exist.</span></b>'

    body = [output]

    if callback:
        return perform_modifyaccounts(req, email_user_pattern, limit_to, maxpage, page, content=output, callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_editaccount(req, userID, mtype='', content='', callback='yes', confirm=-1):
    """form to modify an account. this method is calling other methods which again is calling this and sending back the output of the method.
    if callback, the method will call perform_editcollection, if not, it will just return its output.
    userID - id of the user
    mtype - the method that called this method.
    content - the output from that method."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    res = run_sql("SELECT id, email FROM user WHERE id=%s", (userID, ))
    if not res:
        if mtype == "perform_deleteaccount":
            text = """<b><span class="info">The selected account has been deleted, to continue editing, go back to 'Manage Accounts'.</span></b>"""
            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_DELETION == 1:
                text += """<br /><b><span class="info">An email has been sent to the owner of the account.</span></b>"""
        else:
            text = """<b><span class="info">The selected accounts does not exist, please go back and select an account to edit.</span></b>"""

        return index(req=req,
                title='Edit Account',
                subtitle="Edit account",
                body=[text],
                adminarea=7,
                authorized=1)

    fin_output = """
    <table>
    <tr>
    <td><b>Menu</b></td>
    </tr>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/editaccount?userID=%s">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/editaccount?userID=%s&amp;mtype=perform_modifylogindata">Modify login-data</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/editaccount?userID=%s&amp;mtype=perform_modifypreferences">Modify preferences</a></small></td>
    </tr><tr>
    <td>3.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/editaccount?userID=%s&amp;mtype=perform_deleteaccount">Delete account</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/webaccess/webaccessadmin.py/editaccount?userID=%s&amp;mtype=perform_modifyapikeydata">Edit REST API Key</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_SECURE_URL, userID, CFG_SITE_SECURE_URL, userID, CFG_SITE_SECURE_URL, userID, CFG_SITE_SECURE_URL, userID, CFG_SITE_SECURE_URL, userID)

    if mtype == "perform_modifylogindata" and content:
        fin_output += content
    elif mtype == "perform_modifylogindata" or not mtype:
        fin_output += perform_modifylogindata(req, userID, callback='')

    if mtype == "perform_modifypreferences" and content:
        fin_output += content
    elif mtype == "perform_modifypreferences" or not mtype:
        fin_output += perform_modifypreferences(req, userID, callback='')

    if mtype == "perform_deleteaccount" and content:
        fin_output += content
    elif mtype == "perform_deleteaccount" or not mtype:
        fin_output += perform_deleteaccount(req, userID, callback='')

    if mtype == "perform_modifyapikeydata" and content:
        fin_output += content
    elif mtype == "perform_modifyapikeydata" or not mtype:
        fin_output += perform_modifyapikeydata(req, userID, callback='')

    return index(req=req,
                title='Edit Account',
                subtitle="Edit account '%s'" % res[0][1],
                body=[fin_output],
                adminarea=7,
                authorized=1)

def perform_becomeuser(req, userID='', callback='yes', confirm=0):
    """modify email and password of an account"""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="5"></a>5. Became user.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#5">?</a>]</small>""" % CFG_SITE_SECURE_URL

    res = run_sql("SELECT email FROM user WHERE id=%s", (userID, ))
    output = ""
    if res:
        update_Uid(req, res[0][0])
        redirect_to_url(req, CFG_SITE_SECURE_URL)
    else:
        output += '<b><span class="info">The account id given does not exist.</span></b>'

    body = [output]

    if callback:
        return perform_editaccount(req, userID, mtype='perform_becomeuser', content=addadminbox(subtitle, body), callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_modifylogindata(req, userID, nickname='', email='', password='', callback='yes', confirm=0):
    """modify email and password of an account"""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="1"></a>1. Edit login-data.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    res = run_sql("SELECT id, email, nickname FROM user WHERE id=%s", (userID, ))
    output = ""
    if res:
        if not email and not password:
            email = res[0][1]
            nickname = res[0][2]
        text =  ' <span class="adminlabel">Account id:</span>%s<br />\n' % userID
        text =  ' <span class="adminlabel">Nickname:</span>\n'
        text += ' <input class="admin_wvar" type="text" name="nickname" value="%s" /><br />' % (nickname, )
        text += ' <span class="adminlabel">Email:</span>\n'
        text += ' <input class="admin_wvar" type="text" name="email" value="%s" /><br />' % (email, )
        text += ' <span class="adminlabel">Password:</span>\n'
        text += ' <input class="admin_wvar" type="text" name="password" value="%s" /><br />' % (password, )

        output += createhiddenform(action="modifylogindata",
                                text=text,
                                userID=userID,
                                confirm=1,
                                button="Modify")
        if confirm in [1, "1"] and email and email_valid_p(email):
            res = run_sql("SELECT nickname FROM user WHERE nickname=%s AND id<>%s", (nickname, userID))
            if res:
                output += '<b><span class="info">Sorry, the specified nickname is already used.</span></b>'
            else:
                res = run_sql("UPDATE user SET email=%s WHERE id=%s", (email, userID))
                if password:
                    from invenio.modules.accounts.models import User
                    from invenio.ext.sqlalchemy import db
                    u = User.query.filter_by(id=userID).first()
                    if u:
                        u.password = password
                        db.session.commit()
                else:
                    output += '<b><span class="info">Password not modified.</span></b> '
                res = run_sql("UPDATE user SET nickname=%s WHERE id=%s", (nickname, userID))
                output += '<b><span class="info">Nickname/email and/or password  modified.</span></b>'
        elif confirm in [1, "1"]:
            output += '<b><span class="info">Please specify an valid email-address.</span></b>'
    else:
        output += '<b><span class="info">The account id given does not exist.</span></b>'

    body = [output]

    if callback:
        return perform_editaccount(req, userID, mtype='perform_modifylogindata', content=addadminbox(subtitle, body), callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_modifypreferences(req, userID, login_method='', callback='yes', confirm=0):
    """modify email and password of an account"""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="2"></a>2. Modify preferences.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    res = run_sql("SELECT id, email FROM user WHERE id=%s", (userID, ))
    output = ""
    if res:
        user_pref = get_user_preferences(userID)
        if confirm in [1, "1"]:
            if login_method:
                user_pref['login_method'] = login_method
                set_user_preferences(userID, user_pref)

        output += "Select default login method:<br />"
        text = ""
        methods = CFG_EXTERNAL_AUTHENTICATION.keys()
        methods.sort()
        for system in methods:
            text += """<input type="radio" name="login_method" value="%s" %s>%s<br />""" % (system, (user_pref['login_method'] == system and "checked" or ""), system)


        output += createhiddenform(action="modifypreferences",
                                text=text,
                                confirm=1,
                                userID=userID,
                                button="Select")

        if confirm in [1, "1"]:
            if login_method:
                output += """<b><span class="info">The login method has been changed</span></b>"""
            else:
                output += """<b><span class="info">Nothing to update</span></b>"""
    else:
        output += '<b><span class="info">The account id given does not exist.</span></b>'

    body = [output]

    if callback:
        return perform_editaccount(req, userID, mtype='perform_modifypreferences', content=addadminbox(subtitle, body), callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_deleteaccount(req, userID, callback='yes', confirm=0):
    """delete account"""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="3"></a>3. Delete account.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    res = run_sql("SELECT id, email FROM user WHERE id=%s", (userID, ))
    output = ""
    if res:
        if confirm in [0, "0"]:
            text = '<b><span class="important">Are you sure you want to delete the account with email: "%s"?</span></b>' % res[0][1]
            output += createhiddenform(action="deleteaccount",
                                    text=text,
                    userID=userID,
                                    confirm=1,
                                    button="Delete")

        elif confirm in [1, "1"]:
            res2 = run_sql("DELETE FROM user WHERE id=%s", (userID, ))
            output += '<b><span class="info">Account deleted.</span></b>'
            if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_DELETION == 1:
                emailsent = send_account_deleted_message(res[0][1], res[0][1])
    else:
        output += '<b><span class="info">The account id given does not exist.</span></b>'

    body = [output]

    if callback:
        return perform_editaccount(req, userID, mtype='perform_deleteaccount', content=addadminbox(subtitle, body), callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_modifyapikeydata(req, userID, keyID='', status='' , callback='yes', confirm=0):
    """modify REST API keys of an account"""

    from invenio.modules.apikeys.models import WebAPIKey
    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="4"></a>4. Edit REST API Keys.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    if confirm in [1, "1"]:
        run_sql("UPDATE webapikey SET status=%s WHERE id=%s", (status, keyID))

    res = run_sql("SELECT id, description, status FROM webapikey WHERE id_user=%s", (userID, ))
    output = ""
    if res:
        for key_info in res:
            text = ''
            text += ' <span class="adminlabel">Key: </span><code>%s</code><br />\n' % key_info[0]
            text += ' <input class="admin_wvar" type="hidden" name="keyID" value="%s" />' % key_info[0]
            text += ' <span class="adminlabel">Description: </span>%s<br />\n' % key_info[1]
            text += ' <select name="status"> '
            for status in WebAPIKey.CFG_WEB_API_KEY_STATUS.values():
                text += ' <option %s value="%s">%s</option>' % (("", "selected")[key_info[2] == status], status, status)
            text += ' </select> <br />\n'
            if key_info[0] == keyID:
                text += '<b><span class="info">Key status modified</span></b>'
            output += createhiddenform(action="modifyapikeydata",
                                       text=text,
                                       userID=userID,
                                       confirm=1,
                                       button="Modify")
    else:
        output += '<b><span class="info">The account id given does not have REST API Keys.</span></b>'

    body = [output]

    if callback:
        return perform_editaccount(req, userID, mtype='perform_modifyapikeydata', content=addadminbox(subtitle, body), callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_rejectaccount(req, userID, email_user_pattern, limit_to, maxpage, page, callback='yes', confirm=0):
    """Delete account and send an email to the owner."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    res = run_sql("SELECT id, email, note FROM user WHERE id=%s", (userID, ))
    output = ""
    subtitle = ""
    if res:
        res2 = run_sql("DELETE FROM user WHERE id=%s", (userID, ))
        output += '<b><span class="info">Account rejected and deleted.</span></b>'
        if CFG_ACCESS_CONTROL_NOTIFY_USER_ABOUT_DELETION == 1:
            if not res[0][2] or res[0][2] == "0":
                emailsent = send_account_rejected_message(res[0][1], res[0][1])
            elif res[0][2] == "1":
                emailsent = send_account_deleted_message(res[0][1], res[0][1])
            if emailsent:
                output += """<br /><b><span class="info">An email has been sent to the owner of the account.</span></b>"""
            else:
                output += """<br /><b><span class="info">Could not send an email to the owner of the account.</span></b>"""
    else:
        output += '<b><span class="info">The account id given does not exist.</span></b>'

    body = [output]

    if callback:
        return perform_modifyaccounts(req, email_user_pattern, limit_to, maxpage, page, content=output, callback='yes')
    else:
        return addadminbox(subtitle, body)

def perform_modifyaccounts(req, email_user_pattern='', limit_to=-1, maxpage=MAXPAGEUSERS, page=1, content='', callback='yes', confirm=0):
    """Modify default behaviour of a guest user or if new accounts should automatically/manually be modified."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    subtitle = """<a name="4"></a>4. Edit accounts.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/webaccess-admin-guide#4">?</a>]</small>""" % CFG_SITE_SECURE_URL

    output = ""

    # remove letters not allowed in an email
    email_user_pattern = cleanstring_email(email_user_pattern)
    try:
        maxpage = int(maxpage)
    except:
        maxpage = MAXPAGEUSERS
    try:
        page = int(page)
        if page < 1:
            page = 1
    except:
        page = 1

    text  = ' <span class="adminlabel">Email (part of):</span>\n'
    text += ' <input class="admin_wvar" type="text" name="email_user_pattern" value="%s" /><br />' % (email_user_pattern, )

    text += """<span class="adminlabel">Limit to:</span>
    <select name="limit_to" class="admin_w200">
    <option value="all" %s>All accounts</option>
    <option value="enabled" %s>Active accounts</option>
    <option value="disabled" %s>Inactive accounts</option>
    </select><br />""" % ((limit_to=="all" and "selected" or ""), (limit_to=="enabled" and "selected" or ""), (limit_to=="disabled" and "selected" or ""))

    text += """<span class="adminlabel">Accounts per page:</span>
    <select name="maxpage" class="admin_wvar">
    <option value="25" %s>25</option>
    <option value="50" %s>50</option>
    <option value="100" %s>100</option>
    <option value="250" %s>250</option>
    <option value="500" %s>500</option>
    <option value="1000" %s>1000</option>
    </select><br />""" % ((maxpage==25 and "selected" or ""), (maxpage==50 and "selected" or ""), (maxpage==100 and "selected" or ""), (maxpage==250 and "selected" or ""), (maxpage==500 and "selected" or ""), (maxpage==1000 and "selected" or ""))

    output += createhiddenform(action="modifyaccounts",
                            text=text,
                            button="search for accounts")

    if limit_to not in [-1, "-1"] and maxpage:
        options = []
        users1 = "SELECT id,email,note FROM user WHERE "
        if limit_to == "enabled":
            users1 += " email!='' AND note=1"
        elif limit_to == "disabled":
            users1 += " email!='' AND note=0 OR note IS NULL"
        elif limit_to == "guest":
            users1 += " email=''"
        else:
            users1 += " email!=''"
        if email_user_pattern:
            users1 += " AND email RLIKE %s"
            options += [email_user_pattern]
        users1 += " ORDER BY email LIMIT %s"
        options += [maxpage * page + 1]
        try:
            users1 = run_sql(users1, tuple(options))
        except OperationalError:
            users1 = ()
        if not users1:
            output += '<b><span class="info">There are no accounts matching the email given.</span></b>'
        else:
            users = []
            if maxpage * (page  - 1) > len(users1):
                page = len(users1) / maxpage + 1
            for (id, email, note) in users1[maxpage * (page  - 1):(maxpage * page)]:
                users.append(['', id, email, (note=="1" and '<strong class="info">Active</strong>' or '<strong class="important">Inactive</strong>')])
                for col in [(((note=="1" and 'Inactivate' or 'Activate'), 'modifyaccountstatus'), ((note == "0" and 'Reject' or 'Delete'), 'rejectaccount'), ),
                            (('Edit account', 'editaccount'), ),]:
                    users[-1].append('<a href="%s?userID=%s&amp;email_user_pattern=%s&amp;limit_to=%s&amp;maxpage=%s&amp;page=%s">%s</a>' % (col[0][1], id, email_user_pattern, limit_to, maxpage, page, col[0][0]))
                    for (str, function) in col[1:]:
                        users[-1][-1] += ' / <a href="%s?userID=%s&amp;email_user_pattern=%s&amp;limit_to=%s&amp;maxpage=%s&amp;page=%s">%s</a>' % (function, id, email_user_pattern, limit_to, maxpage, page, str)
                users[-1].append('<a href=%s?userID=%s&amp;email_user_pattern=%s&amp;limit_to=%s&amp;maxpage=%s&amp;page=%s">%s</a>' % ('becomeuser', id, email_user_pattern, limit_to, maxpage, page, 'Become user'))

            last = ""
            next = ""
            if len(users1) > maxpage:
                if page > 1:
                    last += '<b><span class="info"><a href="modifyaccounts?email_user_pattern=%s&amp;limit_to=%s&amp;maxpage=%s&amp;page=%s">Last Page</a></span></b>' % (email_user_pattern, limit_to, maxpage, (page - 1))
                if len(users1[maxpage * (page  - 1):(maxpage * page)]) == maxpage:
                    next += '<b><span class="info"><a href="modifyaccounts?email_user_pattern=%s&amp;limit_to=%s&amp;maxpage=%s&amp;page=%s">Next page</a></span></b>' % (email_user_pattern, limit_to, maxpage, (page + 1))
                output += '<b><span class="info">Showing accounts %s-%s:</span></b>' % (1 + maxpage * (page - 1), maxpage * page)
            else:
                output += '<b><span class="info">%s matching account(s):</span></b>' % len(users1)
            output += tupletotable(header=[last, 'id', 'email', 'Status', '', '', next], tuple=users)

    else:
        output += '<b><span class="info">Please select which accounts to find and how many to show per page.</span></b>'

    if content:
        output += "<br />%s" % content

    body = [output]

    if callback:
        return perform_manageaccounts(req, "perform_modifyaccounts", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_delegate_startarea(req):
    """start area for lower level delegation of rights."""

    # refuse access to guest users:
    uid = getUid(req)
    if isGuestUser(uid):
        return index(req=req,
                    title='Delegate Rights',
                    adminarea=0,
                    authorized=0)

    subtitle = 'select what to do'

    output = ''

    if is_adminuser(req)[0] == 0:
        output += """
        <p>
        You are also allowed to be in the <a href="../webaccessadmin.py">Main Admin Area</a> which gives you<br />
        the access to the full functionality of WebAccess.
        </p>
        """

    output += """
    <dl>
    <dt><a href="delegate_adduserrole">Connect users to roles</a></dt>
    <dd>add users to the roles you have delegation rights to.</dd>
    <dt><a href="delegate_deleteuserrole">Remove users from roles</a></dt>
    <dd>remove users from the roles you have delegation rights to.</dd>
    </dl>
    <dl>
    <dt><a href="delegate_adminsetup">Set up delegation rights</a></dt>
    <dd>specialized area to set up the delegation rights used in the areas above. <br />
        you need to be a web administrator to access the area.</dd>
    </dl>
    """

    return index(req=req,
                title='Delegate Rights',
                subtitle=subtitle,
                body=[output],
                adminarea=0,
                authorized=1)


def perform_delegate_adminsetup(req, id_role_admin=0, id_role_delegate=0, confirm=0):
    """lets the webadmins set up the delegation rights for the other roles

    id_role_admin - the role to be given delegation rights

    id_role_delegate - the role over which the delegation rights are given

            confirm - make the connection happen """

    subtitle = 'step 1 - select admin role'

    admin_roles = acca.acc_get_all_roles()

    output = """
    <p>
    This is a specialized area to handle a task that also can be handled<br />
    from the &quot;add authorization&quot; interface.
    </p>
    <p>
    By handling the delegation rights here you get the advantage of<br />
    not having to select the correct action <i>(%s)</i> or<br />
    remembering the names of available roles.
    </p>
    """ % (DELEGATEADDUSERROLE, )

    output += createroleselect(id_role=id_role_admin,
                            step=1,
                            button='select admin role',
                            name='id_role_admin',
                            action='delegate_adminsetup',
                            roles=admin_roles)

    if str(id_role_admin) != '0':
        subtitle = 'step 2 - select delegate role'

        name_role_admin = acca.acc_get_role_name(id_role=id_role_admin)

        delegate_roles_old = acca.acc_find_delegated_roles(id_role_admin=id_role_admin)

        delegate_roles = []
        delegate_roles_old_names = []
        for role in admin_roles:
            if (role,) not in delegate_roles_old:
                delegate_roles.append(role)
            else:
                delegate_roles_old_names.append(role[1])

        if delegate_roles_old_names:
            delegate_roles_old_names.sort()
            names_str = ''
            for name in delegate_roles_old_names:
                if names_str: names_str += ', '
                names_str += name
            output += '<p>previously selected roles: <strong>%s</strong>.</p>' % (names_str, )

            extra = """
            <dl>
            <dt><a href="modifyauthorizations?id_role=%s&amp;id_action=%s">Remove delegated roles</a></dt>
            <dd>use the standard administration area to remove delegation rights
                you no longer want to be available.</dd>
            </dl>
            """ % (id_role_admin, acca.acc_get_action_id(name_action=DELEGATEADDUSERROLE))

        else:
            output += '<p>no previously selected roles.</p>'

        output += createroleselect(id_role=id_role_delegate,
                                step=2,
                                button='select delegate role',
                                name='id_role_delegate',
                                action='delegate_adminsetup',
                                roles=delegate_roles,
                                id_role_admin=id_role_admin)

        if str(id_role_delegate) != '0':
            subtitle = 'step 3 - confirm to add delegation right'

            name_role_delegate = acca.acc_get_role_name(id_role=id_role_delegate)

            output += """
            <p>
            <span class="warning"><strong>Warning:</strong> don't hand out delegation rights that can harm the system (e.g. delegating superrole).</span>
            </p> """

            output += createhiddenform(action="delegate_adminsetup",
                                    text='let role <strong>%s</strong> delegate rights over role <strong>%s</strong>?' % (name_role_admin, name_role_delegate),
                                    id_role_admin=id_role_admin,
                                    id_role_delegate=id_role_delegate,
                                    confirm=1)

            if int(confirm):
                subtitle = 'step 4 - confirm delegation right added'
                # res1 = acca.acc_add_role_action_arguments_names(name_role=name_role_admin,
                #                                              name_action=DELEGATEADDUSERROLE,
                #                                              arglistid=-1,
                #                                              optional=0,
                #                                              role=name_role_delegate)
                res1 = acca.acc_add_authorization(name_role=name_role_admin,
                                                name_action=DELEGATEADDUSERROLE,
                                                optional=0,
                                                role=name_role_delegate)

                if res1:
                    output += '<p>confirm: role <strong>%s</strong> delegates role <strong>%s</strong>.' % (name_role_admin, name_role_delegate)

                else: output += '<p>sorry, delegation right could not be added,<br />it probably already exists.</p>'

    # see if right hand menu is available
    try: body = [output, extra]
    except NameError: body = [output]

    return index(req=req,
                title='Delegate Rights',
                subtitle=subtitle,
                body=body,
                adminarea=1)


def perform_delegate_adduserrole(req, id_role=0, email_user_pattern='', id_user=0, confirm=0):
    """let a lower level web admin add users to a limited set of roles.

    id_role - the role to connect to a user

    id_user - the user to connect to a role

    confirm - make the connection happen """

    # finding the allowed roles for this user
    id_admin = getUid(req)
    id_action = acca.acc_get_action_id(name_action=DELEGATEADDUSERROLE)
    actions = acca.acc_find_possible_actions_user(id_user=id_admin, id_action=id_action)

    allowed_roles = []
    allowed_id_roles = []
    for (id, arglistid, name_role_help) in actions[1:]:
        id_role_help = acca.acc_get_role_id(name_role=name_role_help)
        if id_role_help and [id_role_help, name_role_help, ''] not in allowed_roles:
            allowed_roles.append([id_role_help, name_role_help, ''])
            allowed_id_roles.append(str(id_role_help))

    output = ''

    if not allowed_roles:
        subtitle = 'no delegation rights'
        output += """
        <p>
        You do not have the delegation rights over any roles.<br />
        If you think you should have such rights, contact a WebAccess Administrator.
        </p>"""
        extra = ''
    else:
        subtitle = 'step 1 - select role'

        output += """
        <p>
        Lower level delegation of access rights to roles.<br />
        An administrator with all rights have to give you these rights.
        </p>"""

        email_out = acca.acc_get_user_email(id_user=id_user)
        name_role = acca.acc_get_role_name(id_role=id_role)

        output += createroleselect(id_role=id_role, step=1, name='id_role',
                                action='delegate_adduserrole', roles=allowed_roles)

        if str(id_role) != '0' and str(id_role) in allowed_id_roles:
            subtitle = 'step 2 - search for users'

            # remove letters not allowed in an email
            email_user_pattern = cleanstring_email(email_user_pattern)

            text  = ' <span class="adminlabel">2. search for user </span>\n'
            text += ' <input class="admin_wvar" type="text" name="email_user_pattern" value="%s" />\n' % (email_user_pattern, )

            output += createhiddenform(action="delegate_adduserrole",
                                    text=text,
                                    button="search for users",
                                    id_role=id_role)

            # pattern is entered
            if email_user_pattern:
                # users with matching email-address
                try:
                    users1 = run_sql("""SELECT id, email FROM user WHERE email<>'' AND email RLIKE %s ORDER BY email """, (email_user_pattern, ))
                except OperationalError:
                    users1 = ()
                # users that are connected
                try:
                    users2 = run_sql("""SELECT DISTINCT u.id, u.email
                    FROM user u LEFT JOIN user_accROLE ur ON u.id = ur.id_user
                    WHERE ur.id_accROLE = %s AND u.email RLIKE %s
                    ORDER BY u.email """,  (id_role, email_user_pattern))
                except OperationalError:
                    users2 = ()
                # no users that match the pattern
                if not (users1 or users2):
                    output += '<p>no qualified users, try new search.</p>'
                # too many matching users
                elif len(users1) > MAXSELECTUSERS:
                    output += '<p><strong>%s hits</strong>, too many qualified users, specify more narrow search. (limit %s)</p>' % (len(users1), MAXSELECTUSERS)

                # show matching users
                else:
                    subtitle = 'step 3 - select a user'

                    users = []
                    extrausers = []
                    for (id, email) in users1:
                        if (id, email) not in users2: users.append([id,email,''])
                    for (id, email) in users2:
                        extrausers.append([-id, email,''])

                    output += createuserselect(id_user=id_user,
                                            action="delegate_adduserrole",
                                            step=3,
                                            users=users,
                                            extrausers=extrausers,
                                            button="add this user",
                                            id_role=id_role,
                                            email_user_pattern=email_user_pattern)

                    try: id_user = int(id_user)
                    except ValueError: pass
                    # user selected already connected to role
                    if id_user < 0:
                        output += '<p>users in brackets are already attached to the role, try another one...</p>'
                    # a user is selected
                    elif email_out:
                        subtitle = "step 4 - confirm to add user"

                        output += createhiddenform(action="delegate_adduserrole",
                                                text='add user <strong>%s</strong> to role <strong>%s</strong>?' % (email_out, name_role),
                                                id_role=id_role,
                                                email_user_pattern=email_user_pattern,
                                                id_user=id_user,
                                                confirm=1)

                        # it is confirmed that this user should be added
                        if confirm:
                            # add user
                            result = acca.acc_add_user_role(id_user=id_user, id_role=id_role)

                            if result and result[2]:
                                subtitle = 'step 5 - confirm user added'
                                output  += '<p>confirm: user <strong>%s</strong> added to role <strong>%s</strong>.</p>' % (email_out, name_role)
                            else:
                                subtitle = 'step 5 - user could not be added'
                                output += '<p>sorry, but user could not be added.</p>'

        extra = """
        <dl>
        <dt><a href="delegate_deleteuserrole?id_role=%s">Remove users from role</a></dt>
        <dd>remove users from the roles you have delegating rights to.</dd>
        </dl>
        """ % (id_role, )

    return index(req=req,
                title='Connect users to roles',
                subtitle=subtitle,
                body=[output, extra],
                adminarea=1,
                authorized=1)


def perform_delegate_deleteuserrole(req, id_role=0, id_user=0, confirm=0):
    """let a lower level web admin remove users from a limited set of roles.

    id_role - the role to connect to a user

    id_user - the user to connect to a role

    confirm - make the connection happen """

    subtitle = 'in progress...'

    output = '<p>in progress...</p>'

    # finding the allowed roles for this user
    id_admin = getUid(req)
    id_action = acca.acc_get_action_id(name_action=DELEGATEADDUSERROLE)
    actions = acca.acc_find_possible_actions_user(id_user=id_admin, id_action=id_action)

    output = ''

    if not actions:
        subtitle = 'no delegation rights'
        output += """
        <p>
        You do not have the delegation rights over any roles.<br />
        If you think you should have such rights, contact a WebAccess Administrator.
        </p>"""
        extra = ''
    else:
        subtitle = 'step 1 - select role'

        output += """
        <p>
        Lower level delegation of access rights to roles.<br />
        An administrator with all rights have to give you these rights.
        </p>"""

        email_out = acca.acc_get_user_email(id_user=id_user)
        name_role = acca.acc_get_role_name(id_role=id_role)

        # create list of allowed roles
        allowed_roles = []
        allowed_id_roles = []
        for (id, arglistid, name_role_help) in actions[1:]:
            id_role_help = acca.acc_get_role_id(name_role=name_role_help)
            if id_role_help and [id_role_help, name_role_help, ''] not in allowed_roles:
                allowed_roles.append([id_role_help, name_role_help, ''])
                allowed_id_roles.append(str(id_role_help))

        output += createroleselect(id_role=id_role, step=1,
                                action='delegate_deleteuserrole', roles=allowed_roles)

        if str(id_role) != '0' and str(id_role) in allowed_id_roles:
            subtitle = 'step 2 - select user'

            users = acca.acc_get_role_users(id_role)

            output += createuserselect(id_user=id_user,
                                    step=2,
                                    action='delegate_deleteuserrole',
                                    users=users,
                                    id_role=id_role)

            if str(id_user) != '0':
                subtitle = 'step 3 - confirm delete of user'
                email_user = acca.acc_get_user_email(id_user=id_user)

                output += createhiddenform(action="delegate_deleteuserrole",
                                        text='delete user %s from %s?'
                                        % (headerstrong(user=id_user), headerstrong(role=id_role)),
                                        id_role=id_role,
                                        id_user=id_user,
                                        confirm=1)

                if confirm:
                    res = acca.acc_delete_user_role(id_user=id_user, id_role=id_role)
                    if res:
                        subtitle = 'step 4 - confirm user deleted from role'
                        output += '<p>confirm: deleted user <strong>%s</strong> from role <strong>%s</strong>.</p>' % (email_user, name_role)
                    else:
                        subtitle = 'step 4 - user could not be deleted'
                        output += 'sorry, but user could not be deleted<br />user is probably already deleted.'

        extra = """
        <dl>
        <dt><a href="delegate_adduserrole?id_role=%s">Connect users to role</a></dt>
        <dd>add users to the roles you have delegating rights to.</dd>
        </dl>
        """ % (id_role, )

    return index(req=req,
                title='Remove users from roles',
                subtitle=subtitle,
                body=[output, extra],
                adminarea=1,
                authorized=1)

def perform_showactiondetails(req, id_action):
    """show the details of an action. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    output = createactionselect(id_action=id_action,
                                action="showactiondetails",
                                step=1,
                                actions=acca.acc_get_all_actions(),
                                button="select action")

    if id_action not in [0, '0']:
        output += actiondetails(id_action=id_action)

        extra = """
        <dl>
        <dt><a href="addauthorization?id_action=%s&amp;reverse=1">Add new authorization</a></dt>
        <dd>add an authorization.</dd>
        <dt><a href="modifyauthorizations?id_action=%s&amp;reverse=1">Modify authorizations</a></dt>
        <dd>modify existing authorizations.</dd>
        <dt><a href="deleteroleaction?id_action=%s&amp;reverse=1">Remove role</a></dt>
        <dd>remove all authorizations from action and a role.</dd>
        </dl>
        """ % (id_action, id_action, id_action)
        body = [output, extra]

    else:
        output += '<p>no details to show</p>'
        body = [output]

    return index(req=req,
                title='Show Action Details',
                subtitle='show action details',
                body=body,
                adminarea=4)


def actiondetails(id_action=0):
    """show details of given action. """

    output = ''

    if id_action not in [0, '0']:
        name_action = acca.acc_get_action_name(id_action=id_action)

        output += '<p>action details:</p>'
        output += tupletotable(header=['id', 'name', 'description', 'allowedkeywords', 'optional'],
                            tuple=[acca.acc_get_action_details(id_action=id_action)])

        roleshlp = acca.acc_get_action_roles(id_action=id_action)
        if roleshlp:
            roles = []
            for (id, name, dummy) in roleshlp:
                res = acca.acc_find_possible_actions(id, id_action)
                if res:
                    authorization_details = tupletotable(header=res[0], tuple=res[1:])
                else:
                    authorization_details = 'no details to show'

                roles.append([id, '<a href="showroledetails?id_role=%s">%s</a>' % (id, escape(name)),
                            authorization_details])
            roletable = tupletotable(header=['id', 'name', 'authorization details', ''], tuple=roles)

            output += '<p>roles connected to %s:</p>\n' % (headerstrong(action=name_action, query=0), )
            output += roletable

        else:
            output += '<p>no roles connected to %s.</p>\n' % (headerstrong(action=name_action, query=0), )

    else:
        output += '<p>no details to show</p>'

    return output


def perform_addrole(req, id_role=0, name_role='', description='put description here.', firerole_def_src=CFG_ACC_EMPTY_ROLE_DEFINITION_SRC, confirm=0):
    """form to add a new role with these values:

    name_role - name of the new role

    description - optional description of the role """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    name_role = cleanstring(name_role)

    title='Add Role'
    subtitle = 'step 1 - give values to the requested fields'

    output = """
    <form action="addrole" method="POST">
    <table><tbody><tr><td align='right' valign='top'>
    <span class="adminlabel">role name </span>
    </td><td>
    <input class="admin_wvar" type="text" name="name_role" value="%s" />
    </td></tr><tr><td align='right' valign='top'>
    <span class="adminlabel">description </span>
    </td><td>
    <textarea class="admin_wvar" rows="6" cols="80" name="description">%s</textarea>
    </td></tr><tr><td align='right' valign='top'>
    <span class="adminlabel">firewall like role definition [<a href="/help/admin/webaccess-admin-guide#6">?</a>]</span>
    </td><td>
    <textarea class="admin_wvar" rows="6" cols="80" name="firerole_def_src">%s</textarea>
    </td></tr>
    <tr><td></td><td>See the <a href="listgroups" target="_blank">list of groups</a> for a hint about which group names you can use.</td></tr>
    <tr><td></td><td>
    <input class="adminbutton" type="submit" value="add role" />
    </td></tr></tbody></table>
    </form>
    """ % (escape(name_role, '"'), escape(description),  escape(firerole_def_src))

    if name_role:
        # description must be changed before submitting
        subtitle = 'step 2 - confirm to add role'
        internaldesc = ''
        if description != 'put description here.':
            internaldesc = description

        try:
            firerole_def_ser = serialize(compile_role_definition(firerole_def_src))
        except InvenioWebAccessFireroleError as msg:
            output += "<strong>%s</strong>" % msg
        else:
            text = """
            add role with: <br />\n
            name: <strong>%s</strong> <br />""" % (name_role, )
            if internaldesc:
                text += 'description: <strong>%s</strong>?\n' % (description, )

            output += createhiddenform(action="addrole",
                                    text=text,
                                    name_role=escape(name_role, '"'),
                                    description=escape(description, '"'),
                                    firerole_def_src=escape(firerole_def_src, '"'),
                                    confirm=1)

            if confirm not in ["0", 0]:
                result = acca.acc_add_role(name_role=name_role,
                                        description=internaldesc,
                                        firerole_def_ser=firerole_def_ser,
                                        firerole_def_src=firerole_def_src)

                if result:
                    subtitle = 'step 3 - role added'
                    output += '<p>role added: </p>'
                    result = list(result)
                    result[3] = result[3].replace('\n', '<br/>')
                    result = tuple(result)
                    output += tupletotable(header=['id', 'role name', 'description', 'firewall like role definition'],
                                        tuple=[result])
                else:
                    subtitle = 'step 3 - role could not be added'
                    output += '<p>sorry, could not add role, <br />role with the same name probably exists.</p>'

                id_role = acca.acc_get_role_id(name_role=name_role)
                extra = """
                <dl>
                <dt><a href="addauthorization?id_role=%s">Add authorization</a></dt>
                <dd>start adding new authorizations to role %s.</dd>
                </dl>
                <dt><a href="adduserrole?id_role=%s">Connect user</a></dt>
                <dd>connect a user to role %s.</dd>
                <dl>
                </dl>""" % (id_role, name_role, id_role, name_role)

    try: body = [output, extra]
    except NameError: body = [output]

    return index(req=req,
                title=title,
                body=body,
                subtitle=subtitle,
                adminarea=3)

def perform_modifyrole(req, id_role='0', name_role='', description='put description here.', firerole_def_src='', modified='0', confirm=0):
    """form to add a new role with these values:

    name_role - name of the role to be changed

    description - optional description of the role

    firerole_def_src - optional firerole like definition of the role
    """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    ret = acca.acc_get_role_details(id_role)
    if ret and modified =='0':
        name_role = ret[1]
        description = ret[2]
        firerole_def_src = ret[3]

    if not firerole_def_src or firerole_def_src == '' or firerole_def_src is None:
        firerole_def_src = 'deny any'

    name_role = cleanstring(name_role)

    title='Modify Role'
    subtitle = 'step 1 - give values to the requested fields and confirm to modify role'

    output = """
    <form action="modifyrole" method="POST">
    <table><tbody><tr><td align='right' valign='top'>
    <input type="hidden" name="id_role" value="%s" />
    <span class="adminlabel">role name </span>
    </td><td>
    <input class="admin_wvar" type="text" name="name_role" value="%s" /> <br />
    </td></tr><tr><td align='right' valign='top'>
    <span class="adminlabel">description </span>
    </td><td>
    <textarea class="admin_wvar" rows="6" cols="80" name="description">%s</textarea> <br />
    </td></tr><tr><td align='right' valign='top'>
    <span class="adminlabel">firewall like role definition</span> [<a href="/help/admin/webaccess-admin-guide#6">?</a>]
    </td><td>
    <textarea class="admin_wvar" rows="6" cols="80" name="firerole_def_src">%s</textarea><br />
    </td></tr>
    <tr><td></td><td>See the <a href="listgroups" target="_blank">list of groups</a> for a hint about which group names you can use.</td></tr>
    <tr><td></td><td>
    <input class="adminbutton" type="submit" value="modify role" />
    <input type="hidden" name="modified" value="1" />
    </td></tr></tbody></table>
    </form>
    """ % (id_role, escape(name_role), escape(description), escape(firerole_def_src))

    if modified in [1, '1']:
        # description must be changed before submitting
        internaldesc = ''
        if description != 'put description here.':
            internaldesc = description

        text = """
        modify role with: <br />\n
        name: <strong>%s</strong> <br />""" % (name_role, )
        if internaldesc:
            text += 'description: <strong>%s</strong>?<br />' % (description, )
        text += 'firewall like role definition: <strong>%s</strong>' % firerole_def_src.replace('\n', '<br />')

        try:
            firerole_def_ser = serialize(compile_role_definition(firerole_def_src))
        except InvenioWebAccessFireroleError as msg:
            subtitle = 'step 2 - role could not be modified'
            output += '<p>sorry, could not modify role because of troubles with            its definition:<br />%s</p>' % msg
        else:
            output += createhiddenform(action="modifyrole",
                                        text=text,
                                        id_role = id_role,
                                        name_role=escape(name_role, True),
                                        description=escape(description, True),
                                        firerole_def_src=escape(firerole_def_src, True),
                                        modified=1,
                                        confirm=1)
            if confirm not in ["0", 0]:
                result = acca.acc_update_role(id_role, name_role=name_role,
                                            description=internaldesc, firerole_def_ser=firerole_def_ser, firerole_def_src=firerole_def_src)

                if result:
                    subtitle = 'step 2 - role modified'
                    output += '<p>role modified: </p>'
                    output += tupletotable(header=['id', 'role name',
                        'description', 'firewall like role definition'],
                        tuple=[(id_role, name_role, description, firerole_def_src.replace('\n', '<br />'))])
                else:
                    subtitle = 'step 2 - role could not be modified'
                    output += '<p>sorry, could not modify role, <br />please contact the administrator.</p>'


    body = [output]

    return index(req=req,
                    title=title,
                    body=body,
                    subtitle=subtitle,
                    adminarea=3)



def perform_deleterole(req, id_role="0", confirm=0):
    """select a role and show all connected information,

    users - users that can access the role.

    actions - actions with possible authorizations."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    title = 'Delete role'
    subtitle = 'step 1 - select role to delete'

    name_role = acca.acc_get_role_name(id_role=id_role)
    output = createroleselect(id_role=id_role,
                            action="deleterole",
                            step=1,
                            roles=acca.acc_get_all_roles(),
                            button="delete role")

    if id_role != "0" and name_role:
        subtitle = 'step 2 - confirm delete of role'

        output += roledetails(id_role=id_role)

        output += createhiddenform(action="deleterole",
                                text='delete role <strong>%s</strong> and all connections?' % (name_role, ),
                                id_role=id_role,
                                confirm=1)

        if confirm:
            res = acca.acc_delete_role(id_role=id_role)
            subtitle = 'step 3 - confirm role deleted'
            if res:
                output += "<p>confirm: role <strong>%s</strong> deleted.<br />" % (name_role, )
                output += "<strong>%s</strong> entries were removed.</p>" % (res, )
            else:
                output += "<p>sorry, the role could not be deleted.</p>"
    elif id_role != "0":
        output += '<p>the role has been deleted...</p>'

    return index(req=req,
                title=title,
                subtitle=subtitle,
                body=[output],
                adminarea=3)


def perform_showroledetails(req, id_role):
    """show the details of a role."""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    output = createroleselect(id_role=id_role,
                            action="showroledetails",
                            step=1,
                            roles=acca.acc_get_all_roles(),
                            button="select role")

    if id_role not in [0, '0']:
        name_role = acca.acc_get_role_name(id_role=id_role)

        output += roledetails(id_role=id_role)

        extra = """
        <dl>
        <dt><a href="modifyrole?id_role=%(id_role)s">Modify role</a><dt>
        <dd>modify the role you are seeing</dd>
        <dt><a href="addauthorization?id_role=%(id_role)s">Add new authorization</a></dt>
        <dd>add an authorization.</dd>
        <dt><a href="modifyauthorizations?id_role=%(id_role)s">Modify authorizations</a></dt>
        <dd>modify existing authorizations.</dd>
        </dl>
        <dl>
        <dt><a href="adduserrole?id_role=%(id_role)s">Connect user</a></dt>
        <dd>connect a user to role %(name_role)s.</dd>
        <dt><a href="deleteuserrole?id_role=%(id_role)s">Remove user</a></dt>
        <dd>remove a user from role %(name_role)s.</dd>
        </dl>
        """ % {'id_role' : id_role, 'name_role' : name_role}
        body = [output, extra]

    else:
        output += '<p>no details to show</p>'
        body = [output]

    return index(req=req,
                title='Show Role Details',
                subtitle='show role details',
                body=body,
                adminarea=3)


def roledetails(id_role=0):
    """create the string to show details about a role. """

    name_role = acca.acc_get_role_name(id_role=id_role)

    usershlp = acca.acc_get_role_users(id_role)
    users = []
    for (id, email, dummy) in usershlp:
        users.append([id, email, '<a href="showuserdetails?id_user=%s">show user details</a>' % (id, )])
    usertable = tupletotable(header=['id', 'email'], tuple=users, highlight_rows_p=True,
                             alternate_row_colors_p=True)

    actionshlp = acca.acc_get_role_actions(id_role)
    actions = []
    for (action_id, name, dummy) in actionshlp:
        res = acca.acc_find_possible_actions(id_role, action_id)
        if res:
            authorization_details = tupletotable(header=res[0], tuple=res[1:])
        else:
            authorization_details = 'no details to show'

        actions.append([action_id, name, authorization_details,
                        '<a href="showactiondetails?id_role=%s&amp;id_action=%s">show action details</a>' % (id_role, action_id)])

    actiontable = tupletotable(header=['id', 'name', 'parameters', ''], tuple=actions)

    # show role details
    details  = '<p>role details:</p>'
    role_details = acca.acc_get_role_details(id_role=id_role)
    if role_details[3] is None:
        role_details[3] = ''
    role_details[3] = role_details[3].replace('\n', '<br />') # Hack for preformatting firerole rules
    details += tupletotable(header=['id', 'name', 'description', 'firewall like role definition'],
                            tuple=[role_details])

    # show connected users
    details += '<p>users connected to %s:</p>' % (headerstrong(role=name_role, query=0), )
    if users:
        details += usertable
    else:
        details += '<p>no users connected.</p>'
    # show connected authorizations
    details += '<p>authorizations for %s:</p>' % (headerstrong(role=name_role, query=0), )
    if actions:
        details += actiontable
    else:
        details += '<p>no authorizations connected</p>'

    return details



def perform_adduserrole(req, id_role='0', email_user_pattern='', id_user='0', confirm=0):
    """create connection between user and role.

            id_role - id of the role to add user to

    email_user_pattern - search for users using this pattern

            id_user - id of user to add to the role. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    email_out = acca.acc_get_user_email(id_user=id_user)
    name_role = acca.acc_get_role_name(id_role=id_role)

    title = 'Connect user to role '
    subtitle = 'step 1 - select a role'

    output = createroleselect(id_role=id_role,
                            action="adduserrole",
                            step=1,
                            roles=acca.acc_get_all_roles())

    # role is selected
    if id_role != "0":
        title += name_role

        subtitle = 'step 2 - search for users'

        # remove letters not allowed in an email
        email_user_pattern = cleanstring_email(email_user_pattern)

        text  = ' <span class="adminlabel">2. search for user </span>\n'
        text += ' <input class="admin_wvar" type="text" name="email_user_pattern" value="%s" />\n' % (email_user_pattern, )

        output += createhiddenform(action="adduserrole",
                                text=text,
                                button="search for users",
                                id_role=id_role)

        # pattern is entered
        if email_user_pattern:
            # users with matching email-address
            try:
                users1 = run_sql("""SELECT id, email FROM user WHERE email<>'' AND email RLIKE %s ORDER BY email """, (email_user_pattern, ))
            except OperationalError:
                users1 = ()
            # users that are connected
            try:
                users2 = run_sql("""SELECT DISTINCT u.id, u.email
                FROM user u LEFT JOIN user_accROLE ur ON u.id = ur.id_user
                WHERE ur.id_accROLE = %s AND u.email RLIKE %s
                ORDER BY u.email """, (id_role, email_user_pattern))
            except OperationalError:
                users2 = ()

            # no users that match the pattern
            if not (users1 or users2):
                output += '<p>no qualified users, try new search.</p>'
            elif len(users1) > MAXSELECTUSERS:
                output += '<p><strong>%s hits</strong>, too many qualified users, specify more narrow search. (limit %s)</p>' % (len(users1), MAXSELECTUSERS)

            # show matching users
            else:
                subtitle = 'step 3 - select a user'

                users = []
                extrausers = []
                for (user_id, email) in users1:
                    if (user_id, email) not in users2: users.append([user_id,email,''])
                for (user_id, email) in users2:
                    extrausers.append([-user_id, email,''])

                output += createuserselect(id_user=id_user,
                                        action="adduserrole",
                                        step=3,
                                        users=users,
                                        extrausers=extrausers,
                                        button="add this user",
                                        id_role=id_role,
                                        email_user_pattern=email_user_pattern)

                try: id_user = int(id_user)
                except ValueError: pass
                # user selected already connected to role
                if id_user < 0:
                    output += '<p>users in brackets are already attached to the role, try another one...</p>'
                # a user is selected
                elif email_out:
                    subtitle = "step 4 - confirm to add user"

                    output += createhiddenform(action="adduserrole",
                                            text='add user <strong>%s</strong> to role <strong>%s</strong>?' % (email_out, name_role),
                                            id_role=id_role,
                                            email_user_pattern=email_user_pattern,
                                            id_user=id_user,
                                            confirm=1)

                    # it is confirmed that this user should be added
                    if confirm:
                        # add user
                        result = acca.acc_add_user_role(id_user=id_user, id_role=id_role)

                        if result and result[2]:
                            subtitle = 'step 5 - confirm user added'
                            output  += '<p>confirm: user <strong>%s</strong> added to role <strong>%s</strong>.</p>' % (email_out, name_role)
                        else:
                            subtitle = 'step 5 - user could not be added'
                            output += '<p>sorry, but user could not be added.</p>'

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a></dt>
    <dd>go here to add a new role.</dd>
    </dl>
    """
    if str(id_role) != "0":
        extra += """
    <dl>
    <dt><a href="deleteuserrole?id_role=%s">Remove users</a></dt>
    <dd>remove users from role %s.</dd>
    <dt><a href="showroleusers?id_role=%s">Connected users</a></dt>
    <dd>show all users connected to role %s.</dd>
    </dl>
    <dl>
    <dt><a href="addauthorization?id_role=%s">Add authorization</a></dt>
    <dd>start adding new authorizations to role %s.</dd>
    </dl>
    """ % (id_role, name_role, id_role, name_role, id_role, name_role)

    return index(req=req,
                title=title,
                subtitle=subtitle,
                body=[output, extra],
                adminarea=3)


def perform_addroleuser(req, email_user_pattern='', id_user='0', id_role='0', confirm=0):
    """delete connection between role and user.

    id_role - id of role to disconnect

    id_user - id of user to disconnect. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    email_out = acca.acc_get_user_email(id_user=id_user)
    name_role = acca.acc_get_role_name(id_role=id_role)
    # used to sort roles, and also to determine right side links
    con_roles = []
    not_roles = []

    title = 'Connect user to roles'
    subtitle = 'step 1 - search for users'

    # clean email search string
    email_user_pattern = cleanstring_email(email_user_pattern)

    text  = ' <span class="adminlabel">1. search for user </span>\n'
    text += ' <input class="admin_wvar" type="text" name="email_user_pattern" value="%s" />\n' % (email_user_pattern, )

    output = createhiddenform(action='addroleuser',
                            text=text,
                            button='search for users',
                            id_role=id_role)

    if email_user_pattern:
        subtitle = 'step 2 - select user'

        try:
            users1 = run_sql("""SELECT id, email FROM user WHERE email<>'' AND email RLIKE %s ORDER BY email """, (email_user_pattern, ))
        except OperationalError:
            users1 = ()
        users = []
        for (id, email) in users1: users.append([id, email, ''])

        # no users
        if not users:
            output += '<p>no qualified users, try new search.</p>'
        # too many users
        elif len(users) > MAXSELECTUSERS:
            output += '<p><strong>%s hits</strong>, too many qualified users, specify more narrow search. (limit %s)</p>' % (len(users), MAXSELECTUSERS)
        # ok number of users
        else:
            output += createuserselect(id_user=id_user,
                                    action='addroleuser',
                                    step=2,
                                    users=users,
                                    button='select user',
                                    email_user_pattern=email_user_pattern)

            if int(id_user):
                subtitle = 'step 3 - select role'

                # roles the user is connected to
                role_ids = acca.acc_get_user_roles(id_user=id_user)
                # all the roles, lists are sorted on the background of these...
                all_roles = acca.acc_get_all_roles()

                # sort the roles in connected and not connected roles
                for (id, name, description, dummy, dummy) in all_roles:
                    if id in role_ids: con_roles.append([-id, name, description])
                    else: not_roles.append([id, name, description])

                # create roleselect
                output += createroleselect(id_role=id_role,
                                        action='addroleuser',
                                        step=3,
                                        roles=not_roles,
                                        extraroles=con_roles,
                                        extrastamp='(connected)',
                                        button='add this role',
                                        email_user_pattern=email_user_pattern,
                                        id_user=id_user)

                if int(id_role) < 0:
                    name_role = acca.acc_get_role_name(id_role=-int(id_role))
                    output += '<p>role %s already connected to the user, try another one...<p>' % (name_role, )
                elif int(id_role):
                    subtitle = 'step 4 - confirm to add role to user'

                    output += createhiddenform(action='addroleuser',
                                            text='add role <strong>%s</strong> to user <strong>%s</strong>?' % (name_role, email_out),
                                            email_user_pattern=email_user_pattern,
                                            id_user=id_user,
                                            id_role=id_role,
                                            confirm=1)

                    if confirm:
                        # add role
                        result = acca.acc_add_user_role(id_user=id_user, id_role=id_role)

                        if result and result[2]:
                            subtitle = 'step 5 - confirm role added'
                            output  += '<p>confirm: role <strong>%s</strong> added to user <strong>%s</strong>.</p>' % (name_role, email_out)
                        else:
                            subtitle = 'step 5 - role could not be added'
                            output += '<p>sorry, but role could not be added</p>'

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a></dt>
    <dd>go here to add a new role.</dd>
    """
    if int(id_user) and con_roles:
        extra += """
    </dl>
    <dl>
    <dt><a href="deleteuserrole?id_user=%s&amp;reverse=1">Remove roles</a></dt>
    <dd>disconnect roles from user %s.</dd>
    </dl>
    """ % (id_user, email_out)
        if int(id_role):
            if int(id_role) < 0: id_role = -int(id_role)
            extra += """
            <dl>
            <dt><a href="deleteuserrole?id_role=%s">Remove users</a></dt>
            <dd>disconnect users from role %s.<dd>
            </dl>
            """ % (id_role, name_role)

    return index(req=req,
                title=title,
                subtitle=subtitle,
                body=[output, extra],
                adminarea=5)


def perform_deleteuserrole(req, id_role='0', id_user='0', reverse=0, confirm=0):
    """delete connection between role and user.

    id_role - id of role to disconnect

    id_user - id of user to disconnect. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    title = 'Remove user from role'
    email_user = acca.acc_get_user_email(id_user=id_user)
    name_role = acca.acc_get_role_name(id_role=id_role)

    output = ''

    if reverse in [0, '0']:
        adminarea = 3
        subtitle = 'step 1 - select the role'
        output += createroleselect(id_role=id_role,
                                action="deleteuserrole",
                                step=1,
                                roles=acca.acc_get_all_roles())

        if id_role != "0":
            subtitle = 'step 2 - select the user'
            output += createuserselect(id_user=id_user,
                                    action="deleteuserrole",
                                    step=2,
                                    users=acca.acc_get_role_users(id_role=id_role),
                                    id_role=id_role)

    else:
        adminarea = 5
        # show only if user is connected to a role, get users connected to roles
        users = run_sql("""SELECT DISTINCT(u.id), u.email, u.note
        FROM user u LEFT JOIN user_accROLE ur
        ON u.id = ur.id_user
        WHERE ur.id_accROLE != 'NULL' AND u.email != ''
        ORDER BY u.email """)

        has_roles = 1

        # check if the user is connected to any roles
        for (id, email, note) in users:
            if str(id) == str(id_user): break
        # user not connected to a role
        else:
            subtitle = 'step 1 - user not connected'
            output += '<p>no need to remove roles from user <strong>%s</strong>,<br />user is not connected to any roles.</p>' % (email_user, )
            has_roles, id_user = 0, '0' # stop the rest of the output below...

        # user connected to roles
        if has_roles:
            output += createuserselect(id_user=id_user,
                                    action="deleteuserrole",
                                    step=1,
                                    users=users,
                                    reverse=reverse)

            if id_user != "0":
                subtitle = 'step 2 - select the role'

                role_ids = acca.acc_get_user_roles(id_user=id_user)
                all_roles = acca.acc_get_all_roles()
                roles = []
                for (id, name, desc, dummy, dummy) in all_roles:
                    if id in role_ids: roles.append([id, name, desc])

                output += createroleselect(id_role=id_role,
                                        action="deleteuserrole",
                                        step=2,
                                        roles=roles,
                                        id_user=id_user,
                                        reverse=reverse)

    if id_role != '0' and id_user != '0':
        subtitle = 'step 3 - confirm delete of user'
        output += createhiddenform(action="deleteuserrole",
                                text='delete user %s from %s?' % (headerstrong(user=id_user), headerstrong(role=id_role)),
                                id_role=id_role,
                                id_user=id_user,
                                reverse=reverse,
                                confirm=1)

        if confirm:
            res = acca.acc_delete_user_role(id_user=id_user, id_role=id_role)
            if res:
                subtitle = 'step 4 - confirm delete of user'
                output += '<p>confirm: deleted user <strong>%s</strong> from role <strong>%s</strong>.</p>' % (email_user, name_role)
            else:
                subtitle = 'step 4 - user could not be deleted'
                output += 'sorry, but user could not be deleted<br />user is probably already deleted.'

    extra = ''
    if str(id_role) != "0":
        extra += """
        <dl>
        <dt><a href="adduserrole?id_role=%s">Connect user</a></dt>
        <dd>add users to role %s.</dd>
        """ % (id_role, name_role)
        if int(reverse):
            extra += """
            <dt><a href="deleteuserrole?id_role=%s">Remove user</a></dt>
            <dd>remove users from role %s.</dd> """ % (id_role, name_role)
        extra += '</dl>'
    if str(id_user) != "0":
        extra += """
        <dl>
        <dt><a href="addroleuser?email_user_pattern=%s&amp;id_user=%s">Connect role</a></dt>
        <dd>add roles to user %s.</dd>
        """ % (email_user, id_user, email_user)
        if not int(reverse):
            extra += """
            <dt><a href="deleteuserrole?id_user=%s&amp;email_user_pattern=%s&amp;reverse=1">Remove role</a></dt>
            <dd>remove roles from user %s.</dd> """ % (id_user, email_user, email_user)
        extra += '</dl>'

    if extra: body = [output, extra]
    else: body = [output]

    return index(req=req,
                title=title,
                subtitle=subtitle,
                body=body,
                adminarea=adminarea)


def perform_showuserdetails(req, id_user=0):
    """show the details of a user. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    if id_user not in [0, '0']:
        output = userdetails(id_user=id_user)
        email_user = acca.acc_get_user_email(id_user=id_user)

        extra = """
        <dl>
        <dt><a href="addroleuser?id_user=%s&amp;email_user_pattern=%s">Connect role</a></dt>
        <dd>connect a role to user %s.</dd>
        <dt><a href="deleteuserrole?id_user=%s&amp;reverse=1">Remove role</a></dt>
        <dd>remove a role from user %s.</dd>
        </dl>
        """ % (id_user, email_user, email_user, id_user, email_user)

        body = [output, extra]
    else:
        body = ['<p>no details to show</p>']

    return index(req=req,
                title='Show User Details',
                subtitle='show user details',
                body=body,
                adminarea=5)


def userdetails(id_user=0):
    """create the string to show details about a user. """

    # find necessary details
    email_user = acca.acc_get_user_email(id_user=id_user)

    userroles = acca.acc_get_user_roles(id_user=id_user)
    conn_roles = []

    # find connected roles
    for (id, name, desc, dummy, dummy) in acca.acc_get_all_roles():
        if id in userroles:
            conn_roles.append([id, name, desc])
            conn_roles[-1].append('<a href="showroledetails?id_role=%s">show details</a>' % (id, ))

    if conn_roles:
        # print details
        details  = '<p>roles connected to user <strong>%s</strong></p>' % (email_user, )
        details += tupletotable(header=['id', 'name', 'description', ''], tuple=conn_roles)
    else:
        details  = '<p>no roles connected to user <strong>%s</strong>.</p>' % (email_user, )

    return details

def perform_addauthorization(req, id_role="0", id_action="0", optional=0, reverse="0", confirm=0, **keywords):
    """ form to add new connection between user and role:

    id_role - role to connect

    id_action - action to connect

    reverse - role or action first? """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    # values that might get used
    name_role = acca.acc_get_role_name(id_role=id_role) or id_role
    name_action = acca.acc_get_action_name(id_action=id_action) or id_action

    optional = optional == 'on' and 1 or int(optional)

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a></dt>
    <dd>go here to add a new role.</dd>
    </dl>
    """

    # create the page according to which step the user is on
    # role -> action -> arguments
    if reverse in ["0", 0]:
        adminarea = 3
        subtitle = 'step 1 - select role'
        output = createroleselect(id_role=id_role,
                                action="addauthorization",
                                step=1,
                                roles=acca.acc_get_all_roles(),
                                reverse=reverse)

        if str(id_role) != "0":
            subtitle = 'step 2 - select action'
            rolacts = acca.acc_get_role_actions(id_role)
            allhelp = acca.acc_get_all_actions()
            allacts = []
            for r in allhelp:
                if r not in rolacts: allacts.append(r)
            output += createactionselect(id_action=id_action,
                                        action="addauthorization",
                                        step=2,
                                        actions=rolacts,
                                        extraactions=allacts,
                                        id_role=id_role,
                                        reverse=reverse)

    # action -> role -> arguments
    else:
        adminarea = 4
        subtitle = 'step 1 - select action'
        output = createactionselect(id_action=id_action,
                                    action="addauthorization",
                                    step=1,
                                    actions=acca.acc_get_all_actions(),
                                    reverse=reverse)
        if str(id_action) != "0":
            subtitle = 'step 2 - select role'
            actroles = acca.acc_get_action_roles(id_action)
            allhelp = acca.acc_get_all_roles()
            allroles = []
            for r in allhelp:
                if r not in actroles: allroles.append(r)
            output += createroleselect(id_role=id_role,
                                    action="addauthorization",
                                    step=2,
                                    roles=actroles,
                                    extraroles=allroles,
                                    id_action=id_action,
                                    reverse=reverse)

    # ready for step 3 no matter which direction we took to get here
    if id_action != "0" and id_role != "0":
        # links to adding authorizations in the other direction
        if str(reverse) == "0":
            extra += """
            <dl>
            <dt><a href="addauthorization?id_action=%s&amp;reverse=1">Add authorization</a></dt>
            <dd>add authorizations to action %s.</dd>
            </dl> """ % (id_action, name_action)
        else:
            extra += """
            <dl>
            <dt><a href="addauthorization?id_role=%s">Add authorization</a></dt>
            <dd>add authorizations to role %s.</dd>
            </dl> """ % (id_role, name_role)

        subtitle = 'step 3 - enter values for the keywords\n'

        output += """
        <form action="addauthorization" method="POST">
        <input type="hidden" name="id_role" value="%s">
        <input type="hidden" name="id_action" value="%s">
        <input type="hidden" name="reverse" value="%s">
        """  % (id_role, id_action, reverse)

        # the actions argument keywords
        res_keys = acca.acc_get_action_keywords(id_action=id_action)

        # res used to display existing authorizations
        # res used to determine if showing "create connection without arguments"
        res_auths = acca.acc_find_possible_actions(id_role, id_action)

        if not res_keys:
            # action without arguments
            if not res_auths:
                output += """
                <input type="hidden" name="confirm" value="1">
                create connection between %s?
                <input class="adminbutton" type="submit" value="confirm">
                </form>
                """ % (headerstrong(role=name_role, action=name_action, query=0), )
            else:
                output += '<p><strong>connection without arguments is already created.</strong></p>'

        else:
            # action with arguments
            optionalargs = acca.acc_get_action_is_optional(id_action=id_action)

            output += '<span class="adminlabel">3. authorized arguments</span><br />'
            if optionalargs:
                # optional arguments
                output += """
                <p>
                <input type="radio" name="optional" value="1" %s />
                connect %s to %s for any arguments <br />
                <input type="radio" name="optional" value="0" %s />
                connect %s to %s for only these argument cases:
                </p>
                """ % (optional and 'checked="checked"' or '', name_role, name_action, not optional and 'checked="checked"' or '', name_role, name_action)

            # list the arguments
            allkeys = 1
            for key in res_keys:
                output += '<span class="adminlabel" style="margin-left: 30px;">%s </span>\n <input class="admin_wvar" type="text" name="%s"' % (key, key)
                try:
                    val = keywords[key] # = cleanstring_argumentvalue(keywords[key])
                    if val: output += 'value="%s" ' % (escape(val, True), )
                    else: allkeys = 0
                except KeyError: allkeys = 0
                output += ' /> <br />\n'
            output = output[:-8] + ' <input class="adminbutton" type="submit" value="create authorization -->" />\n'
            output += '</form>\n'

            # ask for confirmation
            if str(allkeys) != "0" or optional:
                keys = keywords.keys()
                keys.reverse()
                subtitle = 'step 4 - confirm add of authorization\n'

                text = """
                create connection between <br />
                %s <br />
                """ % (headerstrong(role=name_role, action=name_action, query=0), )

                if optional:
                    text += 'withouth arguments'
                    keywords = {}
                else:
                    for key in keys:
                        text += '<strong>%s</strong>: %s \n' % (escape(key), escape(keywords[key]))

                output += createhiddenform(action="addauthorization",
                                        text=text,
                                        id_role=id_role,
                                        id_action=id_action,
                                        reverse=reverse,
                                        confirm=1,
                                        optional=optional,
                                        **keywords)

        # show existing authorizations, found authorizations further up in the code...
        # res_auths = acca.acc_find_possible_actions(id_role, id_action)
        output += '<p>existing authorizations:</p>'
        if res_auths:
            output += tupletotable(header=res_auths[0], tuple=res_auths[1:])
            # shortcut to modifying authorizations
            extra += """
            <dl>
            <dt><a href="modifyauthorizations?id_role=%s&amp;id_action=%s&amp;reverse=%s">Modify authorizations</a></dt>
            <dd>modify the existing authorizations.</dd>
            </dl> """ % (id_role, id_action, reverse)

        else:   output += '<p>no details to show</p>'


    # user confirmed to add entries
    if confirm:
        subtitle = 'step 5 - confirm authorization added'
        res1 = acca.acc_add_authorization(name_role=name_role,
                                        name_action=name_action,
                                        optional=optional,
                                        **keywords)

        if res1:
            res2 = acca.acc_find_possible_actions(id_role, id_action)
            arg = res1[0][3] # the arglistid
            new = [res2[0]]
            for row in res2[1:]:
                if int(row[0]) == int(arg): new.append(row)

            newauths = tupletotable(header=new[0], tuple=new[1:])
            newentries = tupletotable(header=['role id', 'action id', 'argument id', '#'], tuple=res1)

            st = 'style="vertical-align: top"'
            output += """
            <p>new authorization and entries:</p>
            <table><tr>
            <td class="admintd" %s>%s</td>
            <td class="admintd" %s>%s</td>
            </tr></table> """ % (st, newauths, st, newentries)

        else: output += '<p>sorry, authorization could not be added,<br />it probably already exists</p>'

    # trying to put extra link on the right side
    try: body = [output, extra]
    except NameError: body = [output]

    return index(req=req,
                title = 'Create entry for new authorization',
                subtitle=subtitle,
                body=body,
                adminarea=adminarea)


def perform_deleteroleaction(req, id_role="0", id_action="0", reverse=0, confirm=0):
    """delete all connections between a role and an action.

    id_role - id of the role

    id_action - id of the action

    reverse - 0: ask for role first
                1: ask for action first"""

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    title = 'Remove action from role '

    if reverse in ["0", 0]:
        # select role -> action
        adminarea = 3
        subtitle = 'step 1 - select a role'
        output  = createroleselect(id_role=id_role,
                                action="deleteroleaction",
                                step=1,
                                roles=acca.acc_get_all_roles(),
                                reverse=reverse)

        if id_role != "0":
            rolacts = acca.acc_get_role_actions(id_role=id_role)
            subtitle = 'step 2 - select the action'
            output += createactionselect(id_action=id_action,
                                        action="deleteroleaction",
                                        step=2,
                                        actions=rolacts,
                                        reverse=reverse,
                                        id_role=id_role,
                                        button="remove connection and all authorizations")
    else:
        # select action -> role
        adminarea = 4
        subtitle = 'step 1 - select an action'
        output = createactionselect(id_action=id_action,
                                    action="deleteroleaction",
                                    step=1,
                                    actions=acca.acc_get_all_actions(),
                                    reverse=reverse)

        if id_action != "0":
            actroles = acca.acc_get_action_roles(id_action=id_action)
            subtitle = 'step 2 - select the role'
            output += createroleselect(id_role=id_role,
                                    action="deleteroleaction",
                                    step=2,
                                    roles=actroles,
                                    button="remove connection and all authorizations",
                                    id_action=id_action,
                                    reverse=reverse)

    if id_action != "0" and id_role != "0":
        subtitle = 'step 3 - confirm to remove authorizations'
        # ask for confirmation

        res = acca.acc_find_possible_actions(id_role, id_action)

        if res:
            output += '<p>authorizations that will be deleted:</p>'
            output += tupletotable(header=res[0], tuple=res[1:])

            output += createhiddenform(action="deleteroleaction",
                                    text='remove %s from %s' % (headerstrong(action=id_action), headerstrong(role=id_role)),
                                    confirm=1,
                                    id_role=id_role,
                                    id_action=id_action,
                                    reverse=reverse)
        else:
            output += 'no authorizations'

        # confirmation is given
        if confirm:
            subtitle = 'step 4 - confirm authorizations removed '
            res = acca.acc_delete_role_action(id_role=id_role, id_action=id_action)
            if res:
                output += '<p>confirm: removed %s from %s<br />' % (headerstrong(action=id_action), headerstrong(role=id_role))
                output += '<strong>%s</strong> entries were removed.</p>' % (res, )
            else:
                output += '<p>sorry, no entries could be removed.</p>'

    return index(req=req,
                title=title,
                subtitle=subtitle,
                body=[output],
                adminarea=adminarea)


def perform_modifyauthorizations(req, id_role="0", id_action="0", reverse=0, confirm=0, errortext='', sel='', authids=[]):
    """given ids of a role and an action, show all possible action combinations
    with checkboxes and allow user to access other functions.

    id_role - id of the role

    id_action - id of the action

    reverse - 0: ask for role first
                1: ask for action first

        sel - which button and modification that is selected

    errortext - text to print when no connection exist between role and action

    authids - ids of checked checkboxes """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0: return mustloginpage(req, auth_message)

    name_role = acca.acc_get_role_name(id_role)
    name_action = acca.acc_get_action_name(id_action)

    output = ''

    try: id_role, id_action, reverse = int(id_role), int(id_action), int(reverse)
    except ValueError: pass

    extra = """
    <dl>
    <dt><a href="addrole">Create new role</a></dt>
    <dd>go here to add a new role.</dd>
    </dl>
    """
    if id_role or id_action:
        extra += '\n<dl>\n'
        if id_role and id_action:
            extra += """
            <dt><a href="addauthorization?id_role=%s&amp;id_action=%s&amp;reverse=%s">Add authorizations</a></dt>
            <dd>add an authorization to the existing ones.</dd> """ % (id_role, id_action, reverse)
        if id_role:
            extra += """
            <dt><a href="addauthorization?id_role=%s">Add authorizations</a></dt>
            <dd>add to role %s.</dd> """ % (id_role, name_role)
        if id_action:
            extra += """
            <dt><a href="addauthorization?id_action=%s&amp;reverse=1">Add authorizations</a></dt>
            <dd>add to action %s.</dd> """ % (id_action, name_action)
        extra += '\n</dl>\n'


    if not reverse:
        # role -> action
        adminarea = 3
        subtitle = 'step 1 - select the role'
        output += createroleselect(id_role=str(id_role),
                                action="modifyauthorizations",
                                step=1,
                                roles=acca.acc_get_all_roles(),
                                reverse=reverse)

        if id_role:
            rolacts = acca.acc_get_role_actions(id_role=id_role)
            subtitle = 'step 2 - select the action'
            output += createactionselect(id_action=str(id_action),
                                        action="modifyauthorizations",
                                        step=2,
                                        actions=rolacts,
                                        id_role=id_role,
                                        reverse=reverse)
    else:
        adminarea = 4
        # action -> role
        subtitle = 'step 1 - select the action'
        output += createactionselect(id_action=str(id_action),
                                    action="modifyauthorizations",
                                    step=1,
                                    actions=acca.acc_get_all_actions(),
                                    reverse=reverse)
        if id_action:
            actroles = acca.acc_get_action_roles(id_action=id_action)
            subtitle = 'step 2 - select the role'
            output += createroleselect(id_role=str(id_role),
                                    action="modifyauthorizations",
                                    step=2,
                                    roles=actroles,
                                    id_action=id_action,
                                    reverse=reverse)

    if errortext: output += '<p>%s</p>' % (errortext, )

    if id_role and id_action:
        # adding to main area
        if type(authids) is not list: authids = [authids]
        subtitle = 'step 3 - select groups and modification'

        # get info
        res = acca.acc_find_possible_actions(id_role, id_action)

        # clean the authids
        hiddenids = []
        if sel in ['delete selected']:
            hiddenids = authids[:]
        elif sel in ['split groups', 'merge groups']:
            for authid in authids:
                arghlp = res[int(authid)][0]
                if authid not in hiddenids and arghlp not in [-1, '-1', 0, '0']: hiddenids.append(authid)
            authids = hiddenids[:]

        if confirm:
            # do selected modification and output with new authorizations
            if sel == 'split groups':
                res = splitgroups(id_role, id_action, authids)
            elif sel == 'merge groups':
                res = mergegroups(id_role, id_action, authids)
            elif sel == 'delete selected':
                res = deleteselected(id_role, id_action, authids)
            authids = []
            res = acca.acc_find_possible_actions(id_role, id_action)
            output += 'authorizations after <strong>%s</strong>.<br />\n' % (sel, )

        elif sel and authids:
            output += 'confirm choice of authorizations and modification.<br />\n'
        else:
            output += 'select authorizations and perform modification.<br />\n'

        if not res:
            errortext = 'all connections deleted, try different '
            if reverse in ["0", 0]:
                return perform_modifyauthorizations(req=req, id_role=id_role, errortext=errortext + 'action.')
            else:
                return perform_modifyauthorizations(req=req, id_action=id_action, reverse=reverse, errortext=errortext + 'role.')

        # display
        output += modifyauthorizationsmenu(id_role, id_action, header=res[0], tuple=res[1:], checked=authids, reverse=reverse)

        if sel and authids:
            subtitle = 'step 4 - confirm to perform modification'
            # form with hidden authids
            output += '<form action="%s" method="POST">\n' % ('modifyauthorizations', )

            for hiddenid in hiddenids:
                output += '<input type="hidden" name="authids" value="%s" />\n' % (hiddenid, )

            # choose what to do
            if sel == 'split groups':
                output += '<p>split groups containing:</p>'
            elif sel == 'merge groups':
                output += '<p>merge groups containing:</p>'
            elif sel == 'delete selected':
                output += '<p>delete selected entries:</p>'

            extracolumn  = '<input type="checkbox" name="confirm" value="1" />\n'
            extracolumn += '<input class="adminbutton" type="submit" value="confirm" />\n'

            # show the entries here...
            output += tupletotable_onlyselected(header=res[0],
                                                tuple=res[1:],
                                                selected=hiddenids,
                                                extracolumn=extracolumn)

            output += '<input type="hidden" name="id_role" value="%s" />\n' \
                % (id_role, )
            output += '<input type="hidden" name="id_action" value="%s" />\n' \
                % (id_action, )
            output += '<input type="hidden" name="sel" value="%s" />\n' \
                % (sel, )
            output += '<input type="hidden" name="reverse" value="%s" />\n' \
                % (reverse, )
            output += '</form>'

        # tried to perform modification without something selected
        elif sel and not authids and not confirm:
            output += '<p>no valid groups selected</p>'

    # trying to put extra link on the right side
    try:
        body = [output, extra]
    except NameError:
        body = [output]

    # Display the page
    return index(req=req,
                title='Modify Authorizations',
                subtitle=subtitle,
                body=body,
                adminarea=adminarea)


def modifyauthorizationsmenu(id_role, id_action, tuple=[], header=[],
        checked=[], reverse=0):
    """create table with header and checkboxes, used for multiple choice.
    makes use of tupletotable to add the actual table

    id_role - selected role, hidden value in the form

    id_action - selected action, hidden value in the form

        tuple - all rows to be put in the table (with checkboxes)

    header - column headers, empty strings added at start and end

    checked - ids of rows to be checked """

    if not tuple:
        return 'no authorisations...'

    argnum = len(acca.acc_get_action_keywords(id_action=id_action))

    tuple2 = []
    for t in tuple:
        tuple2.append(t[:])

    tuple2 = addcheckboxes(datalist=tuple2, name='authids', startindex=1,
        checked=checked)

    hidden  = '<input type="hidden" name="id_role" value="%s" /> \n' \
        % (id_role, )
    hidden += '<input type="hidden" name="id_action" value="%s" /> \n' \
        % (id_action, )
    hidden += '<input type="hidden" name="reverse" value="%s" /> \n' \
        % (reverse, )


    button = '<input type="submit" class="adminbutton" ' \
        'value="delete selected" name="sel" />\n'
    if argnum > 1:
        button += '<input type="submit" class="adminbutton" ' \
            'value="split groups" name="sel" />\n'
        button += '<input type="submit" class="adminbutton" ' \
            'value="merge groups" name="sel" />\n'

    hdrstr = ''
    for h in [''] + header + ['']:
        hdrstr += '  <th class="adminheader">%s</th>\n' % (h, )
    if hdrstr:
        hdrstr = ' <tr>\n%s\n </tr>\n' % (hdrstr, )

    output  = '<form action="modifyauthorizations" method="POST">\n'
    output += '<table class="admin_wvar_nomargin"> \n'
    output += hdrstr
    output += '<tr><td>%s</td></tr>\n' % (hidden, )

    align = ['admintdleft'] * len(tuple2[0])
    try:
        align[1] = 'admintdright'
    except IndexError:
        pass

    output += '<tr>'
    for i in range(len(tuple2[0])):
        output += '<td class="%s">%s</td>\n' % (align[i], tuple2[0][i])
    output += '<td rowspan="%s" style="vertical-align: bottom">\n%s\n</td>\n' \
        % (len(tuple2), button)

    output += '</tr>\n'
    for row in tuple2[1:]:
        output += ' <tr>\n'
        for i in range(len(row)):
            output += '<td class="%s">%s</td>\n' % (align[i], row[i])
        output += ' </tr>\n'

    output += '</table>\n</form>\n'

    return output


def splitgroups(id_role=0, id_action=0, authids=[]):
    """get all the old ones, gather up the arglistids find a list of
    arglistidgroups to be split, unique get all actions in groups outside
    of the old ones, (old arglistid is allowed).

    show them like in showselect. """

    if not id_role or not id_action or not authids:
        return 0

    # find all the actions
    datalist = acca.acc_find_possible_actions(id_role, id_action)

    if type(authids) is str:
        authids = [authids]
    for i in range(len(authids)):
        authids[i] = int(authids[i])

    # argumentlistids of groups to be split
    splitgrps = []
    for authid in authids:
        hlp = datalist[authid][0]
        if hlp not in splitgrps and authid in range(1, len(datalist)):
            splitgrps.append(hlp)

    # split groups and return success or failure
    result = 1
    for splitgroup in splitgrps:
        result = 1 and acca.acc_split_argument_group(id_role, id_action,
            splitgroup)

    return result


def mergegroups(id_role=0, id_action=0, authids=[]):
    """get all the old ones, gather up the argauthids find a list
    of arglistidgroups to be split, unique get all actions in groups
    outside of the old ones, (old arglistid is allowed).

    show them like in showselect."""

    if not id_role or not id_action or not authids:
        return 0

    datalist = acca.acc_find_possible_actions(id_role, id_action)

    if type(authids) is str:
        authids = [authids]
    for i in range(len(authids)):
        authids[i] = int(authids[i])

    # argumentlistids of groups to be merged
    mergegroups = []
    for authid in authids:
        hlp = datalist[authid][0]
        if hlp not in mergegroups and authid in range(1, len(datalist)):
            mergegroups.append(hlp)

    # merge groups and return success or failure
    if acca.acc_merge_argument_groups(id_role, id_action, mergegroups):
        return 1
    else:
        return 0



def deleteselected(id_role=0, id_action=0,  authids=[]):
    """delete checked authorizations/possible actions, ids in authids.

    id_role - role to delete from

    id_action - action to delete from

    authids - listids for which possible actions to delete."""

    if not id_role or not id_action or not authids:
        return 0

    if type(authids) in [str, int]:
        authids = [authids]
    for i in range(len(authids)):
        authids[i] = int(authids[i])

    result = acca.acc_delete_possible_actions(id_role=id_role,
                                            id_action=id_action,
                                            authids=authids)

    return result

def headeritalic(**ids):
    """transform keyword=value pairs to string with value in italics.

    **ids - a dictionary of pairs to create string from """

    output = ''
    value = ''
    table = ''

    for key in ids.keys():
        if key in ['User', 'user']:
            value, table = 'email', 'user'
        elif key in ['Role', 'role']:
            value, table = 'name', 'accROLE'
        elif key in ['Action', 'action']:
            value, table = 'name', 'accACTION'
        else:
            if output:
                output += ' and '
            output += ' %s <i>%s</i>' % (key, ids[key])
            continue

        res = run_sql("""SELECT %%s FROM %s WHERE id = %%s""" % wash_table_column_name(table), (value, ids[key])) # kwalitee: disable=sql

        if res:
            if output:
                output += ' and '
            output += ' %s <i>%s</i>' % (key, res[0][0])

    return output


def headerstrong(query=1, **ids):
    """transform keyword=value pairs to string with value in strong text.

    **ids - a dictionary of pairs to create string from

    query - 1 -> try to find names to ids of role, user and action.
            0 -> do not try to find names, use the value passed on """

    output = ''
    value = ''
    table = ''

    for key in ids.keys():
        if key in ['User', 'user']:
            value, table = 'email', 'user'
        elif key in ['Role', 'role']:
            value, table = 'name', 'accROLE'
        elif key in ['Action', 'action']:
            value, table = 'name', 'accACTION'
        else:
            if output:
                output += ' and '
            output += ' %s <strong>%s</strong>' % (key, ids[key])
            continue

        if query:
            res = run_sql("""SELECT %%s FROM %s WHERE id = %%s""" % wash_table_column_name(table), (value, ids[key])) # kwalitee: disable=sql
            if res:
                if output:
                    output += ' and '
                output += ' %s <strong>%s</strong>' % (key, res[0][0])
        else:
            if output:
                output += ' and '
            output += ' %s <strong>%s</strong>' % (key, ids[key])

    return output


def startpage():
    """create the menu for the startpage"""

    body = """
<table class="admin_wvar" width="100%" summary="">
<thead>
<tr>
<th class="adminheaderleft">selection for WebAccess Admin</th>
</tr>
</thead>
<tbody>
<tr>
<td>
    <dl>
    <dt><a href="webaccessadmin.py/rolearea">Role Area</a></dt>
    <dd>main area to configure administration rights and authorization rules.</dd>
    <dt><a href="webaccessadmin.py/actionarea">Action Area</a></dt>
    <dd>configure administration rights with the actions as starting point.</dd>
    <dt><a href="webaccessadmin.py/userarea">User Area</a></dt>
    <dd>configure administration rights with the users as starting point.</dd>
    <dt><a href="webaccessadmin.py/resetarea">Reset Area</a></dt>
    <dd>reset roles, actions and authorizations.</dd>
    <dt><a href="webaccessadmin.py/manageaccounts">Manage accounts Area</a></dt>
    <dd>manage user accounts.</dd>
    <dt><a href="webaccessadmin.py/delegate_startarea">Delegate Rights - With Restrictions</a></dt>
    <dd>delegate your rights for some roles.</dd>
    </dl>
</td>
</tr>
</tbody>
</table>"""

    return body

def rankarea():
    return "Rankmethod area"

def perform_simpleauthorization(req, id_role=0, id_action=0):
    """show a page with simple overview of authorizations between a
    connected role and action. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    res = acca.acc_find_possible_actions(id_role, id_action)
    if res:
        extra = createhiddenform(action='modifyauthorizations',
            button='modify authorizations',
            id_role=id_role,
            id_action=id_action)

        output  = '<p>authorizations for %s:</p>' \
            % (headerstrong(action=id_action, role=id_role), )
        output += tupletotable(header=res[0], tuple=res[1:], extracolumn=extra)
    else:
        output = 'no details to show'

    return index(req=req,
                title='Simple authorization details',
                subtitle='simple authorization details',
                body=[output],
                adminarea=3)


def perform_showroleusers(req, id_role=0):
    """show a page with simple overview of a role and connected users. """

    (auth_code, auth_message) = is_adminuser(req)
    if auth_code != 0:
        return mustloginpage(req, auth_message)

    res = acca.acc_get_role_users(id_role=id_role)
    name_role = acca.acc_get_role_name(id_role=id_role)

    if res:
        users = []
        for (role_id, name, dummy) in res:
            users.append([role_id, name, '<a href="showuserdetails?'
                'id_user=%s">show user details</a>' % (role_id, )])
        output  = '<p>users connected to %s:</p>' \
            % (headerstrong(role=id_role), )
        output += tupletotable(header=['id', 'name', ''], tuple=users)
    else:
        output = 'no users connected to role <strong>%s</strong>' \
            % (name_role, )

    extra = """
    <dl>
    <dt><a href="adduserrole?id_role=%s">Connect user</a></dt>
    <dd>connect users to the role.</dd>
    </dl>
    """ % (id_role, )

    return index(req=req,
                title='Users connected to role %s' % (name_role, ),
                subtitle='simple details',
                body=[output, extra],
                adminarea=3)





def createselect(id_input="0", label="", step=0, name="",
                action="", list=[], extralist=[], extrastamp='',
                button="", **hidden):
    """create form with select and hidden values

            id - the one to choose as selected if exists

        label - label shown to the left of the select

        name - the name of the select on which to reference it

        list - primary list to select from

    extralist - list of options to be put in paranthesis

    extrastamp - stamp extralist entries with this if not ''
                usually paranthesis around the entry

        button - the value/text to be put on the button

    **hidden - name=value pairs to be put as hidden in the form. """

    step = step and '%s. ' % step or ''

    output  = '<form action="%s" method="POST">\n' % (action, )
    output += ' <span class="adminlabel">%s</span>\n' % (step + label, )
    output += ' <select name="%s" class="admin_w200">\n' % (name, )
    if not list and not extralist:
        output += '  <option value="0">*** no %ss to select from ***' \
            '</option>\n' % (label.split()[-1], )
    else:
        output += '  <option value="0">*** %s ***</option>\n' % (label, )
        for elem in list:
            elem_id = elem[0]
            email = elem[1]
            if str(elem_id) == id_input:
                output += '  <option value="%s" selected="selected">' \
                    '%s</option>\n' % (elem_id, email)
            else:
                output += '  <option value="%s">%s</option>\n' \
                    % (elem_id, email)
        for elem in extralist:
            elem_id = elem[0]
            email = elem[1]
            if str(elem_id) == id_input:
                if not extrastamp:
                    output += '  <option value="%s" selected="selected">' \
                        '(%s)</option>\n' % (elem_id, email)
                else:
                    output += '  <option value="%s">%s %s</option>\n' \
                        % (elem_id, email, extrastamp)
            elif not extrastamp:
                output += '  <option value="%s">(%s)</option>\n' \
                    % (elem_id, email)
            else:
                output += '  <option value="%s">%s %s</option>\n' \
                    % (elem_id, email, extrastamp)

    output += ' </select>\n'
    for key in hidden.keys():
        output += ' <input type="hidden" name="%s" value="%s" />\n' \
            % (key, hidden[key])
    output += ' <input class="adminbutton" type="submit" value="%s" />\n' \
        % (button, )
    output += '</form>\n'

    return output


def createactionselect(id_action="0", label="select action", step=0,
        name="id_action", action="", actions=[], extraactions=[],
        extrastamp='', button="select action", **hidden):
    """create a select for roles in a form. see createselect."""

    return createselect(id_input=id_action, label=label, step=step, name=name,
        action=action, list=actions, extralist=extraactions,
        extrastamp=extrastamp, button=button, **hidden)


def createroleselect(id_role="0", label="select role", step=0, name="id_role",
        action="", roles=[], extraroles=[], extrastamp='',
        button="select role", **hidden):
    """create a select for roles in a form. see createselect."""

    return createselect(id_input=id_role, label=label, step=step, name=name,
        action=action, list=roles, extralist=extraroles, extrastamp=extrastamp,
        button=button, **hidden)


def createuserselect(id_user="0", label="select user", step=0, name="id_user",
        action="", users=[], extrausers=[], extrastamp='(connected)',
        button="select user", **hidden):
    """create a select for users in a form.see createselect."""

    return createselect(id_input=id_user, label=label, step=step, name=name,
        action=action, list=users, extralist=extrausers, extrastamp=extrastamp,
        button=button, **hidden)


def cleanstring(txt='', comma=0):
    """clean all the strings before submitting to access control admin.
    remove characters not letter, number or underscore, also remove leading
    underscores and numbers. return cleaned string.

    str - string to be cleaned

    comma - 1 -> allow the comma to divide multiple arguments
            0 -> wash commas as well """

    # remove not allowed characters
    txt = re.sub(r'[^a-zA-Z0-9_,]', '', txt)

    # split string on commas
    items = txt.split(',')
    txt = ''
    for item in items:
        if not item:
            continue
        if comma and txt:
            txt += ','
        # create valid variable names
        txt += re.sub(r'^([0-9_])*', '', item)

    return txt


def cleanstring_argumentvalue(txt=''):
    """clean the value of an argument before submitting it.
    allowed characters: a-z A-Z 0-9 _ * and space

    txt - string to be cleaned """

    # remove not allowed characters
    txt = re.sub(r'[^a-zA-Z0-9_ *.]', '', txt)
    # trim leading and ending spaces
    txt = re.sub(r'^ *| *$', '', txt)

    return txt


def cleanstring_email(txt=''):
    """clean the string and return a valid email address.

    txt - string to be cleaned """

    # remove not allowed characters
    txt = re.sub(r'[^a-zA-Z0-9_.@-]', '', txt)

    return txt


def check_email(txt=''):
    """control that submitted emails are correct.
    this little check is not very good, but better than nothing. """

    r = re.compile(r'(.)+\@(.)+\.(.)+')
    return r.match(txt) and 1 or 0

def send_account_activated_message(account_email, send_to, password, ln=CFG_SITE_LANG):
    """Send an email to the address given by send_to about the new activated
    account."""
    _ = gettext_set_language(ln)
    sub = _("Your account on '%(x_name)s' has been activated", x_name=CFG_SITE_NAME)
    body = _("Your account earlier created on '%(x_name)s' has been activated:",
             x_name=CFG_SITE_NAME) + '\n\n'
    body += '   ' + _("Username/Email:") + " %s\n" % account_email
    body += '   ' + _("Password:") + " %s\n" % ("*" * len(str(password)))
    body += "\n---------------------------------"
    body += "\n%s" % CFG_SITE_NAME

    return send_email(CFG_SITE_SUPPORT_EMAIL, send_to, sub, body, header='')

def send_new_user_account_warning(new_account_email, send_to, password, ln=CFG_SITE_LANG):
    """Send an email to the address given by send_to about the new account
    new_account_email."""
    _ = gettext_set_language(ln)
    sub = _("Account created on '%(x_name)s'", x_name=CFG_SITE_NAME)
    body = _("An account has been created for you on '%(x_name)s':", x_name=CFG_SITE_NAME) + '\n\n'
    body += '   ' + _("Username/Email:") + " %s\n" % new_account_email
    body += '   ' + _("Password:") + " %s\n" % ("*" * len(str(password)))
    body += "\n---------------------------------"
    body += "\n%s" % CFG_SITE_NAME

    return send_email(CFG_SITE_SUPPORT_EMAIL, send_to, sub, body, header='')

def send_account_rejected_message(new_account_email, send_to, ln=CFG_SITE_LANG):
    """Send an email to the address given by send_to about the new account
    new_account_email."""
    _ = gettext_set_language(ln)
    sub = _("Account rejected on '%(x_name)s'", x_name=CFG_SITE_NAME)
    body = _("Your request for an account has been rejected on '%(x_name)s':",
             x_name=CFG_SITE_NAME) + '\n\n'
    body += '   ' + _("Username/Email: %(x_email)s", x_email=new_account_email) + "\n"
    body += "\n---------------------------------"
    body += "\n%s" % CFG_SITE_NAME

    return send_email(CFG_SITE_SUPPORT_EMAIL, send_to, sub, body, header='')

def send_account_deleted_message(new_account_email, send_to, ln=CFG_SITE_LANG):
    """Send an email to the address given by send_to about the new account
    new_account_email."""
    _ = gettext_set_language(ln)
    sub = _("Account deleted on '%(x_name)s'", x_name=CFG_SITE_NAME)
    body = _("Your account on '%(x_name)s' has been deleted:", x_name=CFG_SITE_NAME) + '\n\n'
    body += '   ' + _("Username/Email:") + " %s\n" % new_account_email
    body += "\n---------------------------------"
    body += "\n%s" % CFG_SITE_NAME

    return send_email(CFG_SITE_SUPPORT_EMAIL, send_to, sub, body, header='')
