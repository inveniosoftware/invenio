## $Id$

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

"""Group features."""

from invenio.config import cdslang
from invenio.messages import gettext_set_language
from invenio.websession_config import CFG_WEBSESSION_INFO_MESSAGES, \
      CFG_WEBSESSION_USERGROUP_STATUS, \
      CFG_WEBSESSION_GROUP_JOIN_POLICY, \
      CFG_WEBSESSION_WARNING_MESSAGES
from invenio.webuser import nickname_valid_p, get_user_info
from invenio.webmessage import perform_request_send
import invenio.webgroup_dblayer as db
try:
    import invenio.template
    websession_templates = invenio.template.load('websession')
except ImportError:
    pass
    
def perform_request_group_display(uid, infos=[], errors = [], warnings = [], ln=cdslang):
    """Display all the groups the user belong to
    @param uid:   user id
    @param info: info about last user action
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    _ = gettext_set_language(ln)
    body = ""
    (body_admin, errors_admin) = display_admin_group(uid, ln)
    (body_member, errors_member) = display_member_group(uid, ln)
            
    if errors_admin:
        errors.extend(errors_admin)
    if errors_member:
        errors.extend(errors_member)
    
    body = websession_templates.tmpl_display_all_groups(infos=infos,
                                                        admin_group_html=body_admin,
                                                        member_group_html=body_member,
                                                        warnings=warnings,
                                                        ln=ln)
    return (body, errors, warnings)

      
def display_admin_group(uid, ln=cdslang):
    """Display groups the user is admin of
    @param uid: user id
    @param ln: language
    @return a (body, errors[]) formed tuple
    return html groups representation the user is admin of"""
    body = ""
    errors = []
    record = db.get_groups_by_user_status(uid=uid,
                                          user_status=CFG_WEBSESSION_USERGROUP_STATUS["ADMIN"])
    body = websession_templates.tmpl_display_admin_group(groups=record,
                                                         ln=ln)
    return (body, errors)


def display_member_group(uid, ln=cdslang):
    """Display groups the user is member of
    @param uid: user id
    @param ln: language
    @return a (body, errors[]) formed tuple
    body : html groups representation the user is member of"""
    body = ""
    errors = []
    records = db.get_groups_by_user_status(uid,
                                           user_status=CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"] )
    
    body = websession_templates.tmpl_display_member_group(groups=records,
                                                          ln=ln)
    return (body, errors)


def perform_request_input_create_group(group_name,
                                       group_description,
                                       join_policy,
                                       warnings=[],
                                       ln=cdslang):
    """Display form for creating new group.
    @param group_name: name of the group entered if the page has been reloaded
    @param group_description: description entered if the page has been reloaded
    @param join_policy: join  policy chosen if the page has been reloaded
    @param warnings: warnings
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    body: html for group creation page"""
    body = ""
    errors = []
    body = websession_templates.tmpl_display_input_group_info(group_name,
                                                              group_description,
                                                              join_policy,
                                                              act_type="create",
                                                              warnings=warnings,
                                                              ln=ln)
    return (body, errors, warnings)

def perform_request_create_group(uid,
                                 group_name,
                                 group_description,
                                 join_policy,
                                 ln=cdslang):
    """Create new group
    @param group_name: name of the group entered 
    @param group_description: description of the group entered 
    @param join_policy: join  policy of the group entered 
    @param ln: language
    @return a (body, errors, warnings) formed tuple
    warning != [] if group_name or join_policy are not valid
    or if the name already exists in the database
    body="1" if succeed in order to display info on the main page
    """
    _ = gettext_set_language(ln)
    body = ""
    warnings = []
    errors = []
    infos = []
    if group_name == "":
        warnings.append(('WRN_WEBSESSION_NO_GROUP_NAME',))
        (body, errors, warnings) = perform_request_input_create_group(group_name,
                                                                      group_description,
                                                                      join_policy,
                                                                      warnings=warnings)
    elif not group_name_valid_p(group_name):
        warnings.append('WRN_WEBSESSION_NOT_VALID_GROUP_NAME')
        (body, errors, warnings) = perform_request_input_create_group(group_name,
                                                                      group_description,
                                                                      join_policy,
                                                                      warnings=warnings)
    
    elif join_policy=="-1":
        warnings.append('WRN_WEBSESSION_NO_JOIN_POLICY')
        (body, errors, warnings) = perform_request_input_create_group(group_name,
                                                                      group_description,
                                                                      join_policy,
                                                                      warnings=warnings)
    elif db.group_name_exist(group_name):
        warnings.append('WRN_WEBSESSION_GROUP_NAME_EXISTS')
        (body, errors, warnings) = perform_request_input_create_group(group_name,
                                                                      group_description,
                                                                      join_policy,
                                                                      warnings=warnings)
          
    else:
        db.insert_new_group(uid,
                            group_name,
                            group_description,
                            join_policy)
        infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["GROUP_CREATED"]))
        (body, errors, warnings) = perform_request_group_display(uid,
                                                                 infos=infos,
                                                                 errors=errors,
                                                                 warnings=warnings,
                                                                 ln=cdslang)
    return (body, errors, warnings)


def perform_request_input_join_group(uid,
                                     group_name,
                                     search,
                                     warnings=[],
                                     ln=cdslang):
    """Return html for joining new group
    @param group_name: name of the group entered if user is looking for a group
    @param search=1 if search performed else 0
    @param warnings: warnings coming from perform_request_join_group
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    errors = []
    group_from_search = {}
    records = db.get_visible_group_list(uid=uid)
    if search:
        group_from_search = db.get_visible_group_list(uid, group_name)
    body = websession_templates.tmpl_display_input_join_group(records.items(),
                                                              group_name,
                                                              group_from_search.items(),
                                                              search,
                                                              warnings=warnings,
                                                              ln=ln)

    return (body, errors, warnings)
    
def perform_request_join_group(uid,
                               grpID,
                               group_name,
                               search,
                               ln=cdslang):
    """Join group
    @param grpID: list of the groups the user wants to join,
    only one value must be selected among the two group lists
    (default group list, group list resulting from the search)
    @param group_name: name of the group entered if search on name performed
    @param search=1 if search performed else 0
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    warnings != [] if 0 or more than one group is selected
    """
    _ = gettext_set_language(ln)
    body = ""
    warnings = []
    errors = []
    infos = []
    if "-1" in grpID:
        grpID.remove("-1")
    if len(grpID)==1 :
        grpID = grpID[0]
        """test if user is already member or pending"""
        status = db.get_user_status(uid, grpID)
        if status:
            warnings.append('WRN_WEBSESSION_ALREADY_MEMBER')
            
            (body, errors, warnings) = perform_request_group_display(uid,
                                                                     infos=infos,
                                                                     errors=errors,
                                                                     warnings=warnings,
                                                                     ln=cdslang)
            """insert new user of group"""
        else:
            group_infos = db.get_group_infos(grpID)
            group_type = group_infos[0][3]
            if group_type == CFG_WEBSESSION_GROUP_JOIN_POLICY["VISIBLEMAIL"]:
                db.insert_new_member(uid,
                                     grpID,
                                     CFG_WEBSESSION_USERGROUP_STATUS["PENDING"])
                admin = db.get_users_by_status(grpID,
                                               CFG_WEBSESSION_USERGROUP_STATUS["ADMIN"])[0][1]
                group_name = group_infos[0][1]
                msg_subjet, msg_body = websession_templates.tmpl_admin_msg(group_name=group_name,
                                                                           grpID=grpID,
                                                                           ln=ln)
                (body, errors, warnings, title, navtrail) = perform_request_send(uid,
                                                                                 msg_to_user=admin,
                                                                                 msg_to_group="",
                                                                                 msg_subject=msg_subjet,
                                                                                 msg_body=msg_body,
                                                                                 ln=ln)
                infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["JOIN_REQUEST"]))
                            
                
            elif group_type == CFG_WEBSESSION_GROUP_JOIN_POLICY["VISIBLEOPEN"]:
                db.insert_new_member(uid,
                                     grpID,
                                     CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])

                infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["JOIN_GROUP"]))
            (body, errors, warnings) = perform_request_group_display(uid,
                                                                     infos=infos,
                                                                     errors=errors,
                                                                     warnings=warnings,
                                                                     ln=cdslang)
    else:
        warnings.append('WRN_WEBSESSION_MULTIPLE_GROUPS')
        (body, errors, warnings) = perform_request_input_join_group(uid,
                                                                    group_name,
                                                                    search,
                                                                    warnings,
                                                                    ln)
    return (body, errors, warnings)

def perform_request_input_leave_group(uid,
                                      warnings=[],
                                      ln=cdslang):
    """Return html for leaving group
    @param uid: user ID
    @param warnings: warnings != [] if 0 group is selected or if not admin of the
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ""
    errors = []
    groups = []
    records = db.get_groups_by_user_status(uid=uid,
                                           user_status=CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])
    map(lambda x: groups.append((x[0], x[1])), records)
    body = websession_templates.tmpl_display_input_leave_group(groups,
                                                               warnings=warnings,
                                                               ln=ln)

    return (body, errors, warnings)

def perform_request_leave_group(uid,
                                grpID,
                                confirmed=0,
                                ln=cdslang):
                                      
    """Leave group 
    @param uid: user ID
    @param grpID: ID of the group the user wants to leave
    @param warnings: warnings != [] if 0 group is selected 
    @param confirmed: a confirmed page is first displayed 
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    _ = gettext_set_language(ln)
    body = ""
    warnings = []
    errors = []
    infos = []
    if not grpID == "-1":
        if confirmed:
            db.leave_group(grpID, uid)
            infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["LEAVE_GROUP"]))
            (body, errors, warnings) = perform_request_group_display(uid,
                                                                     infos=infos,
                                                                     errors=errors,
                                                                     warnings=warnings,
                                                                     ln=cdslang)
                
        else:
            body = websession_templates.tmpl_confirm_leave(uid, grpID, ln)
    else:
        warnings.append('WRN_WEBSESSION_NO_GROUP_SELECTED')
        (body, errors, warnings) = perform_request_input_leave_group(uid,
                                                                    warnings= warnings,
                                                                    ln=ln)
    return (body, errors, warnings)

    
def perform_request_edit_group(uid,
                               grpID,
                               warnings=[],
                               ln=cdslang):
    """Return html for group editing
    @param uid: user ID
    @param grpID: ID of the group
    @param warnings: warnings 
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    
    body = ''
    errors = []
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    elif user_status[0][0] != CFG_WEBSESSION_USERGROUP_STATUS['ADMIN']:
        errors.append(('ERR_WEBSESSION_GROUP_NO_RIGHTS',))
        return (body, errors, warnings)
    
    group_infos = db.get_group_infos(grpID)[0]
    if not len(group_infos):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    
    body = websession_templates.tmpl_display_input_group_info(group_name=group_infos[1],
                                                              group_description=group_infos[2],
                                                              join_policy=group_infos[3],
                                                              act_type="update",
                                                              grpID=grpID,
                                                              warnings=warnings,
                                                              ln=ln)
    
    return (body, errors, warnings)

def perform_request_update_group(uid,
                                 grpID,
                                 group_name,
                                 group_description,
                                 join_policy,
                                 ln=cdslang):
    """Update group datas in database
    @param uid: user ID
    @param grpID: ID of the group
    @param group_name: name of the group
    @param group_description: description of the group
    @param join_policy: join policy of the group
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ''
    errors = []
    warnings = []
    infos = []
    _ = gettext_set_language(ln)
    group_name_available = db.group_name_exist(group_name)
    if group_name == "":
        warnings.append('WRN_WEBSESSION_NO_GROUP_NAME')
        (body, errors, warnings) = perform_request_edit_group(uid,
                                                              grpID,
                                                              warnings=warnings,
                                                              ln=ln)
    elif not group_name_valid_p(group_name):
        warnings.append('WRN_WEBSESSION_NOT_VALID_GROUP_NAME')
        (body, errors, warnings) = perform_request_edit_group(uid,
                                                              grpID,
                                                              warnings=warnings,
                                                              ln=ln)
    elif join_policy == "-1":
        warnings.append('WRN_WEBSESSION_NO_JOIN_POLICY')
        (body, errors, warnings) = perform_request_edit_group(uid,
                                                              grpID,
                                                              warnings=warnings,
                                                              ln=ln)
    elif (group_name_available and group_name_available[0][0]!= int(grpID)):
        warnings.append('WRN_WEBSESSION_GROUP_NAME_EXISTS')
        (body, errors, warnings) = perform_request_edit_group(uid,
                                                              grpID,
                                                              warnings=warnings,
                                                              ln=ln)

    else:
        grpID = db.update_group_infos(grpID,
                                      group_name,
                                      group_description,
                                      join_policy)
        infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["GROUP_UPDATED"]))
        (body, errors, warnings) = perform_request_group_display(uid,
                                                                 infos=infos,
                                                                 errors=errors,
                                                                 warnings=warnings,
                                                                 ln=cdslang)
                
    return (body, errors, warnings)
    

def  perform_request_delete_group(uid,
                                  grpID,
                                  confirmed=0,
                                  ln=cdslang):
    """First display confirm message(confirmed=0)
    then(confirmed=1) delete group and all its members
    @param uid: user ID
    @param grpID: ID of the group
    @param confirmed =1 if confirmed message has been previously displayed 
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ""
    warnings = []
    errors = []
    infos = []
    _ = gettext_set_language(ln)
    group_infos = db.get_group_infos(grpID)
    user_status = db.get_user_status(uid, grpID)
    if not group_infos:
        warnings.append('WRN_WEBSESSION_GROUP_ALREADY_DELETED')
        (body, errors, warnings) = perform_request_group_display(uid,
                                                                 infos=infos,
                                                                 errors=errors,
                                                                 warnings=warnings,
                                                                 ln=cdslang)
    else:
        if not len(user_status):
            errors.append('ERR_WEBSESSION_DB_ERROR')
        elif confirmed:
            group_infos = db.get_group_infos(grpID)
            group_name = group_infos[0][1]
            msg_subjet, msg_body = websession_templates.tmpl_delete_msg(group_name=group_name,
                                                                        ln=ln)
            (body, errors, warnings, title, navtrail) = perform_request_send(uid,
                                                                             msg_to_user="",
                                                                             msg_to_group=group_name,
                                                                             msg_subject=msg_subjet,
                                                                             msg_body=msg_body,
                                                                             ln=ln)
            db.delete_group_and_members(grpID)
            infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["GROUP_DELETED"]))
            (body, errors, warnings) = perform_request_group_display(uid,
                                                                     infos=infos,
                                                                     errors=errors,
                                                                            warnings=warnings,
                                                                     ln=cdslang)
        else:
            body = websession_templates.tmpl_confirm_delete(grpID, ln)
        
    return (body, errors, warnings)
            

def perform_request_manage_member(uid,
                                  grpID,
                                  infos=[],
                                  warnings=[],
                                  ln=cdslang):
    """Return html for managing group's members
    @param uid: user ID
    @param grpID: ID of the group
    @param info: info about last user action
    @param warnings: warnings
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ''
    errors = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    elif user_status[0][0] != CFG_WEBSESSION_USERGROUP_STATUS['ADMIN']:
        errors.append(('ERR_WEBSESSION_GROUP_NO_RIGHTS',))
        return (body, errors, warnings)
    group_infos = db.get_group_infos(grpID)
    if not len(group_infos):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    members = db.get_users_by_status(grpID, CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])
    pending_members = db.get_users_by_status(grpID, CFG_WEBSESSION_USERGROUP_STATUS["PENDING"])
    
    body = websession_templates.tmpl_display_manage_member(grpID=grpID,
                                                           group_name=group_infos[0][1],
                                                           members=members,
                                                           pending_members=pending_members,
                                                           warnings=warnings,
                                                           infos=infos,
                                                           ln=ln)
    return (body, errors, warnings)

def perform_request_remove_member(uid,
                                  grpID,
                                  member_id,
                                  ln=cdslang):
    """Remove member from a group
    @param uid: user ID
    @param grpID: ID of the group
    @param member_id: selected member ID
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ''
    errors = []
    warnings = []
    infos = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)

    if member_id == -1:
        warnings.append('WRN_WEBSESSION_NO_MEMBER_SELECTED')
        (body, errors, warnings) = perform_request_manage_member(uid,
                                                                 grpID,
                                                                 warnings=warnings,
                                                                 ln=ln)

    else:
        db.delete_member(grpID, member_id)
        infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["MEMBER_DELETED"]))
        (body, errors, warnings) = perform_request_manage_member(uid,
                                                                 grpID,
                                                                 infos=infos,
                                                                 warnings=warnings,
                                                                 ln=ln)
    return (body, errors, warnings)
        
def perform_request_add_member(uid,
                               grpID,
                               user_id,
                               ln=cdslang):
    """Add waiting member to a group
    @param uid: user ID
    @param grpID: ID of the group
    @param user_id: selected member ID
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ''
    errors = []
    warnings = []
    infos = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    if user_id == -1:
        warnings.append('WRN_WEBSESSION_NO_USER_SELECTED_ADD')
        (body, errors, warnings) = perform_request_manage_member(uid,
                                                                 grpID,
                                                                 warnings=warnings,
                                                                 ln=ln)
    else :
        """test if user is already member or pending"""
        status = db.get_user_status(user_id, grpID)
        if status and status[0][0] == 'M':
            warnings.append('WRN_WEBSESSION_ALREADY_MEMBER_ADD')
            (body, errors, warnings) = perform_request_manage_member(uid,
                                                                     grpID,
                                                                     infos=infos,
                                                                     warnings=warnings,
                                                                     ln=ln)
            
            
        else:
            db.add_pending_member(grpID,
                                  user_id,
                                  CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])
        
            infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["MEMBER_ADDED"]))
            group_infos = db.get_group_infos(grpID)
            group_name = group_infos[0][1]
            user = get_user_info(user_id, ln)[2]
            msg_subjet, msg_body = websession_templates.tmpl_member_msg(group_name=group_name,
                                                                        accepted=1,
                                                                        ln=ln)
            (body, errors, warnings, title, navtrail) = perform_request_send(uid,
                                                                             msg_to_user=user,
                                                                             msg_to_group="",
                                                                             msg_subject=msg_subjet,
                                                                             msg_body=msg_body,
                                                                             ln=ln)
            (body, errors, warnings) = perform_request_manage_member(uid,
                                                                     grpID,
                                                                     infos=infos,
                                                                     warnings=warnings,
                                                                     ln=ln)
        
        
    return (body, errors, warnings)

def perform_request_reject_member(uid,
                                  grpID,
                                  user_id,
                                  ln=cdslang):
    """Reject waiting member and delete it from the list
    @param uid: user ID
    @param grpID: ID of the group
    @param member_id: selected member ID
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    body = ''
    errors = []
    warnings = []
    infos = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    if user_id == -1:
        warnings.append('WRN_WEBSESSION_NO_USER_SELECTED_DEL')
        (body, errors, warnings) = perform_request_manage_member(uid,
                                                                 grpID,
                                                                 warnings=warnings,
                                                                 ln=ln)
    else :
        """test if user is already member or pending"""
        status = db.get_user_status(user_id, grpID)
        if not status:
            warnings.append('WRN_WEBSESSION_ALREADY_MEMBER_REJECT')
            (body, errors, warnings) = perform_request_manage_member(uid,
                                                                     grpID,
                                                                     infos=infos,
                                                                     warnings=warnings,
                                                                     ln=ln)
        else:
            db.delete_member(grpID,
                             user_id)
            group_infos = db.get_group_infos(grpID)
            group_name = group_infos[0][1]
            user = get_user_info(user_id, ln)[2]
            msg_subjet, msg_body = websession_templates.tmpl_member_msg(group_name=group_name,
                                                                        accepted=0,
                                                                        ln=ln)
            (body, errors, warnings, title, navtrail) = perform_request_send(uid,
                                                                             msg_to_user=user,
                                                                             msg_to_group="",
                                                                             msg_subject=msg_subjet,
                                                                             msg_body=msg_body,
                                                                             ln=ln)
            infos.append(_(CFG_WEBSESSION_INFO_MESSAGES["MEMBER_REJECTED"]))
            (body, errors, warnings) = perform_request_manage_member(uid,
                                                                     grpID,
                                                                     infos=infos,
                                                                     warnings=warnings,
                                                                     ln=ln)
        
        
    return (body, errors, warnings)

def account_group(uid, ln=cdslang):
    """
    display group info for myaccount.py page.
    @param uid: user id (int)
    @param ln: language
    @return html body
    """
    nb_admin_groups = db.count_nb_group_user(uid, CFG_WEBSESSION_USERGROUP_STATUS["ADMIN"])
    nb_member_groups = db.count_nb_group_user(uid, CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])
    nb_total_groups = nb_admin_groups + nb_member_groups
    return websession_templates.tmpl_group_info(nb_admin_groups,
                                                nb_member_groups,
                                                nb_total_groups,
                                                ln=ln)
def get_navtrail(ln=cdslang, title=""):
    """
    gets the navtrail for title...
    @param title: title of the page
    @param ln: language
    @return HTML output
    """
    navtrail = websession_templates.tmpl_navtrail(ln, title)
    return navtrail

def group_name_valid_p(group_name):
    """Test if the group's name is valid"""
    return nickname_valid_p(group_name)
