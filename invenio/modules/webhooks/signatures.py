# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
import re
import hmac
from hashlib import sha1

from invenio.base.globals import cfg


def get_hmac(message):
    """
    Helper function which calculates HMAC value.
    """
    key = str(cfg["WEBHOOKS_SECRET_KEY"])
    hmac_value = hmac.new(key, message, sha1).hexdigest()
    return hmac_value


def check_x_hub_signature(signature, message):
    """
    Checks X-Hub-Signature. Secret key to compare
    signature: WEBHOOKS_SECRET_KEY.
    """
    hmac_value = get_hmac(message)
    if hmac_value == signature or \
       (signature.find('=') > -1 and \
            hmac_value == signature[signature.find('=') + 1:]):
        return True
    return False