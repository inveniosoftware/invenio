## $Id$
## CDSware Web Session utilities, implementing persistence.

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
Classes necessary for using in CDSware, as a complement of session, which adds persistence to sessions
by using a MySQL table. Consists of the following classes:

	- SessionNotInDb: Exception to be raised when a session doesn't exit
	- pSession(Session): Specialisation of the class Session which adds persistence to session
	- pSessionMapping: Implements only the necessary methods to make it work with the session manager 
"""
import cPickle
import time
from dbquery import run_sql
import session
from session import Session
from UserDict import UserDict

class SessionNotInDb(Exception):
    """Exception to be raised when a requested session doesn't exist in the DB
    """
    pass


class pSession(Session):
    """Specialisation of the class Session which adds persistence to sessions 
        by using a MySQL table (it pickles itself into the corresponding row of 
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
    __ExpireTime = 1050043127
    
    def __init__( self, request, id, uid=-1 ):
        Session.__init__( self, request, id )
        self.__uid = uid
        self.__dirty = 0

    def is_dirty( self ):
        return self.__dirty

    def getUid( self ):
        return self.__uid

    def setUid( self, newUid ):
        self.__uid = int(newUid)
        self.__dirty = 1    

    def retrieve( cls, sessionId ):
        """method for retrieving a session from the DB for the given id. If the
             id has no corresponding session an exception is raised
        """
        sql = "select session_object from %s where session_key='%s'"%(cls.__tableName, sessionId)
        res = run_sql(sql)
        if len(res)==0:
            raise SessionNotInDb("Session %s doesn't exist"%sessionId)
        s = cPickle.loads( res[0][0] )
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
      
        repr = self.__getRepr().replace("'", "\\\'")
        repr = repr.replace('"', '\\\"')
        try:
            sql = 'insert into %s (session_key, session_object, uid) values ("%s","%s",%s)'\
                  % (self.__class__.__tableName, self.id, repr, int(self.getUid()))
            res = run_sql(sql)
        #TODO. WARNING!! it should be "except IntegrityError, e:" but this will 
        #   create a dependency on package MySQL. I'll leave it like this for
        #   the time being but this can lead to Exception masking
        except Exception, e:
            sql = 'update %s set uid=%s, session_object="%s" where session_key="%s"'%(self.__class__.__tableName, int(self.getUid()), repr, self.id)
            res = run_sql(sql)
            self.__dirty=0

    def _set_access_time (self, resolution):
        now = time.time()
        if now - self._Session__access_time > resolution:
            self._Session__access_time = now
            run_sql("UPDATE session SET session_expiry=%d WHERE session_key='%s'" % (now+60*60*24*2, self.id))

class pSessionMapping(UserDict):
    """Only the necessary methods to make it work with the session manager 
        have been implemented.
    """
    
    def __includeItemFromDB(self, key):
        if  key not in self.data.keys():
            try:
                s = pSession.retrieve( key )
                self.data[key] = s
            except SessionNotInDb, e:
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

