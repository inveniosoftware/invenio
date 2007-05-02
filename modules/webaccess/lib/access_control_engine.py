## $Id$
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

"""CDS Invenio Access Control Engine in mod_python."""

__revision__ = "$Id$"

from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS, \
     version
from invenio.dbquery import run_sql, ProgrammingError
from invenio.access_control_config import SUPERADMINROLE, CFG_WEBACCESS_WARNING_MSGS, CFG_WEBACCESS_MSGS

called_from = 1 #1=web,0=cli
try:
    import _apache
except ImportError, e:
    called_from = 0

## access controle engine function
def acc_authorize_action(id_user, name_action, verbose=0, **arguments):
    """Check if user is allowed to perform action
    with given list of arguments.
    Return (0, message) if authentication succeeds, (error code, error message) if it fails.

    The arguments are as follows:

          id_user - id of the user in the database

      name_action - the name of the action

        arguments - dictionary with keyword=value pairs created automatically
                    by python on the extra arguments. these depend on the
                    given action.
    """

    #TASK -1: Checking external source if user is authorized:
    #if CFG_:
    #    em_pw = run_sql("SELECT email, password FROM user WHERE id=%s", (id_user,))
    #    if em_pw:
    #        if not CFG_EXTERNAL_ACCESS_CONTROL.loginUser(em_pw[0][0], em_pw[0][1]):
    #            return (10, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[10], (called_from and CFG_WEBACCESS_MSGS[1] or "")))
    # TASK 0: find id and allowedkeywords of action
    if verbose: print 'task 0 - get action info'
    query1 = """select a.id, a.allowedkeywords, a.optional
                from accACTION a
                where a.name = '%s'""" % (name_action)

    try: id_action, aallowedkeywords, optional = run_sql(query1)[0]
    except (ProgrammingError, IndexError): return (3, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[3] % name_action, (called_from and CFG_WEBACCESS_MSGS[1] or "")))

    defkeys = aallowedkeywords.split(',')
    for key in arguments.keys():
        if key not in defkeys: return (8, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[8], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or ""))) #incorrect arguments?
    # -------------------------------------------


    # TASK 1: check if user is a superadmin
    # we know the action exists. no connection with role is necessary
    # passed arguments must have allowed keywords
    # no check to see if the argument exists
    if verbose: print 'task 1 - is user %s' % (SUPERADMINROLE, )

    if run_sql("""SELECT *
    FROM accROLE r LEFT JOIN user_accROLE ur
    ON r.id = ur.id_accROLE
    WHERE r.name = '%s' AND
    ur.id_user = '%s' """ % (SUPERADMINROLE, id_user)):
        return (0, CFG_WEBACCESS_WARNING_MSGS[0])
    # ------------------------------------------


    # TASK 2: check if user exists and find all the user's roles and create or-string
    if verbose: print 'task 2 - find user and userroles'

    try:
        query2 = """SELECT email, note from user where id=%s""" % id_user
        res2 = run_sql(query2)
        if not res2:
            raise Exception
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1 and res2[0][1] not in [1, "1"]:
            if res2[0][0]:
                return (9, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[9] % res2[0][0], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))
            else:
                raise Exception
        query2 = """SELECT ur.id_accROLE FROM user_accROLE ur WHERE ur.id_user=%s ORDER BY ur.id_accROLE """ % id_user
        res2 = run_sql(query2)
    except Exception: return (6, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[6], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))

    if not res2: return (2, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[2], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or ""))) #user has no roles
    # -------------------------------------------

    # create role string (add default value? roles='(raa.id_accROLE='def' or ')
    str_roles = ''
    for (role, ) in res2:
        if str_roles: str_roles += ','
        str_roles += '%s' % (role, )

    # TASK 3: authorizations with no arguments given
    if verbose: print 'task 3 - checks with no arguments'
    if not arguments:
        # 3.1
        if optional == 'no':
            if verbose: print ' - action with zero arguments'
            connection = run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
            WHERE id_accROLE IN (%s) AND
            id_accACTION = %s AND
            argumentlistid = 0 AND
            id_accARGUMENT = 0 """ % (str_roles, id_action))

            if connection and 1:
                return (0, CFG_WEBACCESS_WARNING_MSGS[0])
            else:
                return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))

        # 3.2
        if optional == 'yes':
            if verbose: print ' - action with optional arguments'
            connection = run_sql("""SELECT * FROM accROLE_accACTION_accARGUMENT
            WHERE id_accROLE IN (%s) AND
            id_accACTION = %s AND
            id_accARGUMENT = -1 AND
            argumentlistid = -1 """ % (str_roles, id_action))

            if connection and 1:
                return (0, CFG_WEBACCESS_WARNING_MSGS[0])
            else:
                return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))

        # none of the zeroargs tests succeded
        if verbose: print ' - not authorization without arguments'
        return (5, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[5], (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or ""))))

    # TASK 4: create list of keyword and values that satisfy part of the authentication and create or-string
    if verbose: print 'task 4 - create keyword=value pairs'

    # create dictionary with default values and replace entries from input arguments
    defdict = {}

    for key in defkeys:
        try: defdict[key] = arguments[key]
        except KeyError: return (5, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[5], (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or "")))) # all keywords must be present
        # except KeyError: defdict[key] = 'x' # default value, this is not in use...

    # create or-string from arguments
    str_args = ''
    for key in defkeys:
        if str_args: str_args += ' OR '
        str_args += """(arg.keyword = '%s' AND arg.value = '%s')""" % (key, defdict[key])


    # TASK 5: find all the table entries that partially authorize the action in question
    if verbose: print 'task 5 - find table entries that are part of the result'

    query4 = """SELECT DISTINCT raa.id_accROLE, raa.id_accACTION, raa.argumentlistid,
    raa.id_accARGUMENT, arg.keyword, arg.value
    FROM accROLE_accACTION_accARGUMENT raa, accARGUMENT arg
    WHERE raa.id_accACTION = %s AND
    raa.id_accROLE IN (%s) AND
    (%s) AND
    raa.id_accARGUMENT = arg.id """ % (id_action, str_roles, str_args)

    try: res4 = run_sql(query4)
    except ProgrammingError: return (3, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[3], (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or ""))))

    if not res4: return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or ""))) # no entries at all

    res5 = []
    for res in res4:
        res5.append(res)
    res5.sort()

    # USER AUTHENTICATED TO PERFORM ACTION WITH ONE ARGUMENT
    if len(defdict) == 1: return (0, CFG_WEBACCESS_WARNING_MSGS[0])


    # CHECK WITH MORE THAN 1 ARGUMENT

    # TASK 6: run through the result and try to satisfy authentication
    if verbose: print 'task 6 - combine results and try to satisfy'

    cur_role = cur_action = cur_arglistid = 0

    booldict = {}
    for key in defkeys: booldict[key] = 0

    # run through the results

    for (role, action, arglistid, arg, keyword, val) in res5 + [(-1, -1, -1, -1, -1, -1)]:
        # not the same role or argumentlist (authorization group), i.e. check if thing are satisfied
        # if cur_arglistid != arglistid or cur_role != role or cur_action != action:
        if (cur_arglistid, cur_role, cur_action) != (arglistid, role, action):
            if verbose: print ' : checking new combination',

            # test if all keywords are satisfied
            for value in booldict.values():
                if not value: break
            else:
                if verbose: print '-> found satisfying combination'
                return (0, CFG_WEBACCESS_WARNING_MSGS[0]) # USER AUTHENTICATED TO PERFORM ACTION

            if verbose: print '-> not this one'

            # assign the values for the current tuple from the query
            cur_arglistid, cur_role, cur_action = arglistid, role, action

            for key in booldict.keys():
                booldict[key] = 0

        # set keyword qualified for the action, (whatever result of the test)
        booldict[keyword] = 1

    if verbose: print 'finished'
    # authentication failed
    return (4, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[4], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))


## access controle engine function
def acc_authorize_action_req(req, name_action, verbose=0, **arguments):
    """Check if user is allowed to perform action
    with given list of arguments.
    Return (0, message) if authentication succeeds, (error code, error message) if it fails.

    The arguments are as follows:

          req - mod_python req necessary to discover info on the user

      name_action - the name of the action

        arguments - dictionary with keyword=value pairs created automatically
                    by python on the extra arguments. these depend on the
                    given action.
    """

    #TASK -1: Checking external source if user is authorized:
    #if CFG_:
    #    em_pw = run_sql("SELECT email, password FROM user WHERE id=%s", (id_user,))
    #    if em_pw:
    #        if not CFG_EXTERNAL_ACCESS_CONTROL.loginUser(em_pw[0][0], em_pw[0][1]):
    #            return (10, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[10], (called_from and CFG_WEBACCESS_MSGS[1] or "")))
    # TASK 0: find id and allowedkeywords of action
    from invenio.firewall import load_role_definition, firewall
    if type(req) in [type(1), type(1L)]:
        return acc_authorize_action(req, name_action, verbose, **arguments)
    if verbose: print 'task 0 - get action info'
    query1 = """select a.id, a.allowedkeywords, a.optional
                from accACTION a
                where a.name = '%s'""" % (name_action)

    try: id_action, aallowedkeywords, optional = run_sql(query1)[0]
    except (ProgrammingError, IndexError): return (3, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[3] % name_action, (called_from and CFG_WEBACCESS_MSGS[1] or "")))

    defkeys = aallowedkeywords.split(',')
    for key in arguments.keys():
        if key not in defkeys: return (8, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[8], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or ""))) #incorrect arguments?
    # -------------------------------------------


    # TASK 1: check if user is a superadmin
    # we know the action exists. no connection with role is necessary
    # passed arguments must have allowed keywords
    # no check to see if the argument exists
    if verbose: print 'task 1 - is user %s' % (SUPERADMINROLE, )

    from webuser import extract_user_info
    user_info = extract_user_info(req)

    if firewall(user_info, load_role_definition(SUPERADMINROLE)):
        return (0, CFG_WEBACCESS_WARNING_MSGS[0])
    # ------------------------------------------


    # TASK 2: check if user exists
    if verbose: print 'task 2 - find user'

    query2 = """SELECT email, note from user where id=%s""" % id_user
    res2 = run_sql(query2)
    if res2:
        if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1 and res2[0][1] not in [1, "1"]:
            if res2[0][0]:
                return (9, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[9] % res2[0][0], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))
            else:
                raise Exception

    # TASK 3: authorizations with no arguments given
    if verbose: print 'task 3 - checks with no arguments'
    if not arguments:
        # 3.1
        if optional == 'no':
            if verbose: print ' - action with zero arguments'
            connection = run_sql("""SELECT id_accROLE FROM accROLE_accACTION_accARGUMENT
            WHERE id_accACTION = %s AND
            argumentlistid = 0 AND
            id_accARGUMENT = 0 """ % id_action)

            for id_accROLE in connection:
                if firewall(user_info, load_role_definition(id_accROLE[0])):
                    return (0, CFG_WEBACCESS_WARNING_MSGS[0])

            return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))

        # 3.2
        if optional == 'yes':
            if verbose: print ' - action with optional arguments'
            connection = run_sql("""SELECT id_accROLE FROM accROLE_accACTION_accARGUMENT
            WHERE id_accACTION = %s AND
            id_accARGUMENT = -1 AND
            argumentlistid = -1 """ % id_action)

            for id_accROLE in connection:
                if firewall(user_info, load_role_definition(id_accROLE[0])):
                    return (0, CFG_WEBACCESS_WARNING_MSGS[0])
            return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))

        # none of the zeroargs tests succeded
        if verbose: print ' - not authorization without arguments'
        return (5, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[5], (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or ""))))

    # TASK 4: create list of keyword and values that satisfy part of the authentication and create or-string
    if verbose: print 'task 4 - create keyword=value pairs'

    # create dictionary with default values and replace entries from input arguments
    defdict = {}

    for key in defkeys:
        try: defdict[key] = arguments[key]
        except KeyError: return (5, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[5], (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or "")))) # all keywords must be present
        # except KeyError: defdict[key] = 'x' # default value, this is not in use...

    # create or-string from arguments
    str_args = ''
    for key in defkeys:
        if str_args: str_args += ' OR '
        str_args += """(arg.keyword = '%s' AND arg.value = '%s')""" % (key, defdict[key])


    # TASK 5: find all the table entries that partially authorize the action in question
    if verbose: print 'task 5 - find table entries that are part of the result'

    query4 = """SELECT DISTINCT raa.id_accROLE, raa.id_accACTION, raa.argumentlistid,
    raa.id_accARGUMENT, arg.keyword, arg.value, ar.definition
    FROM accROLE_accACTION_accARGUMENT raa INNER JOIN accRole ar ON raa.id_accROLE = ar.id, accARGUMENT arg
    WHERE raa.id_accACTION = %s AND
    (%s) AND
    raa.id_accARGUMENT = arg.id """ % (id_action, str_args)

    try: res4 = run_sql(query4)
    except ProgrammingError: return (3, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[3], (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or ""))))

    res5 = []
    for row in res4:
        if firewall(user_info, load_role_definition(row[0])):
            res5.append(row)
    if not res5:
        return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or ""))) # no entries at all
    res5.sort()

    # USER AUTHENTICATED TO PERFORM ACTION WITH ONE ARGUMENT
    if len(defdict) == 1: return (0, CFG_WEBACCESS_WARNING_MSGS[0])


    # CHECK WITH MORE THAN 1 ARGUMENT

    # TASK 6: run through the result and try to satisfy authentication
    if verbose: print 'task 6 - combine results and try to satisfy'

    cur_role = cur_action = cur_arglistid = 0

    booldict = {}
    for key in defkeys: booldict[key] = 0

    # run through the results

    for (role, action, arglistid, arg, keyword, val) in res5 + [(-1, -1, -1, -1, -1, -1)]:
        # not the same role or argumentlist (authorization group), i.e. check if thing are satisfied
        # if cur_arglistid != arglistid or cur_role != role or cur_action != action:
        if (cur_arglistid, cur_role, cur_action) != (arglistid, role, action):
            if verbose: print ' : checking new combination',

            # test if all keywords are satisfied
            for value in booldict.values():
                if not value: break
            else:
                if verbose: print '-> found satisfying combination'
                return (0, CFG_WEBACCESS_WARNING_MSGS[0]) # USER AUTHENTICATED TO PERFORM ACTION

            if verbose: print '-> not this one'

            # assign the values for the current tuple from the query
            cur_arglistid, cur_role, cur_action = arglistid, role, action

            for key in booldict.keys():
                booldict[key] = 0

        # set keyword qualified for the action, (whatever result of the test)
        booldict[keyword] = 1

    if verbose: print 'finished'
    # authentication failed
    return (4, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[4], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % name_action[3:], CFG_WEBACCESS_MSGS[1]) or "")))


