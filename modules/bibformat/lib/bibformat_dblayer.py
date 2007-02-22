# -*- coding: utf-8 -*-
##
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

"""
Database access related functions for BibFormat engine and
administration pages.
"""

__revision__ = "$Id$"

import zlib
import time

from invenio.dbquery import run_sql, escape_string

# Cache the mapping name -> id for each kb
kb_id_name_cache = {}

## MARC-21 tag/field access functions
def get_fieldvalues(recID, tag):
    """Returns list of values of the MARC-21 'tag' fields for the record
       'recID'."""
    out = []
    bibXXx = "bib" + tag[0] + tag[1] + "x"
    bibrec_bibXXx = "bibrec_" + bibXXx
    query = "SELECT value FROM %s AS b, %s AS bb WHERE bb.id_bibrec=%s AND bb.id_bibxxx=b.id AND tag LIKE '%s'" \
            % (bibXXx, bibrec_bibXXx, recID, tag)
    res = run_sql(query)
    for row in res:
        out.append(row[0])
    return out

def localtime_to_utc(date):
    "Convert localtime to UTC"

    ldate = date.split(" ")[0]
    ltime = date.split(" ")[1]

    lhour   = ltime.split(":")[0]
    lminute = ltime.split(":")[1]
    lsec    = ltime.split(":")[2]

    lyear   = ldate.split("-")[0]
    lmonth  = ldate.split("-")[1]
    lday    = ldate.split("-")[2]

    timetoconvert = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.mktime((int(lyear), int(lmonth), int(lday), int(lhour), int(lminute), int(lsec), 0, 0, -1))))

    return timetoconvert

def get_creation_date(sysno):
    "Returns the creation date of the record 'sysno'."
    out   = ""
    res = run_sql("SELECT DATE_FORMAT(creation_date, '%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_modification_date(sysno):
    "Returns the date of last modification for the record 'sysno'."
    out = ""
    res = run_sql("SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res and res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

## Knowledge base access functions
def get_kbs():
    """Returns all kbs as list of dictionaries {id, name, description}"""
    out = []
    query = "SELECT * FROM fmtKNOWLEDGEBASES ORDER BY name"
    res = run_sql(query)
    for row in res:
        out.append({'id': row[0], 'name':row[1], 'description': row[2]})
        # out.append(row)
    return out

def get_kb_id(kb_name):
    """Returns the id of the kb with given name"""
    if kb_id_name_cache.has_key(kb_name):
        return kb_id_name_cache[kb_name]
    
    query = """SELECT id FROM fmtKNOWLEDGEBASES WHERE name LIKE '%s'""" % escape_string(kb_name)
    res = run_sql(query)
    if len(res) > 0:
        kb_id_name_cache[kb_name] = res[0][0] 
        return res[0][0]
    else:
        return None

def get_kb_name(kb_id):
    """Returns the name of the kb with given id"""
    query = """SELECT name FROM fmtKNOWLEDGEBASES WHERE id='%s'""" % escape_string(str(kb_id))
    res = run_sql(query)
    if len(res) > 0:
        return res[0][0]
    else:
        return None

def get_kb_mappings(kb_name, sortby="to"):
    """Returns a list of all mappings from the given kb, ordered by key

    @param sortby the sorting criteria ('from' or 'to')
    """
    out = []
    k_id = get_kb_id(kb_name)
    if (sortby == "to"):
        sort = "m_value"
    else:
        sort = "m_key"
        
    query = """SELECT * FROM fmtKNOWLEDGEBASEMAPPINGS
    WHERE id_fmtKNOWLEDGEBASES = '%(k_id)s' ORDER BY %(sort)s""" \
    % {'k_id':k_id, 'sort':sort}
    res = run_sql(query)
    for row in res:
        out.append({'id':row[0], 'key':row[1], 'value': row[2]})
    return out

def get_kb_description(kb_name):
    """Returns the description of the given kb"""
    k_id = get_kb_id(kb_name)
    query = """SELECT description FROM fmtKNOWLEDGEBASES WHERE id='%s'""" % k_id
    res = run_sql(query)
    return res[0][0]
    
def add_kb(kb_name, kb_description):
    """
    Adds a new kb with given name and description. Returns the id of
    the kb.

    If name already exists replace old value

    @param kb_name the name of the kb to create
    @param kb_description a description for the kb
    @return the id of the newly created kb
    """
    query = """REPLACE INTO fmtKNOWLEDGEBASES (name, description)
    VALUES('%s', '%s')""" % (escape_string(kb_name), escape_string(kb_description))
    run_sql(query)

    return get_kb_id(kb_name)

def delete_kb(kb_name):
    """Deletes the given kb"""
    k_id = get_kb_id(kb_name)
    query = """DELETE FROM fmtKNOWLEDGEBASEMAPPINGS WHERE id_fmtKNOWLEDGEBASES = '%s'""" % (k_id)
    run_sql(query)
    query = """DELETE FROM fmtKNOWLEDGEBASES WHERE id = '%s'""" % (k_id)
    run_sql(query)

    # Update cache
    if kb_id_name_cache.has_key(kb_name):
        del kb_id_name_cache[kb_name]
    
    return True

def kb_exists(kb_name):
    """Returns True if a kb with the given name exists"""
    query = """SELECT id FROM fmtKNOWLEDGEBASES
    WHERE name = '%s'""" % (escape_string(kb_name))
    rows = run_sql(query)
    if len(rows) > 0:
        return True
    else:
        return False
    
def update_kb(kb_name, new_name, new_description):
    """Updates given kb with new name and new description"""
    k_id = get_kb_id(kb_name)
    query = """UPDATE fmtKNOWLEDGEBASES
    SET name = '%s' , description = '%s'
    WHERE id = '%s'""" % (escape_string(new_name), escape_string(new_description), k_id)
    run_sql(query)
    # Update cache
    if kb_id_name_cache.has_key(kb_name):
        del kb_id_name_cache[kb_name]
        
    kb_id_name_cache[new_name] = k_id
    return True

def add_kb_mapping(kb_name, key, value):
    """Adds new mapping key->value in given kb"""
    k_id = get_kb_id(kb_name)
    query = """REPLACE INTO fmtKNOWLEDGEBASEMAPPINGS (m_key, m_value, id_fmtKNOWLEDGEBASES)
    VALUES('%s', '%s', '%s')""" % (escape_string(key), escape_string(value), k_id)
    run_sql(query)
    
    return True

def remove_kb_mapping(kb_name, key):
    """Removes mapping with given key from given kb"""
    k_id = get_kb_id(kb_name)
    query = """DELETE FROM fmtKNOWLEDGEBASEMAPPINGS
    WHERE m_key = '%s' AND id_fmtKNOWLEDGEBASES = '%s'""" \
    % (escape_string(key), k_id)
    run_sql(query)
    return True

def kb_mapping_exists(kb_name, key):
    """Returns true if the mapping with given key exists in the given kb"""
    if kb_exists(kb_name):
        k_id = get_kb_id(kb_name)
        query = """SELECT id FROM fmtKNOWLEDGEBASEMAPPINGS
        WHERE m_key = '%s' AND id_fmtKNOWLEDGEBASES = '%s'""" % (escape_string(key), k_id)
        rows = run_sql(query)
        if len(rows) > 0:
            return True
    
    return False

def get_kb_mapping_value(kb_name, key):
    """
    Returns a value of the given key from the given kb.
    If mapping not found, returns None #'default'

    @param kb_name the name of a knowledge base
    @param key the key to look for
    #@param default a default value to return if mapping is not found
    """
    k_id = get_kb_id(kb_name)
    query = """SELECT m_value FROM fmtKNOWLEDGEBASEMAPPINGS
    WHERE m_key LIKE '%s' AND id_fmtKNOWLEDGEBASES = '%s' LIMIT 1""" % (escape_string(key), k_id)
    res = run_sql(query)
    if len(res) > 0:
        return res[0][0]
    else:
        return None # default

def update_kb_mapping(kb_name, key, new_key, new_value):
    """Updates the mapping given by key with new key and value"""
    k_id = get_kb_id(kb_name)
    query = """UPDATE fmtKNOWLEDGEBASEMAPPINGS
    SET m_key = '%s' , m_value = '%s'
    WHERE m_key = '%s'
    AND id_fmtKNOWLEDGEBASES  = '%s'""" % (escape_string(new_key),
                                           escape_string(new_value),
                                           escape_string(key),
                                           k_id)
    run_sql(query)
    return True

def create_knowledge_bases_table():
    """
    Create the table that holds knowledge bases
    """
    # TO BE MOVED TO tabcreate.sql
    query = """
    CREATE TABLE IF NOT EXISTS fmtKNOWLEDGEBASES (
    id mediumint(8) unsigned NOT NULL auto_increment,
    name varchar(255) default '',
    description text default '',
    PRIMARY KEY  (id),
    UNIQUE KEY name (name)
    ) TYPE=MyISAM;"""
    run_sql(query)
    return True

def create_kb_mappings_table():
    """
    Create the table that holds all mappings of knowledge bases
    """
    # TO BE MOVED TO tabcreate.sql
    query = """
    CREATE TABLE IF NOT EXISTS fmtKNOWLEDGEBASEMAPPINGS (
    id mediumint(8) unsigned NOT NULL auto_increment,
    m_key varchar(255) NOT NULL default '',
    m_value text NOT NULL default '',
    id_fmtKNOWLEDGEBASES mediumint(8) NOT NULL default '0',
    PRIMARY KEY  (id),
    KEY id_fmtKNOWLEDGEBASES (id_fmtKNOWLEDGEBASES)
    ) TYPE=MyISAM;"""
    run_sql(query)

    # add_kb(marc_codes_mappings_kb_name, "Mapping from text label to marc codes. Used by bibformat in templates when calling <BFE_some_label /> for some_label that does not exist as element.")
    # bibformat_dblayer.add_kb_mapping("Marc tags", "date", "260$c")
    return True

def drop(): #TO BE REMOVED
    """
    Drop tables related to knowledge bases
    """
    query = """DROP TABLE fmtKNOWLEDGEBASES"""
    run_sql(query)
    query = """DROP TABLE fmtKNOWLEDGEBASEMAPPINGS"""
    run_sql(query)

## XML Marc related functions
def get_tag_from_name(name):
    """
    Returns the marc code corresponding the given name
    """
    res = run_sql("SELECT value FROM tag WHERE name LIKE '%s'" % escape_string(name))
    if len(res)>0:
        return res[0][0]
    else:
        return None

def get_tags_from_name(name):
    """
    Returns the marc codes corresponding the given name,
    ordered by value
    """
    res = run_sql("SELECT value FROM tag WHERE name LIKE '%s'ORDER BY value" % escape_string(name))
    if len(res)>0:
        return list(res[0])
    else:
        return None

def tag_exists_for_name(name):
    """
    Returns True if a tag exists for name in 'tag' table.
    """
    query = "SELECT value FROM tag WHERE name LIKE '%s'" % escape_string(name)
    rows = run_sql(query)
    if len(rows) > 0:
        return True
    return False

def get_name_from_tag(tag):
    """
    Returns the name corresponding to a marc code
    """
    res = run_sql("SELECT name FROM tag WHERE value LIKE '%s'" % escape_string(tag))
    if len(res)>0:
        return res[0][0]
    else:
        return None
    
def name_exists_for_tag(tag):
    """
    Returns True if a name exists for tag in 'tag' table.
    """
    query = "SELECT name FROM tag WHERE value LIKE '%s'" % escape_string(tag)
    rows = run_sql(query)
    if len(rows) > 0:
        return True
    return False
    
def get_all_name_tag_mappings():
    """
    Return the list of mappings name<->tag from 'tag' table.
    
    The returned object is a dict with name as key (if 2 names are the same
    we will take the value of one of them, as we cannot make the difference in format
    templates)

    @return a dict containing list of mapping in 'tag' table
    """
    out = {}
    query = "SELECT value, name FROM tag"
    res = run_sql(query)
    for row in res:
        out[row[1]] = row[0]
    return out

    
## Output formats related functions

def get_output_format_id(code):
    """
    Returns the id of output format given by code in the database.

    Output formats are located inside 'format' table

    @return the id in the database of the output format. None if not found
    """
    f_code = code
    if len(code)>6:
        f_code = code[:6]
        
    query = "SELECT id FROM format WHERE code='%s'" % escape_string(f_code.lower())
    res = run_sql(query)

    if len(res)>0:
        return res[0][0]
    else:
        return None

def add_output_format(code, name="", description="", content_type="text/html"):
    """
    Add output format into format table.

    If format with given code already exists, do nothing

    @param code the code of the new format
    @param name a new for the new format
    @param description a description for the new format
    @param content_type the content_type (if applicable) of the new output format
    """
    output_format_id = get_output_format_id(code);
    if output_format_id is None:
        query = "INSERT INTO format SET code=%s, description=%s, content_type=%s"
        params = (code.lower(), description, content_type)
        run_sql(query, params)
        set_output_format_name(code, name)
        
def remove_output_format(code):
    """
    Removes the output format with 'code'

    If code does not exist in database, do nothing
    The function also removes all localized names in formatname table
    
    @param the code of the output format to remove
    """
    output_format_id = get_output_format_id(code);
    if output_format_id is None:
        return
    
    query = "DELETE FROM formatname WHERE id_format='%s'" % output_format_id
    run_sql(query)
    query = "DELETE FROM format WHERE id='%s'" % output_format_id
    run_sql(query)
    
def get_output_format_description(code):
    """
    Returns the description of the output format given by code

    If code or description does not exist, return empty string

    @param code the code of the output format to get the description from
    @return output format description
    """
    
    query = "SELECT description FROM format WHERE code='%s'" % escape_string(code)
    res = run_sql(query)
    if len(res) > 0:
        res = res[0][0]
        if res is not None:
            return res
    return ""
    
def set_output_format_description(code, description):
    """
    Sets the description of an output format, given by its code

    If 'code' does not exist, create format
    
    @param code the code of the output format to update
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        add_output_format(code, "", description)
        
    query = "UPDATE format SET description=%s WHERE code=%s"
    params = (description, code.lower())
    run_sql(query, params)

def get_existing_content_types():
    """
    Returns the list of all MIME content-types used in existing output
    formats.

    Always returns at least a list with 'text/html'

    @return a list of content-type strings
    """
    query = "SELECT DISTINCT content_type FROM format GROUP BY content_type"
    res = run_sql(query)
    
    if res is not None:
        res = [val[0] for val in res if len(val) > 0]
        if not 'text/html' in res:
            res.append('text/html')
        return res
    else:
        return ['text/html']

def get_output_format_content_type(code):
    """
    Returns the content_type of the output format given by code

    If code or content_type does not exist, return empty string

    @param code the code of the output format to get the description from
    @return output format content_type
    """
    query = "SELECT content_type FROM format WHERE code='%s'" % escape_string(code)
    res = run_sql(query)
    if len(res) > 0:
        res = res[0][0]
        if res is not None:
            return res
    return ""
    
def set_output_format_content_type(code, content_type):
    """
    Sets the content_type of an output format, given by its code

    If 'code' does not exist, create format
    
    @param code the code of the output format to update
    @param content_type the content type for the format
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        # add one if not exist (should not happen)
        add_output_format(code, "", "", content_type)
        
    query = "UPDATE format SET content_type=%s WHERE code=%s"
    params = (content_type, code.lower())
    run_sql(query, params)


def get_output_format_names(code):
    """
    Returns the localized names of the output format designated by 'code'

    The returned object is a dict with keys 'ln' (for long name) and 'sn' (for short name),
    containing each a dictionary with languages as keys.
    The key 'generic' contains the generic name of the output format (for use in admin interface)
    For eg:  {'ln':{'en': "a long name", 'fr': "un long nom", 'de': "ein lange Name"},
              'sn':{'en': "a name", 'fr': "un nom", 'de': "ein Name"}
              'generic': "a name"}
              
    The returned dictionary is never None. The keys 'ln' and 'sn' are always present. However
    only languages present in the database are in dicts 'sn' and 'ln'. language "cdslang" is always
    in dict.
    
    The localized names of output formats are located in formatname table.
    
    @param code the code of the output format to get the names from
    @return a dict containing output format names
    """
    out = {'sn':{}, 'ln':{}, 'generic':''}
    output_format_id = get_output_format_id(code);
    if output_format_id is None:
        return out

    query = "SELECT name FROM format WHERE code='%s'" % escape_string(code)
    res = run_sql(query)
    if len(res) > 0:
        out['generic'] = res[0][0]

    query = "SELECT type, ln, value FROM formatname WHERE id_format='%s'" % output_format_id
    res = run_sql(query)
    for row in res:
        if row[0] == 'sn' or row[0] == 'ln':
            out[row[0]][row[1]] = row[2]
    return out

def set_output_format_name(code, name, lang="generic", type='ln'):
    """
    Sets the name of an output format given by code.

    if 'type' different from 'ln' or 'sn', do nothing
    if 'name' exceeds 256 chars, 'name' is truncated to first 256 chars.
    if 'code' does not correspond to exisiting output format, create format if "generic" is given as lang

    The localized names of output formats are located in formatname table.
    
    @param code the code of an ouput format
    @param type either 'ln' (for long name) and 'sn' (for short name)
    @param lang the language in which the name is given
    @param name the name to give to the output format
    """

    if len(name) > 256:
        name = name[:256]
    if type.lower() != "sn" and type.lower() != "ln":
        return
    output_format_id = get_output_format_id(code);
    if output_format_id is None and lang == "generic" and type.lower() == "ln":
        # Create output format inside table if it did not exist
        # Happens when the output format was added not through web interface
        add_output_format(code, name)
        output_format_id = get_output_format_id(code) # Reload id, because it was not found previously
        
    if lang =="generic" and type.lower()=="ln":
        # Save inside format table for main name
        query = "UPDATE format SET name=%s WHERE code=%s"
        params = (name, code.lower())
        run_sql(query, params)
    else:
        # Save inside formatname table for name variations
        query = "REPLACE INTO formatname SET id_format='%s', ln='%s', type='%s', value='%s'" \
                % (id, escape_string(lang), type.lower(), escape_string(name))
        run_sql(query)

def change_output_format_code(old_code, new_code):
    """
    Change the code of an output format

    @param old_code the code of the output format to change
    @param new_code the new code
    """
    output_format_id = get_output_format_id(old_code);
    if output_format_id is None:
        return
    
    query = "UPDATE format SET code='%s' WHERE id='%s'" % (new_code, id)
    run_sql(query)
    
def get_preformatted_record(recID, of, decompress=zlib.decompress):
    """
    Returns the preformatted record with id 'recID' and format 'of'
    
    If corresponding record does not exist for given output format,
    returns None

    @param recID the id of the record to fetch
    @param of the output format code
    @param decompress the method used to decompress the preformatted record in database
    @return formatted record as String, or None if not exist
    """
    # Try to fetch preformatted record
    query = "SELECT value FROM bibfmt WHERE id_bibrec='%s' AND format='%s'" % (recID, of)
    res = run_sql(query)
    if res:
	# record 'recID' is formatted in 'of', so return it
        return "%s" % decompress(res[0][0])
    else:
        return None
    
## def keep_formats_in_db(output_formats):
##     """
##     Remove from db formats that are not in the list
##     TOBE USED ONLY ONCE OLD BIBFORMAT IS REMOVED (or old behaviours will be erased...)
##     """
##     query = "SELECT code FROM format"
##     res = run_sql(query)
##     for row in res:
##         if not row[0] in output_formats: 
##             query = "DELETE FROM format WHERE code='%s'"%row[0]
    
## def add_formats_in_db(output_formats):
##     """
##     Add given formats in db (if not already there)
##     """
##     for output_format in output_format:
        
##         if get_format_from_db(output_format) is None:
##             #Add new
##             query = "UPDATE TABLE format "
##         else:
##             #Update
##             query = "UPDATE TABLE format "
            
##     query = "UPDATE TABLE format "
##     res = run_sql(query)
##     for row in res:
##         if not row[0] in output_formats: 
##             query = "DELETE FROM format WHERE code='%s'"%row[0]
    
