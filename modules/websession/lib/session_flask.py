# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
from flask import g, current_app, request
from warnings import warn

from invenio.sqlalchemyutils import db
from invenio.webuser_flask import current_user
from invenio.config import \
    CFG_SITE_SECURE_URL, \
    CFG_WEBSEARCH_PERMITTED_RESTRICTED_COLLECTIONS_LEVEL

__all__ = ["InvenioSession", "InvenioSessionInterface"]

#CFG_SUPPORT_HTTPS = CFG_SITE_SECURE_URL.startswith("https://")
CFG_SUPPORT_HTTPS = False ## FIXME: add support for redirecting to HTTPS

# Store session information in memory cache (Redis, Memcache, ...).
CFG_SESSION_USE_CACHE = True
# Session key prefix for storing in db.
CFG_SESSION_KEY_PREFIX = 'session::'

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
        current_app.logger.info("initializing session with sid=%s" % sid)

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
        if CFG_SESSION_USE_CACHE:
            cache.delete(CFG_SESSION_KEY_PREFIX+self.sid)
        else:
            from invenio.websession_model import Session
            Session.query.filter(Session.session_key==self.sid).delete()
        if clear:
            self.clear()

    def invalidate(self):
        """
        Declare the session as invalid.
        """
        self.delete()
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
        current_app.logger.info("checking session IP against %s" % remote_ip)

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
        current_app.logger.info("setting uid to %s" % uid)
        if self.get('_uid') != uid:
            current_app.logger.info("detected logging in...")
            self.logging_in = True
        self['_uid'] = uid

    def _get_user_info(self):
        if 'user_info' in self and not self.logging_in:
            current_app.logger.info("accessing user_info")
            return self['user_info']

        current_app.logger.info("reloading user_info")
        current_user.reload()
        self.logging_in = False
        return self['user_info']

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

class InvenioSessionInterface(SessionInterface):
    serializer = InvenioSerializer()
    session_class = InvenioSession

    def generate_sid(self):
        sid = uuid4().hex
        current_app.logger.info("generating new session id: %s" % sid)
        return sid

    def get_session_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name) or \
              request.args.get('session_id')
        current_app.logger.info("opening session %s" % sid)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid)
        current_app.logger.info("loading session data sid: %s" % sid)
        try:
            if CFG_SESSION_USE_CACHE:
                data = self.serializer.loads(cache.get(CFG_SESSION_KEY_PREFIX+sid))
            else:
                from invenio.websession_model import Session
                from datetime import datetime
                s = Session.query.filter(db.and_(
                    Session.session_key == sid,
                    Session.session_expiry >= db.func.current_timestamp())).one()
                data = self.serializer.loads(s.session_object)

            session = self.session_class(data, sid=sid)
            session['_uid'] = session.uid
            session['uid'] = session.uid
            session['user_info'] = session.user_info
            current_app.logger.info("initilized session")
            if session.check_ip(request):
                return session
        except Exception, err:
            current_app.logger.warning("Detected error: %s" % err)
            pass
        except:
            current_app.logger.warning("Error: loading session object")
        current_app.logger.info("returning empty session")
        return self.session_class(sid=sid)

    def save_session(self, app, session, response):
        current_app.logger.info("saving session %s" % session.sid)
        domain = self.get_cookie_domain(app)
        from invenio.websession_model import Session
        if not session:
            current_app.logger.info("empty session detected. Deleting it")
            response.delete_cookie(app.session_cookie_name,
                                    domain=domain)
            response.delete_cookie(app.session_cookie_name + 'stub',
                                    domain=domain)
            return
        timeout = self.get_session_expiration_time(app, session)
        session_expiry = datetime.utcnow() + timeout
        max_age = cookie_expiry = None
        uid = session.uid
        if uid > -1 and session.permanent:
            max_age = app.permanent_session_lifetime.total_seconds()
            cookie_expiry = session_expiry
        sid = session.sid
        if session.logging_in:
            ## The user just logged in, better change the session ID
            current_app.logger.info("detected logging in. generating new sid")
            sid = self.generate_sid()
            ## And remove the cookie that has been set
            current_app.logger.info("... and delete previous one")
            session.delete(clear=False)
            response.delete_cookie(app.session_cookie_name, domain=domain)
            response.delete_cookie(app.session_cookie_name + 'stub',
                                   domain=domain)
            session.sid = sid
        #FIXME REPLACE OR UPDATE
        current_app.logger.info(str(dict(session)))
        session['_uid'] = uid
        session['user_info'] = session.user_info
        if CFG_SESSION_USE_CACHE:
            cache.set(CFG_SESSION_KEY_PREFIX+sid, self.serializer.dumps(dict(session)),
                      timeout = timeout)
        else:
            s = Session()
            s.session_key = sid
            s.session_expiry = session_expiry
            s.session_object = self.serializer.dumps(dict(session))
            s.uid = uid or -1
            db.session.merge(s)
            db.session.commit()

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
