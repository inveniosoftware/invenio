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
    import cgi
    import sys
    import time
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)
try:
    from access_control_engine import ace_authorize_action	
    from config import *
    from dbquery import run_sql
    from MySQLdb import ProgrammingError
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)


def ace_addAction(name_action, description, keyvalstr='', **allowedkeywordsdict):
    """function to create new entry in aceACTION for an action
    
        name_action     - name of the new action, must be unique
        
          keyvalstr     - string with allowed keywords
          
    allowedkeywordsdict - keyword=value pairs used to create a keyvalstr
    
    keyvalstr and allowedkeywordsdict can not be in use simultanously
    
    success -> return id_action, name_action, description and allowedkeywords
    failure -> return 0"""

    # users are not allowed to add value pairs both places
    if keyvalstr and allowedkeywordsdict:
        return 0

    # action with this name all ready exists, return 0
    if run_sql("""SELECT * FROM aceACTION WHERE name = '%s'""" % (name_action, )):
        return 0

    # action can be inserted
    else:
        # add keyword=value pairs to string with keywords
        for key in allowedkeywordsdict.keys():
            if keyvalstr: keyvalstr += '&'
            keyvalstr += '%s=%s' % (key, allowedkeywordsdict[key])

        # insert the new entry
        try: res = run_sql("""INSERT INTO aceACTION (name, description, allowedkeywords) VALUES ('%s', '%s', '%s')""" % (name_action, description, keyvalstr))
        except ProgrammingError: return 0
        
        if res: return res, name_action, description, keyvalstr

    return 0


def ace_deleteAction(id_action=0, name_action=0):
    """delete action in aceACTION according to id, or secondly name.
    entries in aceROLE_aceACTION_aceARGUMENT will also be removed.

      id_action - id of action to be deleted, prefered variable

    name_action - this is used if id_action is not given

    if the name or id is wrong, the function does nothing
    """

    # no id_action but name_action is given
    if not id_action and name_action:
         res = run_sql("""SELECT id FROM aceACTION WHERE name = '%s'""" % (name_action, ))
         if res: id_action = res[0][0]

    # try to delete action according to id
    if id_action:
        try:
            # delete the action
            if run_sql("""DELETE FROM aceACTION WHERE id = %s """ % (id_action, )):
                # delete all entries in aceROLE_aceACTION_aceARGUMENT
                run_sql("""DELETE FROM aceROLE_aceACTION_aceARGUMENT WHERE id_aceACTION = %s """ % (id_action, ))
                return 1
            # this action does not exist
            else:
                return 0
        except ProgrammingError:
            return 0
    
    # no actionid to test on
    else:
        return 0


def ace_addRole(name_role, description):
    """add a new role to aceROLE in the database.

      name_role - name of the role, must be unique

    description - text to describe the role"""

    if run_sql("""SELECT * FROM aceROLE WHERE name = '%s'""" % (name_role, )):
        return 0
    else:
        res = run_sql("""INSERT INTO aceROLE (name, description) VALUES ('%s', '%s') """ % (name_role, description))
        if res: return res, name_role, description
        else: return 0


def ace_deleteRole(id_role=0, name_role=0):
    """ delete role entry in table aceROLE and all references from other tables.
    
      id_role - id of role to be deleted, prefered variable
      
    name_role - this is used if id_role is not given """
    
    # no roleid, try to find it
    if not id_role and name_role:
        res = run_sql("""SELECT id FROM aceROLE WHERE name = '%s' """ % (name_role, ))
        if res:
            id_role = res[0][0]

    # try to delete the function according to id, if it succeds, the id is returned, if not 0 is returned
    if id_role and run_sql("""DELETE FROM aceROLE WHERE id = %s """ % (id_role, )):
        # delete everything from the two tables aceROLE_aceACTION_aceARGUMENT and user_aceROLE
        run_sql("""DELETE FROM aceROLE_aceACTION_aceARGUMENT WHERE id_aceROLE = %s""" % (id_role, ))
        run_sql("""DELETE FROM user_aceROLE WHERE id_aceROLE = %s """ % (id_role, ))
        return id_role

    # nothing was deleted
    return 0


def ace_addUserRole(id_user, id_role=0, name_role=0):
    """ this function adds a new entry to table user_aceROLE and returns it

      id_user - id of the user

      id_role - id of the role

    name_role - name of the role"""

    # roleid not given, try to find it, if success we know the role exists
    if not id_role and name_role:
        try: id_role = run_sql("""SELECT id FROM aceROLE WHERE name = '%s' """ % (name_role, ))[0][0]
        except IndexError: return 0
    
    # check if the id_role exists
    if id_role and not run_sql("""SELECT * FROM aceROLE WHERE id = %s """ % (id_role, )):
        return 0
    
    # check that the user actually exist
    if not run_sql("""SELECT * FROM user WHERE id = %s""" % (id_user, )):
        return 0

    # check if an identic entry exists, if not insert it...
    if not run_sql("""SELECT * FROM user_aceROLE WHERE id_user = %s AND id_aceROLE = %s""" % (id_user, id_role)):
        run_sql("""INSERT INTO user_aceROLE (id_user, id_aceROLE) VALUES (%s, %s) """ % (id_user, id_role))

    # it allready exists, and thats nice!
    return id_user, id_role



def ace_deleteUserRole(id_user, id_role=0, name_role=0):
    """ function deletes entry from user_aceROLE and reports the success. """

    if not id_role and name_role:
        try:
            id_role = run_sql("""SELECT id FROM aceROLE WHERE name = '%s' """ % (name_role, ))[0][0]
        except IndexError:
            return 0
    
    # number of deleted entries will be returned (0 or 1)
    return run_sql("""DELETE FROM user_aceROLE WHERE id_user = %s AND id_aceROLE = %s """ % (id_user, id_role))



def ace_addRoleActionArguments(id_role, id_action, arglistid=1, id_arguments=[]): # ids as list or tuple: , arglist=[], *id_arguments):
    """ function inserts entries in aceROLE_aceACTION_aceARGUMENT if all references are valid."""

    inserted = []

    # check that all the ids are valid and reference something...
    if not run_sql("""SELECT * FROM aceROLE WHERE id = %s""" % (id_role, )):
        return 0

    res_action = run_sql("""SELECT * FROM aceACTION WHERE id = %s""" % (id_action, ))
    if not res_action:
        return 0

    # find the allowedkeys
    allowedkeys = cgi.parse_qs(res_action[0][3]).keys()

    # check that the argument exists, and that it is a valid key
    for id_argument in id_arguments:
        res_arg = run_sql("""SELECT * FROM aceARGUMENT WHERE id = %s""" % (id_argument, ))
        if not res_arg or res_arg[0][1] not in allowedkeys:
            return 0

    # arglistid = -1 means that the user wants a new group
    if arglistid < 0:
        try:
            arglistid = run_sql("""SELECT MAX(argumentlistid) FROM aceROLE_aceACTION_aceARGUMENT WHERE id_aceROLE = %s AND id_aceACTION = %s """ %
                                (id_role, id_action))[0][0] + 1
        except ProgrammingError: return 0
        except (IndexError, TypeError): arglistid = 1
    
    if arglistid < 0: arglistid = 1

    # all references are valid, insert: one entry in raa for each argument
    for id_argument in id_arguments:
        if not run_sql("""SELECT * FROM aceROLE_aceACTION_aceARGUMENT WHERE id_aceROLE = %s AND id_aceACTION = %s AND id_aceARGUMENT = %s AND argumentlistid = %s""" %
                       (id_role, id_action, id_argument, arglistid)):
            run_sql("""INSERT INTO aceROLE_aceACTION_aceARGUMENT (id_aceROLE, id_aceACTION, id_aceARGUMENT, argumentlistid) VALUES (%s, %s, %s, %s) """
                    % (id_role, id_action, id_argument, arglistid))
            inserted.append((id_role, id_action, id_argument, arglistid)) 

    return inserted


def ace_addRoleActionArguments_names(name_role, name_action, arglistid=1, **keyval):
    """ this function makes it possible to pass names when creating new entries instead of ids.
    if everything is okay this function will use the one based on ids and return the result from that function.
    if role or action doesn't exist the result is returned as false,
    if one of the arguments doesn't exist it is simply created.
    if arglistid is 1 we add it to the big group, if arglistid is -1 a new group is created... """

    # find id of the role, return 0 if it doesn't exist
    id_role = run_sql("""SELECT id FROM aceROLE where name = '%s'""" % (name_role, ))
    if id_role: id_role = id_role[0][0]
    else: return 0

    # find id of the action, return 0 if it doesn't exist
    res = run_sql("""SELECT * from aceACTION where name = '%s'""" % (name_action, ))
    if res: id_action = res[0][0]
    else: return 0

    # place to keep ids of arguments and list of allowed keywords
    id_arguments = []
    allowedkeys = cgi.parse_qs(res[0][3])

    # find all the id_arguments and create those that does not exist
    for key in keyval.keys():
        # this key does not exist
        if key not in allowedkeys:
            return 0

        try: id_argument = run_sql("""SELECT id from aceARGUMENT WHERE keyword = '%s' and value = '%s'""" % (key, keyval[key]))[0][0]
        except IndexError: id_argument = run_sql("""INSERT INTO aceARGUMENT (keyword, value) values ('%s', '%s') """ % (key, keyval[key]))

        id_arguments.append(id_argument) # append the id to the list

    # use the other function
    return ace_addRoleActionArguments(id_role, id_action, arglistid, id_arguments)


def ace_deleteRoleActionArguments(id_role, id_action, arglistid=1, id_arguments=[]):# ids of arguments passed as list or tuple: arglist=[], *id_arguments):
    """ delete all entries in aceROLE_aceACTION_aceARGUMENT that satisfy the parameters.
    id_arguments is a list of arguments to delete.
    return number of deleted entries"""

    """
    if arglist:
        for id_argument in id_arguments: arglist.append(id_argument)
        id_arguments = arglist
    """
    
    # keep track of how may entries are deleted
    count = 0

    # run through list
    for id_argument in id_arguments:
        # delete entry
        count += run_sql("""DELETE FROM aceROLE_aceACTION_aceARGUMENT WHERE id_aceROLE = %s AND
                                                                   id_aceACTION = %s AND
                                                                   id_aceARGUMENT = %s AND
                                                                   argumentlistid = %s """
                         % (id_role, id_action, id_argument, arglistid))
    
    # return number of deleted entries
    return count


def ace_deleteRoleActionArguments_names(name_role, name_action, arglistid=1, **keyval):
    """ additional interface for the id based function.
    finds the ids and passes the task on.
    return 0 if the data is not valid. """

    # these will be passed on
    id_role = id_action = 0
    id_arguments = []

    # find id of the role
    res = run_sql("""SELECT id FROM aceROLE WHERE name = '%s' """ % (name_role, ))
    if res: id_role = res[0][0]
    else: return 0

    # find id of the action
    res = run_sql("""SELECT id FROM aceACTION WHERE name = '%s' """ % (name_action, ))
    if res: id_action = res[0][0]
    else: return 0

    # find the ids of all the arguments
    for key in keyval.keys():
        res = run_sql("""SELECT id FROM aceARGUMENT WHERE keyword = '%s' AND value = '%s' """ % (key, keyval[key]))
        if res: id_arguments.append(res[0][0])

    # no use passing the function call on if no arguments
    if not len(id_arguments): return 0

    # finish the task
    return ace_deleteRoleActionArguments(id_role, id_action, arglistid, id_arguments)


def ace_cleanupArguments():
    """ function deletes all aceARGUMENTs that are not referenced by aceROLE_aceACTION_aceARGUMENT.
    returns how many arguments where deleted and a list of the deleted id_arguments"""

    # variables to record the result
    count = 0
    ids = []

    # get list of all id_arguments!
    res = run_sql("""SELECT id from aceARGUMENT ORDER BY id ASC""")

    # traverse the list and check if each argument is referenced in aceROLE_aceACTION_aceARGUMENT
    for (id_argument, ) in res:
        # argument is not referenced, increase count and add id to ids list
        if not run_sql("""SELECT * FROM aceROLE_aceACTION_aceARGUMENT WHERE id_aceARGUMENT = %s limit 1""" % (id_argument, )):
            count += run_sql("""DELETE FROM aceARGUMENT where id = %s""" % (id_argument, ))
            ids.append(id_argument)

    # return how many arguments where deleted and the list of the arguments
    return (count, ids)
        

def ace_addArgument(keyword='', value=''):
    """ function to insert an argument into table aceARGUMENT.
    if it exists the old id is returned, if it does not the entry is created and the new id is returned. """
    
    # if one of the values are missing, return 0
    if not keyword or not value: return 0

    # try to return id of existing argument
    try: return run_sql("""SELECT id from aceARGUMENT where keyword = '%s' and value = '%s'""" % (keyword, value))[0][0]
    # return id of newly added argument
    except IndexError: return run_sql("""INSERT INTO aceARGUMENT (keyword, value) values ('%s', '%s') """ % (keyword, value))


def ace_deleteArgument(id_argument):
    """ functions deletes one entry in table aceARGUMENT.
    the success of the operation is returned. """

    # return number of deleted entries, 1 or 0
    return run_sql("""DELETE FROM aceARGUMENT WHERE id = %s """ % (id_argument, ))


def ace_deleteArgument_names(keyword='', value=''):
    """delete argument according to keyword and value,
    send call to another function..."""

    # one of the values is missing
    if not keyword or not value: return 0

    # find id of the entry
    try: return run_sql("""SELECT id from aceARGUMENT where keyword = '%s' and value = '%s'""" % (keyword, value))[0][0]
    except IndexError: return 0


def ace_getActionId(name_action):
    """get id of action when name is given

    name_action - name of the wanted action"""
    
    try: return run_sql("""SELECT id FROM aceACTION WHERE name = '%s'""" % (name_action, ))[0][0]
    except IndexError: return 0


def ace_getActionName(id_action):
    try:
        return run_sql("""SELECT name FROM aceACTION WHERE id = %s""" % (id_action, ))[0][0]
    except (ProgrammingError, IndexError):
        return ''


def ace_getActionKeywords(name_action):
    try:
        return cgi.parse_qs(run_sql("""SELECT allowedkeywords from aceACTION where name = '%s' """ % (name_action, ))[0][0]).keys()
    except IndexError:
        return []

def ace_getRoleId(rolename):
    try: return run_sql("""SELECT id FROM aceROLE WHERE name = '%s'""" % (rolename, ))[0][0]
    except IndexError: return 0


def ace_getArgumentId(keyword, value):
    try: return run_sql("""SELECT id FROM aceARGUMENT WHERE keyword = '%s' and value = '%s'""" % (keyword, value))[0][0]
    except IndexError: return 0


def ace_findUserInfoIds(id=0):
    query = """ SELECT ur.id_user, raa.*
                FROM aceROLE_aceACTION_aceARGUMENT raa, user_aceROLE ur
                WHERE ur.id_user = %s and
                      ur.id_aceROLE = raa.id_aceROLE limit 20 """ % (id, )

    res1 =  run_sql(query)

    res2 = []
    for res in res1: res2.append(res)
    res2.sort()

    return res2

def ace_findUserInfoNames(id_user=0):
    query = """ SELECT ur.id_user, r.name, ac.name, raa.argumentlistid, ar.keyword, ar.value
                FROM aceROLE_aceACTION_aceARGUMENT raa, user_aceROLE ur, aceROLE r, aceACTION ac, aceARGUMENT ar
                WHERE ur.id_user = %s and
                      ur.id_aceROLE = raa.id_aceROLE and
                      raa.id_aceROLE = r.id and
                      raa.id_aceACTION = ac.id and
                      raa.id_aceARGUMENT = ar.id
                      limit 20 """ % (id_user, )
    
    res1 =  run_sql(query)
    
    res2 = []
    for res in res1: res2.append(res)
    res2.sort()
    
    return res2

def ace_findUserRoleActions(id_user=0):
    query = """ SELECT DISTINCT r.name, a.name
                FROM user_aceROLE ur, aceROLE_aceACTION_aceARGUMENT raa, aceACTION a, aceROLE r
                WHERE ur.id_user = %s and
                      ur.id_aceROLE = raa.id_aceROLE and
                      raa.id_aceACTION = a.id and
                      raa.id_aceROLE = r.id
                      limit 20 """ % (id_user, )
    
    res1 = run_sql(query)
    
    res2 = []
    for res in res1: res2.append(res)
    res2.sort()
    
    return res2


# nice function, works perfectly?
# BETTER VERSION BELOW
def ace_findPossibleActions2(id_user, id_action):
    # query to find all entries for user and action
    query = """ SELECT raa.id_aceROLE, raa.argumentlistid, ar.keyword, ar.value
                FROM user_aceROLE ur, aceROLE_aceACTION_aceARGUMENT raa, aceARGUMENT ar
                WHERE ur.id_user = %s and
                      ur.id_aceROLE = raa.id_aceROLE and
                      raa.id_aceACTION = %s and
                      raa.id_aceARGUMENT = ar.id
                      limit 40 """ % (id_user, id_action)
    
    res1 = run_sql(query)
    
    # tuples into lists
    res2, roles= [], {}
    for res in res1:
        res2.append([])
        for r in res:
            res2[-1].append(r)
    res2.sort()
    
    # dictionary on roles
    for res in res2:
        rolekey = res[0]
        if rolekey not in roles.keys():
            roles[rolekey] = [res[1:]]
        else:
            roles[rolekey] = roles[rolekey] + [res[1:]]
    # dictionaries on arglistids
    roles2 = {}
    for r in roles.keys():
        roles2[r] = {}
        for (a, kw, value) in roles[r]:
            # create dictionary
            if not roles2[r].has_key(a):
                roles2[r][a] = {}
            # fill dictionary
            if not roles2[r][a].has_key(kw):
                roles2[r][a][kw] = [value]
            elif not value in roles2[r][a][kw]:
                roles2[r][a][kw] = roles2[r][a][kw] + [value]
    
    # find needed keywords, create header
    keywords = run_sql(""" SELECT allowedkeywords FROM aceACTION WHERE id = %s""" % (id_action, ))
    keywords = cgi.parse_qs(keywords[0][0]).keys()
    keywords.sort()
    res3 = []
    
    # fill list with all possible combinations
    # rolekeys = roles2.keys();    rolekeys.sort()
    for r in roles2.keys(): # roles
        for a in roles2[r].keys(): # argumentlistids
            # fill a list with the new entries, shortcut and copying first keyword list
            next_list = []
            for row in roles2[r][a][keywords[0]]: next_list.append([r, a, row[:] ])
            # run through the rest of the keywords
            for kw in keywords[1:]:
                if kw not in roles2[r][a].keys():
                    roles2[r][a][kw] = ['']
                    # return roles2[r][a][kw][:]
                
                new_list = roles2[r][a][kw][:]
                new_len  = len(new_list)
                # duplicate the list
                temp_list = []
                for row in next_list:
                    for i in range(new_len):
                        temp_list.append(row[:])
                # append new values
                for i in range(len(temp_list)):
                    new_item = new_list[i % new_len][:]
                    temp_list[i].append(  new_item  )
                next_list = temp_list[:]
            
            res3.extend(next_list)
    
    res3.sort()
    
    if res3:
        header = ['role', 'arglistid']
        for keyword in keywords: header.append(keyword)
        
        res3.insert(0, header)
    
    return res3

# nice function, works perfectly?
# THIS IS THE BEST VERSION

def ace_findPossibleActions(id_user, id_action):
    # query to find all entries for user and action
    query = """ SELECT raa.id_aceROLE, raa.argumentlistid, ar.keyword, ar.value
                FROM user_aceROLE ur, aceROLE_aceACTION_aceARGUMENT raa, aceARGUMENT ar
                WHERE ur.id_user = %s and
                      ur.id_aceROLE = raa.id_aceROLE and                
                      raa.id_aceACTION = %s and
                      raa.id_aceARGUMENT = ar.id
                      limit 40 """ % (id_user, id_action)
    
    res1 = run_sql(query)
    
    # tuples into lists
    res2, roles= [], {}
    for res in res1:
        res2.append([])
        for r in res: res2[-1].append(r)
    res2.sort()
    
    # find needed keywords, create header
    keywords = run_sql(""" SELECT allowedkeywords FROM aceACTION WHERE id = %s""" % (id_action, ))
    keywords = cgi.parse_qs(keywords[0][0]).keys()
    keywords.sort()
    res3 = []
    
    # create multilevel dictionary
    for res in res2:
        r, a, kw, value = res # rolekey, argumentlistid, keyword, value
        if kw not in keywords: continue
        if not roles.has_key(r):
            roles[r] = {}
        # create argumentlistid dictionary
        if not roles[r].has_key(a):        roles[r][a] = {}
        # fill dictionary
        if not roles[r][a].has_key(kw):    roles[r][a][kw] = [value]
        elif not value in roles[r][a][kw]: roles[r][a][kw] = roles[r][a][kw] + [value]
    
    # fill list with all possible combinations
    # rolekeys = roles2.keys();    rolekeys.sort()
    for r in roles.keys(): # roles
        for a in roles[r].keys(): # argumentlistids
            # fill a list with the new entries, shortcut and copying first keyword list
            next_list = []
            for row in roles[r][a][keywords[0]]: next_list.append([r, a, row[:] ])
            # run through the rest of the keywords
            for kw in keywords[1:]:
                if not roles[r][a].has_key(kw): roles[r][a][kw] = ['-']
                
                new_list = roles[r][a][kw][:]
                new_len  = len(new_list)
                # duplicate the list
                temp_list = []
                for row in next_list:
                    for i in range(new_len): temp_list.append(row[:])
                # append new values
                for i in range(len(temp_list)):
                    new_item = new_list[i % new_len][:]
                    temp_list[i].append(  new_item  )
                next_list = temp_list[:]
            
            res3.extend(next_list)
    
    res3.sort()
    
    if res3:
        header = ['role', 'arglistid']
        for keyword in keywords: header.append(keyword)
        res3.insert(0, header)
    
    return res3


def ace_findPossibleActions3(id_user, id_action):
    query = """ SELECT raa.id_aceROLE, raa.argumentlistid, ar.keyword, ar.value
                FROM user_aceROLE ur, aceROLE_aceACTION_aceARGUMENT raa, aceARGUMENT ar
                WHERE ur.id_user = %s and
                      ur.id_aceROLE = raa.id_aceROLE and
                      raa.id_aceACTION = %s and
                      raa.id_aceARGUMENT = ar.id
                      limit 50 """ % (id_user, id_action)
    
    res1 = run_sql(query)
    
    if not res1: return []
    
    allowedkeywords = cgi.parse_qs(run_sql("""SELECT allowedkeywords FROM aceACTION WHERE id = %s""" % (id_action, ))[0][0]).keys()
    
    res2 = []
    for res in res1:
        if res[2] in allowedkeywords: res2.append(res)
    res2.sort()
    
    return res2


def ace_splitArgumentGroup(id_role, id_action, arglistid):
    """
    find all arguments in arglistid
    split into all possible actions
    find max arglistid, increment lists from there
    delete group from table
    add new entries to table
    """

    # query to find all entries for user and action
    query = """ SELECT ar.keyword, ar.value, raa.id_aceARGUMENT
                FROM aceROLE_aceACTION_aceARGUMENT raa, aceARGUMENT ar
                WHERE raa.id_aceROLE = %s and                
                      raa.id_aceACTION = %s and
                      raa.argumentlistid = %s and
                      raa.id_aceARGUMENT = ar.id
                      limit 100 """ % (id_role, id_action, arglistid)

    q_del = """ DELETE FROM aceROLE_aceACTION_aceARGUMENT
                WHERE id_aceROLE = %s and                
                      id_aceACTION = %s and
                      argumentlistid = %s """ % (id_role, id_action, arglistid)

    res1 = run_sql(query)
    if not res1: return 0
    
    # find needed keywords, create header
    keywords = run_sql(""" SELECT allowedkeywords FROM aceACTION WHERE id = %s""" % (id_action, ))
    try: keywords = cgi.parse_qs(keywords[0][0]).keys()
    except IndexError: return 0
    
    keywords.sort()

    if not keywords: return 0
    
    res3, dict = [], {}

    for kw, val, id in res1:
        if kw not in keywords: continue
        try: dict[kw] = dict[kw] + [[val, id]]
        except KeyError: dict[kw] = [[val, id]]

    list = []
    for row in dict[keywords[0]]: list.append([row[:]])
    for kw in keywords[1:]:
        if not dict.has_key(kw): dict[kw] = ['-', -1]

        new_list = dict[kw][:]
        new_len  = len(new_list)
        temp_list = []
        for row in list:
            for i in range(new_len): temp_list.append(row[:])
        for i in range(len(temp_list)):
            new_item = new_list[i % new_len][:]
            temp_list[i].append( new_item )
        list = temp_list[:]

    # try:
    run_sql(q_del)
    # except ProgrammingError: return 0

    for r in list:
        argids = [r[0][1]]
        for item in r[1:]:
            argids.append(item[1])
            ace_addRoleActionArguments(id_role, id_action, -1, argids)

    return list


</protect>

