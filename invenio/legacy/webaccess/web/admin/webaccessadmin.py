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

from invenio.config import CFG_SITE_LANG
import invenio.modules.access.admin_lib as wal
from invenio.modules.access.local_config import CFG_ACC_EMPTY_ROLE_DEFINITION_SRC
# reload(wal)
# from invenio.modules.access.admin_lib import index

index = wal.index

def rolearea(req, grep='', ln=CFG_SITE_LANG):
    """create the role area menu page."""

    return wal.perform_rolearea(req=req, grep=grep)


def actionarea(req, grep='', ln=CFG_SITE_LANG):
    """create the role area menu page."""

    return wal.perform_actionarea(req=req, grep=grep)

def userarea(req, email_user_pattern='', ln=CFG_SITE_LANG):
    """create the user area menu page. """

    return wal.perform_userarea(req=req,
                                email_user_pattern=email_user_pattern)

def listgroups(req, ln=CFG_SITE_LANG):
    return wal.perform_listgroups(req=req)

def resetarea(req, ln=CFG_SITE_LANG):
    """create the role area menu page."""

    return wal.perform_resetarea(req=req)


def resetdefaultsettings(req, superusers=[], confirm=0, ln=CFG_SITE_LANG):
    """create the reset default settings page. """

    return wal.perform_resetdefaultsettings(req=req,
                                            superusers=superusers,
                                            confirm=confirm)


def adddefaultsettings(req, superusers=[], confirm=0, ln=CFG_SITE_LANG):
    """create the add default settings page. """

    return wal.perform_adddefaultsettings(req=req,
                                          superusers=superusers,
                                          confirm=confirm)


def manageaccounts(req, mtype='', content='', confirm=0, ln=CFG_SITE_LANG):
    """enable, disable and edit accounts"""

    return wal.perform_manageaccounts(req=req, mtype=mtype, content=content, confirm=confirm)

def modifyaccountstatus(req, userID, email_user_pattern='', limit_to=-1, maxpage=25, page=1, callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """enable or disable account"""

    return wal.perform_modifyaccountstatus(req=req, userID=userID, email_user_pattern=email_user_pattern, limit_to=limit_to, maxpage=maxpage, page=page, callback=callback, confirm=confirm)

def modifypreferences(req, userID, login_method='', callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """modify the preferences of an account"""

    return wal.perform_modifypreferences(req=req, userID=userID, login_method=login_method, callback=callback, confirm=confirm)

def modifyapikeydata(req, userID, keyID, status, callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """modify the status of a REST API key"""

    return wal.perform_modifyapikeydata(req=req, userID=userID, keyID=keyID, status=status, callback=callback, confirm=confirm)

def modifylogindata(req, userID, nickname='', email='', password='', callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """modify the email/password of an account"""

    return wal.perform_modifylogindata(req=req, userID=userID, nickname=nickname, email=email, password=password, callback=callback, confirm=confirm)

def rejectaccount(req, userID, email_user_pattern='', limit_to=-1, maxpage=25, page=1, callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """Set account inactive, delete it and send email to the owner."""

    return wal.perform_rejectaccount(req=req, userID=userID, email_user_pattern=email_user_pattern, limit_to=limit_to, maxpage=maxpage, page=page, callback=callback, confirm=confirm)

def deleteaccount(req, userID, callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """delete account"""

    return wal.perform_deleteaccount(req=req, userID=userID, callback=callback, confirm=confirm)

def createaccount(req, email='', password='', callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """create account"""

    return wal.perform_createaccount(req=req, email=email, password=password, callback=callback, confirm=confirm)

def editaccount(req, userID, mtype='', content='', callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """edit account. """

    return wal.perform_editaccount(req=req, userID=userID, mtype=mtype, content=content, callback=callback, confirm=confirm)

def becomeuser(req, userID='', callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """edit account. """
    return wal.perform_becomeuser(req=req, userID=userID, callback=callback, confirm=confirm)

def modifyaccounts(req, email_user_pattern='', limit_to=-1, maxpage=25, page=1, callback='yes', confirm=0, ln=CFG_SITE_LANG):
    """Modify accounts. """

    return wal.perform_modifyaccounts(req=req, email_user_pattern=email_user_pattern, limit_to=limit_to, maxpage=maxpage, page=page, callback=callback,confirm=confirm)

def delegate_startarea(req, ln=CFG_SITE_LANG):
    """add info here"""

    return wal.perform_delegate_startarea(req=req)


def delegate_adminsetup(req, id_role_admin=0, id_role_delegate=0, confirm=0, ln=CFG_SITE_LANG):
    """add info here"""

    return wal.perform_delegate_adminsetup(req=req,
                                           id_role_admin=id_role_admin,
                                           id_role_delegate=id_role_delegate,
                                           confirm=confirm)


def delegate_adduserrole(req, id_role=0, email_user_pattern='', id_user=0, confirm=0, ln=CFG_SITE_LANG):
    """add info here"""

    return wal.perform_delegate_adduserrole(req=req,
                                            id_role=id_role,
                                            email_user_pattern=email_user_pattern,
                                            id_user=id_user,
                                            confirm=confirm)


def delegate_deleteuserrole(req, id_role=0, id_user=0, confirm=0, ln=CFG_SITE_LANG):
    """add info here"""

    return wal.perform_delegate_deleteuserrole(req=req,
                                               id_role=id_role,
                                               id_user=id_user,
                                               confirm=confirm)


def addrole(req, name_role='', description='put description here.', firerole_def_src=CFG_ACC_EMPTY_ROLE_DEFINITION_SRC, confirm=0, ln=CFG_SITE_LANG):
    """form to add a new role with these values:

      name_role - name of the new role

    description - optional description of the role

    firerole_def_src - optional firerole like definition
    """

    return wal.perform_addrole(req=req,
                               name_role=name_role,
                               description=description,
                               firerole_def_src=firerole_def_src,
                               confirm=confirm)


def modifyrole(req, id_role='0', name_role='', description='put description here.', firerole_def_src='', modified='0', confirm=0, ln=CFG_SITE_LANG):
    """form to add a new role with these values:

      name_role - name of the new role

    description - optional description of the role

    firerole_def_src - optional firerole like definition
    """

    return wal.perform_modifyrole(req=req,
                               id_role=id_role,
                               name_role=name_role,
                               description=description,
                               firerole_def_src=firerole_def_src,
                               modified=modified,
                               confirm=confirm)


def deleterole(req, id_role="0", confirm=0, ln=CFG_SITE_LANG):
    """select a role and show all connected information,

      users - users that can access the role.

    actions - actions with possible authorizations."""

    return wal.perform_deleterole(req=req,
                                  id_role=id_role,
                                  confirm=confirm)


def showroledetails(req, id_role='0', ln=CFG_SITE_LANG):
    """show the details of a role."""

    return wal.perform_showroledetails(req=req,
                                       id_role=id_role)


def showactiondetails(req, id_action="0", ln=CFG_SITE_LANG):
    """show the details of an action. """

    return wal.perform_showactiondetails(req=req,
                                         id_action=id_action)


def showuserdetails(req, id_user="0", ln=CFG_SITE_LANG):
    """show the details of an action. """

    return wal.perform_showuserdetails(req=req,
                                       id_user=id_user)


def adduserrole(req, id_role='0', email_user_pattern='', id_user='0', confirm=0, ln=CFG_SITE_LANG):
    """create connection between user and role.

               id_role - id of the role to add user to

    email_user_pattern - search for users using this pattern

               id_user - id of user to add to the role. """

    return wal.perform_adduserrole(req=req,
                                   id_role=id_role,
                                   email_user_pattern=email_user_pattern,
                                   id_user=id_user,
                                   confirm=confirm)


def addroleuser(req, email_user_pattern='', id_user='0', id_role='0', confirm=0, ln=CFG_SITE_LANG):
    """create connection between user and role.

    email_user_pattern - search for users using this pattern

               id_user - id of user to add to the role.

               id_role - id of the role to add user to. """

    return wal.perform_addroleuser(req=req,
                                   email_user_pattern=email_user_pattern,
                                   id_user=id_user,
                                   id_role=id_role,
                                   confirm=confirm)


def deleteuserrole(req, id_role='0', id_user='0', reverse=0, confirm=0, ln=CFG_SITE_LANG):
    """delete connection between role and user.

    id_role - id of role to disconnect

    id_user - id of user to disconnect. """

    return wal.perform_deleteuserrole(req=req,
                                      id_role=id_role,
                                      id_user=id_user,
                                      reverse=reverse,
                                      confirm=confirm)


def addauthorization(req, id_role="0", id_action="0", reverse="0", confirm=0, **keywords):
    """ form to add new connection between user and role:

      id_role - role to connect

    id_action - action to connect

      reverse - role or action first? """

    return wal.perform_addauthorization(req=req,
                                        id_role=id_role,
                                        id_action=id_action,
                                        reverse=reverse,
                                        confirm=confirm,
                                        **keywords)


def deleteroleaction(req, id_role="0", id_action="0", reverse=0, confirm=0, ln=CFG_SITE_LANG):
    """delete all connections between a role and an action.

      id_role - id of the role

    id_action - id of the action

      reverse - 0: ask for role first
                1: ask for action first"""

    return wal.perform_deleteroleaction(req=req,
                                    id_role=id_role,
                                    id_action=id_action,
                                    reverse=reverse,
                                    confirm=confirm)


def modifyauthorizations(req, id_role="0", id_action="0", reverse=0, confirm=0, sel='', errortext='', authids=[], ln=CFG_SITE_LANG):
    """given ids of a role and an action, show all possible action combinations
    with checkboxes and allow user to access other functions.

      id_role - id of the role

    id_action - id of the action

      reverse - 0: ask for role first
                1: ask for action first

          sel - which button and modification that is selected

    errortext - text to print when no connection exist between role and action

      authids - ids of checked checkboxes """

    return wal.perform_modifyauthorizations(req=req,
                                            id_role=id_role,
                                            id_action=id_action,
                                            reverse=reverse,
                                            confirm=confirm,
                                            sel=sel,
                                            authids=authids)


def simpleauthorization(req, id_role=0, id_action=0, ln=CFG_SITE_LANG):
    """show a page with simple overview of authorizations between a
    connected role and action. """

    return wal.perform_simpleauthorization(req=req,
                                           id_role=id_role,
                                           id_action=id_action)


def showroleusers(req, id_role=0, ln=CFG_SITE_LANG):
    """show a page with simple overview of a role and connected users. """

    return wal.perform_showroleusers(req=req,
                                     id_role=id_role)

