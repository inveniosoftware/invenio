## $Id$
## CDSware Access Control Engine in mod_python.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

"""CDSware Access Control Engine in mod_python."""

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"


# check this: def ace_addUserRole(id_user, id_role=0, name_role=0):

## import interesting modules:
try:
    from ace_extrafunctions import * 
    import cgi
    import sys
    import time
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)

try:
    from config import *
    from dbquery import run_sql
    from MySQLdb import ProgrammingError
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)


def ace_authorize_action(id_user, name_action, **arguments):
    """ Check if user is allowed to perform action
    with given list of arguments.
    Return 1 if authentication succeeds, 0 if it fails.

    The arguments are as follows:
    
          id_user - currently the id of the user in the cdsdev database
      
      name_action - the name of the action
      
        arguments - dictionary with keyword=value pairs created automatically
                    by python on the extra arguments. these depend on the
                    given action.
    """
    
    # TASK 1: find id of action (and other data: name, allowedkeywords)

    query1 = """select a.id, a.allowedkeywords
                from aceACTION a
                where a.name = '%s'""" % (name_action)

    try: aid, aallowedkeywords = run_sql(query1)[0]
    except (ProgrammingError, IndexError): return 0
    # -------------------------------------------
    
    
    # TASK 2: find all the user's roles and create or-string
    
    query2 = """select ur.id_aceROLE from user_aceROLE ur where ur.id_user = %s""" % (id_user)
    try: res2 = run_sql(query2)
    except ProgrammingError: return 0
    
    if not res2: return 0 #user has no roles
    # -------------------------------------------

    # create or-string with roles (add default value? roles='(raa.id_aceROLE='def' or ')
    str_roles = '('
    for (role,) in res2:
        str_roles += """raa.id_aceROLE = %s or """ % (role)
    str_roles = str_roles[:-4] + ')'

    # TASK 3: find list of keyword and values that satisfy part of the authentication and create or-string
        
    # create dictionary with default values and replace entries from input arguments
    defdict = cgi.parse_qs(aallowedkeywords)
    defkeys = defdict.keys()

    for key in defkeys: defdict[key] = defdict[key][0]
    
    for key in arguments.keys():
        try: defdict[key] = arguments[key]
        except KeyError: return 0
    
    # create or-string with arguments
    str_args  = 'and ('

    for key in defkeys:
        str_args = """%s(arg.keyword = '%s' and arg.value = '%s') or """ % (str_args, key, defdict[key])
    
    str_args = str_args[:-4] + ')'
    if len(str_args) < 8: str_args = ''


    # TASK 4: create querystring for for roles, action and keyword=value pairs

    query4 = """select raa.id_aceROLE, raa.id_aceACTION, raa.argumentlistid,
                raa.id_aceARGUMENT, arg.keyword, arg.value
                from aceROLE_aceACTION_aceARGUMENT raa, aceARGUMENT arg
                where raa.id_aceACTION = %s and
                %s
                %s and
                raa.id_aceARGUMENT = arg.id  """ % (aid, str_roles, str_args)                
    
    try: res4 = run_sql(query4)
    except ProgrammingError: return 0

    if not res4: return 0
    
    res5 = []
    for res in res4:
        res5.append(res)
    res5.sort()

    # USER AUTHENTICATED TO PERFORM ACTION WITH ONE ARGUMENT
    if len(defdict) == 1: return 1

    # check with more than one argument: 


    # TASK 5: run through the result and try to satisfy authentication

    cur_role = cur_action = cur_arglistid = 0
    
    booldict = {}
    for key in defkeys: booldict[key] = 0

    # run through the results

    for (role, action, arglistid, arg, keyword, val) in res5 + [(-1, -1, -1, -1, -1, -1)]:
        # not the same role or argumentlist, i.e. check if thing are satisfied
        if cur_arglistid != arglistid or cur_role != role or cur_action != action:

            # test if all keywords are satisfied
            for value in booldict.values():
                if not value: break
            else: return 1 # USER AUTHENTICATED TO PERFORM ACTION

            # assign the values for the current tuple from the query
            cur_arglistid, cur_role, cur_action = arglistid, role, action

            for key in booldict.keys():
                booldict[key] = 0

        # set keyword qualified for the action, (whatever result of the test)
        booldict[keyword] = 1

    # authentication failed
    return 0

</protect>

