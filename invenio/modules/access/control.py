# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
#               2015 CERN.
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

"""Invenio Access Control Admin."""

from __future__ import print_function

import urlparse

from flask import current_app

from intbitset import intbitset

from invenio.config import CFG_SITE_ADMIN_EMAIL, CFG_SITE_LANG, CFG_SITE_RECORD
from invenio.ext import principal
from invenio.ext.sqlalchemy import db
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.firerole import (
    acc_firerole_check_user, compile_role_definition, deserialize,
    load_role_definition, serialize
)
from invenio.modules.access.local_config import (
    CFG_ACC_ACTIVITIES_URLS, CFG_ACC_EMPTY_ROLE_DEFINITION_SER,
    CFG_ACC_EMPTY_ROLE_DEFINITION_SRC, DEF_AUTHS, DEF_ROLES, DEF_USERS,
    DELEGATEADDUSERROLE, SUPERADMINROLE
)
from invenio.modules.access.models import AccACTION, AccAuthorization, \
    UserAccROLE

from six import iteritems

from sqlalchemy.exc import ProgrammingError


def acc_add_action(name_action='', description='', optional='no',
                   *allowedkeywords):
    """Create new entry in accACTION for an action.

    :param name_action: name of the new action, must be unique
    :param allowedkeywords: a list of allowedkeywords

    :return: id_action, name_action, description and allowedkeywords or
             0 in case of failure
    """
    keystr = ''
    # action with this name already exists, return 0
    if db.session.query(
            AccACTION.query.filter(
                AccACTION.name == name_action).exists()).scalar():
        return 0

    # create keyword string
    for value in allowedkeywords:
        if keystr:
            keystr += ','
        keystr += value

    if not allowedkeywords:
        optional = 'no'

    # insert the new entry
    try:
        a = AccACTION(name=name_action, description=description,
                      allowedkeywords=keystr, optional=optional)
        db.session.add(a)
        db.session.commit()
        return True, name_action, description, keystr, optional
    except ProgrammingError:
        return 0


def acc_delete_action(id_action=0, name_action=0):
    """Delete action in accACTION according to id, or secondly name.

    entries in accROLE_accACTION_accARGUMENT will also be removed.
    If the name or id is wrong, the function does nothing.

    :param id_action: id of action to be deleted, prefered variable
    :param name_action: this is used if id_action is not given
    """
    id_action = id_action or acc_get_action_id(name_action=name_action)
    if not id_action:
        return 0

    # delete the action
    if run_sql("""DELETE FROM "accACTION" WHERE id=%s""", (id_action, )):
        # delete all entries related
        return 1 + run_sql("""DELETE FROM "accROLE_accACTION_accARGUMENT" WHERE
            "id_accACTION" =%s""", (id_action, ))
    else:
        return 0


def acc_verify_action(name_action='', description='', allowedkeywords='',
                      dummy=''):
    """Check action.

    check if all the values of a given action are the same as
    those in accACTION in the database. self explanatory parameters.

    return id if identical, 0 if not.
    """
    id_action = acc_get_action_id(name_action=name_action)

    if not id_action:
        return 0

    res_desc = acc_get_action_description(id_action=id_action)
    res_keys = acc_get_action_keywords_string(id_action=id_action)

    bool_desc = res_desc == description and 1 or 0
    bool_keys = res_keys == allowedkeywords and 1 or 0
    bool_opti = acc_get_action_is_optional(id_action=id_action)

    return bool_desc and bool_keys and bool_opti and id_action or 0


def acc_update_action(id_action=0, name_action='', verbose=0, **update):
    """Try to change the values of given action details.

    if there is no change nothing is done.
    some changes require to update other parts of the database.

    :param id_action: id of the action to change
    :param name_action: if no id_action is given try to find it using this name
    :param **update: dictionary containg keywords: description, allowed
        keywords and/or optional other keywords are ignored
    """
    id_action = id_action or acc_get_action_id(name_action=name_action)

    if not id_action:
        return 0

    try:
        if 'description' in update:
            # change the description, no other effects
            if verbose:
                print('desc')
                run_sql(
                    """UPDATE "accACTION" SET description = %s """
                    """WHERE id = %s""",
                    (update['description'], id_action))

        if 'allowedkeywords' in update:
            # change allowedkeywords
            if verbose:
                print('keys')
            # check if changing allowedkeywords or not
            if run_sql("""SELECT id FROM "accACTION"
                       WHERE id = %s AND allowedkeywords != %s """,
                       (id_action, update['allowedkeywords'])):
                # change allowedkeywords
                if verbose:
                    print(' changing')
                run_sql("""UPDATE "accACTION" SET allowedkeywords = %s
                    WHERE id = %s""", (update['allowedkeywords'], id_action))
                # delete entries, but keep optional authorizations
                # if there still is keywords
                if verbose:
                    print(' deleting auths')
                run_sql("""DELETE FROM "accROLE_accACTION_accARGUMENT"
                        WHERE "id_accACTION"  = %s %s """,
                        (id_action, update['allowedkeywords'] and
                         'AND "id_accARGUMENT" != -1' or ''))

        if 'optional' in update:
            # check if there changing optional or not
            if verbose:
                print('optional')
            if run_sql("""SELECT id FROM "accACTION"
                       WHERE id = %s AND optional != %s """,
                       (id_action, update['optional'])):
                # change optional
                if verbose:
                    print(' changing')
                run_sql(
                    """UPDATE "accACTION" SET optional = %s WHERE id = %s""",
                    (update['optional'], id_action))
                # setting it to no, delete authorizations with
                # optional arguments
                if update['optional'] == 'no':
                    if verbose:
                        print('  deleting optional')
                    run_sql("""DELETE FROM "accROLE_accACTION_accARGUMENT"
                        WHERE "id_accACTION"  = %s AND
                        "id_accARGUMENT" = -1 AND
                        argumentlistid = -1 """, (id_action, ))

    except ProgrammingError:
        return 0

    return 1


# ROLES

def acc_add_role(name_role, description,
                 firerole_def_ser=CFG_ACC_EMPTY_ROLE_DEFINITION_SER,
                 firerole_def_src=CFG_ACC_EMPTY_ROLE_DEFINITION_SRC):
    """Add a new role to accROLE in the database.

    :param name_role: name of the role, must be unique
    description - text to describe the role

    firerole_def_ser - compiled firewall like role definition

    firerole_def_src - firewall like role definition sources
    """
    if not run_sql("""SELECT name FROM "accROLE" WHERE name = %s""",
                   (name_role, )):
        res = run_sql(
            """INSERT INTO "accROLE" (name, description, firerole_def_ser,
                                      firerole_def_src)
                VALUES (%s, %s, %s, %s)""",
            (name_role, description, bytearray(firerole_def_ser)
             if firerole_def_ser is not None else None, firerole_def_src))
        return res, name_role, description, firerole_def_src
    return 0


def acc_is_role(name_action, **arguments):
    """Check role.

    check whether the role which allows action name_action  on arguments
    exists (different from SUPERADMINROLE)

    :param action_name: name of the action
    :param arguments: arguments for authorization
    """
    # first check if an action exists with this name
    id_action = acc_get_action_id(name_action)
    arole = run_sql(
        """SELECT "id_accROLE" FROM "accROLE_accACTION_accARGUMENT" WHERE """
        """ "id_accACTION" =%s AND argumentlistid <= 0 LIMIT 1""",
        (id_action, ), 1, run_on_slave=True)
    if arole:
        return True
    other_roles_to_check = run_sql((
        """SELECT "id_accROLE", keyword, value, argumentlistid FROM """
        """ "accROLE_accACTION_accARGUMENT" JOIN "accARGUMENT" """
        """ON "id_accARGUMENT"=id WHERE "id_accACTION" =%s """
        """AND argumentlistid > 0"""), (id_action, ), run_on_slave=True)
    other_roles_to_check_dict = {}
    for id_accROLE, keyword, value, argumentlistid in other_roles_to_check:
        try:
            other_roles_to_check_dict[
                (id_accROLE, argumentlistid)][keyword] = value
        except KeyError:
            other_roles_to_check_dict[
                (id_accROLE, argumentlistid)] = {keyword: value}
    for ((id_accROLE, argumentlistid), stored_arguments) in \
            iteritems(other_roles_to_check_dict):
        for key, value in iteritems(stored_arguments):
            if (value != arguments.get(key, '*') != '*') and value != '*':
                break
        else:
            return True
    return False


def acc_delete_role(id_role=0, name_role=0):
    """Delete role.

    delete role entry in table accROLE and all references from
    other tables.

    note: you can't delete the SUPERADMINROLE

    :param id_role: id of role to be deleted, prefered variable
    :param name_role: this is used if id_role is not given
    """
    count = 0
    id_role = id_role or acc_get_role_id(name_role=name_role)

    if SUPERADMINROLE == acc_get_role_name(id_role):
        return 0

    # try to delete
    if run_sql("""DELETE FROM "accROLE" WHERE id = %s  """, (id_role, )):
        # delete everything related
        # authorization entries
        count += 1 + run_sql(
            """DELETE FROM
            "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE"  = %s""",
            (id_role, ))
        # connected users
        count += run_sql(
            """DELETE FROM user_accROLE WHERE "id_accROLE"  = %s""",
            (id_role, ))

        # delegated rights over the role
        rolenames = run_sql("""SELECT name FROM "accROLE" """)
        # string of rolenames
        roles_str = ''
        for (name, ) in rolenames:
            roles_str += (roles_str and ',' or '') + \
                '"%s"' % (name, )
        # arguments with non existing rolenames
        not_valid = run_sql("""SELECT ar.id FROM "accARGUMENT" ar
            WHERE keyword = 'role' AND value NOT IN (%s)""" % (roles_str, ))
        if not_valid:
            nv_str = ''
            for (id_value, ) in not_valid:
                nv_str += (nv_str and ',' or '') + \
                    '%s' % (id_value, )
            # delete entries
            count += run_sql(
                """DELETE FROM "accROLE_accACTION_accARGUMENT"
                   WHERE "id_accACTION"  = %s AND
                         "id_accARGUMENT" IN (%s) """ %
                (acc_get_action_id(name_action=DELEGATEADDUSERROLE), nv_str))

    # return number of deletes
    return count


def acc_update_role(id_role=0, name_role='', dummy=0, description='',
                    firerole_def_ser=CFG_ACC_EMPTY_ROLE_DEFINITION_SER,
                    firerole_def_src=CFG_ACC_EMPTY_ROLE_DEFINITION_SRC):
    """Try to change the description.

    :param id_role: id of the role to change
    :param name_role: use this to find id if not present
    :param description: new description
    :param firerole_def_ser: compiled firewall like role definition
    :param firerole_def_src: firewall like role definition
    """
    id_role = id_role or acc_get_role_id(name_role=name_role)

    if not id_role:
        return 0

    return run_sql("""UPDATE "accROLE" SET description = %s,
        firerole_def_ser = %s, firerole_def_src = %s
        WHERE id = %s""", (description, firerole_def_ser,
                           firerole_def_src, id_role))


# CONNECTIONS BETWEEN USER AND ROLE

def acc_add_user_role(id_user=0, id_role=0, email='', name_role='',
                      expiration='9999-12-31 23:59:59'):
    """Add a new entry to table user_accROLE and returns it.

    :param id_user: id user
    :param id_role: id role
    :param email: email of the user
    :param name_role: name of the role, to be used instead of id.
    """
    id_user = id_user or acc_get_user_id(email=email)
    id_role = id_role or acc_get_role_id(name_role=name_role)

    # check if the id_role exists
    if id_role and not acc_get_role_name(id_role=id_role):
        return 0

    # check that the user actually exist
    if not acc_get_user_email(id_user=id_user):
        return 0

    # control if existing entry
    if run_sql(
        ("""SELECT id_user FROM "user_accROLE" WHERE id_user = %s AND """
         """ "id_accROLE" = %s"""), (id_user, id_role)):
        run_sql(
            ("""UPDATE "user_accROLE" SET expiration=%s """
             """WHERE id_user=%s AND "id_accROLE"=%s AND expiration<%s"""),
            (expiration, id_user, id_role, expiration))
        return id_user, id_role, 0
    else:
        run_sql(
            """INSERT INTO "user_accROLE" (id_user, "id_accROLE", expiration)
            VALUES (%s, %s, %s) """, (id_user, id_role, expiration))
        return id_user, id_role, 1


def acc_delete_user_role(id_user, id_role=0, name_role=0):
    """Delete entry from user_accROLE and reports the success.

    :param id_user: user in database
    :param id_role: role in the database, prefered parameter
    :param name_role: can also delete role on background of role name.
    """
    # need to find id of the role
    id_role = id_role or acc_get_role_id(name_role=name_role)

    # number of deleted entries will be returned (0 or 1)
    return run_sql("""DELETE FROM "user_accROLE" WHERE id_user = %s
        AND id_accROLE = %s """, (id_user, id_role))


# ARGUMENTS

def acc_add_argument(keyword='', value=''):
    """Insert an argument into table accARGUMENT.

    if it exists the old id is returned, if it does not the entry is
    created and the new id is returned.

    :param keyword: inserted in keyword column
    :param value: inserted in value column.
    """
    # if one of the values are missing, return 0
    if not keyword or not value:
        return 0

    # try to return id of existing argument
    try:
        return run_sql("""SELECT id from "accARGUMENT" where keyword = %s and
        value = %s""", (keyword, value))[0][0]
    # return id of newly added argument
    except IndexError:
        return run_sql("""INSERT INTO "accARGUMENT" (keyword, value)
                          VALUES (%s, %s) """, (keyword, value))


def acc_delete_argument(id_argument):
    """Delete one entry in table accARGUMENT.

    :param id_argument: id of the argument to be deleted
    :return: the success of the operation is returned.
    """
    # return number of deleted entries, 1 or 0
    return run_sql("""DELETE FROM "accARGUMENT" WHERE id = %s """,
                   (id_argument, ))


def acc_delete_argument_names(keyword='', value=''):
    """Delete argument according to keyword and value.

    send call to another function...
    """
    # one of the values is missing
    if not keyword or not value:
        return 0

    # find id of the entry
    try:
        return run_sql("""SELECT id from "accARGUMENT" where keyword = %s
            and value = %s""", (keyword, value))[0][0]
    except IndexError:
        return 0


# AUTHORIZATIONS

# ADD WITH names and keyval list

def acc_add_authorization(name_role='', name_action='', optional=0, **keyval):
    """Insert entries in accROLE_accACTION_accARGUMENT.

    Note: only if all references are valid.
    this function is made specially for the webaccessadmin web interface.
    always inserting only one authorization.

    :param id_role: id role
    :param id_action: id action
    :param name_role: role's name
    :param name_action: action's name
    :param optional: if this is set to 1, check that function can have optional
        arguments and add with arglistid -1 and id_argument -1
    :param **keyval: dictionary of keyword=value pairs, used to find ids.
    """
    inserted = []

    # check that role and action exist
    id_role = run_sql("""SELECT id FROM "accROLE" where name = %s""",
                      (name_role, ))
    action_details = run_sql("""SELECT id,name,description,allowedkeywords,"""
                             """optional from "accACTION" where name = %s """,
                             (name_action, ))
    if not id_role or not action_details:
        return []

    # get role id and action id and details
    id_role, id_action = id_role[0][0], action_details[0][0]
    allowedkeywords_str = action_details[0][3]

    allowedkeywords_lst = acc_get_action_keywords(id_action=id_action)
    optional_action = action_details[0][4] == 'yes' and 1 or 0
    optional = int(optional)

    # this action does not take arguments
    if not optional and not keyval:
        # can not add if user is doing a mistake
        if allowedkeywords_str:
            return []
        # check if entry exists
        if not run_sql("""SELECT "id_accROLE" FROM "accROLE_accACTION_accARGUMENT"
                       WHERE "id_accROLE" = %s AND "id_accACTION"  = %s AND
                       argumentlistid = %s AND "id_accARGUMENT" = %s""",
                       (id_role, id_action, 0, 0)):
            # insert new authorization
            run_sql("""INSERT INTO "accROLE_accACTION_accARGUMENT" ("id_accROLE",
                         "id_accACTION" , "id_accARGUMENT", argumentlistid)
                       VALUES (%s, %s, NULL, %s)""", (id_role, id_action, 0))
            return [[id_role, id_action, 0, 0], ]
        return []

    # try to add authorization without the optional arguments
    elif optional:
        # optional not allowed for this action
        if not optional_action:
            return []
        # check if authorization already exists
        if not run_sql("""SELECT "id_accROLE" FROM "accROLE_accACTION_accARGUMENT"
        WHERE "id_accROLE" = %s AND
        "id_accACTION"  = %s AND
        "id_accARGUMENT" = -1 AND
        argumentlistid = -1""" % (id_role, id_action, )):
            # insert new authorization
            run_sql("""INSERT INTO "accROLE_accACTION_accARGUMENT" ("id_accROLE",
                "id_accACTION" , "id_accARGUMENT", argumentlistid)
                VALUES (%s, %s, -1, -1) """, (id_role, id_action))
            return [[id_role, id_action, -1, -1], ]
        return []

    else:
        # regular authorization

        # get list of ids, if they don't exist, create arguments
        id_arguments = []
        argstr = ''
        for key in keyval.keys():
            if key not in allowedkeywords_lst:
                return []
            id_argument = (acc_get_argument_id(key, keyval[key]) or
                           run_sql(("""INSERT INTO "accARGUMENT" """
                                    """(keyword, value) values (%s, %s) """),
                                   (key, keyval[key])))
            id_arguments.append(id_argument)
            argstr += (argstr and ',' or '') + str(id_argument)

        # check if equal authorization exists
        for (id_trav, ) in run_sql("""SELECT DISTINCT argumentlistid FROM
                "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE" = %s AND
                "id_accACTION"  = %s """, (id_role, id_action)):
            listlength = run_sql(
                """SELECT COUNT(*) FROM
                "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE" = %%s AND
                "id_accACTION"  = %%s AND argumentlistid = %%s AND
                "id_accARGUMENT" IN (%s) """ % (argstr),
                (id_role, id_action, id_trav))[0][0]
            notlist = run_sql(
                """SELECT COUNT(*) FROM
                "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE" = %%s AND
                "id_accACTION"  = %%s AND argumentlistid = %%s AND
                "id_accARGUMENT" NOT IN (%s) """ % (argstr),
                (id_role, id_action, id_trav))[0][0]
            # this means that a duplicate already exists
            if not notlist and listlength == len(id_arguments):
                return []

        # find new arglistid, highest + 1
        try:
            arglistid = 1 + run_sql("""SELECT MAX(argumentlistid) FROM
                "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE" = %s
                AND "id_accACTION"  = %s""", (id_role, id_action))[0][0]
        except (IndexError, TypeError):
            arglistid = 1
        if arglistid <= 0:
            arglistid = 1

        # insert
        for id_argument in id_arguments:
            if id_argument:
                run_sql(
                    """INSERT INTO "accROLE_accACTION_accARGUMENT" ("id_accROLE",
                            "id_accACTION" , "id_accARGUMENT", argumentlistid)
                        VALUES (%s, %s, %s, %s) """,
                    (id_role, id_action, id_argument, arglistid))
            else:
                run_sql(
                    """INSERT INTO "accROLE_accACTION_accARGUMENT" ("id_accROLE",
                            "id_accACTION" , "id_accARGUMENT", argumentlistid)
                        VALUES (%s, %s, NULL, %s) """,
                    (id_role, id_action, arglistid))
            inserted.append([id_role, id_action, id_argument, arglistid])

    return inserted


def acc_add_role_action_arguments(id_role=0, id_action=0, arglistid=-1,
                                  optional=0, verbose=0, id_arguments=[]):
    """Insert entries in accROLE_accACTION_accARGUMENT.

    note: only if all references are valid.

    :param id_role: id role
    :param id_action: id action
    :param arglistid: argumentlistid for the inserted entries
        if -1: create new group
        other values: add to this group, if it exists or not
    :param optional: if this is set to 1, check that function can have
        optional arguments and add with arglistid -1 and
        id_argument -1
    :param verbose: extra output
    :param id_arguments: list of arguments to add to group.
    """
    inserted = []

    if verbose:
        print('ids: starting')
    if verbose:
        print('ids: checking ids')

    # check that all the ids are valid and reference something...
    if not run_sql("""SELECT id FROM "accROLE" WHERE id = %s""", (id_role, )):
        return 0

    if verbose:
        print('ids: get allowed keywords')
    # check action exist and get allowed keywords
    try:
        allowedkeys = acc_get_action_keywords(id_action=id_action)
        # allowedkeys = run_sql("""SELECT id FROM accACTION WHERE id = %s""" %
        # (id_action, ))[0][3].split(',')
    except (IndexError, AttributeError):
        return 0

    if verbose:
        print('ids: is it optional')
    # action with optional arguments
    if optional:
        if verbose:
            print('ids: yes - optional')
        if not acc_get_action_is_optional(id_action=id_action):
            return []

        if verbose:
            print('ids: run query to check if exists')
        if not run_sql("""SELECT "id_accROLE" FROM "accROLE_accACTION_accARGUMENT"
                WHERE "id_accROLE" = %s AND
                "id_accACTION"  = %s AND
                "id_accARGUMENT" = -1 AND
                argumentlistid = -1""", (id_role, id_action, )):
            if verbose:
                print('ids: does not exist')
            run_sql("""INSERT INTO "accROLE_accACTION_accARGUMENT" ("id_accROLE",
                         "id_accACTION" , "id_accARGUMENT", argumentlistid)
                       VALUES (%s, %s, -1, -1) """, (id_role, id_action))
            return ((id_role, id_action, -1, -1), )
        if verbose:
            print('ids: exists')
        return []

    if verbose:
        print('ids: check if not arguments')
    # action without arguments
    if not allowedkeys:
        if verbose:
            print('ids: not arguments')
        if not run_sql(
            """SELECT "id_accROLE" FROM "accROLE_accACTION_accARGUMENT"
               WHERE "id_accROLE" = %s AND "id_accACTION"  = %s AND
               argumentlistid = %s AND "id_accARGUMENT" = %s""",
                (id_role, id_action, 0, 0)):
            if verbose:
                print('ids: try to insert')
            run_sql(
                """INSERT INTO "accROLE_accACTION_accARGUMENT" ("id_accROLE",
                   "id_accACTION" , "id_accARGUMENT", argumentlistid)
                   VALUES (%s, %s, %s, %s)""", (id_role, id_action, 0, 0))
            return ((id_role, id_action, 0, 0), )
        else:
            if verbose:
                print('ids: already existed')
            return 0
    else:
        if verbose:
            print('ids: arguments exist')
        argstr = ''
        # check that the argument exists, and that it is a valid key
        if verbose:
            print('ids: checking all the arguments')
        for id_argument in id_arguments:
            res_arg = run_sql(
                """SELECT id,keyword,value FROM "accARGUMENT" WHERE id = %s""",
                (id_argument, ))
            if not res_arg or res_arg[0][1] not in allowedkeys:
                return 0
            else:
                if argstr:
                    argstr += ','
                argstr += '%s' % (id_argument, )

        # arglistid = -1 means that the user wants a new group
        if verbose:
            print('ids: find arglistid')
        if arglistid < 0:
            # check if such single group already exists
            for (id_trav, ) in run_sql("""SELECT DISTINCT argumentlistid FROM
                    "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE" = %s AND
                    "id_accACTION"  = %s""", (id_role, id_action)):
                listlength = run_sql(
                    """SELECT COUNT(*) FROM "accROLE_accACTION_accARGUMENT"
                    WHERE "id_accROLE" = %%s AND "id_accACTION"  = %%s AND
                          argumentlistid = %%s AND "id_accARGUMENT" IN (%s)"""
                    % (argstr), (id_role, id_action, id_trav))[0][0]
                notlist = run_sql(
                    """SELECT COUNT(*) FROM "accROLE_accACTION_accARGUMENT"
                       WHERE "id_accROLE" = %%s AND "id_accACTION" = %%s AND
                             argumentlistid = %%s AND
                             "id_accARGUMENT" NOT IN (%s)""" % (argstr),
                    (id_role, id_action, id_trav))[0][0]
                # this means that a duplicate already exists
                if not notlist and listlength == len(id_arguments):
                    return 0
            # find new arglistid
            try:
                arglistid = run_sql("""SELECT MAX(argumentlistid) FROM
                    "accROLE_accACTION_accARGUMENT" WHERE "id_accROLE" = %s AND
                    "id_accACTION"  = %s""", (id_role, id_action))[0][0] + 1
            except ProgrammingError:
                return 0
            except (IndexError, TypeError):
                arglistid = 1

        if arglistid <= 0:
            arglistid = 1

        if verbose:
            print('ids: insert all the entries')
        # all references are valid, insert: one entry in raa for each argument
        for id_argument in id_arguments:
            if not run_sql(
                """SELECT "id_accROLE" FROM "accROLE_accACTION_accARGUMENT"
                   WHERE "id_accROLE" = %s AND "id_accACTION"  = %s AND
                   "id_accARGUMENT" = %s AND argumentlistid = %s""",
                    (id_role, id_action, id_argument, arglistid)):
                run_sql(
                    """INSERT INTO "accROLE_accACTION_accARGUMENT"
                       ("id_accROLE", "id_accACTION" , "id_accARGUMENT",
                        argumentlistid) VALUES (%s, %s, %s, %s)""",
                    (id_role, id_action, id_argument, arglistid))
                inserted.append((id_role, id_action, id_argument, arglistid))
        # [(r, ac, ar1, aid), (r, ac, ar2, aid)]

        if verbose:
            print('ids:   inside add function')
            for r in acc_find_possible_actions(id_role=id_role,
                                               id_action=id_action):
                print('ids:   ', r)

    return inserted


def acc_add_role_action_arguments_names(name_role='', name_action='',
                                        arglistid=-1, optional=0, verbose=0,
                                        **keyval):
    """You can pass names when creating new entries instead of ids.

    this function makes it possible to pass names when creating new entries
    instead of ids.
    get ids for all the names,
    create entries in accARGUMENT that does not exist,
    pass on to id based function.

    name_role, name_action - self explanatory

    arglistid - add entries to or create group with arglistid, default -1
    create new.

    optional - create entry with optional keywords, **keyval is ignored, but
    should be empty

    verbose - used to print extra information

    **keyval - dictionary of keyword=value pairs, used to find ids.
    """
    if verbose:
        print('names: starting')
    if verbose:
        print('names: checking ids')

    # find id of the role, return 0 if it doesn't exist
    id_role = run_sql(
        """SELECT id FROM "accROLE" where name = %s""", (name_role, ))
    if id_role:
        id_role = id_role[0][0]
    else:
        return 0

    # find id of the action, return 0 if it doesn't exist
    res = run_sql(
        """SELECT id from "accACTION" where name = %s""", (name_action, ))
    if res:
        id_action = res[0][0]
    else:
        return 0

    if verbose:
        print('names: checking arguments')

    id_arguments = []
    if not optional:
        if verbose:
            print('names: not optional')
        # place to keep ids of arguments and list of allowed keywords
        allowedkeys = acc_get_action_keywords(id_action=id_action)

        # find all the id_arguments and create those that does not exist
        for key in keyval.keys():
            # this key does not exist
            if key not in allowedkeys:
                return 0

            id_argument = acc_get_argument_id(key, keyval[key])
            id_argument = id_argument or \
                run_sql("""INSERT INTO "accARGUMENT" (keyword, value)
                        VALUES (%s, %s) """, (key, keyval[key]))

            id_arguments.append(id_argument)  # append the id to the list
    else:
        if verbose:
            print('names: optional')

    # use the other function
    return acc_add_role_action_arguments(id_role=id_role,
                                         id_action=id_action,
                                         arglistid=arglistid,
                                         optional=optional,
                                         verbose=verbose,
                                         id_arguments=id_arguments)


# DELETE WITH ID OR NAMES

def acc_delete_role_action_arguments(id_role, id_action, arglistid=1,
                                     auths=[[]]):
    """Delete entries in accROLE_accACTION_accARGUMENT.

    Only which satisfy the parameters.
    return number of actual deletes.

    this function relies on the id-lists in auths to have the same order has
    the possible actions...

    id_role, id_action - self explanatory

    arglistid - group to delete from.
    if more entries than deletes, split the group before delete.

    id_arguments - list of ids to delete.
    """
    keepauths = []  # these will be kept
    # find all possible actions
    pas = acc_find_possible_actions_ids(id_role, id_action)
    # decide which to keep or throw away

    for pa in pas[1:]:
        if pa[0] == arglistid and pa[1:] not in auths:
            keepauths.append(pa[1:])

    # delete everything
    run_sql("""DELETE FROM "accROLE_accACTION_accARGUMENT"
        WHERE "id_accROLE"  = %s AND
        "id_accACTION"  = %s AND
        argumentlistid = %s""", (id_role, id_action, arglistid))

    # insert those to be kept
    for auth in keepauths:
        acc_add_role_action_arguments(id_role=id_role,
                                      id_action=id_action,
                                      arglistid=-1,
                                      id_arguments=auth)

    return 1


def acc_delete_role_action_arguments_names(name_role='', name_action='',
                                           arglistid=1, **keyval):
    """Find all ids and redirecting the function call.

    utilize the function on ids by first finding all ids and redirecting the
    function call.
    break of and return 0 if any of the ids can't be found.

    name_role = name of the role

    name_action - name of the action

    arglistid - the argumentlistid, all keyword=value pairs must be in this
    same group.

    **keyval - dictionary of keyword=value pairs for the arguments.
    """
    # find ids for role and action
    id_role = acc_get_role_id(name_role=name_role)
    id_action = acc_get_action_id(name_action=name_action)

    # create string with the ids
    idstr = ''
    idlist = []
    for key in keyval.keys():
        argument_id = acc_get_argument_id(key, keyval[key])
        if not argument_id:
            return 0

        if idstr:
            idstr += ','
        idstr += '%s' % argument_id
        idlist.append(argument_id)

    # control that a fitting group exists
    try:
        count = run_sql("""SELECT COUNT(*) FROM "accROLE_accACTION_accARGUMENT"
        WHERE "id_accROLE"  = %%s AND
        "id_accACTION"  = %%s AND
        argumentlistid = %%s AND
        "id_accARGUMENT" IN (%s)""" % (idstr),
                        (id_role, id_action, arglistid))[0][0]
    except IndexError:
        return 0

    if count < len(keyval):
        return 0

    # call id based function
    return acc_delete_role_action_arguments(id_role, id_action, arglistid,
                                            [idlist])


def acc_delete_role_action_arguments_group(id_role=0, id_action=0,
                                           arglistid=0):
    """Delete entire group of arguments.

    for connection between role and action.
    """
    if not id_role or not id_action:
        return []

    return run_sql("""DELETE FROM "accROLE_accACTION_accARGUMENT"
    WHERE "id_accROLE"  = %s AND
    "id_accACTION"  = %s AND
    argumentlistid = %s """, (id_role, id_action, arglistid))


def acc_delete_possible_actions(id_role=0, id_action=0, authids=[]):
    """delete authorizations in selected rows.

    utilization of the delete function.

    id_role - id of  role to be connected to action.

    id_action - id of action to be connected to role

    authids - list of row indexes to be removed.
    """
    # find all authorizations
    pas = acc_find_possible_actions(id_role=id_role, id_action=id_action)

    # get the keys
    keys = pas[0][1:]

    # create dictionary for all the argumentlistids
    ald = {}
    for authid in authids:
        if authid > len(pas):
            return authid, len(pas)

        # get info from possible action
        pas_auth_id = pas[authid][0]
        values = pas[authid][1:]
        # create list of authids for each authorization
        auth = [acc_get_argument_id(keys[0], values[0])]
        for i in range(1, len(keys)):
            auth.append(acc_get_argument_id(keys[i], values[i]))

        # create entries in the dictionary for each argumentlistid
        try:
            ald[pas_auth_id].append(auth)
        except KeyError:
            ald[pas_auth_id] = [auth]

    # do the deletes
    result = 1
    for key in ald.keys():
        result = 1 and acc_delete_role_action_arguments(id_role=id_role,
                                                        id_action=id_action,
                                                        arglistid=key,
                                                        auths=ald[key])
    return result


def acc_delete_role_action(id_role=0, id_action=0):
    """delete all connections between a role and an action."""
    count = run_sql(
        """DELETE FROM "accROLE_accACTION_accARGUMENT"
           WHERE "id_accROLE" = %s AND "id_accACTION" = %s """,
        (id_role, id_action))

    return count

# GET FUNCTIONS

# ACTION RELATED


def acc_get_action_id(name_action):
    """get id of action when name is given.

    name_action - name of the wanted action
    """
    try:
        return run_sql("""SELECT id FROM "accACTION" WHERE name = %s""",
                       (name_action, ), run_on_slave=True)[0][0]
    except (ProgrammingError, IndexError):
        return 0


def acc_get_action_name(id_action):
    """get name of action when id is given."""
    try:
        return run_sql("""SELECT name FROM "accACTION" WHERE id = %s""",
                       (id_action, ))[0][0]
    except (ProgrammingError, IndexError):
        return ''


def acc_get_action_description(id_action):
    """get description of action when id is given."""
    try:
        return run_sql("""SELECT description FROM "accACTION" WHERE id = %s""",
                       (id_action, ))[0][0]
    except (ProgrammingError, IndexError):
        return ''


def acc_get_action_keywords(id_action=0, name_action=''):
    """get list of keywords for action when id is given.

    empty list if no keywords.
    """
    result = acc_get_action_keywords_string(id_action=id_action,
                                            name_action=name_action)

    if result:
        return result.split(',')
    else:
        return []


def acc_get_action_keywords_string(id_action=0, name_action=''):
    """get keywordstring when id is given."""
    id_action = id_action or acc_get_action_id(name_action)
    try:
        result = run_sql("""SELECT allowedkeywords from "accACTION"
        where id = %s """, (id_action, ))[0][0]
    except IndexError:
        return ''

    return result


def acc_get_action_is_optional(id_action=0):
    """get if the action arguments are optional or not.

    return 1 if yes, 0 if no.
    """
    result = acc_get_action_optional(id_action=id_action)
    return result == 'yes' and 1 or 0


def acc_get_action_optional(id_action=0):
    """get if the action arguments are optional or not.

    return result, but 0 if action does not exist.
    """
    try:
        result = run_sql("""SELECT optional from "accACTION" where id = %s""",
                         (id_action, ))[0][0]
    except IndexError:
        return 0

    return result


def acc_get_action_details(id_action=0):
    """get all the fields for an action."""
    try:
        result = run_sql(
            """SELECT id,name,description,allowedkeywords,optional
            FROM "accACTION" WHERE id = %s""",
            (id_action, ))[0]
    except IndexError:
        return []

    if result:
        return list(result)
    else:
        return []


def acc_get_all_actions():
    """return all entries in accACTION."""
    return run_sql("""SELECT id, name, description
        FROM "accACTION" ORDER BY name""")


def acc_get_action_roles(id_action):
    """Return all the roles connected with an action."""
    return run_sql("""SELECT DISTINCT(r.id), r.name, r.description
        FROM "accROLE_accACTION_accARGUMENT" raa, "accROLE" r
        WHERE (raa."id_accROLE"  = r.id AND raa."id_accACTION"  = %s)
              OR r.name = %s
        ORDER BY r.name """, (id_action, SUPERADMINROLE))


# ROLE RELATED

def acc_get_role_id(name_role):
    """get id of role, name given."""
    try:
        return run_sql("""SELECT id FROM "accROLE" WHERE name = %s""",
                       (name_role, ), run_on_slave=True)[0][0]
    except IndexError:
        return 0


def acc_get_role_name(id_role):
    """get name of role, id given."""
    try:
        return run_sql("""SELECT name FROM "accROLE" WHERE id = %s""",
                       (id_role, ))[0][0]
    except IndexError:
        return ''


def acc_get_role_definition(id_role=0):
    """get firewall like role definition object for a role."""
    try:
        return run_sql("""SELECT firerole_def_ser FROM "accROLE"
        WHERE id = %s""", (id_role, ))[0][0]
    except IndexError:
        return ''


def acc_get_role_details(id_role=0):
    """get all the fields for a role."""
    try:
        result = run_sql("""SELECT id, name, description, firerole_def_src
        FROM "accROLE" WHERE id = %s """, (id_role, ))[0]
    except IndexError:
        return []

    if result:
        return list(result)
    else:
        return []


def acc_get_all_roles():
    """get all entries in accROLE."""
    return run_sql("""SELECT id, name, description,
        firerole_def_ser, firerole_def_src
        FROM "accROLE" ORDER BY name""")


def acc_get_role_actions(id_role):
    """get all actions connected to a role."""
    if acc_get_role_name(id_role) == SUPERADMINROLE:
        return run_sql("""SELECT id, name, description
            FROM "accACTION"
            ORDER BY name """)
    else:
        return run_sql("""SELECT DISTINCT(a.id), a.name, a.description
            FROM "accROLE_accACTION_accARGUMENT" raa, "accACTION" a
            WHERE raa."id_accROLE"  = %s and
                raa."id_accACTION"  = a.id
            ORDER BY a.name""", (id_role, ))


def acc_get_role_users(id_role):
    """get all users that have direct access to a role.

    Note this function will not consider implicit user linked by the
    FireRole definition.
    """
    return run_sql("""SELECT DISTINCT(u.id), u.email, u.settings
        FROM "user_accROLE" ur, user u
        WHERE ur."id_accROLE"  = %s AND
        ur.expiration >= NOW() AND
        u.id = ur.id_user
        ORDER BY u.email""", (id_role, ))


def acc_get_roles_emails(id_roles):
    """Get emails by roles."""
    from invenio.modules.accounts.models import User
    return set(map(lambda u: u.email.lower().strip(),
                   db.session.query(db.func.distinct(User.email)).join(
        User.active_roles
    ).filter(UserAccROLE.id_accROLE.in_(id_roles)).all()))

# ARGUMENT RELATED


def acc_get_argument_id(keyword, value):
    """get id of argument, keyword=value pair given.

    value = 'optional value' is replaced for "id_accARGUMENT" = -1.
    """
    try:
        return run_sql("""SELECT DISTINCT id FROM "accARGUMENT"
        WHERE keyword = %s and value = %s""", (keyword, value))[0][0]
    except IndexError:
        if value == 'optional value':
            return -1
        return 0


# USER RELATED

def acc_get_user_email(id_user=0):
    """get email of user, id given."""
    try:
        return run_sql("""SELECT email FROM "user" WHERE id = %s """,
                       (id_user, ))[0][0].lower().strip()
    except IndexError:
        return ''


def acc_get_user_id(email=''):
    """get id of user, email given."""
    try:
        return run_sql("""SELECT id FROM "user" WHERE email = %s """,
                       (email.lower().strip(), ))[0][0]
    except IndexError:
        return 0


def acc_is_user_in_role(user_info, id_role):
    """Return True if the user belong implicitly or explicitly to the role."""
    if run_sql("""SELECT ur."id_accROLE"
            FROM "user_accROLE" ur
            WHERE ur.id_user = %s AND ur.expiration >= NOW() AND
            ur."id_accROLE"  = %s LIMIT 1""", (user_info['uid'], id_role), 1,
               run_on_slave=True):
        return True

    return acc_firerole_check_user(user_info, load_role_definition(id_role))


def acc_is_user_in_any_role(user_info, id_roles):
    """Check if the user have at least one of that roles."""
    if db.session.query(db.func.count(UserAccROLE.id_accROLE)).filter(db.and_(
            UserAccROLE.id_user == user_info['uid'],
            UserAccROLE.expiration >= db.func.now(),
            UserAccROLE.id_accROLE.in_(id_roles))).scalar() > 0:
        return True

    for id_role in id_roles:
        if acc_firerole_check_user(user_info, load_role_definition(id_role)):
            return True

    return False


def acc_get_user_roles_from_user_info(user_info):
    """get all roles a user is connected to."""
    uid = user_info['uid']
    if uid == -1:
        roles = intbitset()
    else:
        roles = intbitset(run_sql("""SELECT ur."id_accROLE"
            FROM "user_accROLE" ur
            WHERE ur.id_user = %s AND ur.expiration >= NOW()
            ORDER BY ur."id_accROLE" """, (uid, ), run_on_slave=True))

    potential_implicit_roles = run_sql("""SELECT id, firerole_def_ser FROM "accROLE"
        WHERE firerole_def_ser IS NOT NULL""", run_on_slave=True)

    for role_id, firerole_def_ser in potential_implicit_roles:
        if role_id not in roles:
            if acc_firerole_check_user(user_info,
                                       deserialize(firerole_def_ser)):
                roles.add(role_id)

    return roles


def acc_get_user_roles(id_user):
    """get all roles a user is explicitly connected to."""
    explicit_roles = run_sql("""SELECT ur."id_accROLE"
        FROM "user_accROLE" ur
        WHERE ur.id_user = %s AND ur.expiration >= NOW()
        ORDER BY ur."id_accROLE" """, (id_user, ), run_on_slave=True)

    return [id_role[0] for id_role in explicit_roles]


def acc_find_possible_activities(user_info, ln=CFG_SITE_LANG):
    """Return dictionary with all the possible activities.

    The list contains all the possible activities for which the user
    is allowed (i.e. all the administrative action which are connected to
    an web area in Invenio) and the corresponding url.
    """
    your_role_actions = acc_find_user_role_actions(user_info)
    your_admin_activities = {}
    for (role, action) in your_role_actions:
        if action in CFG_ACC_ACTIVITIES_URLS:
            your_admin_activities[action] = CFG_ACC_ACTIVITIES_URLS[action]
        if role == SUPERADMINROLE:
            your_admin_activities = dict(CFG_ACC_ACTIVITIES_URLS)
            break

    # For BibEdit and BibDocFile menu items, take into consideration
    # current record whenever possible

    if 'runbibedit' in your_admin_activities or \
       'runbibdocfile' in your_admin_activities and \
       user_info['uri'].startswith('/' + CFG_SITE_RECORD + '/'):
        try:
            # Get record ID and try to cast it to an int
            current_record_id = int(
                urlparse.urlparse(user_info['uri'])[2].split('/')[2]
            )
        except Exception:
            pass
        else:
            if 'runbibedit' in your_admin_activities:
                your_admin_activities['runbibedit'] = \
                    (your_admin_activities['runbibedit'][0] +
                     '&amp;#state=edit&amp;recid=' + str(current_record_id),
                     your_admin_activities['runbibedit'][1])
            if 'runbibdocfile' in your_admin_activities:
                your_admin_activities['runbibdocfile'] = \
                    (your_admin_activities['runbibdocfile'][0] +
                     '&amp;recid=' + str(current_record_id),
                     your_admin_activities['runbibdocfile'][1])

    ret = {}
    for action, (name, url) in iteritems(your_admin_activities):
        ret[name] = url % ln

    return ret


def acc_find_user_role_actions(user_info):
    """find name of all roles and actions connected to user_info."""
    uid = user_info['uid']
    # Not actions for anonymous
    if uid == -1:
        res1 = []
    else:
        # Let's check if user is superadmin
        id_superadmin = acc_get_role_id(SUPERADMINROLE)
        if id_superadmin in acc_get_user_roles_from_user_info(user_info):
            return [(SUPERADMINROLE, action[1])
                    for action in acc_get_all_actions()]

        query = """SELECT DISTINCT r.name, a.name
                   FROM "user_accROLE" ur, "accROLE_accACTION_accARGUMENT" raa,
                   "accACTION" a, "accROLE" r
                   WHERE ur.id_user = %s AND
                   ur.expiration >= NOW() AND
                   ur."id_accROLE"  = raa."id_accROLE"  AND
                   raa."id_accACTION"  = a.id AND
                   raa."id_accROLE"  = r.id """
        res1 = run_sql(query, (uid, ), run_on_slave=True)

    res2 = []
    for res in res1:
        res2.append(res)
    res2.sort()

    if isinstance(user_info, dict):
        query = """SELECT DISTINCT r.name, a.name, r.firerole_def_ser
        FROM "accROLE_accACTION_accARGUMENT" raa, "accACTION" a, "accROLE" r
        WHERE raa."id_accACTION"  = a.id AND raa."id_accROLE"  = r.id """

        res3 = run_sql(query, run_on_slave=True)
        res4 = []
        for role_name, action_name, role_definition in res3:
            if acc_firerole_check_user(user_info,
                                       deserialize(role_definition)):
                if role_name == SUPERADMINROLE:
                    # Ok, every action. There's no need to go on :-)
                    return [(id_superadmin, action[0]) for action in
                            acc_get_all_actions()]
                res4.append((role_name, action_name))
        return list(set(res2) | set(res4))
    else:
        return res2


# POSSIBLE ACTIONS / AUTHORIZATIONS

def acc_find_possible_actions_all(id_role):
    """find all the possible actions for a role.

    the function utilizes acc_find_possible_actions to find
    all the entries from each of the actions under the given role

    id_role - role to find all actions for

    returns a list with headers
    """
    query = """SELECT DISTINCT(aar."id_accACTION" )
               FROM "accROLE_accACTION_accARGUMENT" aar
               WHERE aar."id_accROLE"  = %s
               ORDER BY aar."id_accACTION" """ % (id_role, )

    res = []

    for (id_action, ) in run_sql(query):
        hlp = acc_find_possible_actions(id_role, id_action)
        if hlp:
            res.append(['role', 'action'] + hlp[0])
        for row in hlp[1:]:
            res.append([id_role, id_action] + row)

    return res


def acc_find_possible_actions_argument_listid(id_role, id_action, arglistid):
    """find all possible actions with the given arglistid only."""
    # get all, independent of argumentlistid
    res1 = acc_find_possible_actions_ids(id_role, id_action)

    # create list with only those with the right arglistid
    res2 = []
    for row in res1[1:]:
        if row[0] == arglistid:
            res2.append(row)

    # return this list
    return res2


def acc_find_possible_roles(name_action, always_add_superadmin=True,
                            batch_args=False, **arguments):
    """Find all the possible roles that are enabled to a given action.

    :return: roles as a list of role_id
    """
    query_roles_without_args = \
        db.select([AccAuthorization.id_accROLE], db.and_(
            AccAuthorization.argumentlistid <= 0,
            AccAuthorization.id_accACTION == db.bindparam('id_action')))

    query_roles_with_args = \
        AccAuthorization.query.filter(db.and_(
            AccAuthorization.argumentlistid > 0,
            AccAuthorization.id_accACTION == db.bindparam('id_action')
        )).join(AccAuthorization.argument)

    id_action = db.session.query(AccACTION.id).filter(
        AccACTION.name == name_action).scalar()
    roles = intbitset(db.engine.execute(query_roles_without_args.params(
        id_action=id_action)).fetchall())

    if always_add_superadmin:
        roles.add(current_app.config.get("CFG_SUPERADMINROLE_ID", 1))

    # Unpack arguments
    if batch_args:
        batch_arguments = [dict(zip(arguments.keys(), values))
                           for values in zip(*arguments.values())]
    else:
        batch_arguments = [arguments]

    acc_authorizations = query_roles_with_args.params(
        id_action=id_action
    ).all()

    result = []
    for arguments in batch_arguments:
        batch_roles = roles.copy()
        for auth in acc_authorizations:
            if auth.id_accROLE not in batch_roles:
                if not ((auth.argument.value != arguments.get(
                    auth.argument.keyword, '*') != '*'
                ) and auth.argument.value != '*'):
                    batch_roles.add(auth.id_accROLE)
        result.append(batch_roles)
    return result if batch_args else result[0]


def acc_find_possible_actions_user_from_user_info(user_info, id_action):
    """Find all action conbination for a given user and action.

    user based function to find all action combination for a given
    user and action. find all the roles and utilize findPossibleActions
    for all these.

    user_info - user information dictionary, used to find roles

    id_action - action id.
    """
    res = []

    for id_role in acc_get_user_roles_from_user_info(user_info):
        hlp = acc_find_possible_actions(id_role, id_action)
        if hlp and not res:
            res.append(['role'] + hlp[0])

        for row in hlp[1:]:
            res.append([id_role] + row)

    return res


def acc_find_possible_actions_user(id_user, id_action):
    """Find all action combination for a given user and action.

    user based function to find all action combination for a given
    user and action. find all the roles and utilize findPossibleActions
    for all these.

    id_user - user id, used to find roles

    id_action - action id.

    Note this function considers only explicit links between users and roles,
    and not FireRole definitions.
    """
    res = []

    for id_role in acc_get_user_roles(id_user):
        hlp = acc_find_possible_actions(id_role, id_action)
        if hlp and not res:
            res.append(['role'] + hlp[0])

        for row in hlp[1:]:
            res.append([id_role] + row)

    return res


def acc_find_possible_actions_ids(id_role, id_action):
    """find the ids of the possible actions.

    utilization of acc_get_argument_id and acc_find_possible_actions.
    """
    pas = acc_find_possible_actions(id_role, id_action)

    if not pas:
        return []

    keys = pas[0]
    pas_ids = [pas[0:1]]

    for pa in pas[1:]:
        auth = [pa[0]]
        for i in range(1, len(pa)):
            auth.append(acc_get_argument_id(keys[i], pa[i]))
        pas_ids.append(auth)

    return pas_ids


def acc_find_possible_actions(id_role, id_action):
    """Find all action combinations for a give role and action.

    Role based function to find all action combinations for a
    give role and action.

      id_role - id of role in the database

    id_action - id of the action in the database

    returns a list with all the combinations.
    first row is used for header.

    if SUPERADMINROLE, nothing is returned since an infinte number of
    combination are possible.
    """
    # query to find all entries for user and action
    res1 = run_sql(""" SELECT raa.argumentlistid, ar.keyword, ar.value
        FROM "accROLE_accACTION_accARGUMENT" raa, "accARGUMENT" ar
        WHERE raa."id_accROLE"  = %s and
        raa."id_accACTION"  = %s and
        raa."id_accARGUMENT" = ar.id """, (id_role, id_action))

    # find needed keywords, create header
    keywords = acc_get_action_keywords(id_action=id_action)
    keywords.sort()

    if not keywords:
        # action without arguments"
        if run_sql(
            """SELECT "id_accROLE"
               FROM "accROLE_accACTION_accARGUMENT"
               WHERE "id_accROLE" = %s AND "id_accACTION"  = %s AND
                     "id_accARGUMENT" = 0 AND argumentlistid = 0""",
                (id_role, id_action)):
            return [['#', 'argument keyword'],
                    ['0', 'action without arguments']]

    # tuples into lists
    res2, arglistids = [], {}
    for res in res1:
        res2.append([])
        for r in res:
            res2[-1].append(r)
    res2.sort()

    # create multilevel dictionary
    for res in res2:
        a, kw, value = res  # rolekey, argumentlistid, keyword, value
        if kw not in keywords:
            continue
        if a not in arglistids:
            arglistids[a] = {}
        # fill dictionary
        if kw not in arglistids[a]:
            arglistids[a][kw] = [value]
        elif value not in arglistids[a][kw]:
            arglistids[a][kw] = arglistids[a][kw] + [value]

    # fill list with all possible combinations
    res3 = []
    # rolekeys = roles2.keys();    rolekeys.sort()
    for a in arglistids.keys():  # argumentlistids
        # fill a list with the new entries, shortcut and copying first
        # keyword list
        next_arglistid = []
        for row in arglistids[a][keywords[0]]:
            next_arglistid.append([a, row[:]])
        # run through the rest of the keywords
        for kw in keywords[1:]:
            if kw not in arglistids[a]:
                arglistids[a][kw] = ['optional value']

            new_list = arglistids[a][kw][:]
            new_len = len(new_list)
            # duplicate the list
            temp_list = []
            for row in next_arglistid:
                for i in range(new_len):
                    temp_list.append(row[:])
            # append new values
            for i in range(len(temp_list)):
                new_item = new_list[i % new_len][:]
                temp_list[i].append(new_item)
            next_arglistid = temp_list[:]

        res3.extend(next_arglistid)

    res3.sort()

    # if optional allowed, put on top
    opt = run_sql("""SELECT "id_accROLE"  FROM "accROLE_accACTION_accARGUMENT"
        WHERE "id_accROLE"  = %s AND
        "id_accACTION"  = %s AND
        "id_accARGUMENT" = -1 AND
        argumentlistid = -1""", (id_role, id_action))

    if opt:
        res3.insert(0, [-1] + ['optional value'] * len(keywords))

    # put header on top
    if res3:
        res3.insert(0, ['#'] + keywords)

    return res3


def acc_split_argument_group(id_role=0, id_action=0, arglistid=0):
    """Split argument group.

    collect the arguments, find all combinations, delete original entries
    and insert the new ones with different argumentlistids for each group

      id_role - id of the role

    id_action - id of the action

    arglistid - argumentlistid to be splittetd
    """
    if not id_role or not id_action or not arglistid:
        return []

    # don't split if none or one possible actions
    res = acc_find_possible_actions_argument_listid(id_role, id_action,
                                                    arglistid)
    if not res or len(res) <= 1:
        return 0

    # delete the existing group
    acc_delete_role_action_arguments_group(id_role, id_action,
                                           arglistid)

    # add all authorizations with new and different argumentlistid
    addlist = []
    for row in res:
        argids = row[1:]
        addlist.append(acc_add_role_action_arguments(id_role=id_role,
                                                     id_action=id_action,
                                                     arglistid=-1,
                                                     id_arguments=argids))

    # return list of added authorizations
    return addlist


def acc_merge_argument_groups(id_role=0, id_action=0, arglistids=[]):
    """Merge argument groups.

    merge the authorizations from groups with different argumentlistids
    into one single group.
    this can both save entries in the database and create extra authorizations.

    id_role - id of the role

    id_action - role of the action

    arglistids - list of groups to be merged together into one.
    """
    if len(arglistids) < 2:
        return []

    argstr = ''
    for arglist_id in arglistids:
        argstr += 'raa.argumentlistid = %s or ' % (arglist_id, )
    argstr = '(%s)' % (argstr[:-4], )

    # query to find all entries that will be merged
    query = """ SELECT ar.keyword, ar.value, raa."id_accARGUMENT"
        FROM "accROLE_accACTION_accARGUMENT" raa, "accARGUMENT" ar
        WHERE raa."id_accROLE"  = %%s and
        raa."id_accACTION"  = %%s and
        %s and
        raa."id_accARGUMENT" = ar.id """ % argstr

    q_del = """DELETE FROM "accROLE_accACTION_accARGUMENT"
        WHERE "id_accROLE"  = %%s and
        "id_accACTION"  = %%s and
        %s """ % (argstr.replace('raa.', ''))

    res = run_sql(query, (id_role, id_action))
    if not res:
        return []

    run_sql(q_del, (id_role, id_action))

    # list of entire entries
    old = []
    # list of only the ids
    ids = []
    for (keyword, value, argument_id) in res:
        if [keyword, value, argument_id] not in old:
            old.append([keyword, value, argument_id])
            ids.append(argument_id)
    # for (k, v, id) in res: if id not in ids: ids.append(id)

    return acc_add_role_action_arguments(id_role=id_role,
                                         id_action=id_action,
                                         arglistid=-1,
                                         id_arguments=ids)


def acc_reset_default_settings(superusers=(),
                               additional_def_user_roles=(),
                               additional_def_roles=(),
                               additional_def_auths=()):
    """reset to default by deleting everything and adding default.

    superusers - list of superuser emails

    additional_def_user_roles - additional list of pair email, rolename
        (see DEF_DEMO_USER_ROLES in access_control_config.py)

    additional_def_roles - additional list of default list of roles
        (see DEF_DEMO_ROLES in access_control_config.py)

    additional_def_auths - additional list of default authorizations
        (see DEF_DEMO_AUTHS in access_control_config.py)
    """
    remove = acc_delete_all_settings()
    add = acc_add_default_settings(
        superusers, additional_def_user_roles,
        additional_def_roles, additional_def_auths)

    return remove, add


def acc_delete_all_settings():
    """Remove all data affiliated with webaccess.

    simply remove all data affiliated with webaccess by truncating
    tables accROLE, accACTION, accARGUMENT and those connected.
    """
    from invenio.ext.sqlalchemy import db
    db.session.commit()

    run_sql("""TRUNCATE "accROLE" """)
    run_sql("""TRUNCATE "accACTION" """)
    run_sql("""TRUNCATE "accARGUMENT" """)
    run_sql("""TRUNCATE "user_accROLE" """)
    run_sql("""TRUNCATE "accROLE_accACTION_accARGUMENT" """)

    return 1


def acc_add_default_settings(superusers=(),
                             additional_def_user_roles=(),
                             additional_def_roles=(),
                             additional_def_auths=()):
    """Add the default settings if they don't exist.

    superusers - list of superuser emails

    additional_def_user_roles - additional list of pair email, rolename
        (see DEF_DEMO_USER_ROLES in access_control_config.py)

    additional_def_roles - additional list of default list of roles
        (see DEF_DEMO_ROLES in access_control_config.py)

    additional_def_auths - additional list of default authorizations
        (see DEF_DEMO_AUTHS in access_control_config.py)
    """
    # from superusers: allow input formats ['email1', 'email2'] and
    # [['email1'], ['email2']] and [['email1', id], ['email2', id]]
    for user in superusers:
        if type(user) is str:
            user = [user]
        DEF_USERS.append(user[0])
    if CFG_SITE_ADMIN_EMAIL not in DEF_USERS:
        DEF_USERS.append(CFG_SITE_ADMIN_EMAIL)

    # add data

    # add roles
    insroles = []
    def_roles = dict([(role[0], role[1:]) for role in DEF_ROLES])
    def_roles.update(
        dict([(role[0], role[1:]) for role in additional_def_roles]))
    for name, (description, firerole_def_src) in iteritems(def_roles):
        # try to add, don't care if description is different
        role_id = acc_add_role(
            name_role=name,
            description=description, firerole_def_ser=serialize(
                compile_role_definition(firerole_def_src)),
            firerole_def_src=firerole_def_src)
        if not role_id:
            role_id = acc_get_role_id(name_role=name)
            acc_update_role(
                id_role=role_id, description=description,
                firerole_def_ser=serialize(compile_role_definition(
                    firerole_def_src)), firerole_def_src=firerole_def_src)
        insroles.append([role_id, name, description, firerole_def_src])

    # add users to superadmin
    insuserroles = []
    for user in DEF_USERS:
        insuserroles.append(acc_add_user_role(email=user,
                                              name_role=SUPERADMINROLE))

    for user, role in additional_def_user_roles:
        insuserroles.append(acc_add_user_role(email=user, name_role=role))

    # add actions
    insactions = []
    for action in principal.actions:
        name = action.name
        description = action.description
        optional = 'yes' if action.optional else 'no'
        allkeys = ','.join(action.allowedkeywords) \
            if action.allowedkeywords is not None else ''
        # try to add action as new
        action_id = acc_add_action(name, description, optional, allkeys)
        # action with the name exist
        if not action_id:
            action_id = acc_get_action_id(name_action=action.name)
            # update the action, necessary updates to the database
            # will also be done
            acc_update_action(id_action=action_id, optional=optional,
                              allowedkeywords=allkeys)
        # keep track of inserted actions
        insactions.append([action_id, name, description, allkeys])

    # add authorizations
    insauths = []
    def_auths = list(DEF_AUTHS) + list(additional_def_auths)
    for (name_role, name_action, args) in def_auths:
        # add the authorization
        optional = not args and acc_get_action_is_optional(
            acc_get_action_id(name_action))
        acc_add_authorization(name_role=name_role,
                              name_action=name_action,
                              optional=optional,
                              **args)
        # keep track of inserted authorizations
        insauths.append([name_role, name_action, args])

    return insroles, insactions, insuserroles, insauths


def acc_find_delegated_roles(id_role_admin=0):
    """find all the roles the admin role has delegation rights over.

    return tuple of all the roles.

    id_role_admin - id of the admin role
    """
    id_action_delegate = acc_get_action_id(name_action=DELEGATEADDUSERROLE)

    rolenames = run_sql("""SELECT DISTINCT(ar.value)
        FROM "accROLE_accACTION_accARGUMENT" raa LEFT JOIN "accARGUMENT" ar
        ON raa."id_accARGUMENT" = ar.id
        WHERE raa."id_accROLE"  = %s AND
        raa."id_accACTION"  = %s""", (id_role_admin, id_action_delegate))

    result = []

    for (name_role, ) in rolenames:
        roledetails = run_sql(
            """SELECT id,name,description,firerole_def_ser,firerole_def_src
            FROM "accROLE" WHERE name = %s """,
            (name_role, ))
        if roledetails:
            result.append(roledetails)

    return result


def acc_cleanup_arguments():
    """Cleanup arguments.

    function deletes all accARGUMENTs that are not referenced by
    accROLE_accACTION_accARGUMENT.
    returns how many arguments where deleted and a list of the deleted
    id_arguments
    """
    # find unreferenced arguments
    ids1 = run_sql("""SELECT DISTINCT ar.id
        FROM "accARGUMENT" ar LEFT JOIN "accROLE_accACTION_accARGUMENT" raa ON
        ar.id = raa."id_accARGUMENT" WHERE raa."id_accARGUMENT" IS NULL """)

    # it is clean
    if not ids1:
        return 1

    # create list and string of the ids
    ids2 = []
    idstr = ''
    for (argument_id, ) in ids1:
        ids2.append(argument_id)
        if idstr:
            idstr += ','
        idstr += '%s' % argument_id

    # delete unreferenced arguments
    count = run_sql("""DELETE FROM "accARGUMENT"
    WHERE id in (%s)""" % (idstr, ))

    # return count and ids of deleted arguments
    return (count, ids2)
