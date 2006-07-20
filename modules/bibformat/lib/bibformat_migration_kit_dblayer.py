# -*- coding: utf-8 -*-
## $Id$
## 
## Every db-related function of module bibformat used to migrate previous bibformat
## files to new formats
##
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

from MySQLdb import escape_string

from invenio.dbquery import run_sql
    
## Knowledge Bases Migration related functions

def old_kbs_exist():
    """
    Returns true if the list of old kbs still exists. Else return false.
    """
    query = "SHOW TABLES LIKE 'flxKBS'"
    res = run_sql(query)
    print res
    if len(res) > 0:
        return True
    else:
        return False
    
def get_old_kbs():
    """
    Returns the list of old kbs
    """
    out = []
    query = "SELECT kb_name, kb_table, doc FROM flxKBS";
    res = run_sql(query)
    for row in res:
        out.append((row[0], row[1], row[2]))
    return out

def delete_old_kbs_list():
    """
    Removes the list of old kbs from the database (drop flxKBS)
    """
    query = "DROP TABLE flxKBS";
    run_sql(query)

def get_old_kb_mappings(kb_table):
    """
    Returns the old mappings in the given kb_table.
    """
    out = []
    query = "SELECT vkey, value FROM %s" % kb_table
    res = run_sql(query)
    for row in res:
        out.append((row[0], row[1]))
    return out

def delete_old_kb_table(kb_table):
    """
    Delete the given kb_table and its mapping
    """
    query = "DROP TABLE %s" % kb_table;
    run_sql(query)

##Behaviours migration related functions

def get_old_behaviours():
    """
    Returns the list of behaviours
    """
    out = []
    query = "SELECT name, type, doc FROM flxBEHAVIORS ORDER BY name"
    res = run_sql(query)
    for row in res:
        out.append((row[0], row[1], row[2]))
    return out

def get_old_behaviour_condition(otype):
    """
    Returns the list of behaviour conditions
    """
    out = []
    query = """SELECT eval_order, el_condition
	FROM flxBEHAVIORCONDITIONS
	WHERE otype='%s'
	ORDER BY eval_order""" % escape_string(otype)
    res = run_sql(query)
    for row in res:
        out.append((row[0], row[1]))
    return out

def get_old_behaviour_action(otype, eorder):
    """
    Return the behaviour action for given otype and eorder
    """
    out = []
    query = """SELECT apply_order, el_code
    FROM flxBEHAVIORCONDITIONSACTIONS
    WHERE otype='%(otype)s'
    AND eval_order=%(eorder)s
    ORDER BY apply_order""" % {'eorder': eorder, 'otype':escape_string(otype)}
    res = run_sql(query)
    for row in res:
        out.append((row[0], row[1]))
    return out


## Formats db related functions

def get_old_formats():
    """
    Return the list of formats
    """
    out = []
    query = "SELECT name, doc FROM flxFORMATS ORDER BY name"
    res = run_sql(query)
    for row in res:
        out.append((row[0], row[1]))
    return out

def get_old_format(format):
    """
    Returns a given format
    """
    query = "SELECT value FROM flxFORMATS WHERE name='%s'" % format
    res = run_sql(query)
    return res[0][0]

# "Behaviours"/output formats related functions

def adapt_tables():
    """
    Adapt MySQL tables
    """
    try:
        run_sql('''
        CREATE TABLE IF NOT EXISTS fmtKNOWLEDGEBASES (
        id mediumint(8) unsigned NOT NULL auto_increment,
        name varchar(255) default '',
        description text default '',
        PRIMARY KEY  (id),
        UNIQUE KEY name (name)
        ) TYPE=MyISAM;
        
        CREATE TABLE IF NOT EXISTS fmtKNOWLEDGEBASEMAPPINGS (
        id mediumint(8) unsigned NOT NULL auto_increment,
        m_key varchar(255) NOT NULL default '',
        m_value text NOT NULL default '',
        id_fmtKNOWLEDGEBASES mediumint(8) NOT NULL default '0',
        PRIMARY KEY  (id),
        KEY id_fmtKNOWLEDGEBASES (id_fmtKNOWLEDGEBASES)
        ) TYPE=MyISAM;
        
        ALTER TABLE format ADD COLUMN (description varchar(255) default '');
        ALTER TABLE format ADD COLUMN (content_type varchar(255) default '');
        ''')
    except:
        pass
    
