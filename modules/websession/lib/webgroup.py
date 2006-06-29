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
from invenio.messages import gettext_set_language, wash_language
from invenio.websession_config import cfg_websession_info_messages, cfg_websession_usergroup_status
from invenio.webmessage import perform_request_send
import invenio.webgroup_dblayer as db
try:
    import invenio.template
    websession_templates = invenio.template.load('websession')
except ImportError:
    pass
    
def perform_request_group_display(uid, errors = [], warnings = [], info=0, ln=cdslang):
    """Display all the groups 
    @param uid:   user id
    @param ln: language
    @return a (body, errors[], warnings[]) formed tuple
    """
    _ = gettext_set_language(ln)
    body = ""
    admin_info = []
    member_info = []
    if info in (1, 3, 4):
        admin_info.append(_(cfg_websession_info_messages[info]))
    elif info in(2, 7):
        member_info.append(_(cfg_websession_info_messages[info]))
                           
    (body_admin, errors_admin) = display_admin_group(uid, infos=admin_info)
    (body_member, errors_member) = display_member_group(uid, infos=member_info)
            
    if errors_admin != [] :
        errors.extend(errors_admin)
    if errors_member != [] :
        errors.extend(errors_member)
    
    body = websession_templates.tmpl_display_all_groups(admin_group_html=body_admin,
                                                        member_group_html=body_member,
                                                        ln=ln)
    return (body, errors, warnings)

    

   
      
def display_admin_group(uid, infos=[], ln=cdslang):
    """return html groups representation the user is admin of"""
    body = ""
    errors = []
    record = db.get_is_admin_of_group(uid)
    body = websession_templates.tmpl_display_admin_group(groups=record,
                                                         infos=infos,
                                                         ln=ln)
    return (body, errors)


def display_member_group(uid, infos=[], ln=cdslang):
    """return html groups representation the user is member of"""
    body = ""
    errors = []
    records = db.get_is_member_of_group(uid,desc=1)
    
    body = websession_templates.tmpl_display_member_group(groups=records,
                                                          infos=infos,
                                                          ln=ln)
    return (body, errors)


def perform_request_input_create_group(group_name,
                                       group_description,
                                       join_policy,
                                       warnings=[],
                                       ln=cdslang):
    """return html for group creation page"""
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
    """Create the new group and return the new group's id """
    _ = gettext_set_language(ln)
    body = ""
    warnings = []
    errors = []
    if group_name == "":
        warning = _("Please enter a group name.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_input_create_group(group_name,
                                                                     group_description,
                                                                     join_policy,
                                                                     warnings=warnings)
    elif join_policy=="-1":
        warning = _("Please choose a group join policy.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_input_create_group(group_name,
                                                                     group_description,
                                                                     join_policy,
                                                                     warnings=warnings)
          
    else:
        db.insert_new_group(uid,
                            group_name,
                            group_description,
                            join_policy)
        (body, errors, warnings) = (1, errors, warnings)
    return (body, errors, warnings)


def perform_request_input_join_group(uid,
                                     group_name,
                                     search,
                                     warnings=[],
                                     ln=cdslang):
    """return html for group creation page"""
    body = ""
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
    _ = gettext_set_language(ln)
    body = ""
    warnings = []
    errors = []
    if "-1" in grpID:
        grpID.remove("-1")
    if len(grpID)==1 :
        grpID = grpID[0] 
        """insert new user of group"""
        group_infos = db.get_group_infos(grpID)
        group_type = group_infos[0][3]
        if group_type in("VM", "IM"):
            db.insert_new_member(uid,
                                 grpID,
                                 cfg_websession_usergroup_status["PENDING"])
            admin = db.get_users_by_status(grpID,
                                           cfg_websession_usergroup_status["ADMIN"])[0][1]
            if not group_name:
                group_name = group_infos[0][1]
            msg_subjet, msg_body = websession_templates.tmpl_new_member_msg(group_name=group_name,
                                                                            grpID=grpID,
                                                                            ln=ln)
            (body, errors, warnings, title, navtrail) = perform_request_send(uid,
                                                                             msg_to_user=admin,
                                                                             msg_to_group="",
                                                                             msg_subject=msg_subjet,
                                                                             msg_body=msg_body,
                                                                             ln=ln)
            body = 7

        elif group_type in("VO","IO"):
            db.insert_new_member(uid,
                                 grpID,
                                 cfg_websession_usergroup_status["MEMBER"])
            body = 2
        return (body, errors, warnings)
        
    else:
        warning = _("Please select only one group.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_input_join_group(uid,
                                                                    group_name,
                                                                    search,
                                                                    warnings,
                                                                    ln)
        return (body, errors, warnings)

def perform_request_input_leave_group(uid,
                                      warnings=[],
                                      ln=cdslang):
    """return html for group creation page"""
    body = ""
    errors = []
    records = db.get_is_member_of_group(uid=uid)
    body = websession_templates.tmpl_display_input_leave_group(records,
                                                               warnings=warnings,
                                                               ln=ln)

    return (body, errors, warnings)

def perform_request_leave_group(uid,
                                grpID,
                                confirmed=0,
                                ln=cdslang):
    _ = gettext_set_language(ln)
    body = ""
    warnings = []
    errors = []
    if "-1" in grpID:
        grpID.remove("-1")
    if len(grpID) == 1 :
        if confirmed:
            db.leave_group(grpID,uid)
            body = 8
        else:
            body = websession_templates.tmpl_confirm_leave(uid, grpID, ln)
    else:
        warning = _("Please select one group.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_input_leave_group(uid,
                                                                    warnings= warnings,
                                                                    ln=ln)
    return (body, errors, warnings)
        
        
        
    
    return (body, errors, warnings)
    
def perform_request_edit_group(uid,
                               grpID,
                               warnings=[],
                               ln=cdslang):
    """Display interface for group editing"""
    body = ''
    errors = []
    
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    elif user_status[0][0] != 'A':
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
    body = ''
    errors = []
    warnings = []
    _ = gettext_set_language(ln)
    if group_name == "":
        warning = _("Please enter a group name.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_edit_group(uid,
                                                              grpID,
                                                              warnings=warnings,
                                                              ln=ln)
    elif join_policy == "-1":
        warning = _("Please choose a group join policy.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_edit_group(uid,
                                                              grpID,
                                                              warnings=warnings,
                                                              ln=ln)
    else:
        grpID = db.update_group_infos(grpID,
                                         group_name,
                                         group_description,
                                         join_policy)
        (body, errors, warnings) = (3, errors, warnings)
        
    return (body, errors, warnings)
    

def  perform_request_delete_group(uid,
                                  grpID,
                                  confirmed=0,
                                  ln=cdslang):
    body = ""
    warnings = []
    errors = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    elif user_status[0][0] != 'A':
        errors.append(('ERR_WEBSESSION_GROUP_NO_RIGHTS',))
        return (body, errors, warnings)
    if confirmed:
        db.delete_group(grpID)
        body = 4
    else:
        body = websession_templates.tmpl_confirm_delete(grpID, ln)
        
    return (body, errors, warnings)
            

def perform_request_manage_member(uid,
                                  grpID,
                                  info=0,
                                  warnings = [],
                                  ln=cdslang):
    body = ''
    errors = []
    infos = ([], [])
    _ = gettext_set_language(ln)
    if info == 5:
        infos[0].append(_(cfg_websession_info_messages[info]))
    elif info == 6:
        infos[1].append(_(cfg_websession_info_messages[info]))
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    elif user_status[0][0] != 'A':
        errors.append(('ERR_WEBSESSION_GROUP_NO_RIGHTS',))
        return (body, errors, warnings)
    group_name = db.get_group_infos(grpID)
    members = db.get_users_by_status(grpID, cfg_websession_usergroup_status["MEMBER"])
    pending_members = db.get_users_by_status(grpID, cfg_websession_usergroup_status["PENDING"])
    
    body = websession_templates.tmpl_display_manage_member(grpID=grpID,
                                                           group_name=group_name[0][1],
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
    body = ''
    errors = []
    warnings = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    if user_status[0][0] != 'A':
        errors.append(('ERR_WEBSESSION_GROUP_NO_RIGHTS',))
        return (body, errors, warnings)

    if member_id == -1:
        warning = _("Please choose a member if you want to remove him from the group.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_manage_member(uid,
                                                                grpID,
                                                                warnings=warnings,
                                                                ln=ln)

    else:
        ok = db.delete_member(grpID, member_id)
    
        if not ok:
            errors.append('ERR_WEBSESSION_DB_ERROR')
            return (body, errors, warnings)
    
        (body, errors, warnings) = (5, errors, warnings)
    return (body, errors, warnings)
        
def perform_request_add_member(uid,
                               grpID,
                               user_id,
                               ln=cdslang):
    body = ''
    errors = []
    warnings = []
    _ = gettext_set_language(ln)
    user_status = db.get_user_status(uid, grpID)
    if not len(user_status):
        errors.append('ERR_WEBSESSION_DB_ERROR')
        return (body, errors, warnings)
    elif user_status[0][0] != 'A':
        errors.append(('ERR_WEBSESSION_GROUP_NO_RIGHTS',))
        return (body, errors, warnings)
    if user_id == -1:
        warning = _("Please choose a user from the list if you want him to be added to the group.")
        warnings.append(warning)
        (body, errors, warnings) = perform_request_manage_member(uid,
                                                                grpID,
                                                                warnings=warnings,
                                                                ln=ln)
    else :
        ok = db.add_pending_member(grpID,
                                   user_id,
                                   cfg_websession_usergroup_status["MEMBER"])
    
        if not ok:
            errors.append('ERR_WEBSESSION_DB_ERROR')
            return (body, errors, warnings)
        
        (body, errors, warnings) = (6, errors, warnings)
        
    return (body, errors, warnings)


def get_navtrail(ln=cdslang, title=""):
    """
    gets the navtrail for title...
    @param title: title of the page
    @param ln: language
    @return HTML output
    """
    navtrail = websession_templates.tmpl_navtrail(ln, title)
    return navtrail
