# -*- coding: utf-8 -*-

## $Id$
## 
## db-related function of group 
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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
""" Database related functions for groups"""
from time import localtime
from zlib import decompress
from MySQLdb import escape_string
from invenio.dbquery import run_sql
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.messages import gettext_set_language
from invenio.config import *

def get_groups_by_user_status(uid, user_status):
    """Select all the groups the user is admin of
    @param uid: user id
    @return ((id_usergroup,
              group_name,
              group_description, ))
    """
    query = """SELECT g.id,
                      g.name,
                      g.description
               FROM usergroup g, user_usergroup ug
               WHERE ug.id_user=%i AND
                     ug.id_usergroup=g.id AND
                     ug.user_status="%s"
               
               ORDER BY g.name"""
    uid = int(uid)
    res = run_sql(query % (uid, escape_string(user_status)))
    return res  

def get_visible_group_list(uid, pattern=""):
    """list the group the user can join"""
    grpID = []
    groups = {}
    #list the group the user is member of"""
    query = """SELECT distinct(id_usergroup)
               FROM user_usergroup 
               WHERE id_user=%i """
    uid = int(uid)
    query %= uid
    res = run_sql(query)
    map(lambda x: grpID.append(int(x[0])), res)
    query2 = """SELECT id,name
                FROM usergroup"""
    if len(grpID) == 0 :
        query2 += " WHERE 1=1"
    elif len(grpID) == 1 :
        query2 += """ WHERE id!=%i""" % grpID[0]
    else:
        query2 += """ WHERE id NOT IN %s""" % str(tuple(grpID))

    if pattern:
        pattern_query = """ AND name RLIKE '%s'""" % escape_string(pattern)
        query2 += pattern_query
    query2 += """ ORDER BY name"""
    res2 = run_sql(query2)
    map(lambda x: groups.setdefault(x[0], x[1]), res2)
    return groups

def get_groupnames_like(uid, pattern=""):
    """Get groupnames like pattern. Will return only groups that user is allowed to see
    """
    groups = {}
    query1 = "SELECT id, name FROM usergroup WHERE join_policy like 'V%%'"
    if pattern :
        query1 += """ AND name RLIKE '%s'"""
        pattern = escape_string(pattern)
        query1 %= pattern
    res = run_sql(query1)
    # The line belows inserts into groups dictionary every tuple the database returned, 
    # assuming field0=key and field1=value
    map(lambda x: groups.setdefault(x[0], x[1]), res)
    query2 = """SELECT g.id, g.name 
                FROM usergroup g, user_usergroup ug 
                WHERE g.id=ug.id_usergroup AND ug.id_user=%i"""
    if pattern :
        pattern_query = """ AND g.name RLIKE '%s'""" % escape_string(pattern)
        query2 += pattern_query
    res = run_sql(query2 % uid)
    map(lambda x: groups.setdefault(x[0], x[1]), res)
    return groups


def insert_new_group(uid,
                      new_group_name,
                      new_group_description,
                      join_policy):
    """Create a new group"""
    query1 = """INSERT INTO usergroup
                VALUES
                (NULL,'%s','%s','%s')
                """
    params1 = (escape_string(new_group_name),
               escape_string(new_group_description),
               escape_string(join_policy))
    res1 = run_sql(query1 % params1)

    date = convert_datestruct_to_datetext(localtime())
    uid = int(uid)
    query2 = """INSERT INTO user_usergroup
                VALUES
                (%i,'%i','A','%s')
                """
    params2 = (uid, res1, date)
    res2 = run_sql(query2 % params2)
    return res1  

def insert_new_member(uid,
                      grpID,
                      status):
    """Insert new member"""
    query = """INSERT INTO user_usergroup
                VALUES
                (%i,%i,'%s','%s')
                """
    date = convert_datestruct_to_datetext(localtime())
    uid = int(uid)
    grpID = int(grpID)
    query %= (uid, grpID, escape_string(status), date)
    res = run_sql(query)
    return res

def get_group_infos(grpID):
    """Get group infos"""
    query = """SELECT * FROM usergroup
                WHERE id = %i"""
    grpID = int(grpID)
    res = run_sql(query % grpID)
    return res

def update_group_infos(grpID,
                       group_name,
                       group_description,
                       join_policy):
    """Update group"""
    query = """UPDATE usergroup
               SET name="%s", description="%s", join_policy="%s"
               WHERE id = %i"""
    grpID = int(grpID)
    res = run_sql(query% (escape_string(group_name),
                          escape_string(group_description),
                          escape_string(join_policy), grpID))
    return res

def get_user_status(uid, grpID):
    """Get the status of the given user"""
    query = """SELECT user_status FROM user_usergroup
                WHERE id_user = %i
                AND id_usergroup=%i"""
    uid = int(uid)
    grpID = int(grpID)
    res = run_sql(query% (uid, grpID))
    return res


def get_users_by_status(grpID, status, ln=cdslang):
    """Get the list of users with the given status"""
    _ = gettext_set_language(ln)
    query = """SELECT ug.id_user, u.nickname
               FROM user_usergroup ug, user u
               WHERE ug.id_usergroup = %i
               AND ug.id_user=u.id
               AND user_status = '%s'"""
    grpID = int(grpID)
    res = run_sql(query% (grpID, escape_string(status)))
    users = []
    if res:
        for (mid, nickname) in res:
            nn = nickname
            if not nickname:
                nn = _("user #%i" % mid)
            users.append((mid, nn))
    return tuple(users)

def delete_member(grpID, member_id):
    """Delete member"""
    query = """DELETE FROM user_usergroup
               WHERE id_usergroup = %i
               AND id_user = %i"""
    grpID = int(grpID)
    member_id = int(member_id)
    res = run_sql(query% (grpID, member_id))
    return res


def delete_group(grpID):
    """Delete member"""
    query = """DELETE FROM usergroup
               WHERE id = %i
               """
    grpID = int(grpID)
    res = run_sql(query% grpID)
    return res

def delete_group_and_members(grpID):
    """Delete the group and its members"""
    query = """DELETE FROM usergroup
               WHERE id = %i
               """
    grpID = int(grpID)
    res = run_sql(query% grpID)
    query = """DELETE FROM user_usergroup
               WHERE id_usergroup = %i
               """
    res = run_sql(query% grpID)
    return res

def add_pending_member(grpID, member_id, user_status):
    """Pending member becomes normal member"""
    query = """UPDATE user_usergroup
               SET user_status = '%s',user_status_date='%s'
               WHERE id_usergroup = %i
               AND id_user = %i"""
    date = convert_datestruct_to_datetext(localtime())
    grpID = int(grpID)
    member_id = int(member_id)
    res = run_sql(query% (escape_string(user_status), date, grpID, member_id))
    return res


def leave_group(grpID, uid):
    query = """DELETE FROM user_usergroup
               WHERE id_usergroup=%i
               AND id_user=%i"""
    grpID = int(grpID)
    uid = int(uid)
    res = run_sql(query% (grpID, uid))
    return res

def group_name_exist(group_name):
    query = """SELECT id
               FROM usergroup
               WHERE name='%s'"""
    res = run_sql(query % escape_string(group_name))
    return res

########################## helpful functions ##################################

def __wash_count(res):
    """If query is like SELECT count(x) FROM y, return a washed version"""
    if res:
        return int(res[0][0])
    else:
        return 0
        
def __decompress_last(item):
    """private function, used to shorten code"""
    item = list(item)
    item[-1] = decompress(item[-1])
    return item
