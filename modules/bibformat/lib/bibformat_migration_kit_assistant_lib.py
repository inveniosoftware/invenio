# -*- coding: utf-8 -*-
## $Id$
## Deal with BibFormat configuraion files.

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import os

from invenio.config import cdslang, weburl, etcdir
from invenio.urlutils import wash_url_argument
from invenio.messages import gettext_set_language, wash_language
from invenio.errorlib import get_msgs_for_code_list

import invenio.template
migration_kit_templates = invenio.template.load('bibformat_migration_kit')

status_filename = 'migration_status.txt'
status_filepath = etcdir + os.sep +"bibformat" + os.sep + status_filename

def getnavtrail(previous = '', ln=cdslang):
    """Get the navtrail"""
    previous = wash_url_argument(previous, 'str')
    ln = wash_language(ln)
    _ = gettext_set_language(ln)
    navtrail = """<a class=navtrail href="%s/admin/">%s</a> &gt; <a class=navtrail href="%s/admin/bibformat/bibformatadmin.py">%s</a> """ % (weburl, _("Admin Area"), weburl, _("BibFormat Admin"))
    navtrail = navtrail + previous
    return navtrail

def perform_request_migration_kit_status(ln=cdslang):
    """
    Show the user migration status

    """

    warnings = []
    #Check that we can write in etc/bibformat and edit the migration status.
    #Else do not allow migration
    if not can_write_migration_status_file():
        warnings.append(("WRN_BIBFORMAT_CANNOT_WRITE_MIGRATION_STATUS"))
        
    if not can_write_etc_bibformat_dir():
        warnings.append(("WRN_BIBFORMAT_CANNOT_WRITE_IN_ETC_BIBFORMAT"))

    if len(warnings) > 0:
        warnings = get_msgs_for_code_list(warnings, 'warning', ln)
        warnings = [x[1] for x in warnings] # Get only message, not code
        return migration_kit_templates.tmpl_admin_cannot_migrate(warnings)

    else:
    
        status = read_status()
        
        steps = []
        steps.append({'link':weburl+"/admin/bibformat/bibformat_migration_kit_assistant.py/migrate_kb", 'label':"Migrate knowledge bases", 'status':status['kbs']})
        steps.append({'link':weburl+"/admin/bibformat/bibformat_migration_kit_assistant.py/migrate_behaviours",'label':"Migrate behaviours", 'status':status['behaviours']})
        steps.append({'link':weburl+"/admin/bibformat/bibformat_migration_kit_assistant.py/migrate_formats",'label':"Migrate formats", 'status':status['formats']})
    
        return migration_kit_templates.tmpl_admin_migration_status(ln, steps)

def perform_request_migration_kit_knowledge_bases(ln=cdslang):
    """
    Migrate and tell user
    """
    
    status = bibformat_migration_kit.migrate_kbs()
    save_status("kbs", status)
    
    return migration_kit_templates.tmpl_admin_migrate_knowledge_bases(ln)

def perform_request_migration_kit_behaviours(ln=cdslang):
    """
    Migrate and tell user
    """
    
    status = bibformat_migration_kit.migrate_behaviours()
    save_status("behaviours", status)
 
    return migration_kit_templates.tmpl_admin_migrate_behaviours(ln, status)

def perform_request_migration_kit_formats(ln=cdslang):
    """
    Display the different options and warnings to the user. Don't migrate yet
    """

    return migration_kit_templates.tmpl_admin_migrate_formats(ln)

def perform_request_migration_kit_formats_do(ln=cdslang):
    """
    Migrate and tell user
    """
    
    status = bibformat_migration_kit.migrate_formats()
    save_status("formats", status)

    return migration_kit_templates.tmpl_admin_migrate_formats_do(ln)


def save_status(step, status="Not migrated"):
    """
    Save the status of a step inside 'migration_status.txt' file
    """
    text = ""
    old_value_replaced = False
    if os.path.exists(status_filepath):
        for line in open(status_filepath):
            #Try to replace previous value
            if line.startswith(step):
                text = text + step+"---"+status +"\n"
                old_value_replaced = True
            else:
                text =  text +line

        if not old_value_replaced:
            #Else add value at the end
            text = text +"\n"+ step+"---"+status +"\n"
    else:
        text = step+"---"+status +"\n"
    
    file = open(status_filepath, 'w')
    file.write(text)
    file.close

def read_status():
    """
    Read the status of the migration.
    Returns a dictionary with step name as key ('kbs', 'behaviours', 'formats') and status string as value
    """

    status = {'kbs':'Not Migrated', 'behaviours':'Not Migrated', 'formats':'Not Migrated'}

    try:
        if os.path.exists(status_filepath):
            for line in open(status_filepath):
                s_line = line.split("---")
                if len(line)>1:
                    status[s_line[0]] = s_line[1].strip("\n")
    except:
        pass
    
    return status

def can_write_migration_status_file():
    """
    Checks that we have write permission on file migration_status.txt
    in etc/bibformat directory.
    
    If file does not exist, return True if we have write permission in
    directory etc/bibformat directory to create this file.
    """
    if os.path.exists(status_filepath):
        return os.access(status_filepath, os.W_OK)
    else:
        #check writability of etc/bibformat dir
        return can_write_etc_bibformat_dir()

from invenio import bibformat_migration_kit
from invenio.bibformatadminlib import can_write_etc_bibformat_dir
