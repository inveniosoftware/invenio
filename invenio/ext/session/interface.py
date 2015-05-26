# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Flask :class:`~flask.sessions.SessionInterface` implementation."""

from datetime import datetime, timedelta
from uuid import uuid4

from flask import current_app, request
from flask.helpers import locked_cached_property
from flask.sessions import SessionInterface as FlaskSessionInterface

from invenio.config import SECRET_KEY as secret_key
from invenio.utils.serializers import LzmaPickle as Serializer

from itsdangerous import BadSignature, TimestampSigner

import six

from werkzeug.exceptions import BadRequest
from werkzeug.utils import import_string


class SessionInterface(FlaskSessionInterface):

    """Extend :class:`~flask.sessions.SessionInterface` class."""

    @locked_cached_property
    def has_secure_url(self):
        """Return ``True`` if secure url is configured."""
        return current_app.config.get('CFG_SITE_SECURE_URL', '').\
            startswith("https://")

    @locked_cached_property
    def serializer(self):
        """Return serializer class."""
        serializer_string = current_app.config.get('SESSION_SERIALIZER',
                                                   Serializer)
        return import_string(serializer_string)() \
            if isinstance(serializer_string, six.string_types) \
            else serializer_string()

    @locked_cached_property
    def session_class(self):
        """Return session class."""
        session_class_string = current_app.config.get(
            'SESSION_CLASS', 'invenio.ext.session.legacy_session:Session')
        return import_string(session_class_string) \
            if isinstance(session_class_string, six.string_types) \
            else session_class_string

    @locked_cached_property
    def backend(self):
        """Return session backend."""
        storage_string = current_app.config.get(
            'SESSION_BACKEND', 'invenio.ext.session.backends.cache:Storage')
        return import_string(storage_string)() \
            if isinstance(storage_string, six.string_types) \
            else storage_string()

    @locked_cached_property
    def sign_sid(self):
        """Return ``True`` if cookie session id is signed."""
        return current_app.config.get('SESSION_SIGN', True)

    @locked_cached_property
    def sign_salt(self):
        """Return salt for session id signing."""
        return current_app.config.get('SESSION_SALT', 'inveniosalt')

    def get_signer(self):
        """Return signer for cookie content signing."""
        return TimestampSigner(secret_key, self.sign_salt)

    def generate_sid(self):
        """Generate unique session identifier."""
        sid = uuid4().hex
        return sid

    def get_session_expiration_time(self, app, session):
        """Return session expiration time."""
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        """Return session instance."""
        sid_signed = request.cookies.get(app.session_cookie_name) or \
            request.args.get('session_id')

        # extract sid from signed version
        sid = None
        if sid_signed:
            if self.sign_sid:
                s = self.get_signer()

                # get maximum age without asking the cache (for
                # session.permanent) so we need to assume the worst case
                max_age = max(
                    app.permanent_session_lifetime.total_seconds(),
                    timedelta(days=1).total_seconds()
                )
                try:
                    sid = s.unsign(
                        sid_signed,
                        max_age=max_age
                    )
                except BadSignature:
                    # just ignore hackers and give them a new sid
                    # (this might also occur in case of clock divergence, but
                    # that should be a rare case)
                    sid = None
            else:
                # we did not sign, so it is just the same
                sid = sid_signed

        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid)
        try:
            data = self.backend.get(sid)
            if data:
                session = self.session_class(self.serializer.loads(data),
                                             sid=sid)
                return session
        except Exception:
            # this might have multiple reasons:
            #   - backend error (cache object timeout, cache flushed, ...)
            #   - error during deserialization
            #   - cache data does not match session_class (upgrades?)
            #   - earth stopped rotating
            current_app.logger.warning(
                "Load session error. Returning empty session.",
                exc_info=True)
        return self.session_class(sid=sid)

    def save_session(self, app, session, response):
        """Save current session."""
        domain = self.get_cookie_domain(app)
        if not session:
            current_app.logger.debug("Empty session: " + str(request.url))
            return

        timeout = self.get_session_expiration_time(app, session)
        session_expiry = datetime.utcnow() + timeout
        max_age = cookie_expiry = None
        uid = session.uid
        if uid > -1 and session.permanent:
            max_age = app.permanent_session_lifetime
            cookie_expiry = session_expiry
        sid = session.sid

        # Set all user id keys for compatibility.
        if len(session.keys()) == 1 and '_id' in session:
            session.delete()
            return
        elif not session.modified:
            return
        import warnings
        warnings.warn(str(session))

        session.uid = uid
        self.backend.set(sid,
                         self.serializer.dumps(dict(session)),
                         timeout=timeout)

        # sign sid
        if self.sign_sid:
            s = self.get_signer()
            sid_signed = s.sign(sid)
        else:
            # we did not sign, so it is just the same
            sid_signed = sid

        if not self.has_secure_url:
            response.set_cookie(app.session_cookie_name, sid_signed,
                                expires=cookie_expiry, httponly=True,
                                domain=domain, max_age=max_age)
        elif session.uid > 0:
            # User is authenticated, we shall use HTTPS then
            if request.scheme == 'https':
                response.set_cookie(app.session_cookie_name, sid_signed,
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
            response.set_cookie(app.session_cookie_name, sid_signed, httponly=True,
                                domain=domain)
            response.set_cookie(app.session_cookie_name + 'stub', 'NO',
                                httponly=True, domain=domain)
