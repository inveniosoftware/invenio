# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""External user authentication for simple robots

This implement an external authentication system suitable for robots usage.
User attributes are retrieved directly from the form dictionary of the request
object.
"""

import os
import sys
import hmac
import time
import base64

if sys.hexversion < 0x2050000:
    import sha as sha1
else:
    from hashlib import sha1

from cPickle import dumps
from zlib import decompress, compress

from invenio.jsonutils import json, json_unicode_to_utf8
from invenio.shellutils import mymkdir
from invenio.external_authentication import ExternalAuth, InvenioWebAccessExternalAuthError
from invenio.config import CFG_ETCDIR, CFG_SITE_URL, CFG_SITE_SECURE_URL

CFG_ROBOT_EMAIL_ATTRIBUTE_NAME = 'email'
CFG_ROBOT_NICKNAME_ATTRIBUTE_NAME = 'nickname'
CFG_ROBOT_GROUPS_ATTRIBUTE_NAME = 'groups'
CFG_ROBOT_TIMEOUT_ATTRIBUTE_NAME = '__timeout__'
CFG_ROBOT_USERIP_ATTRIBUTE_NAME = '__userip__'
CFG_ROBOT_GROUPS_SEPARATOR = ';'
CFG_ROBOT_URL_TIMEOUT = 3600

CFG_ROBOT_KEYS_PATH = os.path.join(CFG_ETCDIR, 'webaccess', 'robot_keys.dat')

def normalize_ip(ip, up_to_bytes=4):
    """
    @param up_to_bytes: set this to the number of bytes that should
    be considered in the normalization. E.g. is this is set two 2, only the
    first two bytes will be considered, while the remaining two will be set
    to 0.
    @return: a normalized IP, e.g. 123.02.12.12 -> 123.2.12.12
    """
    try:
        ret = []
        for i, number in enumerate(ip.split(".")):
            if i < up_to_bytes:
                ret.append(str(int(number)))
            else:
                ret.append("0")
        return '.'.join(ret)
    except ValueError:
        ## e.g. if it's IPV6 ::1
        return ip

def load_robot_keys():
    """
    @return: the robot key dictionary.
    """
    from cPickle import loads
    from zlib import decompress
    try:
        robot_keys = loads(decompress(open(CFG_ROBOT_KEYS_PATH).read()))
        if not isinstance(robot_keys, dict):
            return {}
        else:
            return robot_keys
    except:
        return {}

class ExternalAuthRobot(ExternalAuth):
    """
    This class implement an external authentication method suitable to be
    used by an external service that, after having authenticated a user,
    will provide a URL to the user that, once followed, will successfully
    login the user into Invenio, with any detail the external service
    decided to provide to the Invenio installation.

    Such URL should be built as follows:
        BASE?QUERY

    where BASE is CFG_SITE_SECURE_URL/youraccount/robotlogin

    and QUERY is a urlencoded mapping of the following key->values:
      - assertion: an assertion, i.e. a piece of information describing the
        user, see below for more details.
      - robot: the identifier of the external service providing the assertion
      - login_method: the name of the login method as defined in CFG_EXTERNAL_AUTHENTICATION.
      - digest: the digest of the signature as detailed below.
      - referer: the URL where the user should be redirected after successful
        login (it is called referer as, for historical reasons, this is the
        original URL of the page on which, a human-user has clicked "login".

    the "assertion" should be a JSON serialized mapping with the following
    keys:
      - email: the email of the user (i.e. its identifier).
      - nickname: optional nickname of the user.
      - groups: an optional ';'-separated list of groups to which the user
        belongs to.
      - __timeout__: the number of seconds (floating point) from the Epoch,
        after which the URL will no longer be valid. (expressed in UTC)
      - __userip__: the IP address of the user for whom this URL has been
        created. (if the user will follow this URL using a different URL the
        request will not be valid)
      - any other key can be added and will be merged in the external user
        settings.

    If L{use_zlib} is True the assertion is a base64-url-flavour encoding
    of the zlib compression of the original assertion (useful for shortening
    the URL while make it easy to type).

    The "digest" is the hexadecimal representation of the digest using the
    HMAC-SHA1 method to sign the assertion with the secret key associated
    with the robot for the given login_method.

    @param enforce_external_nicknames: whether to trust nicknames provided by
        the external service and use them (if possible) as unique identifier
        in the system.
    @type enforce_external_nicknames: boolean
    @param email_attribute_name: the actual key in the assertion that will
        contain the email.
    @type email_attribute_name: string
    @param nickname_attribute_name: the actual key in the assertion that will
        contain the nickname.
    @type nickname_attribute_name: string
    @param groups_attribute_name: the actual key in the assertion that will
        contain the groups.
    @type groups_attribute_name: string
    @param groups_separator: the string used to separate groups.
    @type groups_separator: string
    @param timeout_attribute_name: the actual key in the assertion that will
        contain the timeout.
    @type timeout_attribute_name: string
    @param userip_attribute_name: the actual key in the assertion that will
        contain the user IP.
    @type userip_attribute_name: string
    @param external_id_attribute_name: the actual string that identifies the
        user in the external authentication system. By default this is set
        to be the same as the nickname, but this can be configured.
    @param check_user_ip: whether to check for the IP address of the user
        using the given URL, against the IP address stored in the assertion
        to be identical. If 0, no IP check will be performed, if 1, only the
        1st byte will be compared, if 2, only the first two bytes will be
        compared, if 3, only the first three bytes, and if 4, the whole IP
        address will be checked.
    @type check_user_ip: int
    @param use_zlib: whether to use base64-url-flavour encoding of the zlib
        compression of the json serialization of the assertion or simply
        the json serialization of the assertion.
    @type use_zlib: boolean
    """
    def __init__(self, enforce_external_nicknames=False,
            email_attribute_name=CFG_ROBOT_EMAIL_ATTRIBUTE_NAME,
            nickname_attribute_name=CFG_ROBOT_NICKNAME_ATTRIBUTE_NAME,
            groups_attribute_name=CFG_ROBOT_GROUPS_ATTRIBUTE_NAME,
            groups_separator=CFG_ROBOT_GROUPS_SEPARATOR,
            timeout_attribute_name=CFG_ROBOT_TIMEOUT_ATTRIBUTE_NAME,
            userip_attribute_name=CFG_ROBOT_USERIP_ATTRIBUTE_NAME,
            check_user_ip=4,
            external_id_attribute_name=CFG_ROBOT_NICKNAME_ATTRIBUTE_NAME,
            use_zlib=True,
            ):
        ExternalAuth.__init__(self, enforce_external_nicknames=enforce_external_nicknames)
        self.email_attribute_name = email_attribute_name
        self.nickname_attribute_name = nickname_attribute_name
        self.groups_attribute_name = groups_attribute_name
        self.groups_separator = groups_separator
        self.timeout_attribute_name = timeout_attribute_name
        self.userip_attribute_name = userip_attribute_name
        self.external_id_attribute_name = external_id_attribute_name
        self.check_user_ip = check_user_ip
        self.use_zlib = use_zlib

    def __extract_attribute(self, req):
        """
        Load from the request the given assertion, extract all the attribute
        to properly login the user, and verify that the data are actually
        both well formed and signed correctly.
        """
        from invenio.webinterface_handler import wash_urlargd
        args = wash_urlargd(req.form, {
            'assertion': (str, ''),
            'robot': (str, ''),
            'digest': (str, ''),
            'login_method': (str, '')})
        assertion = args['assertion']
        digest = args['digest']
        robot = args['robot']
        login_method = args['login_method']
        shared_key = load_robot_keys().get(login_method, {}).get(robot)
        if shared_key is None:
            raise InvenioWebAccessExternalAuthError("A key does not exist for robot: %s, login_method: %s" % (robot, login_method))
        if not self.verify(shared_key, assertion, digest):
            raise InvenioWebAccessExternalAuthError("The provided assertion does not validate against the digest %s for robot %s" % (repr(digest), repr(robot)))
        if self.use_zlib:
            try:
                ## Workaround to Perl implementation that does not add
                ## any padding to the base64 encoding.
                needed_pad = (4 - len(assertion) % 4) % 4
                assertion += needed_pad * '='
                assertion = decompress(base64.urlsafe_b64decode(assertion))
            except:
                raise InvenioWebAccessExternalAuthError("The provided assertion is corrupted")
        data = json_unicode_to_utf8(json.loads(assertion))
        if not isinstance(data, dict):
            raise InvenioWebAccessExternalAuthError("The provided assertion is invalid")
        timeout = data[self.timeout_attribute_name]
        if timeout < time.time():
            raise InvenioWebAccessExternalAuthError("The provided assertion is expired")
        userip = data.get(self.userip_attribute_name)
        if not self.check_user_ip or (normalize_ip(userip, self.check_user_ip) == normalize_ip(req.remote_ip, self.check_user_ip)):
            return data
        else:
            raise InvenioWebAccessExternalAuthError("The provided assertion has been issued for a different IP address (%s instead of %s)" % (userip, req.remote_ip))

    def auth_user(self, username, password, req=None):
        """Authenticate user-supplied USERNAME and PASSWORD.  Return
        None if authentication failed, or the email address of the
        person if the authentication was successful.  In order to do
        this you may perhaps have to keep a translation table between
        usernames and email addresses.
        Raise InvenioWebAccessExternalAuthError in case of external troubles.
        """
        data = self.__extract_attribute(req)
        email = data.get(self.email_attribute_name)
        ext_id = data.get(self.external_id_attribute_name, email)
        if email:
            if isinstance(email, str):
                return email.strip().lower(), ext_id.strip()
            else:
                raise InvenioWebAccessExternalAuthError("The email provided in the assertion is invalid: %s" % (repr(email)))
        else:
            return None, None

    def fetch_user_groups_membership(self, username, password=None, req=None):
        """Given a username and a password, returns a dictionary of groups
        and their description to which the user is subscribed.
        Raise InvenioWebAccessExternalAuthError in case of troubles.
        """
        if self.groups_attribute_name:
            data = self.__extract_attribute(req)
            groups = data.get(self.groups_attribute_name)
            if groups:
                if isinstance(groups, str):
                    groups = [group.strip() for group in groups.split(self.groups_separator)]
                    return dict(zip(groups, groups))
                else:
                    raise InvenioWebAccessExternalAuthError("The groups provided in the assertion are invalid: %s" % (repr(groups)))
        return {}

    def fetch_user_nickname(self, username, password=None, req=None):
        """Given a username and a password, returns the right nickname belonging
        to that user (username could be an email).
        """
        if self.nickname_attribute_name:
            data = self.__extract_attribute(req)
            nickname = data.get(self.nickname_attribute_name)
            if nickname:
                if isinstance(nickname, str):
                    return nickname.strip().lower()
                else:
                    raise InvenioWebAccessExternalAuthError("The nickname provided in the assertion is invalid: %s" % (repr(nickname)))
        return None

    def fetch_user_preferences(self, username, password=None, req=None):
        """Given a username and a password, returns a dictionary of keys and
        values, corresponding to external infos and settings.

        userprefs = {"telephone": "2392489",
                     "address": "10th Downing Street"}

        (WEBUSER WILL erase all prefs that starts by EXTERNAL_ and will
        store: "EXTERNAL_telephone"; all internal preferences can use whatever
        name but starting with EXTERNAL). If a pref begins with HIDDEN_ it will
        be ignored.
        """
        data = self.__extract_attribute(req)
        for key in (self.email_attribute_name, self.groups_attribute_name, self.nickname_attribute_name, self.timeout_attribute_name, self.userip_attribute_name):
            if key and key in data:
                del data[key]
        return data

    def robot_login_method_p():
        """Return True if this method is dedicated to robots and should
        not therefore be available as a choice to regular users upon login.
        """
        return True
    robot_login_method_p = staticmethod(robot_login_method_p)

    def sign(secret, assertion):
        """
        @return: a signature of the given assertion.
        @rtype: string
        @note: override this method if you want to change the signature
            algorithm (e.g. to use GPG).
        @see: L{verify}
        """
        return hmac.new(secret, assertion, sha1).hexdigest()
    sign = staticmethod(sign)

    def verify(secret, assertion, signature):
        """
        @return: True if the signature is valid
        @rtype: boolean
        @note: override this method if you want to change the signature
            algorithm (e.g. to use GPG)
        @see: L{sign}
        """
        return hmac.new(secret, assertion, sha1).hexdigest() == signature
    verify = staticmethod(verify)

    def test_create_example_url(self, email, login_method, robot, ip, assertion=None, timeout=None, referer=None, groups=None, nickname=None):
        """
        Create a test URL to test the robot login.

        @param email: email of the user we want to login as.
        @type email: string
        @param login_method: the login_method name as specified in CFG_EXTERNAL_AUTHENTICATION.
        @type login_method: string
        @param robot: the identifier of this robot.
        @type robot: string
        @param assertion: any further data we want to send to.
        @type: json serializable mapping
        @param ip: the IP of the user.
        @type: string
        @param timeout: timeout when the URL will expire (in seconds from the Epoch)
        @type timeout: float
        @param referer: the URL where to land after successful login.
        @type referer: string
        @param groups: the list of optional group of the user.
        @type groups: list of string
        @param nickname: the optional nickname of the user.
        @type nickname: string
        @return: the URL to login as the user.
        @rtype: string
        """
        from invenio.access_control_config import CFG_EXTERNAL_AUTHENTICATION
        from invenio.urlutils import create_url
        if assertion is None:
            assertion = {}
        assertion[self.email_attribute_name] = email
        if nickname:
            assertion[self.nickname_attribute_name] = nickname
        if groups:
            assertion[self.groups_attribute_name] = self.groups_separator.join(groups)
        if timeout is None:
            timeout = time.time() + CFG_ROBOT_URL_TIMEOUT
        assertion[self.timeout_attribute_name] = timeout
        if referer is None:
            referer = CFG_SITE_URL
        if login_method is None:
            for a_login_method, details in CFG_EXTERNAL_AUTHENTICATION.iteritems():
                if details[2]:
                    login_method = a_login_method
                    break
        robot_keys = load_robot_keys()
        assertion[self.userip_attribute_name] = ip
        assertion = json.dumps(assertion)
        if self.use_zlib:
            assertion = base64.urlsafe_b64encode(compress(assertion))
        shared_key = robot_keys[login_method][robot]
        digest = self.sign(shared_key, assertion)
        return create_url("%s%s" % (CFG_SITE_SECURE_URL, "/youraccount/robotlogin"), {
            'assertion': assertion,
            'robot': robot,
            'login_method': login_method,
            'digest': digest,
            'referer': referer})

def update_robot_key(login_method, robot, key=None):
    """
    Utility to update the robot key store.
    @param login_method: the login_method name as per L{CFG_EXTERNAL_AUTHENTICATION}.
        It should correspond to a robot-enable login method.
    @type: string
    @param robot: the robot identifier
    @type robot: string
    @param key: the secret
    @type key: string
    @note: if the secret is empty the corresponding key will be removed.
    """
    robot_keys = load_robot_keys()
    if key is None and login_method in robot_keys and robot in robot_keys[login_method]:
        del robot_keys[login_method][robot]
        if not robot_keys[login_method]:
            del robot_keys[login_method]
    else:
        if login_method not in robot_keys:
            robot_keys[login_method] = {}
        robot_keys[login_method][robot] = key
    mymkdir(os.path.join(CFG_ETCDIR, 'webaccess'))
    open(CFG_ROBOT_KEYS_PATH, 'w').write(compress(dumps(robot_keys, -1)))

