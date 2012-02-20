# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Session management adapted from mod_python Session class.

Just use L{get_session} to obtain a session object (with a dictionary
interface, which will let you store permanent information).
"""

from invenio.webinterface_handler_wsgi_utils import add_cookies, Cookie, get_cookie

import cPickle
import time
import random
import re
import sys
import os
if sys.hexversion < 0x2060000:
    from md5 import md5
else:
    from hashlib import md5

from invenio.dateutils import convert_datestruct_to_datetext
from invenio.dbquery import run_sql, blob_to_string
from invenio.config import CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER, \
    CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT, CFG_SITE_URL, CFG_SITE_SECURE_URL, \
    CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS
from invenio.websession_config import CFG_WEBSESSION_COOKIE_NAME, \
    CFG_WEBSESSION_ONE_DAY, CFG_WEBSESSION_CLEANUP_CHANCE, \
    CFG_WEBSESSION_ENABLE_LOCKING

CFG_FULL_HTTPS = CFG_SITE_URL.lower().startswith("https://")

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
    if sid is not None:
        req._session = InvenioSession(req, sid)
        return req._session
    if not hasattr(req, '_session'):
        req._session = InvenioSession(req, sid)
    return req._session

class InvenioSession(dict):
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
        self._created = 0
        self._accessed = 0
        self._timeout = 0
        self._locked = 0
        self._invalid = 0
        self._http_ip = None
        self._https_ip = None
        self.__need_https = False

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
            self._created = time.time()
            self._timeout = CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT * \
                CFG_WEBSESSION_ONE_DAY

        self._accessed = time.time()

        # need cleanup?
        if random.randint(1, CFG_WEBSESSION_CLEANUP_CHANCE) == 1:
            self.cleanup()

    def set_remember_me(self, remember_me=True):
        """
        Set/Unset the L{_remember_me} flag.

        @param remember_me: True if the session cookie should last one day or
            until the browser is closed.
        @type remember_me: bool
        """
        self._remember_me = remember_me
        if remember_me:
            self.set_timeout(CFG_WEBSESSION_EXPIRY_LIMIT_REMEMBER *
                CFG_WEBSESSION_ONE_DAY)
        else:
            self.set_timeout(CFG_WEBSESSION_EXPIRY_LIMIT_DEFAULT *
                CFG_WEBSESSION_ONE_DAY)
        add_cookies(self._req, self.make_cookies())

    def load(self):
        """
        Load the session from the database.
        @return: 1 in case of success, 0 otherwise.
        @rtype: integer
        """
        session_dict = None
        invalid = False
        res = run_sql("SELECT session_object FROM session "
                        "WHERE session_key=%s", (self._sid, ))
        if res:
            session_dict = cPickle.loads(blob_to_string(res[0][0]))
            remote_ip = self._req.remote_ip
            if self._req.is_https():
                if session_dict['_https_ip'] is not None and \
                        _mkip(session_dict['_https_ip']) >> \
                            CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS != \
                        _mkip(remote_ip) >> \
                            CFG_WEBSESSION_IPADDR_CHECK_SKIP_BITS:
                    invalid = True
                else:
                    session_dict['_https_ip'] = remote_ip
            else:
                if session_dict['_http_ip'] is not None and \
                        _mkip(session_dict['_http_ip']) >> \
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

        if (time.time() - session_dict["_accessed"]) > \
                session_dict["_timeout"]:
            return 0

        self._created  = session_dict["_created"]
        self._accessed = session_dict["_accessed"]
        self._timeout  = session_dict["_timeout"]
        self._remember_me = session_dict["_remember_me"]
        self.update(session_dict["_data"])
        return 1

    def save(self):
        """
        Save the session to the database.
        """
        if not self._invalid and self._sid:
            session_dict = {"_data" : self.copy(),
                    "_created" : self._created,
                    "_accessed": self._accessed,
                    "_timeout" : self._timeout,
                    "_http_ip" : self._http_ip,
                    "_https_ip" : self._https_ip,
                    "_remember_me" : self._remember_me
            }
            session_key = self._sid
            session_object = cPickle.dumps(session_dict, -1)
            session_expiry = time.time() + self._timeout + CFG_WEBSESSION_ONE_DAY
            session_expiry = convert_datestruct_to_datetext(time.gmtime(session_expiry))

            uid = self.get('uid', -1)
            run_sql("""
                INSERT session(
                    session_key,
                    session_expiry,
                    session_object,
                    uid
                ) VALUE(%s,
                    %s,
                    %s,
                    %s
                ) ON DUPLICATE KEY UPDATE
                    session_expiry=%s,
                    session_object=%s,
                    uid=%s
            """, (session_key, session_expiry, session_object, uid,
                session_expiry, session_object, uid))
            add_cookies(self._req, self.make_cookies())

    def delete(self):
        """
        Delete the session.
        """
        run_sql("DELETE FROM session WHERE session_key=%s", (self._sid, ))
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
        uid = self.get('uid', -1)
        if uid > 0 and CFG_SITE_SECURE_URL.startswith("https://"):
            stub_cookie = Cookie(CFG_WEBSESSION_COOKIE_NAME + 'stub', 'HTTPS')
        else:
            stub_cookie = Cookie(CFG_WEBSESSION_COOKIE_NAME + 'stub', 'NO')
        cookies.append(stub_cookie)
        if self._req.is_https() or not CFG_SITE_SECURE_URL.startswith("https://") or uid <= 0:
            cookie = Cookie(CFG_WEBSESSION_COOKIE_NAME, self._sid)
            if CFG_SITE_SECURE_URL.startswith("https://") and uid > 0:
                cookie.secure = True
                cookie.httponly = True
            cookies.append(cookie)
        for cookie in cookies:
            cookie.path = '/'
            if self._remember_me:
                cookie.expires = time.time() + self._timeout

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

    def created(self):
        """
        @return: the UNIX timestamp for when the session has been created.
        @rtype: double
        """
        return self._created

    def last_accessed(self):
        """
        @return: the UNIX timestamp for when the session has been last
            accessed.
        @rtype: double
        """
        return self._accessed

    def timeout(self):
        """
        @return: the number of seconds from the last accessed timestamp,
            after which the session is invalid.
        @rtype: double
        """
        return self._timeout

    def set_timeout(self, secs):
        """
        Set the number of seconds from the last accessed timestamp,
            after which the session is invalid.
        @param secs: the number of seconds.
        @type secs: double
        """
        self._timeout = secs

    def cleanup(self):
        """
        Perform the database session cleanup.
        """
        def session_cleanup():
            """
            Session cleanup procedure which to be executed at the end
            of the request handling.
            """
            run_sql("""
                DELETE FROM session
                WHERE session_expiry<=UTC_TIMESTAMP()
            """)
        self._req.register_cleanup(session_cleanup)
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

def _init_rnd():
    """
    Initialize random number generators.
    This is key in multithreaded env, see Python docs for random.
    @return: the generators.
    @rtype: list of generators
    """

    # query max number of threads
    gennum = 10

    # make generators
    # this bit is from Python lib reference
    random_generator = random.Random(time.time())
    result = [random_generator]
    for dummy in range(gennum - 1):
        laststate = random_generator.getstate()
        random_generator = random.Random()
        random_generator.setstate(laststate)
        random_generator.jumpahead(1000000)
        result.append(random_generator)

    return result

_RANDOM_GENERATORS = _init_rnd()
_RANDOM_ITERATOR = iter(_RANDOM_GENERATORS)

def _get_generator():
    """
    get rnd_iter.next(), or start over
    if we reached the end of it
    @return: the next random number.
    @rtype: double
    """
    global _RANDOM_ITERATOR
    try:
        return _RANDOM_ITERATOR.next()
    except StopIteration:
        # the small potential for two threads doing this
        # seems does not warrant use of a lock
        _RANDOM_ITERATOR = iter(_RANDOM_GENERATORS)
        return _RANDOM_ITERATOR.next()

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
    for i in map (int, ip.split ('.')):
        num = (num << 8) + i
    return num
