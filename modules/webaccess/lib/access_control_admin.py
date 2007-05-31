# $Id$
## CDS Invenio Access Control Engine in mod_python.

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

"""CDS Invenio Access Control Admin."""

__revision__ = "$Id$"

# check this: def acc_addUserRole(id_user, id_role=0, name_role=0):

## import interesting modules:

import sys
import time

from invenio.config import \
     supportemail, \
     version
from invenio.access_control_config import *
from invenio.dbquery import run_sql, ProgrammingError
from invenio.access_control_firerole import compile_role_definition, acc_firerole_check_user, serialize, deserialize
from sets import Set

# ACTIONS

def acc_addAction(name_action='', description='', optional='no', *allowedkeywords):
    """function to create new entry in accACTION for an action

    name_action     - name of the new action, must be unique

    keyvalstr       - string with allowed keywords

    allowedkeywords - a list of allowedkeywords

    keyvalstr and allowedkeywordsdict can not be in use simultanously

    success -> return id_action, name_action, description and allowedkeywords
    failure -> return 0 """

    keystr = ''
    # action with this name all ready exists, return 0
    if run_sql("""SELECT * FROM accACTION WHERE name = '%s'""" % (name_action, )):
        return 0

    # create keyword string
    for value in allowedkeywords:
        if keystr: keystr += ','
        keystr += value

    if not allowedkeywords: optional = 'no'

    # insert the new entry
    try: res = run_sql("""INSERT INTO accACTION (name, description, allowedkeywords, optional) VALUES ('%s', '%s', '%s', '%s')""" % (name_action, description, keystr, optional))
    except ProgrammingError: return 0

    if res: return res, name_action, description, keystr, optional
    return 0


def acc_deleteAction(id_action=0, name_action=0):
    """delete action in accACTION according to id, or secondly name.
    entries in accROLE_accACTION_accARGUMENT will also be removed.

      id_action - id of action to be deleted, prefered variable

    name_action - this is used if id_action is not given

    if the name or id is wrong, the function does nothing
    """

    if id_action and name_action:
        return 0

    # delete the action
    if run_sql("""DELETE FROM accACTION WHERE id = %s OR name = '%s'""" % (id_action, name_action)):
        # delete all entries related
        return 1 + run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT WHERE id_accACTION = %s """ % (id_action, ))
    else:
        return 0


def acc_verifyAction(name_action='', description='', allowedkeywords='', optional=''):
    """check if all the values of a given action are the same as
    those in accACTION in the database. self explanatory parameters.

    return id if identical, 0 if not. """

    id_action = acc_getActionId(name_action=name_action)

    if not id_action: return 0

    res_desc = acc_getActionDescription(id_action=id_action)
    res_keys = acc_getActionKeywordsString(id_action=id_action)

    bool_desc = res_desc == description and 1 or 0
    bool_keys = res_keys == allowedkeywords and 1 or 0
    bool_opti = acc_getActionIsOptional(id_action=id_action)

    return bool_desc and bool_keys and bool_opti and id_action or 0


def acc_updateAction(id_action=0, name_action='', verbose=0, **update):
    """try to change the values of given action details.
    if there is no change nothing is done.
    some changes require to update other parts of the database.

      id_action - id of the action to change

    name_action - if no id_action is given try to find it using this name

       **update - dictionary containg keywords: description,
                                                allowedkeywords and/or
                                                optional
                  other keywords are ignored """

    id_action = id_action or acc_getActionId(name_action=name_action)

    if not id_action: return 0

    try:
        if update.has_key('description'):
            # change the description, no other effects
            if verbose: print 'desc'
            run_sql("""UPDATE accACTION SET description = '%s' WHERE id = %s"""
                    % (update['description'], id_action))

        if update.has_key('allowedkeywords'):
            # change allowedkeywords
            if verbose: print 'keys'
            # check if changing allowedkeywords or not
            if run_sql("""SELECT * FROM accACTION
            WHERE id = %s AND allowedkeywords != '%s' """ % (id_action, update['allowedkeywords'])):
                # change allowedkeywords
                if verbose: print ' changing'
                run_sql("""UPDATE accACTION SET allowedkeywords = '%s' WHERE id = %s"""
                        % (update['allowedkeywords'], id_action))
                # delete entries, but keep optional authorizations if there still is keywords
                if verbose: print ' deleting auths'
                run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT
                WHERE id_accACTION = %s %s """ % (id_action, update['allowedkeywords'] and 'AND id_accARGUMENT != -1' or ''))

        if update.has_key('optional'):
            # check if there changing optional or not
            if verbose: print 'optional'
            if run_sql("""SELECT * FROM accACTION
            WHERE id = %s AND optional != '%s' """ % (id_action, update['optional'])):
                # change optional
                if verbose: print ' changing'
                run_sql("""UPDATE accACTION SET optional = '%s' WHERE id = %s"""
                        % (update['optional'], id_action))
                # setting it to no, delete authorizations with optional arguments
                if update['optional'] == 'no':
                    if verbose: print '  deleting optional'
                    run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT
                    WHERE id_accACTION = %s AND
                    id_accARGUMENT = -1 AND
                    argumentlistid = -1 """ % (id_action, ))

    except ProgrammingError:
        return 0

    return 1


# ROLES

def acc_addRole(name_role, description, firerole_def_ser = CFG_ACC_EMPTY_ROLE_DEFINITION_SER, firerole_def_src = CFG_ACC_EMPTY_ROLE_DEFINITION_SRC):
    """add a new role to accROLE in the database.

    name_role - name of the role, must be unique

    description - text to describe the role

    firerole_def_ser - compiled firewall like role definition

    firerole_def_src - firewall like role definition sources
    """

    if not run_sql("""SELECT * FROM accROLE WHERE name = '%s'""" % (name_role, )):
        res = run_sql("""INSERT INTO accROLE (name, description, firerole_def_ser, firerole_def_src) VALUES (%s, %s, %s, %s)""", (name_role, description, firerole_def_ser, firerole_def_src))
        return res, name_role, description, firerole_def_src
    return 0

def acc_isRole(name_action,**arguments):
    """ check whether the role which allows action name_action  on arguments exists

    action_name - name of the action

    arguments - arguments for authorization"""

    # first check if an action exists with this name
    query1 = """select a.id, a.allowedkeywords, a.optional
                from accACTION a
                where a.name = '%s'""" % (name_action)

    try: id_action, aallowedkeywords, optional = run_sql(query1)[0]
    except (ProgrammingError, IndexError): return 0

    defkeys = aallowedkeywords.split(',')
    for key in arguments.keys():
        if key not in defkeys: return 0

    # then check if a role giving this authorization exists
    # create dictionary with default values and replace entries from input arguments
    defdict = {}

    for key in defkeys:
        try: defdict[key] = arguments[key]
        except KeyError: return 0 # all keywords must be present
        # except KeyError: defdict[key] = 'x' # default value, this is not in use...

    # create or-string from arguments
    str_args = ''
    for key in defkeys:
        if str_args: str_args += ' OR '
        str_args += """(arg.keyword = '%s' AND arg.value = '%s')""" % (key, defdict[key])

    query4 = """SELECT DISTINCT raa.id_accROLE, raa.id_accACTION, raa.argumentlistid,
    raa.id_accARGUMENT, arg.keyword, arg.value
    FROM accROLE_accACTION_accARGUMENT raa, accARGUMENT arg
    WHERE raa.id_accACTION = %s AND
    (%s) AND
    raa.id_accARGUMENT = arg.id """ % (id_action, str_args)

    try: res4 = run_sql(query4)
    except ProgrammingError: return 0

    if not res4: return 0 # no entries at all

    res5 = []
    for res in res4:
        res5.append(res)
    res5.sort()

    if len(defdict) == 1: return 1

    cur_role = cur_action = cur_arglistid = 0

    booldict = {}
    for key in defkeys: booldict[key] = 0

    # run through the results
    for (role, action, arglistid, arg, keyword, val) in res5 + [(-1, -1, -1, -1, -1, -1)]:
        # not the same role or argumentlist (authorization group), i.e. check if thing are satisfied
        # if cur_arglistid != arglistid or cur_role != role or cur_action != action:
        if (cur_arglistid, cur_role, cur_action) != (arglistid, role, action):

            # test if all keywords are satisfied
            for value in booldict.values():
                if not value: break
            else:
                return 1 # USER AUTHENTICATED TO PERFORM ACTION

            # assign the values for the current tuple from the query
            cur_arglistid, cur_role, cur_action = arglistid, role, action

            for key in booldict.keys():
                booldict[key] = 0

        # set keyword qualified for the action, (whatever result of the test)
        booldict[keyword] = 1

    # matching failed
    return 0

def acc_deleteRole(id_role=0, name_role=0):
    """ delete role entry in table accROLE and all references from other tables.

      id_role - id of role to be deleted, prefered variable

    name_role - this is used if id_role is not given """

    count = 0
    id_role = id_role or acc_getRoleId(name_role=name_role)

    # try to delete
    if run_sql("""DELETE FROM accROLE WHERE id = %s  """ % (id_role, )):
        # delete everything related
        # authorization entries
        count += 1 + run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = %s""" % (id_role, ))
        # connected users
        count += run_sql("""DELETE FROM user_accROLE WHERE id_accROLE = %s """ % (id_role, ))

        # delegated rights over the role
        rolenames = run_sql("""SELECT name FROM accROLE""")
        # string of rolenames
        roles_str = ''
        for (name, ) in rolenames: roles_str += (roles_str and ',' or '') + '"%s"' % (name, )
        # arguments with non existing rolenames
        not_valid = run_sql("""SELECT ar.id FROM accARGUMENT ar WHERE keyword = 'role' AND value NOT IN (%s)""" % (roles_str, ))
        if not_valid:
            nv_str = ''
            for (id, ) in not_valid: nv_str += (nv_str and ',' or '') + '%s' % (id, )
            # delete entries
            count += run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT
            WHERE id_accACTION = %s AND id_accARGUMENT IN (%s) """ % (acc_getActionId(name_action=DELEGATEADDUSERROLE), nv_str))

    # return number of deletes
    return count


def acc_updateRole(id_role=0, name_role='', verbose=0, description='', \
    firerole_def_ser=CFG_ACC_EMPTY_ROLE_DEFINITION_SER, \
    firerole_def_src=CFG_ACC_EMPTY_ROLE_DEFINITION_SRC):
    """try to change the description.

        id_role - id of the role to change

      name_role - use this to find id if not present

        verbose - extra output

    description - new description

    firerole_def_ser - compiled firewall like role definition

    firerole_def_src - firewall like role definition
    """

    id_role = id_role or acc_getRoleId(name_role=name_role)

    if not id_role: return 0

    return run_sql("""UPDATE accROLE SET description = %s, firerole_def_ser = %s, firerole_def_src = %s
    WHERE id = %s""", (description, firerole_def_ser, firerole_def_src, id_role))


# CONNECTIONS BETWEEN USER AND ROLE

def acc_addUserRole(id_user=0, id_role=0, email='', name_role=''):
    """ this function adds a new entry to table user_accROLE and returns it

      id_user, id_role - self explanatory

        email - email of the user

    name_role - name of the role, to be used instead of id. """

    id_user = id_user or acc_getUserId(email=email)
    id_role = id_role or acc_getRoleId(name_role=name_role)

    # check if the id_role exists
    if id_role and not acc_getRoleName(id_role=id_role): return 0

    # check that the user actually exist
    if not acc_getUserEmail(id_user=id_user): return 0

    # control if existing entry
    if run_sql("""SELECT * FROM user_accROLE WHERE id_user = %s AND id_accROLE = %s""" % (id_user, id_role)):
        return id_user, id_role, 0
    else:
        run_sql("""INSERT INTO user_accROLE (id_user, id_accROLE) VALUES (%s, %s) """ % (id_user, id_role))
        return id_user, id_role, 1


def acc_deleteUserRole(id_user, id_role=0, name_role=0):
    """ function deletes entry from user_accROLE and reports the success.

      id_user - user in database

      id_role - role in the database, prefered parameter

    name_role - can also delete role on background of role name. """

    # need to find id of the role
    id_role = id_role or acc_getRoleId(name_role=name_role)

    # number of deleted entries will be returned (0 or 1)
    return run_sql("""DELETE FROM user_accROLE WHERE id_user = %s AND id_accROLE = %s """ % (id_user, id_role))


# ARGUMENTS

def acc_addArgument(keyword='', value=''):
    """ function to insert an argument into table accARGUMENT.
    if it exists the old id is returned, if it does not the entry is created and the new id is returned.

    keyword - inserted in keyword column

      value - inserted in value column. """

    # if one of the values are missing, return 0
    if not keyword or not value: return 0

    # try to return id of existing argument
    try: return run_sql("""SELECT id from accARGUMENT where keyword = '%s' and value = '%s'""" % (keyword, value))[0][0]
    # return id of newly added argument
    except IndexError: return run_sql("""INSERT INTO accARGUMENT (keyword, value) values ('%s', '%s') """ % (keyword, value))


def acc_deleteArgument(id_argument):
    """ functions deletes one entry in table accARGUMENT.
    the success of the operation is returned.

    id_argument - id of the argument to be deleted"""

    # return number of deleted entries, 1 or 0
    return run_sql("""DELETE FROM accARGUMENT WHERE id = %s """ % (id_argument, ))


def acc_deleteArgument_names(keyword='', value=''):
    """delete argument according to keyword and value,
    send call to another function..."""

    # one of the values is missing
    if not keyword or not value: return 0

    # find id of the entry
    try: return run_sql("""SELECT id from accARGUMENT where keyword = '%s' and value = '%s'""" % (keyword, value))[0][0]
    except IndexError: return 0


# AUTHORIZATIONS

# ADD WITH names and keyval list

def acc_addAuthorization(name_role='', name_action='', optional=0, **keyval):
    """ function inserts entries in accROLE_accACTION_accARGUMENT if all references are valid.
    this function is made specially for the webaccessadmin web interface.
    always inserting only one authorization.

    id_role, id_action - self explanatory, preferably used

    name_role, name_action - self explanatory, used if id not given

    optional - if this is set to 1, check that function can have optional
                arguments and add with arglistid -1 and id_argument -1

    **keyval - dictionary of keyword=value pairs, used to find ids. """

    inserted = []

    # check that role and action exist
    id_role = run_sql("""SELECT id FROM accROLE where name = '%s'""" % (name_role, ))
    action_details = run_sql("""SELECT * from accACTION where name = '%s' """ % (name_action, ))
    if not id_role or not action_details: return []

    # get role id and action id and details
    id_role, id_action = id_role[0][0], action_details[0][0]
    allowedkeywords_str = action_details[0][3]

    allowedkeywords_lst = acc_getActionKeywords(id_action=id_action)
    optional_action = action_details[0][4] == 'yes' and 1 or 0
    optional = int(optional)

    # this action does not take arguments
    if not optional and not keyval:
        # can not add if user is doing a mistake
        if allowedkeywords_str: return []
        # check if entry exists
        if not run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
                       WHERE id_accROLE = %s AND id_accACTION = %s AND argumentlistid = %s AND id_accARGUMENT = %s"""
                       % (id_role, id_action, 0, 0)):
            # insert new authorization
            run_sql("""INSERT INTO accROLE_accACTION_accARGUMENT values (%s, %s, %s, %s)""" % (id_role, id_action, 0, 0))
            return [[id_role, id_action, 0, 0], ]
        return []


    # try to add authorization without the optional arguments
    elif optional:
        # optional not allowed for this action
        if not optional_action: return []
        # check if authorization already exists
        if not run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
        WHERE id_accROLE = %s AND
        id_accACTION = %s AND
        id_accARGUMENT = -1 AND
        argumentlistid = -1""" % (id_role, id_action, )):
            # insert new authorization
            run_sql("""INSERT INTO accROLE_accACTION_accARGUMENT (id_accROLE, id_accACTION, id_accARGUMENT, argumentlistid) VALUES (%s, %s, -1, -1) """ % (id_role, id_action))
            return [[id_role, id_action, -1, -1], ]
        return []


    else:
        # regular authorization

        # get list of ids, if they don't exist, create arguments
        id_arguments = []
        argstr = ''
        for key in keyval.keys():
            if key not in allowedkeywords_lst: return []
            id_argument = (acc_getArgumentId(key, keyval[key])
                           or
                           run_sql("""INSERT INTO accARGUMENT (keyword, value) values ('%s', '%s') """ % (key, keyval[key])))
            id_arguments.append(id_argument)
            argstr += (argstr and ',' or '') + str(id_argument)

        # check if equal authorization exists
        for (id_trav, ) in run_sql("""SELECT DISTINCT argumentlistid FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = '%s' AND id_accACTION = '%s' """% (id_role, id_action)):
            listlength = run_sql("""SELECT COUNT(*) FROM accROLE_accACTION_accARGUMENT
            WHERE id_accROLE = '%s' AND id_accACTION = '%s' AND argumentlistid = '%s' AND
            id_accARGUMENT IN (%s) """ % (id_role, id_action, id_trav, argstr))[0][0]
            notlist = run_sql("""SELECT COUNT(*) FROM accROLE_accACTION_accARGUMENT
            WHERE id_accROLE = '%s' AND id_accACTION = '%s' AND argumentlistid = '%s' AND
            id_accARGUMENT NOT IN (%s) """ % (id_role, id_action, id_trav, argstr))[0][0]
            # this means that a duplicate already exists
            if not notlist and listlength == len(id_arguments): return []

        # find new arglistid, highest + 1
        try: arglistid = 1 + run_sql("""SELECT MAX(argumentlistid) FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = %s AND id_accACTION = %s """
                                     % (id_role, id_action))[0][0]
        except (IndexError, TypeError): arglistid = 1
        if arglistid <= 0: arglistid = 1

        # insert
        for id_argument in id_arguments:
            run_sql("""INSERT INTO accROLE_accACTION_accARGUMENT values (%s, %s, %s, %s) """
                    % (id_role, id_action, id_argument, arglistid))
            inserted.append([id_role, id_action, id_argument, arglistid])


    return inserted


def acc_addRoleActionArguments(id_role=0, id_action=0, arglistid=-1, optional=0, verbose=0, id_arguments=[]):
    """ function inserts entries in accROLE_accACTION_accARGUMENT if all references are valid.

             id_role, id_action - self explanatory

           arglistid - argumentlistid for the inserted entries
                       if -1: create new group
                       other values: add to this group, if it exists or not

            optional - if this is set to 1, check that function can have
                       optional arguments and add with arglistid -1 and
                       id_argument -1

             verbose - extra output

        id_arguments - list of arguments to add to group."""

    inserted = []

    if verbose: print 'ids: starting'
    if verbose: print 'ids: checking ids'

    # check that all the ids are valid and reference something...
    if not run_sql("""SELECT * FROM accROLE WHERE id = %s""" % (id_role, )):
        return 0

    if verbose: print 'ids: get allowed keywords'
    # check action exist and get allowed keywords
    try:
        allowedkeys = acc_getActionKeywords(id_action=id_action)
        # allowedkeys = run_sql("""SELECT * FROM accACTION WHERE id = %s""" % (id_action, ))[0][3].split(',')
    except (IndexError, AttributeError):
        return 0

    if verbose: print 'ids: is it optional'
    # action with optional arguments
    if optional:
        if verbose: print 'ids: yes - optional'
        if not acc_getActionIsOptional(id_action=id_action):
            return []

        if verbose: print 'ids: run query to check if exists'
        if not run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
        WHERE id_accROLE = %s AND
        id_accACTION = %s AND
        id_accARGUMENT = -1 AND
        argumentlistid = -1""" %
                       (id_role, id_action, )):
            if verbose: print 'ids: does not exist'
            run_sql("""INSERT INTO accROLE_accACTION_accARGUMENT (id_accROLE, id_accACTION, id_accARGUMENT, argumentlistid) VALUES (%s, %s, -1, -1) """
                    % (id_role, id_action))
            return ((id_role, id_action, -1, -1), )
        if verbose: print 'ids: exists'
        return []

    if verbose: print 'ids: check if not arguments'
    # action without arguments
    if not allowedkeys:
        if verbose: print 'ids: not arguments'
        if not run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
                       WHERE id_accROLE = %s AND id_accACTION = %s AND argumentlistid = %s AND id_accARGUMENT = %s"""
                       % (id_role, id_action, 0, 0)):
            if verbose: print 'ids: try to insert'
            result = run_sql("""INSERT INTO accROLE_accACTION_accARGUMENT values (%s, %s, %s, %s)""" % (id_role, id_action, 0, 0))
            return ((id_role, id_action, 0, 0), )
        else:
            if verbose: print 'ids: already existed'
            return 0
    else:
        if verbose: print 'ids: arguments exist'
        argstr = ''
        # check that the argument exists, and that it is a valid key
        if verbose: print 'ids: checking all the arguments'
        for id_argument in id_arguments:
            res_arg = run_sql("""SELECT * FROM accARGUMENT WHERE id = %s""" % (id_argument, ))
            if not res_arg or res_arg[0][1] not in allowedkeys:
                return 0
            else:
                if argstr: argstr += ','
                argstr += '%s' % (id_argument, )

        # arglistid = -1 means that the user wants a new group
        if verbose: print 'ids: find arglistid'
        if arglistid < 0:
            # check if such single group already exists
            for (id_trav, ) in run_sql("""SELECT DISTINCT argumentlistid FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = '%s' AND id_accACTION = '%s' """
                                       % (id_role, id_action)):
                listlength = run_sql("""SELECT COUNT(*) FROM accROLE_accACTION_accARGUMENT
                WHERE id_accROLE = '%s' AND id_accACTION = '%s' AND argumentlistid = '%s' AND
                id_accARGUMENT IN (%s) """ % (id_role, id_action, id_trav, argstr))[0][0]
                notlist = run_sql("""SELECT COUNT(*) FROM accROLE_accACTION_accARGUMENT
                WHERE id_accROLE = '%s' AND id_accACTION = '%s' AND argumentlistid = '%s' AND
                id_accARGUMENT NOT IN (%s) """ % (id_role, id_action, id_trav, argstr))[0][0]
                # this means that a duplicate already exists
                if not notlist and listlength == len(id_arguments): return 0
            # find new arglistid
            try:
                arglistid = run_sql("""SELECT MAX(argumentlistid) FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = %s AND id_accACTION = %s """ %
                                    (id_role, id_action))[0][0] + 1
            except ProgrammingError: return 0
            except (IndexError, TypeError): arglistid = 1

        if arglistid <= 0: arglistid = 1

        if verbose: print 'ids: insert all the entries'
        # all references are valid, insert: one entry in raa for each argument
        for id_argument in id_arguments:
            if not run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = %s AND id_accACTION = %s AND id_accARGUMENT = %s AND argumentlistid = %s""" %
                           (id_role, id_action, id_argument, arglistid)):
                run_sql("""INSERT INTO accROLE_accACTION_accARGUMENT (id_accROLE, id_accACTION, id_accARGUMENT, argumentlistid) VALUES (%s, %s, %s, %s) """
                        % (id_role, id_action, id_argument, arglistid))
                inserted.append((id_role, id_action, id_argument, arglistid))
        # [(r, ac, ar1, aid), (r, ac, ar2, aid)]

        if verbose:
            print 'ids:   inside add function'
            for r in acc_findPossibleActions(id_role=id_role, id_action=id_action):
                print 'ids:   ', r

    return inserted


def acc_addRoleActionArguments_names(name_role='', name_action='', arglistid=-1, optional=0, verbose=0, **keyval):
    """ this function makes it possible to pass names when creating new entries instead of ids.
    get ids for all the names,
    create entries in accARGUMENT that does not exist,
    pass on to id based function.

    name_role, name_action - self explanatory

    arglistid - add entries to or create group with arglistid, default -1 create new.

     optional - create entry with optional keywords, **keyval is ignored, but should be empty

      verbose - used to print extra information

     **keyval - dictionary of keyword=value pairs, used to find ids. """

    if verbose: print 'names: starting'
    if verbose: print 'names: checking ids'

    # find id of the role, return 0 if it doesn't exist
    id_role = run_sql("""SELECT id FROM accROLE where name = '%s'""" % (name_role, ))
    if id_role: id_role = id_role[0][0]
    else: return 0

    # find id of the action, return 0 if it doesn't exist
    res = run_sql("""SELECT * from accACTION where name = '%s'""" % (name_action, ))
    if res: id_action = res[0][0]
    else: return 0

    if verbose: print 'names: checking arguments'

    id_arguments = []
    if not optional:
        if verbose: print 'names: not optional'
        # place to keep ids of arguments and list of allowed keywords
        allowedkeys = acc_getActionKeywords(id_action=id_action) # res[0][3].split(',')

        # find all the id_arguments and create those that does not exist
        for key in keyval.keys():
            # this key does not exist
            if key not in allowedkeys:
                return 0

            id_argument = acc_getArgumentId(key, keyval[key])
            id_argument = id_argument or run_sql("""INSERT INTO accARGUMENT (keyword, value) values ('%s', '%s') """ % (key, keyval[key]))

            id_arguments.append(id_argument) # append the id to the list
    else:
        if verbose: print 'names: optional'

    # use the other function
    return acc_addRoleActionArguments(id_role=id_role,
                                      id_action=id_action,
                                      arglistid=arglistid,
                                      optional=optional,
                                      verbose=verbose,
                                      id_arguments=id_arguments)


# DELETE WITH ID OR NAMES

def acc_deleteRoleActionArguments(id_role, id_action, arglistid=1, auths=[[]]):
    """delete all entries in accROLE_accACTION_accARGUMENT that satisfy the parameters.
    return number of actual deletes.

    this function relies on the id-lists in auths to have the same order has the possible actions...

    id_role, id_action - self explanatory

       arglistid - group to delete from.
                   if more entries than deletes, split the group before delete.

    id_arguments - list of ids to delete."""

    keepauths = [] # these will be kept
    # find all possible actions
    pas = acc_findPossibleActions_ids(id_role, id_action)
    header = pas[0]
    # decide which to keep or throw away

    for pa in pas[1:]:
        if pa[0] == arglistid and pa[1:] not in auths:
            keepauths.append(pa[1:])

    # delete everything
    run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT
    WHERE id_accROLE = %s AND
    id_accACTION = %s AND
    argumentlistid = %s """
            % (id_role, id_action, arglistid))

    # insert those to be kept
    for auth in keepauths:
        acc_addRoleActionArguments(id_role=id_role,
                                   id_action=id_action,
                                   arglistid=-1,
                                   id_arguments=auth)

    return 1


def acc_deleteRoleActionArguments_names(name_role='', name_action='', arglistid=1, **keyval):
    """utilize the function on ids by first finding all ids and redirecting the function call.
    break of and return 0 if any of the ids can't be found.

    name_role = name of the role

    name_action - name of the action

    arglistid - the argumentlistid, all keyword=value pairs must be in this same group.

    **keyval - dictionary of keyword=value pairs for the arguments."""

    # find ids for role and action
    id_role = acc_getRoleId(name_role=name_role)
    id_action = acc_getActionId(name_action=name_action)

    # create string with the ids
    idstr = ''
    idlist = []
    for key in keyval.keys():
        id = acc_getArgumentId(key, keyval[key])
        if not id: return 0

        if idstr: idstr += ','
        idstr += '%s' % id
        idlist.append(id)

    # control that a fitting group exists
    try: count = run_sql("""SELECT COUNT(*) FROM accROLE_accACTION_accARGUMENT
    WHERE id_accROLE = %s AND
    id_accACTION = %s AND
    argumentlistid = %s AND
    id_accARGUMENT IN (%s)""" % (id_role, id_action, arglistid, idstr))[0][0]
    except IndexError: return 0

    if count < len(keyval): return 0

    # call id based function
    return acc_deleteRoleActionArguments(id_role, id_action, arglistid, [idlist])


def acc_deleteRoleActionArguments_group(id_role=0, id_action=0, arglistid=0):
    """delete entire group of arguments for connection between role and action."""

    if not id_role or not id_action: return []

    return run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT
    WHERE id_accROLE = %s AND
    id_accACTION = %s AND
    argumentlistid = %s """ % (id_role, id_action, arglistid))


def acc_deletePossibleActions(id_role=0, id_action=0, authids=[]):
    """delete authorizations in selected rows. utilization of the delete function.

    id_role - id of  role to be connected to action.

    id_action - id of action to be connected to role

    authids - list of row indexes to be removed. """

    # find all authorizations
    pas = acc_findPossibleActions(id_role=id_role, id_action=id_action)

    # get the keys
    keys = pas[0][1:]

    # create dictionary for all the argumentlistids
    ald = {}
    for authid in authids:
        if authid > len(pas): return authid, len(pas)

        # get info from possible action
        id = pas[authid][0]
        values = pas[authid][1:]
        # create list of authids for each authorization
        auth = [acc_getArgumentId(keys[0], values[0])]
        for i in range(1, len(keys)):
            auth.append(acc_getArgumentId(keys[i], values[i]))

        # create entries in the dictionary for each argumentlistid
        try: ald[id].append(auth)
        except KeyError: ald[id] = [auth]

    # do the deletes
    result = 1
    for key in ald.keys():
        result = 1 and acc_deleteRoleActionArguments(id_role=id_role,
                                                     id_action=id_action,
                                                     arglistid=key,
                                                     auths=ald[key])
    return result


def acc_deleteRoleAction(id_role=0, id_action=0):
    """delete all connections between a role and an action. """

    count = run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT
    WHERE id_accROLE = '%s' AND id_accACTION = '%s' """ % (id_role, id_action))

    return count

# GET FUNCTIONS

# ACTION RELATED

def acc_getActionId(name_action):
    """get id of action when name is given

    name_action - name of the wanted action"""

    try: return run_sql("""SELECT id FROM accACTION WHERE name = '%s'""" % (name_action, ))[0][0]
    except IndexError: return 0


def acc_getActionName(id_action):
    """get name of action when id is given. """

    try:
        return run_sql("""SELECT name FROM accACTION WHERE id = %s""" % (id_action, ))[0][0]
    except (ProgrammingError, IndexError):
        return ''


def acc_getActionDescription(id_action):
    """get description of action when id is given. """

    try:
        return run_sql("""SELECT description FROM accACTION WHERE id = %s""" % (id_action, ))[0][0]
    except (ProgrammingError, IndexError):
        return ''


def acc_getActionKeywords(id_action=0, name_action=''):
    """get list of keywords for action when id is given.
    empty list if no keywords."""

    result = acc_getActionKeywordsString(id_action=id_action, name_action=name_action)

    if result: return result.split(',')
    else: return []


def acc_getActionKeywordsString(id_action=0, name_action=''):
    """get keywordstring when id is given. """

    id_action = id_action or acc_getActionId(name_action)
    try: result = run_sql("""SELECT allowedkeywords from accACTION where id = %s """ % (id_action, ))[0][0]
    except IndexError: return ''

    return result


def acc_getActionIsOptional(id_action=0):
    """get if the action arguments are optional or not.
    return 1 if yes, 0 if no."""

    result = acc_getActionOptional(id_action=id_action)
    return result == 'yes' and 1 or 0


def acc_getActionOptional(id_action=0):
    """get if the action arguments are optional or not.
    return result, but 0 if action does not exist. """

    try: result = run_sql("""SELECT optional from accACTION where id = %s """ % (id_action, ))[0][0]
    except IndexError: return 0

    return result


def acc_getActionDetails(id_action=0):
    """get all the fields for an action."""

    details = []
    try: result = run_sql("""SELECT * FROM accACTION WHERE id = %s """ % (id_action, ))[0]
    except IndexError: return details

    if result:
        for r in result: details.append(r)

    return details


def acc_getAllActions():
    """returns all entries in accACTION."""
    return run_sql("""SELECT a.id, a.name, a.description FROM accACTION a ORDER BY a.name""")


def acc_getActionRoles(id_action):
    return run_sql("""SELECT DISTINCT(r.id), r.name, r.description
    FROM accROLE_accACTION_accARGUMENT raa LEFT JOIN accROLE r
    ON raa.id_accROLE = r.id
    WHERE raa.id_accACTION = %s
    ORDER BY r.name """ % (id_action, ))


# ROLE RELATED

def acc_getRoleId(name_role):
    """get id of role, name given. """
    try: return run_sql("""SELECT id FROM accROLE WHERE name = %s""", (name_role, ))[0][0]
    except IndexError: return 0


def acc_getRoleName(id_role):
    """get name of role, id given. """

    try: return run_sql("""SELECT name FROM accROLE WHERE id = %s""", (id_role, ))[0][0]
    except IndexError: return ''

def acc_getRoleDefinition(id_role=0):
    """get firewall like role definition object for a role."""

    try: return run_sql("""SELECT firerole_def_ser FROM accROLE WHERE id = %s""", (id_role, ))[0][0]
    except IndexError: return ''


def acc_getRoleDetails(id_role=0):
    """get all the fields for an action."""

    details = []
    try: result = run_sql("""SELECT id, name, description, firerole_def_src FROM accROLE WHERE id = %s """, (id_role, ))[0]
    except IndexError: return details

    if result:
        for r in result: details.append(r)

    return details


def acc_getAllRoles():
    """get all entries in accROLE."""

    return run_sql("""SELECT r.id, r.name, r.description, r.firerole_def_ser, r.firerole_def_src FROM accROLE r ORDER BY r.name""")


def acc_getRoleActions(id_role):
    """get all actions connected to a role. """

    return run_sql("""SELECT DISTINCT(a.id), a.name, a.description
                      FROM accROLE_accACTION_accARGUMENT raa, accACTION a
                      WHERE raa.id_accROLE = %s and
                            raa.id_accACTION = a.id
                      ORDER BY a.name """, (id_role, ))


def acc_getRoleUsers(id_role):
    """get all users that have access to a role. """

    return run_sql("""SELECT DISTINCT(u.id), u.email, u.settings
    FROM user_accROLE ur, user u
    WHERE ur.id_accROLE = %s AND
    u.id = ur.id_user
    ORDER BY u.email""", (id_role, ))


# ARGUMENT RELATED

def acc_getArgumentId(keyword, value):
    """get id of argument, keyword=value pair given.
    value = 'optional value' is replaced for id_accARGUMENT = -1."""

    try: return run_sql("""SELECT DISTINCT id FROM accARGUMENT WHERE keyword = %s and value = %s""", (keyword, value))[0][0]
    except IndexError:
        if value == 'optional value': return -1
        return 0


# USER RELATED

def acc_getUserEmail(id_user=0):
    """get email of user, id given."""

    try: return run_sql("""SELECT email FROM user WHERE id = %s """, (id_user, ))[0][0]
    except IndexError: return ''


def acc_getUserId(email=''):
    """get id of user, email given."""

    try: return run_sql("""SELECT id FROM user WHERE email = %s """, (email, ))[0][0]
    except IndexError: return 0


def acc_getUserRoles(id_user=0):
    """get all roles a user is connected to."""

    res = run_sql("""SELECT ur.id_accROLE
    FROM user_accROLE ur
    WHERE ur.id_user = %s
    ORDER BY ur.id_accROLE""", (id_user, ))

    return res


def acc_findUserInfoIds(id_user=0):
    """find all authorization entries for all the roles a user is connected to."""

    res1 = run_sql("""SELECT ur.id_user, raa.*
    FROM user_accROLE ur LEFT JOIN accROLE_accACTION_accARGUMENT raa
    ON ur.id_accROLE = raa.id_accROLE
    WHERE ur.id_user = %s """, (id_user, ))

    res2 = []
    for res in res1: res2.append(res)
    res2.sort()

    return res2

def acc_findUserInfoNames(id_user=0):
    query = """ SELECT ur.id_user, r.name, ac.name, raa.argumentlistid, ar.keyword, ar.value
    FROM accROLE_accACTION_accARGUMENT raa, user_accROLE ur, accROLE r, accACTION ac, accARGUMENT ar
    WHERE ur.id_user = %s and
    ur.id_accROLE = raa.id_accROLE and
    raa.id_accROLE = r.id and
    raa.id_accACTION = ac.id and
    raa.id_accARGUMENT = ar.id """ % (id_user, )

    res1 =  run_sql(query)

    res2 = []
    for res in res1: res2.append(res)
    res2.sort()

    return res2

def acc_findUserRoleActions(user_info):
    """find name of all roles and actions connected to user_info (or uid), id given."""

    if type(user_info) in [type(1), type(1L)]:
        uid = user_info
    else:
        uid = user_info['uid']

    query = """SELECT DISTINCT r.name, a.name
    FROM user_accROLE ur, accROLE_accACTION_accARGUMENT raa, accACTION a, accROLE r
    WHERE ur.id_user = %s and
    ur.id_accROLE = raa.id_accROLE and
    raa.id_accACTION = a.id and
    raa.id_accROLE = r.id """ % (uid, )

    res1 = run_sql(query)

    res2 = []
    for res in res1: res2.append(res)
    res2.sort()

    if type(user_info) == type({}):
        query = """SELECT DISTINCT r.name, a.name, r.firerole_def_ser
        FROM accROLE_accACTION_accARGUMENT raa, accACTION a, accROLE r
        WHERE raa.id_accACTION = a.id and
        raa.id_accROLE = r.id """

        res3 = run_sql(query)
        res4 = []
        for role_name, action_name, role_definition in res3:
            if acc_firerole_check_user(user_info, deserialize(role_definition)):
                res4.append((role_name, action_name))
        return list(Set(res2) or Set(res4))
    else:
        return res2


# POSSIBLE ACTIONS / AUTHORIZATIONS

def acc_findPossibleActionsAll(id_role):
    """find all the possible actions for a role.
    the function utilizes acc_findPossibleActions to find
    all the entries from each of the actions under the given role

    id_role - role to find all actions for

    returns a list with headers"""

    query = """SELECT DISTINCT(aar.id_accACTION)
               FROM accROLE_accACTION_accARGUMENT aar
               WHERE aar.id_accROLE = %s
               ORDER BY aar.id_accACTION""" % (id_role, )

    res = []

    for (id_action, ) in run_sql(query):
        hlp = acc_findPossibleActions(id_role, id_action)
        if hlp:
            res.append(['role', 'action'] + hlp[0])
        for row in hlp[1:]:
            res.append([id_role, id_action] + row)

    return res

def acc_findPossibleActionsArgumentlistid(id_role, id_action, arglistid):
    """find all possible actions with the given arglistid only."""

    # get all, independent of argumentlistid
    res1 = acc_findPossibleActions_ids(id_role, id_action)

    # create list with only those with the right arglistid
    res2 = []
    for row in res1[1:]:
        if row[0] == arglistid: res2.append(row)

    # return this list
    return res2


def acc_findPossibleActionsUser(id_user, id_action):
    """user based function to find all action combination for a given
    user and action. find all the roles and utilize findPossibleActions for all these.

      id_user - user id, used to find roles

    id_action - action id. """

    res = []

    for (id_role, ) in acc_getUserRoles(id_user):
        hlp = acc_findPossibleActions(id_role, id_action)
        if hlp and not res: res.append(['role'] + hlp[0])

        for row in hlp[1:]:
            res.append([id_role] + row)

    return res


def acc_findPossibleActions_ids(id_role, id_action):
    """finds the ids of the possible actions.
    utilization of acc_getArgumentId and acc_findPossibleActions. """

    pas = acc_findPossibleActions(id_role, id_action)

    if not pas: return []

    keys = pas[0]
    pas_ids = [pas[0:1]]

    for pa in pas[1:]:
        auth = [pa[0]]
        for i in range(1, len(pa)):
            auth.append(acc_getArgumentId(keys[i], pa[i]))
        pas_ids.append(auth)

    return pas_ids


def acc_findPossibleActions(id_role, id_action):
    """Role based function to find all action combinations for a
    give role and action.

      id_role - id of role in the database

    id_action - id of the action in the database

    returns a list with all the combinations.
    first row is used for header."""

    # query to find all entries for user and action
    res1 = run_sql(""" SELECT raa.argumentlistid, ar.keyword, ar.value
    FROM accROLE_accACTION_accARGUMENT raa, accARGUMENT ar
    WHERE raa.id_accROLE = %s and
    raa.id_accACTION = %s and
    raa.id_accARGUMENT = ar.id """, (id_role, id_action))

    # find needed keywords, create header
    keywords = acc_getActionKeywords(id_action=id_action)
    keywords.sort()

    if not keywords:
        # action without arguments
        if run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE = %s AND id_accACTION = %s AND id_accARGUMENT = 0 AND argumentlistid = 0""", (id_role, id_action)):
            return [['#', 'argument keyword'], ['0', 'action without arguments']]


    # tuples into lists
    res2, arglistids = [], {}
    for res in res1:
        res2.append([])
        for r in res: res2[-1].append(r)
    res2.sort()

    # create multilevel dictionary
    for res in res2:
        a, kw, value = res # rolekey, argumentlistid, keyword, value
        if kw not in keywords: continue
        if not arglistids.has_key(a):
            arglistids[a] = {}
        # fill dictionary
        if not arglistids[a].has_key(kw):    arglistids[a][kw] = [value]
        elif not value in arglistids[a][kw]: arglistids[a][kw] = arglistids[a][kw] + [value]

    # fill list with all possible combinations
    res3 = []
    # rolekeys = roles2.keys();    rolekeys.sort()
    for a in arglistids.keys(): # argumentlistids
        # fill a list with the new entries, shortcut and copying first keyword list
        next_arglistid = []
        for row in arglistids[a][keywords[0]]: next_arglistid.append([a, row[:] ])
        # run through the rest of the keywords
        for kw in keywords[1:]:
            if not arglistids[a].has_key(kw): arglistids[a][kw] = ['optional value']

            new_list = arglistids[a][kw][:]
            new_len  = len(new_list)
            # duplicate the list
            temp_list = []
            for row in next_arglistid:
                for i in range(new_len): temp_list.append(row[:])
            # append new values
            for i in range(len(temp_list)):
                new_item = new_list[i % new_len][:]
                temp_list[i].append(  new_item  )
            next_arglistid = temp_list[:]

        res3.extend(next_arglistid)

    res3.sort()

    # if optional allowed, put on top
    opt = run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
    WHERE id_accROLE = %s AND
    id_accACTION = %s AND
    id_accARGUMENT = -1 AND
    argumentlistid = -1""" % (id_role, id_action))

    if opt: res3.insert(0, [-1] + ['optional value'] * len(keywords))

    # put header on top
    if res3:
        res3.insert(0, ['#'] + keywords)

    return res3


def acc_splitArgumentGroup(id_role=0, id_action=0, arglistid=0):
    """collect the arguments, find all combinations, delete original entries
    and insert the new ones with different argumentlistids for each group

      id_role - id of the role

    id_action - id of the action

    arglistid - argumentlistid to be splittetd"""

    if not id_role or not id_action or not arglistid: return []

    # don't split if none or one possible actions
    res = acc_findPossibleActionsArgumentlistid(id_role, id_action, arglistid)
    if not res or len(res) <= 1: return 0

    # delete the existing group
    delete = acc_deleteRoleActionArguments_group(id_role, id_action, arglistid)

    # add all authorizations with new and different argumentlistid
    addlist = []
    for row in res:
        argids = row[1:]
        addlist.append(acc_addRoleActionArguments(id_role=id_role,
                                                  id_action=id_action,
                                                  arglistid=-1,
                                                  id_arguments=argids))

    # return list of added authorizations
    return addlist


def acc_mergeArgumentGroups(id_role=0, id_action=0, arglistids=[]):
    """merge the authorizations from groups with different argumentlistids
    into one single group.
    this can both save entries in the database and create extra authorizations.

    id_role - id of the role

    id_action - role of the action

    arglistids - list of groups to be merged together into one."""

    if len(arglistids) < 2: return []

    argstr = ''
    for id in arglistids:
        argstr += 'raa.argumentlistid = %s or ' % (id, )
    argstr = '(%s)' % (argstr[:-4], )

    # query to find all entries that will be merged
    query = """ SELECT ar.keyword, ar.value, raa.id_accARGUMENT
    FROM accROLE_accACTION_accARGUMENT raa, accARGUMENT ar
    WHERE raa.id_accROLE = %s and
     raa.id_accACTION = %s and
     %s and
     raa.id_accARGUMENT = ar.id """ % (id_role, id_action, argstr)

    q_del = """DELETE FROM accROLE_accACTION_accARGUMENT
    WHERE id_accROLE = %s and
     id_accACTION = %s and
     %s """ % (id_role, id_action, argstr.replace('raa.', ''))

    res = run_sql(query)
    if not res: return []

    run_sql(q_del)

    # list of entire entries
    old = []
    # list of only the ids
    ids = []
    for (k, v, id) in res:
        if [k, v, id] not in old:
            old.append([k, v, id])
            ids.append(id)
    # for (k, v, id) in res: if id not in ids: ids.append(id)

    return acc_addRoleActionArguments(id_role=id_role,
                                      id_action=id_action,
                                      arglistid=-1,
                                      id_arguments=ids)


def acc_reset_default_settings(superusers=[]):
    """reset to default by deleting everything and adding default.

    superusers - list of superuser emails """

    remove = acc_delete_all_settings()
    add = acc_add_default_settings(superusers=superusers)

    return remove, add

def acc_delete_all_settings():
    """simply remove all data affiliated with webaccess by truncating
    tables accROLE, accACTION, accARGUMENT and those connected. """

    run_sql("""TRUNCATE accROLE""")
    run_sql("""TRUNCATE accACTION""")
    run_sql("""TRUNCATE accARGUMENT""")
    run_sql("""TRUNCATE user_accROLE""")
    run_sql("""TRUNCATE accROLE_accACTION_accARGUMENT""")

    return 1


def acc_add_default_settings(superusers=[]):
    """add the default settings if they don't exist.

    superusers - list of superuser emails """

    # imported from config
    global supportemail
    # imported from access_control_config
    global DEF_ROLES
    global DEF_USERS
    global DEF_ACTIONS
    global DEF_AUTHS

    # from superusers: allow input formats ['email1', 'email2'] and [['email1'], ['email2']] and [['email1', id], ['email2', id]]
    for user in superusers:
        if type(user) is str: user = [user]
        DEF_USERS.append(user[0])
    if supportemail not in DEF_USERS: DEF_USERS.append(supportemail)

    # add data

    # add roles
    insroles = []
    for (name, description, firerole_def_src) in DEF_ROLES:
        # try to add, don't care if description is different
        id = acc_addRole(name_role=name,
                         description=description, firerole_def_ser=serialize(compile_role_definition(firerole_def_src)), firerole_def_src=firerole_def_src)
        if not id:
            id = acc_getRoleId(name_role=name)
            acc_updateRole(id_role=id, description=description, firerole_def_ser=serialize(compile_role_definition(firerole_def_src)), firerole_def_src=firerole_def_src)
        insroles.append([id, name, description, firerole_def_src])

    # add users to superadmin
    insuserroles = []
    for user in DEF_USERS:
        insuserroles.append(acc_addUserRole(email=user,
                                            name_role=SUPERADMINROLE))

    # add actions
    insactions = []
    for (name, description, allkeys, optional) in DEF_ACTIONS:
        # try to add action as new
        id = acc_addAction(name, description, optional, allkeys)
        # action with the name exist
        if not id:
            id = acc_getActionId(name_action=name)
            # update the action, necessary updates to the database will also be done
            acc_updateAction(id_action=id, optional=optional, allowedkeywords=allkeys)
        # keep track of inserted actions
        insactions.append([id, name, description, allkeys])

    # add authorizations
    insauths = []
    for (name_role, name_action, arglistid, optional, args) in DEF_AUTHS:
        # add the authorization
        acc_addRoleActionArguments_names(name_role=name_role,
                                         name_action=name_action,
                                         arglistid=arglistid,
                                         optional=optional,
                                         **args)
        # keep track of inserted authorizations
        insauths.append([name_role, name_action, arglistid, optional, args])


    return insroles, insactions, insuserroles, insauths


def acc_find_delegated_roles(id_role_admin=0):
    """find all the roles the admin role has delegation rights over.
    return tuple of all the roles.

    id_role_admin - id of the admin role """

    id_action_delegate = acc_getActionId(name_action=DELEGATEADDUSERROLE)

    rolenames = run_sql("""SELECT DISTINCT(ar.value)
    FROM accROLE_accACTION_accARGUMENT raa LEFT JOIN accARGUMENT ar
    ON raa.id_accARGUMENT = ar.id
    WHERE raa.id_accROLE = '%s' AND
    raa.id_accACTION = '%s'
    """ % (id_role_admin, id_action_delegate))

    result = []

    for (name_role, ) in rolenames:
        roledetails = run_sql("""SELECT * FROM accROLE WHERE name = %s """, (name_role, ))
        if roledetails: result.append(roledetails)

    return result


def acc_cleanupArguments():
    """function deletes all accARGUMENTs that are not referenced by accROLE_accACTION_accARGUMENT.
    returns how many arguments where deleted and a list of the deleted id_arguments"""

    # find unreferenced arguments
    ids1 = run_sql("""SELECT DISTINCT ar.id
    FROM accARGUMENT ar LEFT JOIN accROLE_accACTION_accARGUMENT raa ON ar.id = raa.id_accARGUMENT
    WHERE raa.id_accARGUMENT IS NULL """)

    # it is clean
    if not ids1: return 1

    # create list and string of the ids
    ids2 = []
    idstr = ''
    for (id, ) in ids1:
        ids2.append(id)
        if idstr: idstr += ','
        idstr += '%s' % id

    # delete unreferenced arguments
    count = run_sql("""DELETE FROM accARGUMENT
    WHERE id in (%s)""" % (idstr, ))

    # return count and ids of deleted arguments
    return (count, ids2)


def acc_cleanupUserRoles():
    """remove all entries in user_accROLE referencing non-existing roles.
    return number of deletes and the ids.

    FIXME: THIS FUNCTION HAS NOT BEEN TESTED """

    # find unreferenced arguments
    ids1 = run_sql("""SELECT DISTINCT ur.id_accROLE
    FROM accROLE ur LEFT JOIN accROLE r ON ur.id_accROLE = r.id
    WHERE r.id IS NULL""")

    # it is clean
    if not ids1: return 1

    # create list and string of the ids
    ids2 = []
    idstr = ''
    for (id, ) in ids1:
        ids2.append(id)
        if idstr: idstr += ','
        idstr += '%s' % id

    # delete unreferenced arguments
    count = run_sql("""DELETE FROM user_accROLE
    WHERE id_accROLE in (%s)""" % (idstr, ))

    # return count and ids of deleted arguments
    return (count, ids2)


def acc_garbage_collector(verbose=0):
    """clean the entire database for unused data"""

    # keep track of all deleted entries

    del_entries = []

    # user_accROLEs without existing role or user
    count = 0
    # roles have been deleted
    id_roles = run_sql("""SELECT DISTINCT r.id FROM accROLE r""")
    idrolesstr = ''
    for (id, ) in id_roles:
        idrolesstr += (idrolesstr and ',' or '') + '%s' % id
    if idrolesstr:
        count += run_sql("""DELETE FROM user_accROLE WHERE id_accROLE NOT IN (%s)""" % (idrolesstr, ))
    # users have been deleted
    id_users = run_sql("""SELECT DISTINCT u.id FROM user u WHERE email != ''""")
    idusersstr = ''
    for (id, ) in id_users:
        idusersstr += (idusersstr and ',' or '') + '%s' % id
    if idusersstr:
        count += run_sql("""DELETE FROM user_accROLE WHERE id_user NOT IN (%s) """ % (idusersstr, ))

    del_entries.append([count])

    # accROLE_accACTION_accARGUMENT where role is deleted
    count = 0
    if idrolesstr:
        count += run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT WHERE id_accROLE NOT IN (%s)""" % (idrolesstr, ))
    # accROLE_accACTION_accARGUMENT where action is deleted
    id_actions = run_sql("""SELECT DISTINCT a.id FROM accACTION a""")
    idactionsstr = ''
    for (id, ) in id_actions:
        idactionsstr += (idactionsstr and ',' or '') + '%s' % id # FIXME: here was a syntactic bug, so check the code!
    if idactionsstr:
        count += run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT WHERE id_accACTION NOT IN (%s)""" % (idactionsstr, ))

    del_entries.append([count])

    # delegated roles that does not exist

    nameroles = run_sql("""SELECT DISTINCT r.name FROM accROLE r""")
    namestr = ''
    for (name, ) in nameroles:
        namestr += (namestr and ',' or '') + '"%s"' % name
    if namestr:
        idargs = run_sql("""SELECT ar.id FROM accARGUMENT WHERE keyword = 'role' AND value NOT IN (%s) """ % (namestr, ))
        idstr = ''
        for (id, ) in idargs:
            idstr += (idstr and ',' or '') + '%s' % id

    if namestr and idstr:
        count = run_sql("""DELETE FROM accROLE_accACTION_accARGUMENT WHERE id_accARGUMENT IN (%s) """ % (idstr, ))
    else: count = 0

    del_entries.append([0])

    # delete unreferenced arguments
    unused_args = run_sql("""SELECT DISTINCT ar.id
    FROM accARGUMENT ar LEFT JOIN accROLE_accACTION_accARGUMENT raa ON ar.id = raa.id_accARGUMENT
    WHERE raa.id_accARGUMENT IS NULL """)

    args = []
    idstr = ''
    for (id, ) in unused_args:
        args.append(id)
        idstr += (idstr and ',' or '') + '%s' % id

    count = run_sql("""DELETE FROM accARGUMENT
    WHERE id in (%s)""" % (idstr, ))

    del_entries.append([count, args])

    # return statistics
    return del_entries


