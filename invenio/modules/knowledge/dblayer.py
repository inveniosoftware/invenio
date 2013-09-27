# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Database access related functions for BibKnowledge.
"""

__revision__ = "$Id$"


from invenio.dbquery import run_sql
from invenio.utils.memoise import Memoise

def get_kbs_info(kbtypeparam="", searchkbname=""):
    """Returns all kbs as list of dictionaries {id, name, description, kbtype}
       If the KB is dynamic, the dynamic kb key are added in the dict.
    """
    out = []
    query = "SELECT id, name, description, kbtype FROM knwKB ORDER BY name"
    res = run_sql(query)
    for row in res:
        doappend = 1 # by default
        kbid = row[0]
        name = row[1]
        description = row[2]
        kbtype = row[3]
        dynres = {}
        if kbtype == 'd':
            #get the dynamic config
            dynres = get_kb_dyn_config(kbid)
        if kbtypeparam:
            doappend = 0
            if (kbtype == kbtypeparam):
                doappend = 1
        if searchkbname:
            doappend = 0
            if (name == searchkbname):
                doappend = 1
        if doappend:
            mydict = {'id':kbid, 'name':name,
                      'description':description,
                      'kbtype':kbtype}
            mydict.update(dynres)
            out.append(mydict)
    return out


def get_all_kb_names():
    """Returns all knowledge base names
       @return list of names
    """
    out = []
    res = run_sql("""SELECT name FROM knwKB""")
    for row in res:
        out.append(row[0])
    return out



def get_kb_id(kb_name):
    """Returns the id of the kb with given name"""
    res = run_sql("""SELECT id FROM knwKB WHERE name LIKE %s""",
                  (kb_name,))
    if len(res) > 0:
        return res[0][0]
    else:
        return None

get_kb_id_memoised = Memoise(get_kb_id)

def get_kb_name(kb_id):
    """Returns the name of the kb with given id
    @param kb_id the id
    @return string
    """
    res = run_sql("""SELECT name FROM knwKB WHERE id=%s""",
                  (kb_id,))
    if len(res) > 0:
        return res[0][0]
    else:
        return None

def get_kb_type(kb_id):
    """Returns the type of the kb with given id
    @param kb_id knowledge base id
    @return kb_type
    """
    res = run_sql("""SELECT kbtype FROM knwKB WHERE id=%s""",
                  (kb_id,))
    if len(res) > 0:
        return res[0][0]
    else:
        return None

def get_kb_mappings(kb_name="", sortby="to", keylike="", valuelike="", match_type="s"):
    """Returns a list of all mappings from the given kb, ordered by key
    @param kb_name knowledge base name. if "", return all
    @param sortby the sorting criteria ('from' or 'to')
    @keylike return only entries where key matches this
    @valuelike return only entries where value matches this
    """
    out = []
    k_id = get_kb_id(kb_name)

    if len(keylike) > 0:
        if match_type == "s":
            keylike = "%"+keylike+"%"
    else:
        keylike = '%'
    if len(valuelike) > 0:
        if match_type == "s":
            valuelike = "%"+valuelike+"%"
    else:
        valuelike = '%'
    if not kb_name:
        res = run_sql("""SELECT m.id, m.m_key, m.m_value, m.id_knwKB,
                         k.name
                   FROM knwKBRVAL m, knwKB k
                   where m_key like %s
                   and m_value like %s
                   and m.id_knwKB = k.id""", (keylike, valuelike))
    else:
        res = run_sql("""SELECT m.id, m.m_key, m.m_value, m.id_knwKB,
                         k.name
               FROM knwKBRVAL m, knwKB k
               WHERE id_knwKB=%s
               and m.id_knwKB = k.id
               and m_key like %s
               and m_value like %s""", (k_id, keylike, valuelike))
    #sort res
    lres = list(res)
    if sortby == "from":
        lres.sort(lambda x, y:cmp(x[1], y[1]))
    else:
        lres.sort(lambda x, y:cmp(x[2], y[2]))
    for row in lres:
        out.append({'id':row[0], 'key':row[1],
                     'value': row[2],
                     'kbid': row[3], 'kbname': row[4]})
    return out

def get_kb_dyn_config(kb_id):
    """
    Returns a dictionary of 'field'=> y, 'expression'=> z
    for a knowledge base of type 'd'. The dictionary may have coll_id, collection.
    @param kb_id the id
    @return dict
    """
    res = run_sql("""SELECT output_tag, search_expression, id_collection
               FROM knwKBDDEF where
               id_knwKB = %s""", (kb_id, ))
    mydict = {}
    for row in res:
        mydict['field'] = row[0]
        mydict['expression'] = row[1]
        mydict['coll_id'] = row[2]
    #put a collection field if collection exists..
    if mydict.has_key('coll_id'):
        c_id =  mydict['coll_id']
        res = run_sql("""SELECT name from collection where id = %s""", (c_id,))
        if res:
            mydict['collection'] = res[0][0]
    return mydict

def save_kb_dyn_config(kb_id, field, expression, collection=""):
    """Saves a dynamic knowledge base configuration

    @param kb_id the id
    @param field the field where values are extracted
    @param expression ..using this expression
    @param collection ..in a certain collection (default is all)
    """
    #check that collection exists
    coll_id = None
    if collection:
        res = run_sql("""SELECT id from collection where name = %s""", (collection,))
        if res:
            coll_id = res[0][0]
    run_sql("""DELETE FROM knwKBDDEF where id_knwKB = %s""", (kb_id, ))
    run_sql("""INSERT INTO knwKBDDEF (id_knwKB, output_tag, search_expression, id_collection)
               VALUES (%s,%s,%s,%s)""", (kb_id, field, expression, coll_id))
    return ""

def get_kb_description(kb_name):
    """Returns the description of the given kb

    @param kb_id the id
    @return string
    """
    k_id = get_kb_id(kb_name)
    res = run_sql("""SELECT description FROM knwKB WHERE id=%s""", (k_id,))
    return res[0][0]

def add_kb(kb_name, kb_description, kb_type=None):
    """
    Adds a new kb with given name and description. Returns the id of
    the kb.

    If name already exists replace old value

    @param kb_name the name of the kb to create
    @param kb_description a description for the kb
    @return the id of the newly created kb
    """

    kb_db = 'w' #the typical written_as - change_to
    if not kb_type:
        pass
    else:
        if kb_type == 'taxonomy':
            kb_db = 't'
        if kb_type == 'dynamic':
            kb_db = 'd'
    run_sql("""REPLACE INTO knwKB (name, description, kbtype)
                VALUES (%s,%s,%s)""", (kb_name, kb_description, kb_db))
    return get_kb_id(kb_name)

def delete_kb(kb_name):
    """Deletes the given kb"""
    k_id = get_kb_id(kb_name)
    run_sql("""DELETE FROM knwKBRVAL WHERE id_knwKB = %s""", (k_id,))
    run_sql("""DELETE FROM knwKB WHERE id = %s""", (k_id,))
    #finally, delete from COLL table
    run_sql("""DELETE FROM knwKBDDEF where id_knwKB = %s""", (k_id,))
    return True


def kb_exists(kb_name):
    """Returns True if a kb with the given name exists"""
    rows = run_sql("""SELECT id FROM knwKB WHERE name = %s""",
                   (kb_name,))
    if len(rows) > 0:
        return True
    else:
        return False

def update_kb(kb_name, new_name, new_description=''):
    """Updates given kb with new name and (optionally) new description"""
    k_id = get_kb_id(kb_name)
    run_sql("""UPDATE knwKB
                  SET name = %s , description = %s
                WHERE id = %s""", (new_name, new_description, k_id))
    return True

def add_kb_mapping(kb_name, key, value):
    """Adds new mapping key->value in given kb"""
    k_id = get_kb_id(kb_name)
    run_sql("""REPLACE INTO knwKBRVAL (m_key, m_value, id_knwKB)
                VALUES (%s, %s, %s)""", (key, value, k_id))
    return True

def remove_kb_mapping(kb_name, key):
    """Removes mapping with given key from given kb"""
    k_id = get_kb_id(kb_name)
    run_sql("""DELETE FROM knwKBRVAL
                WHERE m_key = %s AND id_knwKB = %s""",
            (key, k_id))
    return True

def kb_mapping_exists(kb_name, key):
    """Returns true if the mapping with given key exists in the given kb"""
    if kb_exists(kb_name):
        k_id = get_kb_id(kb_name)
        rows = run_sql("""SELECT id FROM knwKBRVAL
                           WHERE m_key = %s
                             AND id_knwKB = %s""", (key, k_id))
        if len(rows) > 0:
            return True
    return False

def kb_key_rules(key):
    """Returns a list of 4-tuples that have a key->value mapping in some KB
       The format of the tuples is [kb_id, kb_name,key,value] """
    res = run_sql("""SELECT f.id, f.name, m.m_key, m.m_value
                     from knwKBRVAL as m JOIN
                     knwKB as f on
                     m.id_knwKB=f.id WHERE
                     m.m_key = %s""", (key, ))
    return res

def kb_value_rules(value):
    """Returns a list of 4-tuples that have a key->value mapping in some KB
       The format of the tuples is [kb_id, kb_name,key,value] """
    res = run_sql("""SELECT f.id, f.name, m.m_key, m.m_value from
                     knwKBRVAL as m JOIN
                     knwKB as f on
                     m.id_knwKB=f.id WHERE
                     m.m_value = %s""", (value, ))
    return res

def get_kb_mapping_value(kb_name, key):
    """
    Returns a value of the given key from the given kb.
    If mapping not found, returns None #'default'

    @param kb_name the name of a knowledge base
    @param key the key to look for
    #@param default a default value to return if mapping is not found
    """
    k_id = get_kb_id(kb_name)
    res = run_sql("""SELECT m_value FROM knwKBRVAL
                      WHERE m_key LIKE %s
                        AND id_knwKB = %s LIMIT 1""",
                  (key, k_id))
    if len(res) > 0:
        return res[0][0]
    else:
        return None # default

def update_kb_mapping(kb_name, key, new_key, new_value):
    """Updates the mapping given by key with new key and value"""
    k_id = get_kb_id(kb_name)
    run_sql("""UPDATE knwKBRVAL
                  SET m_key = %s , m_value = %s
                WHERE m_key = %s AND id_knwKB = %s""",
            (new_key, new_value, key, k_id))
    return True

#the following functions should be used by a higher level API

def get_kba_values(kb_name, searchname="", searchtype="s"):
    """Returns the "authority file" type of list of values for a
       given knowledge base.
       @param kb_name the name of the knowledge base
       @param searchname search by this..
       @param searchtype s=substring, e=exact, sw=startswith
    """
    k_id = get_kb_id(kb_name)
    if searchtype == 's' and searchname:
        searchname = '%'+searchname+'%'
    if searchtype == 'sw' and searchname: #startswith
        searchname = searchname+'%'

    if not searchname:
        searchname = '%'
    res = run_sql("""SELECT m_value FROM knwKBRVAL
                      WHERE m_value LIKE %s
                        AND id_knwKB = %s""",
                  (searchname, k_id))
    return res

def get_kbr_keys(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """Returns keys from a knowledge base
       @param kb_name the name of the knowledge base
       @param searchkey search using this key
       @param searchvalue search using this value
       @param searchtype s=substring, e=exact, sw=startswith
    """
    k_id = get_kb_id(kb_name)
    if searchtype == 's' and searchkey:
        searchkey = '%'+searchkey+'%'
    if searchtype == 's' and searchvalue:
        searchvalue = '%'+searchvalue+'%'
    if searchtype == 'sw' and searchvalue: #startswith
        searchvalue = searchvalue+'%'
    if not searchvalue:
        searchvalue = '%'
    if not searchkey:
        searchkey = '%'
    return run_sql("""SELECT m_key FROM knwKBRVAL
                      WHERE m_value LIKE %s
                      AND m_key LIKE %s
                        AND id_knwKB = %s""",
                  (searchvalue, searchkey, k_id))

def get_kbr_values(kb_name, searchkey="%", searchvalue="", searchtype='s', use_memoise=False):
    """Returns values from a knowledge base

       Note the intentional asymmetry between searchkey and searchvalue:
       If searchkey is unspecified or empty for substring, it matches anything,
       but if it is empty for exact, it matches nothing.
       If searchvalue is unspecified or empty, it matches anything in all cases.

       @param kb_name the name of the knowledge base
       @param searchkey search using this key
       @param searchvalue search using this value
       @param searchtype s=substring, e=exact, sw=startswith
       @param use_memoise: can we memoise while doing lookups?
       @type use_memoise: bool
       @return a list of values
    """
    if use_memoise:
        k_id = get_kb_id_memoised(kb_name)
    else:
        k_id = get_kb_id(kb_name)
    if searchtype == 's':
        searchkey = '%'+searchkey+'%'
    if searchtype == 's' and searchvalue:
        searchvalue = '%'+searchvalue+'%'
    if searchtype == 'sw' and searchvalue: #startswith
        searchvalue = searchvalue+'%'
    if not searchvalue:
        searchvalue = '%'
    return run_sql("""SELECT m_value FROM knwKBRVAL
                      WHERE m_value LIKE %s
                      AND m_key LIKE %s
                        AND id_knwKB = %s""",
                  (searchvalue, searchkey, k_id))

get_kbr_values_memoised = Memoise(get_kbr_values)

def get_kbr_items(kb_name, searchkey="", searchvalue="", searchtype='s'):
    """Returns dicts of 'key' and 'value' from a knowledge base
       @param kb_name the name of the knowledge base
       @param searchkey search using this key
       @param searchvalue search using this value
       @param searchtype s=substring, e=exact, sw=startswith
       @return a list of dictionaries [{'key'=>x, 'value'=>y},..]
    """
    k_id = get_kb_id(kb_name)
    if searchtype == 's' and searchkey:
        searchkey = '%'+searchkey+'%'
    if searchtype == 's' and searchvalue:
        searchvalue = '%'+searchvalue+'%'
    if searchtype == 'sw' and searchvalue: #startswith
        searchvalue = searchvalue+'%'
    if not searchvalue:
        searchvalue = '%'
    if not searchkey:
        searchkey = '%'
    res = []
    rows = run_sql("""SELECT m_key, m_value FROM knwKBRVAL
                      WHERE m_value LIKE %s
                      AND m_key LIKE %s
                        AND id_knwKB = %s""",
                  (searchvalue, searchkey, k_id))
    for row in rows:
        mdict = {}
        m_key = row[0]
        m_value = row[1]
        mdict['key'] = m_key
        mdict['value'] = m_value
        res.append(mdict)
    return res
