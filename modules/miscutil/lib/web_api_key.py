# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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
    Invenio utilities to perform a REST like authentication
"""
import hmac
import time
from cgi import parse_qsl
from urllib import urlencode
import re

try:
    from uuid import uuid4
except ImportError:
    import random
    def uuid4():
        return "%x" % random.getrandbits(16*8)

from invenio.dbquery import run_sql, IntegrityError
from invenio.config import CFG_WEB_API_KEY_ALLOWED_URL
from invenio.access_control_config import CFG_WEB_API_KEY_STATUS
from invenio.hashutils import sha1

_CFG_WEB_API_KEY_ALLOWED_URL = [(re.compile(_url), _authorized_time, _need_timestamp)
        for _url, _authorized_time, _need_timestamp in CFG_WEB_API_KEY_ALLOWED_URL]


def create_new_web_api_key(uid, key_description=None):
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
            run_sql("INSERT INTO webapikey (id,secret,id_user,description) VALUES(%s,%s,%s,%s)",
                    (key_id, key_secrect, uid, key_description))
            break
        except IntegrityError:
            key_id = str(uuid4())

def show_web_api_keys(uid, diff_status=CFG_WEB_API_KEY_STATUS['REMOVED']):
    """
    Makes a query to the DB to obtain all the user's REST API keys

    @param uid: User's id
    @type uid: int
    @param diff_status: This string indicates if the query will show
    all the REST API keys or only the ones that still active (usefull in the
    admin part)
    @type diff_statusparam: string

    @return: Tuples with the id, description and status of the user's REST API
    keys
    """
    keys_info = run_sql("SELECT id, description, status FROM webapikey WHERE id_user = %s AND status <> %s",
                        (uid, diff_status))
    return keys_info

def mark_web_api_key_as_removed(key_id):
    """
    When the user wants to remove one of his key, this functions puts the status
    value of that key to remove, this way the user doesn't see the key anymore
    but the admin user stills see it, make statistics whit it, etc.

    @param key_id: The id of the REST key that will be "removed"
    @type key_id: string
    """
    run_sql("UPDATE webapikey SET status=%s WHERE id=%s", (CFG_WEB_API_KEY_STATUS['REMOVED'], key_id, ))

def get_available_web_api_keys(uid):
    """
    Search for all the available REST keys, it means all the user's keys that are
    not marked as REMOVED or REVOKED

    @param uid: The user id
    @type uid: int

    @return: Tuples of REST API public keys
    """
    keys = run_sql("SELECT id FROM webapikey WHERE id_user=%s AND status <> %s AND status <> %s",
                  (uid, CFG_WEB_API_KEY_STATUS['REMOVED'], CFG_WEB_API_KEY_STATUS['REVOKED']))
    return keys

def acc_get_uid_from_request(path, args):
    """
    Looks in the data base for the secret that matches with the API key in the
    request. If the REST API key is found and if the signature is correct
    returns the user's id.

    @param path: uri of the request until the "?" (i.e.: req.uri)
    @type path: string
    @param args: All the params of the request (i.e.: req.args)
    @type args: string

    @return: If everything goes well it returns the user's uid, it not -1
    """
    from invenio.webstat import register_customevent

    params = parse_qsl(args)
    api_key = signature = timestamp = None

    for param in params:
        if param[0] == 'apikey':
            api_key = param[1]
        elif param[0] == 'signature':
            signature = param[1]
            params.remove(param) #Get rid of the signature
        elif param [0] == 'timestamp':
            timestamp = param[1]
    #Check if the url is well built
    if api_key == None or signature == None:
        return -1

    url_req = "%s?%s" % (path, urlencode(params))

    authorized_time = None
    need_timestamp = False
    for url, authorized_time, need_timestamp in _CFG_WEB_API_KEY_ALLOWED_URL:
        if url.match(url_req) is not None:
            break

    if need_timestamp and timestamp == None:
        return -1

    if authorized_time is None:
        return -1

    if authorized_time != 0 and need_timestamp:
        time_lapse = time.time() - float(timestamp)
        if time_lapse > authorized_time or time_lapse < 0:
            return -1

    key = run_sql("SELECT id_user, secret FROM webapikey WHERE id=%s AND status <> %s AND status <> %s",
                  (api_key, CFG_WEB_API_KEY_STATUS['REMOVED'], CFG_WEB_API_KEY_STATUS['REVOKED']))
    if len(key) == 0 or not key:
        return -1
    else:
        uid = key[0][0]
        secret_key = key[0][1]
        server_signature = hmac.new(secret_key, url_req, sha1).hexdigest()
        if signature == server_signature:
            #If the signature is fine, log the key activity and return the UID
            register_customevent("apikeyusage", [uid, api_key, path, url_req])
            return uid
        else:
            return -1

def build_web_request(path, params, uid=-1, api_key=None, timestamp=True):
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
    if not isinstance(params, dict):
        if len(params) != 0 and params[0] == '?':
            params = params.replace('?','')
        params = parse_qsl(params)

    items = (hasattr(params, 'items') and [params.items()] or [list(params)])[0]

    if api_key:
        items.append(('apikey', api_key))
    elif uid > 0:
        keys = run_sql("SELECT id FROM webapikey WHERE id_user=%s AND status <> %s AND status <> %s",
                  (uid, CFG_WEB_API_KEY_STATUS['REMOVED'], CFG_WEB_API_KEY_STATUS['REVOKED']))
        if keys is not None and len(keys) != 0:
            api_key = keys[0][0]
            items.append(('apikey', api_key))
        else:
            return ''
    else:
        return ''

    if timestamp:
        items.append(('timestamp', str(int(time.time()))))

    items = sorted(items, key=lambda x: x[0].lower())
    url = '%s?%s' % (path, urlencode(items))

    secret_key = run_sql("SELECT secret FROM webapikey WHERE id=%s", (api_key,))
    if len(secret_key) == 0 or not secret_key:
        return ''
    signature = hmac.new(secret_key[0][0], url, sha1).hexdigest()
    items.append(('signature', signature))
    if not items:
        return path
    return '%s?%s' % (path, urlencode(items))
