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

"""
Classes necessary for using in CDS Invenio, as a complement of
session, which adds persistence to sessions by using a MySQL
table. Consists of the following classes:

 - SessionNotInDb: Exception to be raised when a session doesn't exit

 - pSession(Session): Specialisation of the class Session which adds
   persistence to session

 - pSessionMapping: Implements only the necessary methods to make it
   work with the session manager
"""

__revision__ = "$Id$"

import cPickle
from UserDict import UserDict

from invenio.dbquery import run_sql, blob_to_string, \
     OperationalError, IntegrityError
from invenio.session import Session
from invenio.config import CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT, \
    CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER

class SessionNotInDb(Exception):
    """Exception to be raised when a requested session doesn't exist in the DB
    """
    pass

class pSession(Session):
    """Specialisation of the class Session which adds persistence to sessions
        by using a database table (it pickles itself into the corresponding row of
        the table). The class provides methods to save and retrieve an instance
        to/from the DB and to access the main session attributes (uid). The
        table in the DB must have the following structure:
            session_key - text - unique
            uid         - int
            session_object - blob
       Attributes:
            __tableName -- (string) name of the table in the DB where the
                sessions are going to be stored
            __uid -- (int) user identifier who initiated the session
            __dirty -- (bool) flag indicating whether the session has been
                modified (and therefore needs to be saved back to the DB) or not
    """

    __tableName = "session"

    def __init__( self, request, id, uid=-1 ):
        Session.__init__( self, request, id )
        self.__uid = uid
        self.__dirty = 0
        self.__dirty_remember_me = 0
        self.__apache_user = None
        self.__remember_me = False

    def is_dirty( self ):
        return self.__dirty

    def is_dirty_remember_me( self ):
        return self.__dirty_remember_me

    def getUid( self ):
        return self.__uid

    def getApacheUser( self ):
        return self.__apache_user

    def setUid( self, newUid ):
        if newUid:
            self.__uid = int(newUid)
            self.__dirty = 1
        else:
            # something bad happened, e.g. database down, so return user id -1
            self.__uid = -1
            self.__dirty = 1

    def setApacheUser( self, newApacheUser ):
        if newApacheUser:
            self.__apache_user = str(newApacheUser)
            self.__dirty = 1
        else:
            self.__apache_user = None
            self.__dirty = 1

    def setRememberMe( self, remember_me ):
        if remember_me != self.__remember_me:
            self.__dirty_remember_me = 1
            self.__remember_me = remember_me

    def getRememberMe( self ):
        return self.__remember_me

    def retrieve( cls, sessionId ):
        """method for retrieving a session from the DB for the given
           id. If the id has no corresponding session an exception is
           raised
        """
        sql = "select session_object from %s where session_key='%s'" % \
              (cls.__tableName, sessionId)
        try:
            res = run_sql(sql)
        except OperationalError:
            raise SessionNotInDb("Session %s doesn't exist" % \
                                 sessionId)
        if len(res)==0:
            raise SessionNotInDb("Session %s doesn't exist" % \
                                 sessionId)
        try:
            s = cPickle.loads(blob_to_string(res[0][0]))
            try: # For backward compatibility with old sessions
                s.__remember_me
            except AttributeError:
                s.__remember_me = False
                s.__dirty_remember_me = True
        except cPickle.UnpicklingError:
            raise SessionNotInDb("Session %s is broken" % \
                                 sessionId)
        return s
    retrieve = classmethod( retrieve )

    def __getRepr( self ):
        return cPickle.dumps( self )

    def save( self ):
        """method that tries to insert the session as NEW in the DB. If this
            fails (giving an integrity error) it means the session already
            exists there and it must be updated, so it performs the
            corresponding SQL update
        """

        sessrepr = self.__getRepr().replace("'", "\\\'")
        sessrepr = sessrepr.replace('"', '\\\"')
        if self.__remember_me:
            expiration_time = self.get_access_time()+86400*(CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER+1)
        else:
            expiration_time = self.get_access_time()+86400*(CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT+1)
        try:
            sql = """INSERT INTO %s
                     (session_key, session_expiry, session_object, uid)
                     VALUES ("%s","%s","%s","%s")""" % \
                  (self.__class__.__tableName, self.id,
                   expiration_time, sessrepr,
                   int(self.getUid()))
            run_sql(sql)
        except IntegrityError:
            try:
                sql = """UPDATE %s SET uid=%s, session_expiry=%s,
                                       session_object="%s"
                                 WHERE session_key="%s" """ % \
                      (self.__class__.__tableName, int(self.getUid()),
                       expiration_time, sessrepr,
                       self.id)
                run_sql(sql)
            except OperationalError:
                pass
            self.__dirty = 0
        except OperationalError:
            self.__dirty = 0

class pSessionMapping(UserDict):
    """Only the necessary methods to make it work with the session manager
        have been implemented.
    """

    def __includeItemFromDB(self, key):
        if  key not in self.data.keys():
            try:
                s = pSession.retrieve( key )
                self.data[key] = s
            except SessionNotInDb:
                pass

    def __setitem__(self, key, v):
        """when a session is added or updated in the dictionary it means it
            must be updated within the DB
        """
        v.save()
        UserDict.__setitem__(self, key, v)

    def __getitem__(self, key):
        """in order not to have to load all the sessions in the dictionary
            (normally only a single session is needed on each web request) when
            a session is requested the object looks to see if it is in the
            dictionary (memory) and if not it tries to retrieve it from the
            DB, puts it in the dictionary and returns the requested item. If
            the session doesn't exist a normal KeyError exception is raised
        """
        self.__includeItemFromDB( key )
        return UserDict.__getitem__(self, key)

    def has_key(self, key):
        """same as for "__getitem__": it checks whether the session exist in the
            local dictionary or in the DB.
        """
        self.__includeItemFromDB( key )
        return UserDict.has_key( self, key )

