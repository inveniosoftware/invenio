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
     version, sweburl
from invenio.dbquery import run_sql_cached, ProgrammingError
import invenio.access_control_admin as aca
from invenio.access_control_config import SUPERADMINROLE, CFG_WEBACCESS_WARNING_MSGS, CFG_WEBACCESS_MSGS
from invenio import webuser
from invenio import access_control_firerole
from invenio.urlutils import make_canonical_urlargd
from urllib import quote

called_from = 1 #1=web,0=cli
try:
    import _apache
except ImportError, e:
    called_from = 0

def make_list_apache_firerole(name_action, arguments):
    """Given an action and a dictionary arguments returns a list of all the
    roles (and their descriptions) which are authorized to perform this
    action with these arguments, and whose FireRole definition expect
    an Apache Password membership.
    """
    roles = aca.acc_find_possible_roles(name_action, arguments)

    ret = []

    for role in roles:
        res = run_sql_cached('SELECT name, description, firerole_def_ser FROM accROLE WHERE id=%s', (role, ), affected_tables=['accROLE'])
        if access_control_firerole.acc_firerole_suggest_apache_p(access_control_firerole.deserialize(res[0][2])):
            ret.append((res[0][0], res[0][1]))
    return ret

def _format_list_of_apache_firerole(roles, referer):
    """Given a list of tuples (role, description) (returned by make_list_apache_firerole), and a referer url, returns a nice string for
    presenting urls that let the user login with Apache password through
    Firerole.
    This function is needed only at CERN for aiding in the migration of
    Apache Passwords restricted collections to FireRole roles.
    Please use it with care."""
    out = ""
    if roles:
        out += "<p>Here's a list of administrative roles you may have " \
        "received authorization to, via an Apache password. If you are aware " \
        "of such a password, please follow the corresponding link."
        out += "<table>"
        for name, description in roles:
            out += "<tr>"
            out += "<td><a href='%s'>%s</a></td><td> - <em>%s</em></td>" % \
            ('%s%s' % (sweburl, make_canonical_urlargd({'realm' : name, 'referer' : referer}, {})), name, description)
            out += "</tr>"
        out += "</table>"
        out += "</p>"
    return out

def make_apache_message(name_action, arguments, referer=None):
    """Given an action name and a dictionary of arguments and a refere url
    it returns a a nice string for presenting urls that let the user login
    with Apache password through Firerole authorized roles.
    This function is needed only at CERN for aiding in the migration of
    Apache Passwords restricted collections to FireRole roles.
    Please use it with care."""
    if not referer:
        referer = '%s/youraccount/youradminactivities' % sweburl
    roles = make_list_apache_firerole(name_action, arguments)
    if roles:
        return _format_list_of_apache_firerole(roles, referer)
    else:
        return ""

## access controle engine function
def acc_authorize_action(req, name_action, verbose=0, check_only_uid_p=False, **arguments):
    """Check if user is allowed to perform action
    with given list of arguments.
    Return (0, message) if authentication succeeds, (error code, error message) if it fails.

    The arguments are as follows:

          req - could be either one of these three things:
                id_user of the current user
                user_info dictionary built against the user details
                req mod_python request object

      name_action - the name of the action

        arguments - dictionary with keyword=value pairs created automatically
                    by python on the extra arguments. these depend on the
                    given action.

check_only_uid_p - hidden parameter needed to only check against uids without
                    looking at role definitions
    """

    #TASK -1: Checking external source if user is authorized:
    #if CFG_:
    #    em_pw = run_sql("SELECT email, FROM user WHERE id=%s", (id_user,))
    #    if em_pw:
    #        if not CFG_EXTERNAL_ACCESS_CONTROL.loginUser(em_pw[0][0], em_pw[0][1]):
    #            return (10, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[10], (called_from and CFG_WEBACCESS_MSGS[1] or "")))
    # TASK 0: find id and allowedkeywords of action

    user_info = {}
    if check_only_uid_p:
        id_user = req
    else:
        if type(req) in [type(1), type(1L)]: # req is id_user
            id_user = req
            user_info = webuser.collect_user_info(id_user)
        elif type(req) == type({}): # req is user_info
            user_info = req
            if user_info.has_key('uid'):
                id_user = user_info['uid']
            else:
                return (4, CFG_WEBACCESS_WARNING_MSGS[4])
        else: # req is req
            user_info = webuser.collect_user_info(req)
            if user_info.has_key('uid'):
                id_user = user_info['uid']
            else:
                return (4, CFG_WEBACCESS_WARNING_MSGS[4])
        # Check if just the userid is enough to execute this action
        (auth_code, auth_message) = acc_authorize_action(id_user, name_action, verbose, check_only_uid_p=True, **arguments)
        if auth_code == 0:
            return (auth_code, auth_message)

    if verbose: print 'task 0 - get action info'
    query1 = """select a.id, a.allowedkeywords, a.optional
                from accACTION a
                where a.name = '%s'""" % (name_action)

    try:
        id_action, aallowedkeywords, optional = run_sql_cached(query1, affected_tables=['accACTION'])[0]
    except (ProgrammingError, IndexError):
        return (3, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[3] % name_action, (called_from and CFG_WEBACCESS_MSGS[1] or "")))

    defkeys = aallowedkeywords.split(',')
    for key in arguments.keys():
        if key not in defkeys:
            if user_info.has_key('uri'):
                return (8, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[8], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""))) #incorrect arguments?
            else:
                return (8, "%s" % (CFG_WEBACCESS_WARNING_MSGS[8]))
    # -------------------------------------------


    # TASK 1: check if user is a superadmin
    # we know the action exists. no connection with role is necessary
    # passed arguments must have allowed keywords
    # no check to see if the argument exists
    if verbose: print 'task 1 - is user %s' % (SUPERADMINROLE, )

    if check_only_uid_p:
        if run_sql_cached("""SELECT *
                FROM accROLE r LEFT JOIN user_accROLE ur
                ON r.id = ur.id_accROLE
                WHERE r.name = '%s' AND
                ur.id_user = '%s' AND ur.expiration>=NOW()""" % (SUPERADMINROLE, id_user), affected_tables=['accROLE', 'user_accROLE']):
            return (0, CFG_WEBACCESS_WARNING_MSGS[0])
    else:
        if access_control_firerole.acc_firerole_check_user(user_info, access_control_firerole.load_role_definition(aca.acc_get_role_id(SUPERADMINROLE))):
            return (0, CFG_WEBACCESS_WARNING_MSGS[0])


    # TASK 2: check if user exists and find all the user's roles and create or-string
    if verbose: print 'task 2 - find user and userroles'

    try:
        query2 = """SELECT email, note from user where id=%s""" % id_user
        res2 = run_sql_cached(query2, affected_tables=['user'])
        if check_only_uid_p:
            if not res2:
                raise Exception
        if res2:
            if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS >= 1 and res2[0][1] not in [1, "1"]:
                if res2[0][0]:
                    if user_info.has_key('uri'):
                        return (9, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[9] % res2[0][0], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or "")))
                    else:
                        return (9, CFG_WEBACCESS_WARNING_MSGS[9] % res2[0][0])
                else:
                    raise Exception
        if check_only_uid_p:
            query2 = """SELECT ur.id_accROLE FROM user_accROLE ur WHERE ur.id_user=%s AND ur.expiration>=NOW() ORDER BY ur.id_accROLE """ % id_user
            res2 = run_sql_cached(query2, affected_tables=['user_accROLE'])
    except Exception:
        if user_info.has_key('uri'):
            return (6, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[6], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or "")))
        else:
            return (6, CFG_WEBACCESS_WARNING_MSGS[6])

    if check_only_uid_p:
        if not res2:
            if user_info.has_key('uri'):
                return (2, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[2], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""))) #user has no roles
            else:
                return (2, CFG_WEBACCESS_WARNING_MSGS[2])
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
            if check_only_uid_p:
                connection = run_sql_cached("""SELECT * FROM accROLE_accACTION_accARGUMENT
                        WHERE id_accROLE IN (%s) AND
                        id_accACTION = %s AND
                        argumentlistid = 0 AND
                        id_accARGUMENT = 0 """ % (str_roles, id_action), affected_tables=['accROLE_accACTION_accARGUMENT'])

                if connection and 1:
                    return (0, CFG_WEBACCESS_WARNING_MSGS[0])
                else:
                    if user_info.has_key('uri'):
                        return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or "")))
                    else:
                        return (1, "%s" % CFG_WEBACCESS_WARNING_MSGS[1])
            else:
                connection = run_sql_cached("""SELECT id_accROLE FROM
                        accROLE_accACTION_accARGUMENT
                        WHERE id_accACTION = %s AND
                        argumentlistid = 0 AND
                        id_accARGUMENT = 0 """ % id_action, affected_tables=['accROLE_accACTION_accARGUMENT'])

                for id_accROLE in connection:
                    if access_control_firerole.acc_firerole_check_user(user_info, access_control_firerole.load_role_definition(id_accROLE[0])):
                        return (0, CFG_WEBACCESS_WARNING_MSGS[0])

                if user_info.has_key('uri'):
                    return (1, "%s %s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""), make_apache_message(name_action, arguments, user_info.get('referer', None))))
                else:
                    return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], make_apache_message(name_action, arguments, user_info.get('referer', None))))

        # 3.2
        if optional == 'yes':
            if verbose: print ' - action with optional arguments'
            if check_only_uid_p:
                connection = run_sql_cached("""SELECT * FROM accROLE_accACTION_accARGUMENT
                        WHERE id_accROLE IN (%s) AND
                        id_accACTION = %s AND
                        id_accARGUMENT = -1 AND
                        argumentlistid = -1 """ % (str_roles, id_action), affected_tables=['accROLE_accACTION_accARGUMENT'])

                if connection and 1:
                    return (0, CFG_WEBACCESS_WARNING_MSGS[0])
                else:
                    if user_info.has_key('uri'):
                        return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or "")))
                    else:
                        return (1, CFG_WEBACCESS_WARNING_MSGS[1])
            else:
                connection = run_sql_cached("""SELECT id_accROLE FROM
                        accROLE_accACTION_accARGUMENT
                        WHERE id_accACTION = %s AND
                        id_accARGUMENT = -1 AND
                        argumentlistid = -1 """ % id_action, affected_tables=['accROLE_accACTION_accARGUMENT'])

                for id_accROLE in connection:
                    if access_control_firerole.acc_firerole_check_user(user_info, access_control_firerole.load_role_definition(id_accROLE[0])):
                        return (0, CFG_WEBACCESS_WARNING_MSGS[0])
                if user_info.has_key('uri'):
                    return (1, "%s %s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""), make_apache_message(name_action, arguments, user_info.get('referer', None))))
                else:
                    return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], make_apache_message(name_action, arguments, user_info.get('referer', None))))

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

    if check_only_uid_p:
        query4 = """SELECT DISTINCT raa.id_accROLE, raa.id_accACTION, raa.argumentlistid,
                raa.id_accARGUMENT, arg.keyword, arg.value
                FROM accROLE_accACTION_accARGUMENT raa, accARGUMENT arg
                WHERE raa.id_accACTION = %s AND
                raa.id_accROLE IN (%s) AND
                (%s) AND
                raa.id_accARGUMENT = arg.id """ % (id_action, str_roles, str_args)
    else:
        query4 = """SELECT DISTINCT raa.id_accROLE, raa.id_accACTION, raa.argumentlistid,
                raa.id_accARGUMENT, arg.keyword, arg.value, ar.firerole_def_ser
                FROM accROLE_accACTION_accARGUMENT raa INNER JOIN accROLE ar ON
                raa.id_accROLE = ar.id, accARGUMENT arg
                WHERE raa.id_accACTION = %s AND
                (%s) AND
                raa.id_accARGUMENT = arg.id """ % (id_action, str_args)

    try: res4 = run_sql_cached(query4, affected_tables=['accROLE_accACTION_accARGUMENT', 'accARGUMENT', 'accROLE'])
    except ProgrammingError:
        raise query4
        return (3, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[3] % id_action, (called_from and "%s" % (CFG_WEBACCESS_MSGS[1] or ""))))

    res5 = []
    if check_only_uid_p:
        if not res4:
            if user_info.has_key('uri'):
                return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""))) # no entries at all
            else:
                return (1, CFG_WEBACCESS_WARNING_MSGS[1])

        res5 = []
        for res in res4:
            res5.append(res)

    else:
        for row in res4:
            if access_control_firerole.acc_firerole_check_user(user_info, access_control_firerole.load_role_definition(row[0])):
                res5.append(row)
        if not res5:
            if user_info.has_key('uri'):
                return (1, "%s %s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or ""), make_apache_message(name_action, arguments, user_info.get('referer', None))))
            else:
                return (1, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[1], make_apache_message(name_action, arguments, user_info.get('referer', None))))

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
    if user_info.has_key('uri'):
        return (4, "%s %s" % (CFG_WEBACCESS_WARNING_MSGS[4], (called_from and "%s %s" % (CFG_WEBACCESS_MSGS[0] % quote(user_info['uri']), CFG_WEBACCESS_MSGS[1]) or "")))
    else:
        return (4, CFG_WEBACCESS_WARNING_MSGS[4])