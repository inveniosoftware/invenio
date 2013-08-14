# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
Session management adapted from Flask Session class.

Just use L{get_session} to obtain a session object (with a dictionary
interface, which will let you store permanent information).
"""

import cPickle
import zlib

from datetime import timedelta, datetime
from uuid import uuid4
from werkzeug.datastructures import CallbackDict
from werkzeug.exceptions import BadRequest
from flask.sessions import SessionInterface, SessionMixin
from flask import g, current_app, request, get_flashed_messages, flash
from warnings import warn

from invenio.sqlalchemyutils import db
from invenio.websession_model import Session
from invenio.webuser_flask import current_user
from invenio.config import \
    CFG_SITE_SECURE_URL, \
    CFG_FLASK_CACHE_TYPE

__all__ = ["InvenioSession", "InvenioSessionInterface"]

CFG_SUPPORT_HTTPS = CFG_SITE_SECURE_URL.startswith("https://")

# Store session information in memory cache (Redis, Memcache, ...).
CFG_SESSION_IN_CACHE = CFG_FLASK_CACHE_TYPE not in [None, 'null']
# Session key prefix for storing in db.
CFG_CACHE_KEY_PREFIX_SESSION = 'session::'

from invenio.cache import cache

class InvenioSession(dict, SessionMixin):
    """
    This class implement a traditional Invenio session but compatible
    with the Flask session handler.
    """
    def __init__(self, initial=None, sid=None):
        if initial:
            dict.__init__(self, initial)
        SessionMixin.__init__(self)
        self.sid = sid
        self.logging_in = False

    def need_https(self):
        """
        Return True if the user was at some point authenticated and hence his
        session identifier need to be sent via HTTPS
        """
        return request.cookies.get(current_app.session_cookie_name + 'stub', 'NO') == 'HTTPS'

    def delete(self, clear=True):
        """
        Delete the session.
        """
        if clear:
            self.clear()

    def invalidate(self):
        """
        Declare the session as invalid.
        """
        self._invalid = 1

    def set_remember_me(self, remember_me=True):
        """
        Set/Unset the L{_remember_me} flag.

        @param remember_me: True if the session cookie should last one day or
            until the browser is closed.
        @type remember_me: bool
        """
        self._remember_me = remember_me
        self['_permanent'] = remember_me

    def check_ip(self, request):
        """
        Return True if the session is being used from the same IP address
        that was used to create it.
        """
        remote_ip = request.remote_addr

        if '_https_ip' not in self:
            self['_https_ip'] = remote_ip
        if '_http_ip' not in self:
            self['_http_ip'] = remote_ip

        if request.scheme == 'https':
            if self.get('_https_ip', remote_ip) != remote_ip:
                return False
            self['_https_ip'] = remote_ip
            if not self['_http_ip']:
                self['_http_ip'] = None
            return True
        else:
            if self.get('_http_ip', remote_ip) != remote_ip:
                return False
            self['_http_ip'] = remote_ip
            if not self['_https_ip']:
                self['_https_ip'] = None
            return True

    def _get_uid(self):
        return self.get('_uid', -1)

    def _set_uid(self, uid):
        if self.get('_uid') != uid:
            self.logging_in = True
        self['_uid'] = uid

    def _get_user_info(self):
        return current_user

    uid = property(_get_uid, _set_uid)
    user_info = property(_get_user_info)
    del _get_uid, _set_uid, _get_user_info


class InvenioSerializer(object):
    @staticmethod
    def loads(string):
        return cPickle.loads(zlib.decompress(string))

    @staticmethod
    def dumps(data):
        return zlib.compress(cPickle.dumps(data, -1))


class InvenioSessionStorage(object):
    """
    Session storage slub.
    """
    def set(self, name, value, timeout=None):
        """
        Stores data in a key-value storage system for defined time.
        """
        pass

    def get(self, name):
        """
        Returns data from the key-value storage system.
        """
        pass

    def delete(self, name):
        """
        Deletes data from the key-value storage system.
        """
        pass


class InvenioCacheSessionStorage(InvenioSessionStorage):
    """
    Implements session cache (redis) storage.
    """
    def set(self, name, value, timeout=None):
        cache.set(CFG_CACHE_KEY_PREFIX_SESSION+name,
                  value,
                  timeout=3600)

    def get(self, name):
        return cache.get(CFG_CACHE_KEY_PREFIX_SESSION+name)

    def delete(self, name):
        cache.delete(CFG_CACHE_KEY_PREFIX_SESSION+name)


class InvenioDBSessionStorage(InvenioSessionStorage):
    """
    Implements database backend for session storage.
    """
    def set(self, name, value, timeout=None):
        session_expiry = datetime.utcnow() + timeout
        s = Session()
        s.uid = current_user.get_id()
        s.session_key = name
        s.session_object = value
        s.session_expiry = session_expiry
        #FIXME REPLACE OR UPDATE
        db.session.merge(s)
        db.session.commit()

    def get(self, name):
        s = Session.query.filter(db.and_(
            Session.session_key == name,
            Session.session_expiry >= db.func.current_timestamp())).one()
        return s.session_object

    def delete(self, name):
        Session.query.filter(Session.session_key==name).delete()
        db.session.commit()


class InvenioSessionInterface(SessionInterface):
    """
    The session interface replaces standard Flask session
    implementation.
    """
    serializer = InvenioSerializer()
    session_class = InvenioSession
    storage = InvenioDBSessionStorage() if not CFG_SESSION_IN_CACHE \
              else InvenioCacheSessionStorage()

    def generate_sid(self):
        """
        Generates unique session identifier.
        """
        sid = uuid4().hex
        return sid

    def get_session_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name) or \
              request.args.get('session_id')
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid)
        try:
            data = self.serializer.loads(self.storage.get(sid))

            session = self.session_class(data, sid=sid)
            session['_uid'] = session.uid
            session['uid'] = session.uid
            if session.check_ip(request):
                return session
        except Exception, err:
            current_app.logger.warning("Detected error: %s" % err)
            pass
        except:
            current_app.logger.warning("Error: loading session object")
        current_app.logger.warning("returning empty session")
        return self.session_class(sid=sid)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        from invenio.websession_model import Session
        if not session:
            current_app.logger.error("Empty session: " + str(request.url))
            return
        #    response.delete_cookie(app.session_cookie_name,
        #                            domain=domain)
        #    response.delete_cookie(app.session_cookie_name + 'stub',
        #                            domain=domain)
        #    return
        timeout = self.get_session_expiration_time(app, session)
        session_expiry = datetime.utcnow() + timeout
        max_age = cookie_expiry = None
        uid = session.uid
        if uid > -1 and session.permanent:
            max_age = app.permanent_session_lifetime
            cookie_expiry = session_expiry
        sid = session.sid
        if session.logging_in:
            ## The user just logged in, better change the session ID
            sid = self.generate_sid()
            flashes = get_flashed_messages(with_categories=True)
            ## And remove the cookie that has been set
            self.storage.delete(session.sid)
            session.clear()
            response.delete_cookie(app.session_cookie_name, domain=domain)
            response.delete_cookie(app.session_cookie_name + 'stub',
                                   domain=domain)
            session.sid = sid
            # Fixes problem with lost flashes after login.
            map(lambda (cat, msg): flash(msg, cat), flashes)
        session['_uid'] = uid
        self.storage.set(sid,
                         self.serializer.dumps(dict(session)),
                         timeout = timeout)

        if not CFG_SUPPORT_HTTPS:
            response.set_cookie(app.session_cookie_name, sid,
                                expires=cookie_expiry, httponly=True,
                                domain=domain, max_age=max_age)
        elif session.uid > 0:
            ## User is authenticated, we shall use HTTPS then
            if request.scheme == 'https':
                response.set_cookie(app.session_cookie_name, sid,
                                    expires=cookie_expiry, httponly=True,
                                    domain=domain, secure=True, max_age=max_age)
                response.set_cookie(app.session_cookie_name + 'stub', 'HTTPS',
                                    expires=cookie_expiry, httponly=True,
                                    domain=domain, max_age=max_age)
            else:
                raise BadRequest("The user is being authenticated over HTTP "
                                 "rather than HTTPS?")
        else:
            response.set_cookie(app.session_cookie_name, sid, httponly=True,
                                domain=domain)
            response.set_cookie(app.session_cookie_name + 'stub', 'NO',
                                httponly=True, domain=domain)

