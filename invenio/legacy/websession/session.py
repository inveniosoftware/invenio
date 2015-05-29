# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

"""
Session management adapted from mod_python Session class.

Just use L{get_session} to obtain a session object (with a dictionary
interface, which will let you store permanent information).
"""

from invenio.legacy.wsgi.utils import add_cookies, Cookie, get_cookie

import random
import zlib
from six.moves import cPickle
import re
import sys
import os
import time
from datetime import datetime, timedelta
from uuid import uuid4

from invenio.utils.date import convert_datestruct_to_datetext
from invenio.legacy.dbquery import run_sql, blob_to_string
from invenio.config import (CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER,
                            CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT,
                            CFG_SITE_URL,
                            CFG_SITE_SECURE_URL,
                            CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS,
                            CFG_WEBSEARCH_PREV_NEXT_HIT_FOR_GUESTS,
                            CFG_WEBSESSION_STORAGE)
from invenio.legacy.websession.websession_config import (CFG_WEBSESSION_COOKIE_NAME,
                                      CFG_WEBSESSION_ONE_DAY,
                                      CFG_WEBSESSION_CLEANUP_CHANCE)
from invenio.ext.cache import cache
from invenio.utils.hash import md5


CFG_FULL_HTTPS = CFG_SITE_URL.lower().startswith("https://")

if CFG_WEBSEARCH_PREV_NEXT_HIT_FOR_GUESTS:
    _CFG_SESSION_NON_USEFUL_KEYS = ('uid', 'user_info')
else:
    _CFG_SESSION_NON_USEFUL_KEYS = ('uid', 'user_info', 'websearch-last-query', 'websearch-last-query-hits')

def get_session(req, sid=None):
    """
    Obtain a session.

    If the session has already been created for the current request,
    returns the already existing session.

    @param req: the mod_python request object.
    @type req: mod_python request object
    @param sid: the session identifier of an already existing session.
    @type sid: 32 hexadecimal string
    @return: the session.
    @rtype: InvenioSession
    @raise ValueError: if C{sid} is provided and it doesn't correspond to a
        valid session.
    """
    from flask import session
    if sid is not None:
        req._session = session
        return req._session
    if not hasattr(req, '_session'):
        req._session = session
    return req._session


class InvenioSessionBase(dict):
    """
    This class implements a Session handling based on MySQL.

    @param req: the mod_python request object.
    @type req: mod_python request object
    @param sid: the session identifier if already known
    @type sid: 32 hexadecimal string
    @ivar _remember_me: if the session cookie should last one day or until
        the browser is closed.
    @type _remember_me: bool

    @note: The code is heavily based on ModPython 3.3.1 DBMSession
        implementation.
    @note: This class implements IP verification to prevent basic cookie
        stealing.
    @raise ValueError: if C{sid} is provided and correspond to a broken
        session.
    """

    def __init__(self, req, sid=None):
        self._remember_me = False
        self._req, self._sid, self._secret = req, sid, None
        self._lock = CFG_WEBSESSION_ENABLE_LOCKING
        self._new = 1
        self._locked = 0
        self._invalid = 0
        self._dirty = False
        self._http_ip = None
        self._https_ip = None
        self.__need_https = False
        self._cleanup_function = None

        dict.__init__(self)

        if not self._sid:
            # check to see if cookie exists
            cookie = get_cookie(req, CFG_WEBSESSION_COOKIE_NAME)
            if cookie:
                self._sid = cookie.value
            else:
                stub_cookie = get_cookie(req, CFG_WEBSESSION_COOKIE_NAME + 'stub')
                self.__need_https = stub_cookie and stub_cookie.value == 'HTTPS'

        if self._sid:
            if not _check_sid(self._sid):
                if sid:
                    # Supplied explicitly by user of the class,
                    # raise an exception and make the user code
                    # deal with it.
                    raise ValueError("Invalid Session ID: sid=%s" % sid)
                else:
                    # Derived from the cookie sent by browser,
                    # wipe it out so it gets replaced with a
                    # correct value.
                    self._sid = None

        if self._sid:
            # attempt to load ourselves
            self.lock()
            if self.load():
                self._new = 0

        if self._new:
            # make a new session
            if self._sid:
                self.unlock() # unlock old sid
            self._sid = _new_sid(self._req)
            self.lock()                 # lock new sid
            remote_ip = self._req.remote_ip
            if self._req.is_https():
                self._https_ip = remote_ip
            else:
                self._http_ip = remote_ip

        # need cleanup?
        if random.randint(1, CFG_WEBSESSION_CLEANUP_CHANCE) == 1:
            self.cleanup()

    def get_dirty(self):
        """
        Is this session dirty?
        """
        return self._dirty

    def set_dirty(self, dummy=True):
        """
        Flag this session as dirty. It takes a parameter, just in order
        to be used within a property
        """
        self._dirty = True

    dirty = property(get_dirty, set_dirty)

    def __setitem__(self, key, value):
        if self.get(key) != value:
            dict.__setitem__(self, key, value)
            self._dirty = True

    def __delitem__(self, key):
        if key in self:
            dict.__delitem__(self, key)
            self._dirty = True

    def set_remember_me(self, remember_me=True):
        """
        Set/Unset the L{_remember_me} flag.

        @param remember_me: True if the session cookie should last one day or
            until the browser is closed.
        @type remember_me: bool
        """
        self._remember_me = remember_me
        self['_permanent'] = remember_me
        add_cookies(self._req, self.make_cookies())

    def load(self):
        """
        Load the session from the database.
        @return: 1 in case of success, 0 otherwise.
        @rtype: integer
        """
        session_dict = None
        invalid = False
        res = self.load_from_storage(self._sid)
        if res:
            session_dict = cPickle.loads(blob_to_string(res))
            remote_ip = self._req.remote_ip
            if self._req.is_https():
                if session_dict['_https_ip'] is not None:
                    if ':' in remote_ip:
                        ## IPV6 address, we don't skip bits
                        if session_dict['_https_ip'] != remote_ip:
                            invalid = True
                    else:
                        if _mkip(session_dict['_https_ip']) >> \
                                CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS != \
                            _mkip(remote_ip) >> \
                                CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS:
                            invalid = True
                else:
                    session_dict['_https_ip'] = remote_ip
            else:
                if session_dict['_http_ip'] is not None:
                    if ':' in remote_ip:
                        ## IPV6 address, we don't skip bits
                        if session_dict['_http_ip'] != remote_ip:
                            invalid = True
                    else:
                        if _mkip(session_dict['_http_ip']) >> \
                                CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS != \
                            _mkip(remote_ip) >> \
                                CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS:
                            invalid = True
                else:
                    session_dict['_http_ip'] = remote_ip

        if session_dict is None:
            return 0

        if invalid:
            return 0

        self.update(session_dict)
        self._remember_me = session_dict.get("_permanent", False)
        return 1

    def is_useful(self):
        """
        Return True if the session contains some key considered
        useful (i.e. that deserve being preserved)
        """
        for key in self:
            if key not in _CFG_SESSION_NON_USEFUL_KEYS:
                return True
        return False

    def save(self):
        """
        Save the session to the database.
        """
        uid = self.get('uid', -1)
        if not self._invalid and self._sid and self._dirty and (uid > 0 or self.is_useful()):
            ## We store something only for real users or useful sessions.
            session_dict = {"_data" : self.copy(),
                    "_created" : self._created,
                    "_accessed": self._accessed,
                    "_timeout" : self._timeout,
                    "_http_ip" : self._http_ip,
                    "_https_ip" : self._https_ip,
                    "_remember_me" : self._remember_me
            }
            session_object = cPickle.dumps(session_dict, -1)

            self.save_in_storage(self._sid,
                                 session_object,
                                 self._timeout,
                                 uid)

            for cookie in self.make_cookies():
                self._req.set_cookie(cookie)
        ## No more dirty :-)
        self._dirty = False

    def delete(self):
        """
        Delete the session.
        """
        self.delete_from_storage(self._sid)
        self.clear()

    def invalidate(self):
        """
        Declare the session as invalid.
        """
        cookies = self.make_cookies()
        for cookie in cookies:
            cookie.expires = 0
        add_cookies(self._req, cookies)
        self.delete()
        self._invalid = 1
        if hasattr(self._req, '_session'):
            delattr(self._req, '_session')

    def make_cookies(self):
        """
        Create the necessary cookies to implement secure session handling
        (possibly over HTTPS).

        @return: a list of cookies.
        """
        cookies = []
        uid = self.get('_uid', -1)
        if uid > 0 and CFG_SITE_SECURE_URL.startswith("https://"):
            stub_cookie = Cookie(CFG_WEBSESSION_COOKIE_NAME + 'stub', 'HTTPS', HttpOnly=True)
        else:
            stub_cookie = Cookie(CFG_WEBSESSION_COOKIE_NAME + 'stub', 'NO', HttpOnly=True)
        cookies.append(stub_cookie)
        if self._req.is_https() or not CFG_SITE_SECURE_URL.startswith("https://") or uid <= 0:
            cookie = Cookie(CFG_WEBSESSION_COOKIE_NAME, self._sid, HttpOnly=True)
            if CFG_SITE_SECURE_URL.startswith("https://") and uid > 0:
                cookie.secure = True
            cookies.append(cookie)
        for cookie in cookies:
            cookie.path = '/'
            if self._remember_me:
                cookie.expires = time.time() + CFG_WEBSESSION_ONE_DAY * CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER
                cookie.max_age = CFG_WEBSESSION_ONE_DAY * CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER
        return cookies


    def initial_http_ip(self):
        """
        @return: the initial ip addressed for the HTTP protocol for which this
        session was issued.
        @rtype: string
        @note: it returns None if this session has always been used through
            HTTPS requests.
        """
        return self._http_ip

    def initial_https_ip(self):
        """
        @return: the initial ip addressed for the HTTPS protocol for which this
        session was issued.
        @rtype: string
        @note: it returns None if this session has always been used through
            HTTP requests.
        """
        return self._https_ip

    def lock(self):
        """
        Lock the session.
        """
        if self._lock:
            self._locked = 1

    def unlock(self):
        """
        Unlock the session.
        """
        if self._lock and self._locked:
            self._locked = 0

    def is_new(self):
        """
        @return: True if the session has just been created.
        @rtype: bool
        """
        return not not self._new

    def sid(self):
        """
        @return: the session identifier.
        @rtype: 32 hexadecimal string
        """
        return self._sid

    def cleanup(self):
        """
        Perform the database session cleanup.
        """
        if self._cleanup_function:
            self._req.register_cleanup(self._cleanup_function)
        self._req.log_error("InvenioSession: registered database cleanup.")

    def __del__(self):
        self.save()
        self.unlock()

    def get_need_https(self):
        return self.__need_https

    ## This property will be True if the connection need to be set to HTTPS
    ## in order for the session to be successfully read. This can actually
    ## be checked by not having a cookie, but just having the stub_cookie.
    ## The default cookie is only sent via HTTPS, while the stub_cookie
    ## is also sent via HTTP and contains the uid, of the user. So if there
    ## is actually a stub cookie and its value is different than -1 this
    ## property will be True, meaning the server should redirect the client
    ## to an HTTPS connection if she really wants to access authenticated
    ## resources.
    need_https = property(get_need_https)

def _unlock_session_cleanup(session):
    """
    Auxliary function to unlock a session.
    """
    session.unlock()


_RE_VALIDATE_SID = re.compile('[0-9a-f]{32}$')
def _check_sid(sid):
    """
    Check the validity of the session identifier.
    The sid must be 32 characters long, and consisting of the characters
    0-9 and a-f.

    The sid may be passed in a cookie from the client and as such
    should not be trusted. This is particularly important in
    FileSession, where the session filename is derived from the sid.
    A sid containing '/' or '.' characters could result in a directory
    traversal attack

    @param sid: the session identifier.
    @type sid: string
    @return: True if the session identifier is valid.
    @rtype: bool
    """
    return not not _RE_VALIDATE_SID.match(sid)

def _new_sid(req):
    """
    Make a number based on current time, pid, remote ip
    and two random ints, then hash with md5. This should
    be fairly unique and very difficult to guess.

    @param req: the mod_python request object.
    @type req: mod_python request object.
    @return: the session identifier.
    @rtype: 32 hexadecimal string

    @warning: The current implementation of _new_sid returns an
        md5 hexdigest string. To avoid a possible directory traversal
        attack in FileSession the sid is validated using
        the _check_sid() method and the compiled regex
        validate_sid_re. The sid will be accepted only if len(sid) == 32
        and it only contains the characters 0-9 and a-f.

        If you change this implementation of _new_sid, make sure to also
        change the validation scheme, as well as the test_Session_illegal_sid()
        unit test in test/test.py.
    """
    return uuid4().hex

    the_time = long(time.time()*10000)
    pid = os.getpid()
    random_generator = _get_generator()
    rnd1 = random_generator.randint(0, 999999999)
    rnd2 = random_generator.randint(0, 999999999)
    remote_ip = req.remote_ip

    return md5("%d%d%d%d%s" % (
        the_time,
        pid,
        rnd1,
        rnd2,
        remote_ip)
    ).hexdigest()

def _mkip(ip):
    """
    Compute a numerical value for a dotted IP
    """
    num = 0L
    for i in ip.split('.'):
        num = (num << 8) + int(i)
    return num



class InvenioSessionMySQL(InvenioSessionBase):
    def __init__(self, req, sid=None):

        def cb_session_cleanup(data=None):
            """
            Session cleanup procedure which to be executed at the end
            of the request handling.
            """
            run_sql("""DELETE LOW_PRIORITY FROM session
                       WHERE session_expiry <= UTC_TIMESTAMP()""")

        self.cleanup_function = cb_session_cleanup
        super(InvenioSessionMySQL, self).__init__(req, sid)

    def load_from_storage(self, sid):
        ret = run_sql("""SELECT session_object FROM session
                         WHERE session_key = %s""", [sid])
        if ret:
            return ret[0][0]

    def delete_from_storage(self, sid):
        return run_sql("""DELETE LOW_PRIORITY FROM session
                          WHERE session_key=%s""", [sid])

    def save_in_storage(self, sid, session_object, timeout, uid):
        session_key = sid
        session_expiry = time.time() + timeout + CFG_WEBSESSION_ONE_DAY
        session_expiry = convert_datestruct_to_datetext(time.gmtime(session_expiry))

        run_sql("""INSERT INTO session(
                                    session_key,
                                    session_expiry,
                                    session_object,
                                    uid
                    ) VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                        session_expiry=%s,
                        session_object=%s,
                        uid=%s
        """, (session_key, session_expiry, session_object, uid,
            session_expiry, session_object, uid))


class InvenioSessionRedis(InvenioSessionBase):

    def generate_key(self, sid):
        return 'session_%s' % sid

    def load_from_storage(self, sid):
        return cache.get(self.generate_key(sid))

    def delete_from_storage(self, sid):
        return cache.delete(self.generate_key(sid))

    def save_in_storage(self, sid, session_object, timeout, uid):  # pylint: disable=W0613
        return cache.set(self.generate_key(sid), session_object,
                         timeout=timeout)

if CFG_WEBSESSION_STORAGE == 'mysql':
    InvenioSession = InvenioSessionMySQL
elif CFG_WEBSESSION_STORAGE == 'redis':
    InvenioSession = InvenioSessionRedis
