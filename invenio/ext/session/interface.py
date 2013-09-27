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
    invenio.ext.session.interface
    -----------------------------

    Implements Flask `SessionInterface`.
"""

import cPickle
import zlib

from datetime import timedelta, datetime
from flask import current_app, request
from flask.helpers import locked_cached_property
from flask.sessions import SessionInterface as FlaskSessionInterface, \
    SecureCookieSession
from uuid import uuid4
from werkzeug.utils import import_string
from werkzeug.exceptions import BadRequest


class Serializer(object):
    @staticmethod
    def loads(string):
        return cPickle.loads(zlib.decompress(string))

    @staticmethod
    def dumps(data):
        return zlib.compress(cPickle.dumps(data, -1))


class SessionInterface(FlaskSessionInterface):
    """
    The session interface replaces standard Flask session
    implementation.
    """

    @locked_cached_property
    def has_secure_url(self):
        return current_app.config.get('CFG_SITE_SECURE_URL', '').\
            startswith("https://")

    @locked_cached_property
    def serializer(self):
        serializer_string = current_app.config.get('SESSION_SERIALIZER',
                                                   Serializer)
        return import_string(serializer_string)() \
            if isinstance(serializer_string, basestring) \
            else serializer_string()

    @locked_cached_property
    def session_class(self):
        session_class_string = current_app.config.get(
            'SESSION_CLASS', 'invenio.ext.session.legacy_session:Session')
        return import_string(session_class_string) \
            if isinstance(session_class_string, basestring) \
            else session_class_string

    @locked_cached_property
    def backend(self):
        storage_string = current_app.config.get(
            'SESSION_BACKEND', 'invenio.ext.session.backends.cache:Storage')
        return import_string(storage_string)() \
            if isinstance(storage_string, basestring) \
            else storage_string()

    def generate_sid(self):
        """Generates unique session identifier."""
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
            data = self.serializer.loads(self.backend.get(sid))

            session = self.session_class(data, sid=sid)
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
            #FIXME Do we really need to delete the session after login?
            ## The user just logged in, better change the session ID
            #sid = self.generate_sid()
            #flashes = get_flashed_messages(with_categories=True)
            ## And remove the cookie that has been set
            #self.backend.delete(session.sid)
            #session.clear()
            #response.delete_cookie(app.session_cookie_name, domain=domain)
            #response.delete_cookie(app.session_cookie_name + 'stub',
            #                       domain=domain)
            #session.sid = sid
            #session.uid = uid
            # Fixes problem with lost flashes after login.
            #map(lambda (cat, msg): flash(msg, cat), flashes)
            pass
        # Set all user id keys for compatibility.
        session.uid = uid
        self.backend.set(sid,
                         self.serializer.dumps(dict(session)),
                         timeout=timeout)

        if not self.has_secure_url:
            response.set_cookie(app.session_cookie_name, sid,
                                expires=cookie_expiry, httponly=True,
                                domain=domain, max_age=max_age)
        elif session.uid > 0:
            ## User is authenticated, we shall use HTTPS then
            if request.scheme == 'https':
                response.set_cookie(app.session_cookie_name, sid,
                                    expires=cookie_expiry, httponly=True,
                                    domain=domain, secure=True,
                                    max_age=max_age)
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
