# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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

from __future__ import print_function

"""
*** HIGHLY EXPERIMENTAL; PLEASE DO NOT USE. ***

Invenio configuration dumper and loader CLI tool.

Usage: python inveniocfg_dumperloader.py [options]

General options:
   -h, --help                            print this help
   -V, --version                         print version number

Dumper options:
   -d file                               dump the collections into a INI file
       -col COLLECTION1,COLLECTION2...   collection/s to dump
       -all                              dump all the collections
       --force-ids                       also dump the ids of the tables to the file
       --output                          print the file in the screen

Loader options:
   -l file                               load a file into the database
      -mode i|c|r                        select the mode to load(insert, correct, replace)
"""

__revision__ = "$Id$"

import sys
import random
import re
import datetime
import StringIO
from string import Template
from invenio.legacy.dbquery import run_sql, wash_table_column_name

from configobj import ConfigObj

IDENT_TYPE = "    " #Identation in the *.INI file can be a tab/spaces/etc...

MESSAGES = [] #List of messages to display to the user at the end of the execution

LOAD_DEFAULT_MODE = 'i'

SEPARATOR = '.'

#Dict of blacklisted fields and the message to display
BLACKLIST_TABLE_COLUMNS = {
  'collection.reclist': '#INFO Please rerun webcoll.',
  'accROLE.firefole_def_ser': '#INFO Please rerun webaccessadmin -c.',
  'score':'#INFO Run whatever relevant',
  'tag.value':'#INFO Please run inveniocfg --do-something',
  'field_tag.score':'#INFO please run inveniocfg --fill-scores'
}

COLLECTIONS = {

    'FIELD' : {
                     'tables':{
                     'field':'extend(field.id=fieldname.id_field,fieldname.$ln.$type = $value)',
                     'field_tag':'field_tag.id_field = field.id, field_tag.id_tag = tag.id',
                     'tag':'normal'},
                     'relations':'field-field_tag-tag',
                     },
    'COLLECTION' : {
        'tables':{
            'collection':'normal',
            'collection_example':'collection_example.id_example = example.id, collection_example.id_collection = collection.id',
            'example':'normal'},
        'relations':'collection-collection_example-example',
        },
    'PORTALBOX' : {
        'tables':{
            'collection':'normal',
            'collection_portalbox':'collection_portalbox.id_portalbox = portalbox.id, collection_portalbox.id_collection = collection.id',
            'portalbox':'normal',
        },
        'relations':'collection-collection_portalbox-portalbox',
     },
}


def print_usage():
    """Print help."""
    print(__doc__)

def create_section_id(num, with_date=True):
    """
    Generate a unique section id.
    Convert the given number in base 18 and append a 5 digit random string
    If with_date=True append the date at the beginnig so it can be ordered.
    Estructure:
    if with_date:
           date . base18(id) . 5 random chars    e.g. tag.2010-07-30.ddcbz2lf
    else:
           base18(id) . 5 random chars   e.g. field.ddcbz2lf
    """
    digits = "abcdefghijklmnopqrstuvwxyz0123456789"
    str_id = ""
    tail = ''.join([random.choice(digits) for x in range(4)])
    while 1:
        rest = num % 18
        str_id = digits[rest] + str_id
        num = num / 18
        if num == 0:
            break
    if with_date == True:
        date = str(datetime.date.today())
        return date + "."  + str_id + tail
    return str_id + tail

def dict2db(table_name, dict_data, mode):
    """
    Load the dict values into the database
    Three modes of operation:
    i - insert
    r - replace
    c - correct
    """
    #Escape all the content in dict data to avoid " and '
    for data in dict_data:
        dict_data[data] = re.escape(dict_data[data])

    if mode == 'i': #Insert mode
        query_fields = " , " .join(dict_data.keys())
        query_values = "' , '" .join(dict_data.values())
        query = "INSERT IGNORE INTO %s(%s) VALUES ('%s')" % (wash_table_column_name(table_name),
                                                            query_fields,
                                                            query_values)
    elif mode == 'c': #Correct mode
        if '_' in table_name:
            query = "SELECT * FROM %s" % table_name#FIXIT Trick to execute something instead of giving error
        else:
            tbl_id = get_primary_keys(table_name)[0]
            del dict_data[tbl_id]
            query_update = " , " .join(["%s=\'%s\'" % (field, dict_data[field]) for field in dict_data])
            query = "UPDATE %s SET %s" % (wash_table_column_name(table_name),
                                         query_update)
    else: #Try in the default mode
        dict2db(table_name, dict_data, LOAD_DEFAULT_MODE)
    try:
        run_sql(query)
    except:
        print("VALUES: %s ALREADY EXIST IN TABLE %s. SKIPPING" % (query_values, table_name))
        pass

def query2list(query, table_name):
    """Given a SQL query return a list of dictionaries with the results"""
    results = run_sql(query, with_desc=True)
    lst_results = []
    dict_results = {}
    for section_id, result in enumerate(results[0]):
        dict_results = {}
        for index, field in enumerate(results[1]):
            if not is_blacklisted(table_name, field[0]):
                dict_results[field[0]] = result[index]
        lst_results.append(dict_results)
    return lst_results

def get_primary_keys(table_name):
    """
    Get the primary keys from the table with the DESC mysql function
    """
    lst_keys = []
    query = "DESC %s" % wash_table_column_name(table_name)
    results = run_sql(query)
    for field in results:
        if field[3] == 'PRI':
            lst_keys.append(field[0])
    return lst_keys

def get_unused_primary_key(table_name):
    """
    Returns the first free id from a table
    """
    table_id = get_primary_keys(table_name)[0]#FIXIT the table can have more than an id
    query = "SELECT %s FROM %s" % (table_id, table_name)
    results = query2list(query, table_name)
    list_used_ids = [result[table_id] for result in results]
    for unused_id in range(1, len(list_used_ids)+2):
        if not unused_id in list_used_ids:
            return str(unused_id)

def is_blacklisted(table, field):
    """
    Check if the current field is blacklisted, if so add the message to the messages list
    """
    if (table+ "." + field) in BLACKLIST_TABLE_COLUMNS.keys():
        msg = BLACKLIST_TABLE_COLUMNS[(table + "." + field)]
        if not msg in MESSAGES:
            MESSAGES.append(msg)
        return True
    return False

def get_relationship(collection, table, field_id):
    """Return the name of the related field"""
    tbl_field = table + "." + field_id
    dict_relationship = {}
    for tbl in collection['tables'].values():
        if tbl_field in tbl:
            for foo in tbl.split(","):
                dict_value, dict_key = foo.split("=")
                dict_relationship[dict_key.strip()] = dict_value
    return dict_relationship

def delete_keys_from_dict(dict_del, lst_keys):
    """
    Delete the keys present in the lst_keys from the dictionary.
    Loops recursively over nested dictionaries.
    """
    for k in lst_keys:
        try:
            del dict_del[k]
        except KeyError:
            pass
    for v in dict_del.values():
        if isinstance(v, dict):
            delete_keys_from_dict(v, lst_keys)
    return dict_del

def extract_from_template(template, str_data):
    """
    Extract the values from a string given the template
    If the template and the string are different, this function may fail
    Return a dictionary with the keys from the template and the values from the string
    """
    #FIXIT this code can be more elegant
    lst_str_data = []
    dict_result = {}
    pattern = re.compile("\$\w*")
    patt_match = pattern.findall(template)
    lst_foo = str_data.split("=")
    for data in lst_foo:
        lst_str_data.extend(data.split("."))
    for index, data in enumerate(patt_match):
        data = data.replace('$','')
        dict_result[data] = lst_str_data[index+1].strip()
    return dict_result

def delete_ids(dict_fields, lst_tables):
    """
    Remove the ids of the tables from the dictionary
    """
    lst_primary = []
    for tbl in lst_tables:
        lst_primary.extend(get_primary_keys(tbl))
    return delete_keys_from_dict(dict_fields, lst_primary)

def add_special_field(collection, tbl_name , dict_data):
    """Add the value for the translation to the dictionary"""
    str_template = collection['tables'][tbl_name].split(",")[1][:-1]#FIXIT if the final character is other?
    template_key, template_value = str_template.split("=")
    template_key = Template(template_key.strip())
    template_value = Template(template_value.strip())
    id_field = dict_data['id']
    query = "SELECT * FROM %s WHERE %s=%s" % ("fieldname", "id_field", id_field)
    result = query2list(query, "fieldname")
    if result:
        for res in result:
            dict_data[template_key.safe_substitute(res)] = template_value.safe_substitute(res)

def dump_collection(collection, config, force_ids, print_to_screen=False):
    """
    Dump the current collection
    Note: there are a special notation, ori(origin) - rel(relation) - fin(final)
    For example in the relation field-field_tag-tag:
    ori(origin): field table
    rel(relation): field_tag
    fin(final): tag
    """
    tbl_ori, tbl_rel, tbl_fin = collection['relations'].split("-")
    query = "SELECT * FROM %s" % (wash_table_column_name(tbl_ori))
    lst_ori = query2list(query, tbl_ori)
    tbl_ori_id = get_primary_keys(tbl_ori)[0]
    for index_ori, result_ori in enumerate(lst_ori):
        dict_rels = get_relationship(collection, tbl_ori, tbl_ori_id)
        query = "SELECT * FROM %s WHERE %s=%s" % (wash_table_column_name(tbl_rel),
                                                 dict_rels[tbl_ori+"."+tbl_ori_id],
                                                 result_ori[tbl_ori_id])
        if collection['tables'][tbl_ori].startswith('extend'):
            add_special_field(collection, tbl_ori, result_ori)
        lst_rel = query2list(query, tbl_rel)
        for result_rel in lst_rel:
            tbl_fin_id = get_primary_keys(tbl_fin)[0]
            tbl_rel_id = dict_rels[tbl_fin+"."+tbl_fin_id].split(".")[1].strip()
            query = "SELECT * FROM %s WHERE %s=%s" % (wash_table_column_name(tbl_fin),
                                                     tbl_fin_id, result_rel[tbl_rel_id])
            lst_fin = query2list(query, tbl_fin)
            for index_fin, result_fin in enumerate(lst_fin):
                result_ori[tbl_fin+"."+create_section_id(index_fin, with_date=False)] = result_fin

        section_name = tbl_ori + "." + create_section_id(index_ori)
        if force_ids == False:#Remove the ids from the dict
            results = delete_ids(result_ori, collection['relations'].split("-"))
            config[section_name] = results
        else:
            config[section_name] = result_ori

        if print_to_screen == True:
            output = StringIO.StringIO()
            config.write(output)#Write to the output string instead of the file
            print(output.getvalue())
        else:
            config.write()

def get_collection(table_name):
    """Get the collection asociated with the section"""
    for collection in COLLECTIONS.items():
        if table_name in collection[1]['relations'].split("-")[0]:
            return COLLECTIONS[collection[0]]#this is the collection to load

def load_section(section_name, dict_data, mode):
    """
    Load the section back into the database

    table_name is the name of the main section
    There are some special notation: ori(origin) - rel(related) - fin(final) - ext(extended)
    For example for the field-tag collection:
    ori: field
    ext: fieldname
    rel: field_tag
    fin:tag
    """
    table_ori = section_name.split(".")[0]
    collection = get_collection(table_ori)
    ori_definition = collection['tables'][table_ori]
    if ori_definition.startswith("extend"):
        tbl_ext_name = ori_definition.split(",")[1].split(SEPARATOR)[0]

    lst_tables = collection['relations'].split("-")

    ori_id = get_primary_keys(lst_tables[0])[0]
    ori_id_value = get_unused_primary_key(lst_tables[0])
    dict_data[ori_id] = ori_id_value#Add the calculated id to the dictionary
    #I will separate the dict_data into these 3 dicts corresponding to 3 different tables
    dict_ori = {}
    dict_rel = {}
    dict_ext = {}

    for field in dict_data:
        if type(dict_data[field]) == str:#the field is a string
            if "tbl_ext_name" in locals() and field.startswith(tbl_ext_name):#is extended table
                dict2db("fieldname",
                        extract_from_template("fieldname.$ln.$type = $value",
                                              str(field) + " = " + str(dict_data[field])),
                        mode)
            else:
                dict_ori[field] = dict_data[field]
        else:#if the field is a dictionary
            fin_id = get_primary_keys(lst_tables[2])[0]
            fin_id_value = get_unused_primary_key(lst_tables[2])
            dict_data[field][fin_id] = fin_id_value
            dict2db(lst_tables[2], dict_data[field], mode)#Insert the final into the DB

            fieldtag_ids = get_primary_keys(lst_tables[1])
            dict_rel[fieldtag_ids[0]] = ori_id_value
            dict_rel[fieldtag_ids[1]] = fin_id_value
            dict2db(lst_tables[1], dict_rel, mode)#Insert the relation into the DB

    dict2db(lst_tables[0], dict_ori, mode)

def cli_cmd_dump_config():
    """Dump the selected collection/s"""
    config = ConfigObj(indent_type=IDENT_TYPE)
    config.initial_comment = [
        str(datetime.datetime.now()),
        "This file is automatically generated by Invenio, running:",
        " ".join(sys.argv) ,
        "" ]

    force_ids = False
    if "--force-ids" in sys.argv:
        force_ids = True
    print_to_screen = False
    if '--output' in sys.argv:
        print_to_screen = True

    try:
        config.filename = sys.argv[sys.argv.index('-d') + 1]
    except:
        print_usage()

    if '-col' in sys.argv:
        try:
            collection = COLLECTIONS[sys.argv[sys.argv.index('-col') + 1].upper()]
            dump_collection(collection, config, force_ids, print_to_screen)
        except:
            print("ERROR: you must especify the collection to dump with the -col COLLECTION_NAME option")
    elif '-all' in sys.argv:
        for collection in COLLECTIONS:
            dump_collection(COLLECTIONS[collection], config, force_ids, print_to_screen)
    else:
        print("Please specify the collection to dump")

def cli_cmd_load_config():
    """Load all the config sections back into the database"""
    config = ConfigObj(sys.argv[sys.argv.index('-l') + 1])
    mode = "r"
    if '-mode' in sys.argv:
        try:
            mode = sys.argv[sys.argv.index('-mode') + 1]
            if mode not in ['i', 'c', 'r']:
                print("Not valid mode please select one of the following (i)nsert, (c)orrect or (r)eplace")
                sys.exit(1)
        except IndexError:
            print("You must especify the mode with the -mode option")
            sys.exit(1)

    for section in config.sections:
        load_section(section, config[section], mode)

def main():
    """
    Main section, makes the calls to all the functions
    """
    if  "-d" in sys.argv:
        cli_cmd_dump_config()
    elif "-l" in sys.argv:
        cli_cmd_load_config()
    elif "-h" in sys.argv:
        print_usage()
    else:
        print_usage()

    for message in MESSAGES:
        print(message)

if __name__ == '__main__':
    main()
