# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2015 CERN.
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

"""Database access related functions."""

import time
import zlib

from invenio.legacy.dbquery import run_sql
from invenio.utils.date import localtime_to_utc


def get_creation_date(sysno, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """Return the creation date of the record 'sysno'.

    :param sysno: the record ID for which we want to retrieve creation date
    :param fmt: output format for the returned date
    :return: creation date of the record
    @rtype: string
    """
    out = ""
    res = run_sql("SELECT DATE_FORMAT(creation_date, '%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res[0][0]:
        out = localtime_to_utc(res[0][0], fmt)
    return out

def get_modification_date(sysno, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    Returns the date of last modification for the record 'sysno'.

    :param sysno: the record ID for which we want to retrieve modification date
    :param fmt: output format for the returned date
    :return: modification date of the record
    @rtype: string
    """
    out = ""
    res = run_sql("SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res and res[0][0]:
        out = localtime_to_utc(res[0][0], fmt)
    return out

# XML Marc related functions
def get_tag_from_name(name):
    """
    Returns the marc code corresponding the given name

    :param name: name for which we want to retrieve the tag
    :return: a tag corresponding to X{name} or None if not found
    """
    res = run_sql("SELECT value FROM tag WHERE name LIKE %s", (name,))
    if len(res)>0:
        return res[0][0]
    else:
        return None

def get_tags_from_name(name):
    """
    Returns the marc codes corresponding the given name,
    ordered by value

    :param name: name for which we want to retrieve the tags
    :return: list of tags corresponding to X{name} or None if not found
    """
    res = run_sql("SELECT value FROM tag WHERE name LIKE %s ORDER BY value", (name,))
    if len(res)>0:
        return list(res[0])
    else:
        return None

def tag_exists_for_name(name):
    """
    Returns True if a tag exists for name in 'tag' table.

    :param name: name for which we want to check if a tag exist
    :return: True if a tag exist for X{name} or False
    """
    rows = run_sql("SELECT value FROM tag WHERE name LIKE %s", (name,))
    if len(rows) > 0:
        return True
    return False

def get_name_from_tag(tag):
    """
    Returns the name corresponding to a marc code

    :param tag: tag to consider
    :return: a name corresponding to X{tag}
    """
    res = run_sql("SELECT name FROM tag WHERE value LIKE %s", (tag,))
    if len(res)>0:
        return res[0][0]
    else:
        return None

def name_exists_for_tag(tag):
    """
    Returns True if a name exists for tag in 'tag' table.

    :param tag: tag for which we want to check if a name exist
    :return: True if a name exist for X{tag} or False
    """
    rows = run_sql("SELECT name FROM tag WHERE value LIKE %s", (tag,))
    if len(rows) > 0:
        return True
    return False

def get_all_name_tag_mappings():
    """
    Return the list of mappings name<->tag from 'tag' table.

    The returned object is a dict with name as key (if 2 names are the same
    we will take the value of one of them, as we cannot make the difference in format
    templates)

    :return: a dict containing list of mapping in 'tag' table
    """
    out = {}
    query = "SELECT value, name FROM tag"
    res = run_sql(query)
    for row in res:
        out[row[1]] = row[0]
    return out


# Output formats related functions

def get_output_format_id(code):
    """
    Returns the id of output format given by code in the database.

    Output formats are located inside 'format' table

    :param code: the code of an output format
    :return: the id in the database of the output format. None if not found
    """
    f_code = code
    if len(code)>6:
        f_code = code[:6]
    res = run_sql("SELECT id FROM format WHERE code=%s", (f_code.lower(),))
    if len(res)>0:
        return res[0][0]
    else:
        return None

def add_output_format(code, name="", description="", content_type="text/html", visibility=1):
    """
    Add output format into format table.

    If format with given code already exists, do nothing

    :param code: the code of the new format
    :param name: a new for the new format
    :param description: a description for the new format
    :param content_type: the content_type (if applicable) of the new output format
    :param visibility: if the output format is shown to users (1) or not (0)
    :return: None
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        query = "INSERT INTO format SET code=%s, description=%s, content_type=%s, visibility=%s"
        params = (code.lower(), description, content_type, visibility)
        run_sql(query, params)
        set_output_format_name(code, name)

def remove_output_format(code):
    """
    Removes the output format with 'code'

    If code does not exist in database, do nothing.
    The function also removes all localized names in formatname table.

    :param code: the code of the output format to remove
    :return: None
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        return

    query = "DELETE FROM formatname WHERE id_format='%s'" % output_format_id
    run_sql(query)
    query = "DELETE FROM format WHERE id='%s'" % output_format_id
    run_sql(query)

def get_output_format_description(code):
    """Return the description of the output format given by code.

    If code or description does not exist, return empty string.

    :param code: the code of the output format to get the description from
    :return: output format description
    """

    res = run_sql("SELECT description FROM format WHERE code=%s", (code,))
    if len(res) > 0:
        res = res[0][0]
        if res is not None:
            return res
    return ""

def set_output_format_description(code, description):
    """
    Sets the description of an output format, given by its code

    If 'code' does not exist, create format

    :param code: the code of the output format to update
    :param description: the new description
    :return: None
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        add_output_format(code, "", description)

    query = "UPDATE format SET description=%s WHERE code=%s"
    params = (description, code.lower())
    run_sql(query, params)

def get_output_format_visibility(code):
    """
    Returns the visibility of the output format, given by its code

    If code does not exist, return 0.

    :param code: the code of an output format
    :return: output format visibility (0 if not visible, 1 if visible
    """
    res = run_sql("SELECT visibility FROM format WHERE code=%s", (code,))
    if len(res) > 0:
        res = res[0][0]
        if res is not None and int(res) in range(0, 2):
            return int(res)
    return 0

def set_output_format_visibility(code, visibility):
    """
    Sets the visibility of an output format, given by its code

    If 'code' does not exist, create format

    :param code: the code of the output format to update
    :param visibility: the new visibility (0: not visible, 1:visible)
    :return: None
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        add_output_format(code, "", "", "", visibility)

    query = "UPDATE format SET visibility=%s WHERE code=%s"
    params = (visibility, code.lower())
    run_sql(query, params)


def set_output_format_content_type(code, content_type):
    """
    Sets the content_type of an output format, given by its code

    If 'code' does not exist, create format

    :param code: the code of the output format to update
    :param content_type: the content type for the format
    :return: None
    """
    output_format_id = get_output_format_id(code)
    if output_format_id is None:
        # add one if not exist (should not happen)
        add_output_format(code, "", "", content_type)

    query = "UPDATE format SET content_type=%s WHERE code=%s"
    params = (content_type, code.lower())
    run_sql(query, params)


def set_output_format_name(code, name, lang="generic", type='ln'):
    """Set the name of an output format given by code.

    If 'type' different from 'ln' or 'sn', do nothing.
    If 'name' exceeds 256 chars, 'name' is truncated to first 256 chars.
    If 'code' does not correspond to exisiting output format, create format.
    If "generic" is given has lang.

    The localized names of output formats are located in formatname table.

    :param code: the code of an ouput format
    :param type: either 'ln' (for long name) and 'sn' (for short name)
    :param lang: the language in which the name is given
    :param name: the name to give to the output format
    :return: None
    """

    if len(name) > 256:
        name = name[:256]
    if type.lower() != "sn" and type.lower() != "ln":
        return
    output_format_id = get_output_format_id(code)
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
        run_sql("REPLACE INTO formatname SET id_format=%s, ln=%s, type=%s, value=%s",
                (output_format_id, lang, type.lower(), name))

def change_output_format_code(old_code, new_code):
    """Change the code of an output format.

    :param old_code: the code of the output format to change
    :param new_code: the new code
    :return: None
    """
    output_format_id = get_output_format_id(old_code)
    if output_format_id is None:
        return

    query = "UPDATE format SET code=%s WHERE id=%s"
    params = (new_code.lower(), output_format_id)
    run_sql(query, params)

def get_preformatted_record(recID, of, decompress=zlib.decompress):
    """Return the preformatted record with id 'recID' and format 'of'.

    Note that second item in tuple is True if we need a 2nd pass.
    If corresponding record does not exist for given output format,
    returns None.

    :param recID: the id of the record to fetch
    :param of: the output format code
    :param decompress: the method used to decompress the preformatted record in database
    :return: formatted record as String, or None if not exist
    """
    # Decide whether to use DB slave:
    if of in ('xm', 'recstruct'):
        run_on_slave = False # for master formats, use DB master
    else:
        run_on_slave = True # for other formats, we can use DB slave
    # Try to fetch preformatted record
    query = """SELECT value, needs_2nd_pass FROM bibfmt
               WHERE id_bibrec = %s AND format = %s"""
    params = (recID, of)
    res = run_sql(query, params, run_on_slave=run_on_slave)
    if res:
        value = decompress(res[0][0])
        needs_2nd_pass = bool(res[0][1])
        # record 'recID' is formatted in 'of', so return it
        return value, needs_2nd_pass
    else:
        return None, None


def save_preformatted_record(recID, of, res, needs_2nd_pass=False,
                             low_priority=False, compress=zlib.compress):
    """Store preformated record in the database."""
    start_date = time.strftime('%Y-%m-%d %H:%M:%S')
    formatted_record = compress(res)
    sql_str = ""
    if low_priority:
        sql_str = " LOW_PRIORITY"
    run_sql("""INSERT%s INTO bibfmt
               (id_bibrec, format, last_updated, value, needs_2nd_pass)
               VALUES (%%s, %%s, %%s, %%s, %%s)
               ON DUPLICATE KEY UPDATE
                    last_updated = VALUES(last_updated),
                    value = VALUES(value),
                    needs_2nd_pass = VALUES(needs_2nd_pass)
               """ % sql_str,
            (recID, of, start_date, formatted_record, needs_2nd_pass))
