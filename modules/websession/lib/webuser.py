## $Id$
## CDSware User related utilities.

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

"""
This file implements all methods necessary for working with users and sessions in cdsware.
Contains methods for logging/registration when a user log/register into the system, checking if it
is a guest user or not.

At the same time this presents all the stuff it could need with sessions managements, working with websession.

It also contains Apache-related user authentication stuff.
"""

from dbquery import run_sql
import sys
import time
import os
import crypt
import string
import session
import websession
from websession import pSession, pSessionMapping
from session import SessionError
from config import *
from messages import *
from cdsware.access_control_engine import acc_authorize_action
from access_control_admin import acc_findUserRoleActions

def createGuestUser():
    """Create a guest user , insert into user null values in all fields 

       createGuestUser() -> GuestUserID
    """    
    return run_sql("insert into user (email) values ('')")

def getUid (req):
    """It gives the userId taking it from the cookie of the request,also has the control mechanism for the guest users,
       inserting in the MySql table when need it, and raise the cookie to the client.

       getUid(req) -> userId	 
    """
    sm = session.MPSessionManager(pSession, pSessionMapping())
    try:
	s = sm.get_session(req)
    except SessionError,e:
	sm.revoke_session_cookie (req)
	s = sm.get_session(req)
    userId = s.getUid()
    if userId == -1: # first time, so create a guest user
        s.setUid(createGuestUser())
    sm.maintain_session(req,s)
    return userId

def setUid(req,uid):
    """It sets the userId into the session, and raise the cookie to the client.
    """
    sm = session.MPSessionManager(pSession, pSessionMapping())
    try:
	s = sm.get_session(req)
    except SessionError,e:
	sm.revoke_session_cookie (req)
	s = sm.get_session(req)
    s.setUid(uid)
    sm.maintain_session(req,s)
    return uid
    
def isGuestUser(uid):
    """It Checks if the userId corresponds to a guestUser or not
      
       isGuestUser(uid) -> boolean
    """
    out = 1
    try:
        res = run_sql("select email from user where id=%s", (uid,))
        if res:
            if res[0][0]:
                out = 0
    except:
        pass
    return out

def isUserSubmitter(uid):
    u_email = get_email(uid)
    res = run_sql("select * from sbmSUBMISSIONS where email=%s",(u_email,))
    if len(res) > 0:
        return 1
    else:
        return 0

def isUserReferee(uid):
    res = run_sql("select sdocname from sbmDOCTYPE")
    for row in res:
        doctype = row[0]
        categ = "*"
        (auth_code, auth_message) = acc_authorize_action(uid, "referee",doctype=doctype, categ=categ)
        if auth_code == 0:
            return 1
        res2 = run_sql("select sname from sbmCATEGORIES where doctype=%s",(doctype,))
        for row2 in res2:
            categ = row2[0]
            (auth_code, auth_message) = acc_authorize_action(uid, "referee",doctype=doctype, categ=categ)
            if auth_code == 0:
                return 1
    return 0

def isUserAdmin(uid):
    "Return 1 if the user UID has some admin rights; 0 otherwise."
    out = 0
    if acc_findUserRoleActions(uid):
        out = 1
    return out    

def checkRegister(user,passw):
    """It checks if the user is register with the correct password
       
       checkRegister(user,passw) -> boolean
    """
    
    query_result = run_sql("select * from user where email=%s and password=%s", (user,passw))
    if len(query_result)> 0 :
        return 0
    return 1

def userOnSystem(user):
    """It checks if the user is registered already on the system
    """
    query_register = run_sql("select * from user where email=%s", (user,))
    if len(query_register)>0:
	return 1
    return 0
	
def checkemail(email):
    """Check whether the EMAIL address supplied by the user is valid.
       At the moment we just check whether it contains '@' and
       whether it doesn't contain blanks.
       
       checkemail(email) -> boolean
    """
    if (string.find(email, "@") <= 0) or (string.find(email, " ") > 0):
       return 0
    return 1

def getDataUid(req,uid):
    """It takes the email and password from a given userId, from the MySQL database, if don't exist it just returns
       guest values for email and password	
	
       getDataUid(req,uid) -> [email,password]

    """	

    email = 'guest'
    password = 'none'

    query_result = run_sql("select email, password from user where id=%s", (uid,))
    
    if len(query_result)>0:
        
        email = query_result[0][0]
        password = query_result[0][1]
        
    if password == None or  email =='':
        email = 'guest'
    list = [email] +[password]
    return list


def registerUser(req,user,passw):
    """It registers the user, inserting into the user table of MySQL database, the email and the pasword 
	of the user. It returns 1 if the insertion is done, 0 if there is any failure with the email 
	and -1 if the user is already on the data base
   
       registerUser(req,user,passw) -> int 
    """ 
    if userOnSystem(user) and  user !='':
	return -1	
    if checkRegister(user,passw) and checkemail(user):
	setUid(req, run_sql("INSERT INTO user (email, password) VALUES (%s,%s)",
                                (user,passw)))
	return 1
    return 0

def updateDataUser(req,uid,email,password):
    """It updates the data from the user. It is used when a user set his email and password
    """
    if email =='guest':
        return 0
    query_result = run_sql("update user set email=%s,password=%s where id=%s", (email,password,uid))
    
def loginUser(p_email,p_pw):
    """It is a first simple version for the authentication of user. It returns the id of the user, 
       for checking afterwards if the login is correct
    """
    query_result = run_sql("SELECT id from user where email=%s and password=%s", (p_email,p_pw))
    return query_result

def logoutUser(req):
    """It logout the user of the system, creating a guest user.
    """
    sm = session.MPSessionManager(pSession, pSessionMapping())
    try:
	s = sm.get_session(req)
    except SessionError,e:
	sm.revoke_session_cookie (req)
	s = sm.get_session(req)
    id1 = createGuestUser()
    s.setUid(id1)
    sm.maintain_session(req,s)
    return id1	

def userNotExist(p_email,p_pw):
    """Check if the user exits or not in the system
    """
    query_result = run_sql("select email from user where email=%s", (p_email,))
    if len(query_result)>0 and query_result[0]!='':
        return 0
    return 1

def update_Uid(req,p_email,p_pw):
    """It updates the userId of the session. It is used when a guest user is logged in succesfully in the system 
    with a given email and password
    """	
    query_ID = int(run_sql("select id from user where email=%s and password=%s",
                           (p_email,p_pw))[0][0])
    setUid(req,query_ID)
    return query_ID
	
def givePassword(email):
    """ It checks in the database the password for a given email. It is used to send the password to the email of the user.It returns 
	the password if the user exists, otherwise it returns -999
    """
    query_pass = run_sql("select password from user where email =%s",(email,))
    if len(query_pass)>0:
	return query_pass[0][0]
    return -999

def get_email(uid):
    """Return email address of the user uid.  Return string 'guest' in case
    the user is not found."""
    out = "guest"
    res = run_sql("SELECT email FROM user WHERE id=%s", (uid,), 1)
    if res and res[0][0]: 
        out = res[0][0]
    return out

def create_userinfobox_body(uid, language="en"):
    """Create user info box body for user UID in language LANGUAGE.""" 
    out = ""
    if isGuestUser(uid):
        out += """%s ::
	       <a class="userinfo" href="%s/youraccount.py/display?ln=%s">%s</a> ::
               <a class="userinfo" href="%s/youralerts.py/list?ln=%s">%s</a> ::
               <a class="userinfo" href="%s/yourbaskets.py/display?ln=%s">%s</a> ::
               <a class="userinfo" href="%s/youraccount.py/login?ln=%s">%s</a>""" % \
               (msg_guest[language], weburl, language, msg_session[language], weburl, language, msg_alerts[language],
                weburl, language, msg_baskets[language], weburl, language, msg_login[language])
    else:
        out += """%s ::
	       <a class="userinfo" href="%s/youraccount.py/display?ln=%s">%s</a> ::
               <a class="userinfo" href="%s/youralerts.py/list?ln=%s">%s</a> ::
               <a class="userinfo" href="%s/yourbaskets.py/display?ln=%s">%s</a> :: """ % \
               (get_email(uid), weburl, language, msg_account[language], weburl, language, msg_alerts[language],
                weburl, language, msg_baskets[language])
        if isUserSubmitter(uid):
            out += """<a class="userinfo" href="%s/yoursubmissions.py?ln=%s">%s</a> :: """ % \
                   (weburl, language, msg_submissions[language])            
        if isUserReferee(uid):
            out += """<a class="userinfo" href="%s/yourapprovals.py?ln=%s">%s</a> :: """ % \
                   (weburl, language, msg_approvals[language])
        if isUserAdmin(uid):
            out += """<a class="userinfo" href="%s/youraccount.py/youradminactivities?ln=%s">%s</a> :: """ % \
                   (weburl, language, msg_administration[language])
        out += """<a class="userinfo" href="%s/youraccount.py/logout?ln=%s">%s</a>""" % \
               (weburl, language, msg_logout[language])
    return """<img src="%s/img/head.gif" border="0"> %s""" % (weburl, out) 

def list_registered_users():
    """List all registered users."""    
    return run_sql("SELECT id,email FROM user where email!=''")

## --- follow some functions for Apache user/group authentication

def auth_apache_user_p(user, password):
    """Check whether user-supplied credentials correspond to valid
    Apache password data file.  Return 0 in case of failure, 1 in case
    of success."""    
    try:
        pipe_input, pipe_output = os.popen2(["/bin/grep", "^" + user + ":", cfg_apache_password_file], 'r')
        line =  pipe_output.readlines()[0]
        password_apache = string.split(string.strip(line),":")[1]
    except: # no pw found, so return not-allowed status	
        return 0	
    salt = password_apache[:2]
    if crypt.crypt(password, salt) == password_apache:
        return 1
    else:
        return 0

def auth_apache_user_in_groups(user):
    """Return list of Apache groups to which Apache user belong."""
    out = []
    try:        
        pipe_input,pipe_output = os.popen2(["/bin/grep", user, cfg_apache_group_file], 'r')
        for line in pipe_output.readlines():
            out.append(string.split(string.strip(line),":")[0])
    except: # no groups found, so return empty list
        pass
    return out

def auth_apache_user_collection_p(user, password, coll):
    """Check whether user-supplied credentials correspond to valid
    Apache password data file, and whether this user is authorized to
    see the given collections.  Return 0 in case of failure, 1 in case
    of success."""    
    from search_engine import coll_restricted_p, coll_restricted_group
    if not auth_apache_user_p(user, password):
        return 0
    if not coll_restricted_p(coll):
        return 1
    if coll_restricted_group(coll) in auth_apache_user_in_groups(user):
        return 1
    else:
        return 0
    
