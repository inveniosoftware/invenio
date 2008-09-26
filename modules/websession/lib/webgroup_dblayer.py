# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

""" Database related functions for groups"""

__revision__ = "$Id$"

from time import localtime
from zlib import decompress

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_VERSION
from invenio.dbquery import run_sql, run_sql_cached, OperationalError
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.messages import gettext_set_language
from invenio.websession_config import CFG_WEBSESSION_GROUP_JOIN_POLICY


def get_groups_by_user_status(uid, user_status, login_method='INTERNAL'):
    """Select all the groups the user is admin of.
    @param uid: user id
    @return ((id_usergroup,
              group_name,
              group_description, ))
    """
    query = """SELECT g.id,
                      g.name,
                      g.description
               FROM usergroup g, user_usergroup ug
               WHERE ug.id_user=%s AND
                     ug.id_usergroup=g.id AND
                     ug.user_status=%s AND
                     g.login_method = %s
               ORDER BY g.name"""
    uid = int(uid)
    res = run_sql_cached(query, (uid, user_status, login_method), affected_tables=['usergroup', 'user_usergroup'])
    return res

def get_groups_by_login_method(uid, login_method):
    """Select all the groups the user is member of selecting the login_method.
    @param uid: user id
    @param login_method: the login_method (>0 external)
    @return ((id_usergroup,
              group_name,
              group_description, ))
    """
    query = """SELECT g.id,
                      g.name,
                      g.description
               FROM usergroup g, user_usergroup ug
               WHERE ug.id_user=%s AND
                     ug.id_usergroup=g.id AND
                     g.login_method=%s

               ORDER BY g.name"""
    uid = int(uid)
    res = run_sql_cached(query, (uid, login_method), affected_tables=['usergroup', 'user_usergroup'])
    return res

def get_groups_with_description(uid):
    """Select all the groups the user is member of.
    @param uid: user id
    @return ((id_usergroup,
              group_name,
              group_description, ))
    """
    query = """SELECT g.id,
                      g.name,
                      g.description
               FROM usergroup g, user_usergroup ug
               WHERE ug.id_user=%s AND
                     ug.id_usergroup=g.id
               ORDER BY g.name"""
    uid = int(uid)
    res = run_sql_cached(query, (uid, ), affected_tables=['usergroup', 'user_usergroup'])
    return res


def get_external_groups(uid):
    """Select all the groups the user is member of selecting the login_method.
    @param uid: user id
    @param login_method: the login_method (>0 external)
    @return ((id_usergroup,
              group_name,
              group_description, ))
    """
    query = """SELECT g.id,
                      g.name,
                      g.description
               FROM usergroup g, user_usergroup ug
               WHERE ug.id_user=%s AND
                     ug.id_usergroup=g.id AND
                     g.login_method != 'INTERNAL'

               ORDER BY g.name"""
    uid = int(uid)
    res = run_sql_cached(query, (uid, ), affected_tables=['usergroup', 'user_usergroup'])
    return res

def get_groups(uid):
    """Select all the groups id the user is member of."""
    query = """SELECT g.id, g.name
               FROM usergroup g, user_usergroup ug
               WHERE ug.id_user=%s AND
                     ug.id_usergroup=g.id
            """
    res = run_sql_cached(query, (uid, ), affected_tables=['usergroup', 'user_usergroup'])
    res = list(res)
    return res

def get_group_id(group_name, login_method):
    """@return the id of the group called group_name with given login_method."""
    return run_sql("""
        SELECT id FROM usergroup
        WHERE  login_method = %s AND name = %s""", (login_method, group_name,))

def get_login_method_groups(uid, login_method):
    """Select all the external groups of a particular login_method for which
    the user is subscrided.
    @return ((group_name, group_id))
    """
    return run_sql("""
        SELECT g.name as name, g.id as id
        FROM user_usergroup as u JOIN usergroup as g
        ON u.id_usergroup = g.id
        WHERE u.id_user = %s and g.login_method = %s""",
        (uid, login_method,))


def get_all_login_method_groups(login_method):
    """Select all the external groups of a particular login_method.
    @return ({group_name: group_id, ...})
    """
    return dict(run_sql("""
        SELECT name, id
        FROM usergroup
        WHERE login_method = %s""",
        (login_method,)))


def get_all_users_with_groups_with_login_method(login_method):
    """Select all the users that belong at least to one external group
    of kind login_method.
    """
    return dict(run_sql("""
        SELECT DISTINCT u.email, u.id
        FROM user AS u JOIN user_usergroup AS uu ON u.id = uu.id_user
        JOIN usergroup AS ug ON ug.id = uu.id_usergroup
        WHERE ug.login_method = %s""", (login_method,)))



def get_visible_group_list(uid, pattern=""):
    """List the group the user can join (not already member
    of the group regardless user's status).
     @return groups {id : name} whose name matches pattern
    """
    grpID = []
    groups = {}
    #list the group the user is member of"""
    query = """SELECT distinct(id_usergroup)
               FROM user_usergroup
               WHERE id_user=%s """
    uid = int(uid)
    res = run_sql(query, (uid,))
    map(lambda x: grpID.append(int(x[0])), res)
    query2 = """SELECT id,name
                FROM usergroup
                WHERE (join_policy='%s' OR join_policy='%s')""" % (
                        CFG_WEBSESSION_GROUP_JOIN_POLICY['VISIBLEOPEN'],
                        CFG_WEBSESSION_GROUP_JOIN_POLICY['VISIBLEMAIL'])

    if len(grpID) == 1 :
        query2 += """ AND id!=%i""" % grpID[0]
    elif len(grpID) > 1:
        query2 += """ AND id NOT IN %s""" % str(tuple(grpID))

    if pattern:
        try:
            res2 = run_sql(query2 + """ AND name RLIKE %s ORDER BY name""", (pattern,))
        except OperationalError:
            res2 = ()
    else:
        res2 = run_sql(query2 + """ ORDER BY name""")

    map(lambda x: groups.setdefault(x[0], x[1]), res2)
    return groups


def insert_new_group(uid,
                     new_group_name,
                     new_group_description,
                     join_policy,
                     login_method='INTERNAL'):
    """Create a new group and affiliate a user."""
    query1 = """INSERT INTO usergroup (id, name, description, join_policy,
                   login_method)
                VALUES (NULL,%s,%s,%s,%s)
                """
    params1 = (new_group_name,
               new_group_description,
               join_policy,
               login_method)
    res1 = run_sql(query1, params1)

    date = convert_datestruct_to_datetext(localtime())
    uid = int(uid)
    query2 = """INSERT INTO user_usergroup (id_user, id_usergroup, user_status,
                   user_status_date)
                VALUES (%s,%s,'A',%s)
                """
    params2 = (uid, res1, date)
    res2 = run_sql(query2, params2)
    return res1

def insert_only_new_group(new_group_name,
                          new_group_description,
                          join_policy,
                          login_method='INTERNAL'):
    """Create a group with no user in (yet).
    @return its id
    """

    query = """INSERT INTO usergroup (name, description, join_policy, login_method)
               VALUES (%s, %s, %s, %s)
            """
    res = run_sql(query, (new_group_name, new_group_description, join_policy, login_method))
    return res

def insert_new_member(uid,
                      grpID,
                      status):
    """Insert new member."""
    query = """INSERT INTO user_usergroup (id_user, id_usergroup, user_status,
                   user_status_date)
               VALUES (%s,%s,%s,%s)
            """
    date = convert_datestruct_to_datetext(localtime())
    res = run_sql(query, (uid, grpID, status, date))
    return res

def get_group_infos(grpID):
    """Get group infos."""
    query = """SELECT id,name,description,join_policy,login_method FROM usergroup
                WHERE id = %s"""
    grpID = int(grpID)
    res = run_sql(query, (grpID, ))
    return res

def get_all_groups_description(login_method):
    """Get all groups description, dictionary with key name."""
    query = """SELECT name, description
               FROM usergroup
               WHERE login_method = %s
            """
    res = run_sql(query, (login_method, ))
    if res:
        return dict(res)
    else:
        return {}

def update_group_infos(grpID,
                       group_name,
                       group_description,
                       join_policy):
    """Update group."""
    res = run_sql("""UPDATE usergroup
                        SET name=%s, description=%s, join_policy=%s
                      WHERE id=%s""",
                  (group_name, group_description, join_policy, grpID))
    return res

def get_user_status(uid, grpID):
    """Get the status of the user for the given group."""
    query = """SELECT user_status FROM user_usergroup
                WHERE id_user = %s
                AND id_usergroup=%s"""
    uid = int(uid)
    grpID = int(grpID)
    res = run_sql(query, (uid, grpID))
    return res


def get_users_by_status(grpID, status, ln=CFG_SITE_LANG):
    """Get the list of users with the given status.
    @return ((id, nickname),) nickname= user # uid if
    the user has no nickname
    """
    _ = gettext_set_language(ln)
    res = run_sql("""SELECT ug.id_user, u.nickname
                       FROM user_usergroup ug, user u
                      WHERE ug.id_usergroup = %s
                        AND ug.id_user=u.id
                        AND user_status = %s""",
                  (grpID, status))
    users = []
    if res:
        for (mid, nickname) in res:
            nn = nickname
            if not nickname:
                nn = _("user") + "#%i" % mid
            users.append((mid, nn))
    return tuple(users)

def delete_member(grpID, member_id):
    """Delete member."""
    query = """DELETE FROM user_usergroup
               WHERE id_usergroup = %s
               AND id_user = %s"""
    grpID = int(grpID)
    member_id = int(member_id)
    res = run_sql(query, (grpID, member_id))
    return res


def delete_group_and_members(grpID):
    """Delete the group and its members."""
    query = """DELETE FROM usergroup
               WHERE id = %s
               """
    grpID = int(grpID)
    res = run_sql(query, (grpID,))
    query = """DELETE FROM user_usergroup
               WHERE id_usergroup = %s
               """
    res = run_sql(query, (grpID,))
    return res

def add_pending_member(grpID, member_id, user_status):
    """Change user status:
    Pending member becomes normal member"""
    date = convert_datestruct_to_datetext(localtime())
    res = run_sql("""UPDATE user_usergroup
                        SET user_status = %s, user_status_date = %s
                        WHERE id_usergroup = %s
                        AND id_user = %s""",
                  (user_status, date, grpID, member_id))
    return res


def leave_group(grpID, uid):
    """Remove user from the group member list."""
    query = """DELETE FROM user_usergroup
               WHERE id_usergroup=%s
               AND id_user=%s"""
    grpID = int(grpID)
    uid = int(uid)
    res = run_sql(query, (grpID, uid))
    return res

def drop_external_groups(userId):
    """Drops all the external groups memberships of userid."""
    query = """DELETE user_usergroup FROM user_usergroup, usergroup
               WHERE user_usergroup.id_user=%s
               AND usergroup.id = user_usergroup.id_usergroup
               AND usergroup.login_method <> 'INTERNAL'"""
    return run_sql(query, (userId,))

def group_name_exist(group_name, login_method='INTERNAL'):
    """Get all group id whose name like group_name and login_method."""
    query = """SELECT id
               FROM usergroup
               WHERE login_method=%s AND name=%s"""
    res = run_sql(query, (group_name, login_method,))
    return res


def get_group_login_method(grpID):
    """Return the login_method of the group or None if the grpID doesn't exist."""
    query = """SELECT login_method
               FROM usergroup
               WHERE id=%s"""
    res = run_sql(query, (grpID, ))
    if res:
        return res[0][0]
    else:
        return None

def count_nb_group_user(uid, user_status):
    """
    @param uid: user id
    @param status: member status
    @return integer of number of groups the user belongs to
    with the given status, 0 if none
    """
    res = run_sql("""SELECT count(id_user)
                       FROM   user_usergroup
                      WHERE  id_user = %s
                        AND user_status = %s""",
                  (uid, user_status))
    if res:
        return int(res[0][0])
    else:
        return 0

def get_all_users():
    """@return all the email:id"""
    query = """SELECT UPPER(email), id
               FROM user
               WHERE email != ''
            """
    res = run_sql(query)
    if res:
        return dict(res)
    else:
        return {}

def get_users_in_group(grpID):
    """@return all uids of users belonging to group grpID"""

    grpID = int(grpID)
    query = """SELECT id_user
               FROM user_usergroup
               WHERE id_usergroup = %s
            """
    res = run_sql(query, (grpID, ))
    return [uid[0] for uid in res]

########################## helpful functions ##################################

def __decompress_last(item):
    """private function, used to shorten code"""
    item = list(item)
    item[-1] = decompress(item[-1])
    return item
