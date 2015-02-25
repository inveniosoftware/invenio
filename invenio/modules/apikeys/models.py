# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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
Web API Key database models.
"""
# General imports.
from werkzeug import cached_property
from six.moves.urllib.parse import parse_qs, urlparse, urlunparse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import hmac
import time
import re

try:
    from uuid import uuid4
except ImportError:
    import random

    def uuid4():
        return "%x" % random.getrandbits(16*8)
from urllib import urlencode, basejoin

from invenio.base.globals import cfg
from invenio.utils.hash import sha1
from invenio.ext.sqlalchemy import db


# Create your models here.
from invenio.modules.accounts.models import User


def allowed_urls():
    """List of allowed urls."""
    return [(re.compile(_url), _authorized_time, _need_timestamp)
            for _url, _authorized_time, _need_timestamp in
            cfg.get('CFG_WEB_API_KEY_ALLOWED_URL', [])]


class WebAPIKey(db.Model):
    """Represents a Web API Key record."""
    __tablename__ = 'webapikey'

    #There are three status key that must be here: OK, REMOVED and REVOKED
    #the value doesn't matter at all
    CFG_WEB_API_KEY_STATUS = {'OK': 'OK',
                              'REMOVED': 'REMOVED',
                              'REVOKED': 'REVOKED',
                              'WARNING': 'WARNING',
                              }

    id = db.Column(db.String(150), primary_key=True, nullable=False)
    secret = db.Column(db.String(150), nullable=False)
    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id),
                        nullable=False)
    status = db.Column(db.String(25), nullable=False,
                       server_default='OK', index=True)
    description = db.Column(db.String(255), nullable=True)

    @classmethod
    def create_new(cls, uid, key_description=None):
        """
        Creates a new pair REST API key / secret key for the user. To do that it
        uses the uuid4 function.

        @param uid: User's id for the new REST API key
        @type uid: int
        @param key_description: User's description for the REST API key
        @type key_description: string
        """
        key_id = str(uuid4())
        key_secrect = str(uuid4())
        while True:
            try:
                new_key = WebAPIKey(id=key_id, secret=key_secrect, id_user=uid,
                                    description=key_description)
                db.session.add(new_key)
                db.session.commit()
                break
            except IntegrityError:
                key_id = str(uuid4())

    @classmethod
    def show_keys(cls, uid, diff_status=None):
        """
        Makes a query to the DB to obtain all the user's REST API keys

        @param uid: User's id
        @type uid: int
        @param diff_status: This string indicates if the query will show
        all the REST API keys or only the ones that still active (usable in the
        admin part)
        @type diff_statusparam: string

        @return: Tuples with the id, description and status of the user's REST API
        keys
        """
        if diff_status is None:
            diff_status = cls.CFG_WEB_API_KEY_STATUS['REMOVED']

        return db.session.query(WebAPIKey.id, WebAPIKey.description, WebAPIKey.status).\
            filter(WebAPIKey.id_user == uid,
                   WebAPIKey.status != diff_status).all()

    @classmethod
    def mark_as(cls, key_id, status):
        """
        When the user wants to remove one of his key, this functions puts the status
        value of that key to remove, this way the user doesn't see the key anymore
        but the admin user stills see it, make statistics whit it, etc.

        @param key_id: The id of the REST key that will be "removed"
        @type key_id: string
        """
        assert status in cls.CFG_WEB_API_KEY_STATUS
        cls.query.filter_by(id=key_id).\
            update({'status': status})

    @classmethod
    def get_available(cls, uid=None, apikey=None):
        """
        Search for all the available REST keys, it means all the user's keys that are
        not marked as REMOVED or REVOKED

        @param uid: The user id
        @type uid: int
        @param apikey: the apikey/id

        @return: WebAPIKey objects
        """

        filters = {}
        if uid is not None:
            filters['id_user'] = uid
        if apikey is not None:
            filters['id'] = apikey

        return cls.query.\
            filter_by(**filters). \
            filter(WebAPIKey.status != cls.CFG_WEB_API_KEY_STATUS['REMOVED'],
                   WebAPIKey.status != cls.CFG_WEB_API_KEY_STATUS['REVOKED']
                   ).all()

    @classmethod
    def get_server_signature(cls, secret, url):
        from flask import request
        secret = str(secret)
        if request.base_url not in url:
            url = basejoin(request.base_url, url)
        return hmac.new(secret, url, sha1).hexdigest()

    @classmethod
    def acc_get_uid_from_request(cls):
        """
        Looks in the data base for the secret that matches with the API key in the
        request. If the REST API key is found and if the signature is correct
        returns the user's id.

        @return: If everything goes well it returns the user's uid, if not -1
        """

        from invenio.legacy.webstat.api import register_customevent
        from flask import request
        api_key = signature = timestamp = None

        # Get the params from the GET/POST request
        if 'apikey' in request.values:
            api_key = request.values['apikey']

        if cfg.get('CFG_WEB_API_KEY_ENABLE_SIGNATURE'):
            if 'signature' in request.values:
                signature = request.values['signature']

        if 'signature' in request.values:
            signature = request.values['signature']

        if 'timestamp' in request.values:
            timestamp = request.values['timestamp']

        # Check if the request is well built
        if api_key is None or (signature is None and
           cfg.get('CFG_WEB_API_KEY_ENABLE_SIGNATURE')):
            return -1

        # Remove signature from the url params
        path = request.base_url
        url_req = request.url
        parsed_url = urlparse(url_req)
        params = parse_qs(parsed_url.query)
        params = dict([(i, j[0]) for i, j in list(params.items())])

        try:
            del params['signature']
        except KeyError:  # maybe signature was in post params
            pass

        # Reconstruct the url
        query = urlencode(sorted(params.items(), key=lambda x: x[0]))
        url_req = urlunparse((parsed_url.scheme,
                              parsed_url.netloc,
                              parsed_url.path,
                              parsed_url.params,
                              query,
                              parsed_url.fragment))

        authorized_time = None
        need_timestamp = False
        for url, authorized_time, need_timestamp in allowed_urls():
            if url.match(url_req) is not None:
                break

        if need_timestamp and timestamp is None:
            return -1

        if authorized_time is None:
            return -1

        if authorized_time != 0 and need_timestamp:
            time_lapse = time.time() - float(timestamp)
            if time_lapse > authorized_time or time_lapse < 0:
                return -1

        keys = cls.get_available(apikey=api_key)
        if not len(keys):
            return -1
        key = keys[0]

        uid = key.id_user
        if cfg.get('CFG_WEB_API_KEY_ENABLE_SIGNATURE'):
            secret_key = key.secret
            server_signature = cls.get_server_signature(secret_key, url_req)
            if signature != server_signature:
                return -1

        #If the signature is fine, log the key activity and return the UID
        register_customevent("apikeyusage", [uid, api_key, path, url_req])
        return uid

    @classmethod
    def build_web_request(cls, path, params=None, uid=-1, api_key=None, timestamp=True):
        """
        Build a new request that uses REST authentication.
        1. Add your REST API key to the params
        2. Add the current timestamp to the params, if needed
        3. Sort the query string params
        4. Merge path and the sorted query string to a single string
        5. Create a HMAC-SHA1 signature of this string using your secret key as the key
        6. Append the hex-encoded signature to your query string

        @note: If the api_key parameter is None, then this method performs a search
            in the data base using the uid parameter to get on of the user's REST
            API key. If the user has one or more usable REST  API key this method
            uses the first to appear.

        @param path: uri of the request until the "?" (i.e.: /search)
        @type path: string
        @param params: All the params of the request (i.e.: req.args or a dictionary
        with the param name as key)
        @type params: string or dict
        @param api_key: User REST API key
        @type api_key: string
        @param uid: User's id to do the search for the REST API key
        @type uid: int
        @param timestamp: Indicates if timestamp is needed in the request
        @type timestamp: boolean

        @return: Signed request string or, in case of error, ''
        """

        if params is None:
            params = {}

        if not isinstance(params, dict):
            if len(params) != 0 and params[0] == '?':
                params = params.replace('?', '')
            params = parse_qs(params)
            params = dict([(i, j[0]) for i, j in list(params.items())])

        if api_key:
            params['apikey'] = api_key
        elif uid > 0:
            keys = cls.get_available(uid=uid)
            if len(keys):
                api_key = keys[0][0]
                params['apikey'] = api_key
            else:
                return ''
        else:
            return ''

        if timestamp:
            params['timestamp'] = str(int(time.time()))

        parsed_url = urlparse(path)
        query = urlencode(sorted(params.items(), key=lambda x: x[0]))
        url = urlunparse((parsed_url.scheme,
                          parsed_url.netloc,
                          parsed_url.path,
                          parsed_url.params,
                          query,
                          parsed_url.fragment))

        if cfg.get('CFG_WEB_API_KEY_ENABLE_SIGNATURE'):
            try:
                secret_key = cls.query.filter_by(id=api_key).one().secret
            except NoResultFound:
                return ''

            signature = cls.get_server_signature(secret_key, url)
        params['signature'] = signature
        query = urlencode(params)
        return urlunparse((parsed_url.scheme,
                           parsed_url.netloc,
                           parsed_url.path,
                           parsed_url.params,
                           query,
                           parsed_url.fragment))
