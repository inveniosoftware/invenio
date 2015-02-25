# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

""" Bibcheck plugin that checks for invalid urls """

import urlparse
import re
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    print "Requests module not available, no redirect/broken url detection"
    HAS_REQUESTS = False

from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL

DOMAIN_REGEXP = r"^[a-zA-Z0-9\-\.]+\.([a-z]{2}|com|edu|gov|info|net|org)\/"

def clean_url(url):
    """
    Return a canonical url, and add a http protocol if the url lacks protocol
    """
    # Does it start with with something that looks like a domain?
    if re.match(DOMAIN_REGEXP, url):
        url = "http://" + url

    # Canonicalize
    parsed = list(urlparse.urlsplit(url))

    if parsed[1] == "": # Relative or invalid URL
        return None

    if parsed[0] not in ("http", "https", "ftp"): # No/invalid schema
        parsed[0] = "http"
    return urlparse.urlunsplit(parsed)


def check_record(record, fields):
    """
    Checks that the specified field contains a correctly formatted url, if it
    doesn't it tries to figure out the correct url (for example by adding
    http:// at the beginning) and amends the record.

    It also makes a HEAD request to the url to check for broken links, server
    errors etc...

    If it encounters a permanent redirection (301) it will amend the record with
    the new url of the resource.
    """

    for (position, url) in record.iterfields(fields):
        url_cleaned = clean_url(url)

        if url_cleaned is None:
            record.set_invalid('Field %s: invalid URL' % position[0])
            continue

        if HAS_REQUESTS:
            try:
                if any(url in url_cleaned for url in [CFG_SITE_URL, CFG_SITE_SECURE_URL]):
                    continue
                response = requests.head(url_cleaned, allow_redirects=False,
                                         verify=False)
                code = response.status_code
                if code >= 400 and code < 600:
                    record.set_invalid('Server error: %s - %s' % (code, url_cleaned))
                elif code == 301:
                    url_cleaned = response.headers['Location']
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError,
                    requests.exceptions.Timeout,
                    requests.exceptions.TooManyRedirects,
                    requests.exceptions.InvalidSchema,
                    requests.exceptions.InvalidURL) as e:
                # Problem with the request occurred
                record.set_invalid('Server error: %s - %s' % (e, url_cleaned))

        record.amend_field(position, url_cleaned)
