# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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
The Dataciteutils module contains the standard functions to connect with
the DataCite RESTful API.

https://mds.datacite.org/static/apidoc

The main API functions are:
    - get_url_by_doi()
    - get_metadata_by_doi()
    - post_doi()
    - post_metadata()
    - delete_metadata()
    - generate_doi()
"""

# FIXME
# OpenSSL 1.0.0 has a reported bug with SSLv3/TLS handshake.
# Python libs affected are httplib2 and urllib2. Eg:
# httplib2.SSLHandshakeError: [Errno 1] _ssl.c:497:
# error:14077438:SSL routines:SSL23_GET_SERVER_HELLO:tlsv1 alert internal error
# Using pycurl while error is solved... :)
# More info:
# https://bugs.launchpad.net/ubuntu/+source/openssl/+bug/861137


# Example DOI:
# http://dx.doi.org/10.2314/CERN-THESIS-2007-001
# https://mds.datacite.org/doi/10.2314/CERN-THESIS-2007-001
# doi = '10.2314/CERN-THESIS-2007-001'

import pycurl
from StringIO import StringIO

__all__ = [ 'get_url_by_doi', 'get_metadata_by_doi', 'post_doi', \
            'post_metadata', 'delete_metadata', 'generate_doi']

# TODO check config mode
"""
ENDPOINT = 'https://mds.datacite.org/'
USER = 'someuser'
PASSWORD = 'somepassword'
TEST_PREFIX = '10.xxxx'
TEST_SUFFIX = '?testMode=true'
"""

from invenio.config import CFG_ETCDIR
CFG_DATACITEUTILS_CONFIG_PATH = CFG_ETCDIR + "/miscutil/dataciteutils.cfg"

from ConfigParser import ConfigParser
conf = ConfigParser()
conf.read(CFG_DATACITEUTILS_CONFIG_PATH)
ENDPOINT = conf.get("general", "endpoint")
USER = conf.get("general", "user")
PASSWORD = conf.get("general", "password")
PREFIX = conf.get("general", "prefix")
SUFFIX = conf.get("general", "suffix")
CHECK_DB = conf.get("general", "check_db")
TESTING = conf.get("general", "testing")

class CurlException(Exception):
    """
    Exception raised when pyCurl has some problem
    """
    pass

class DataciteUtilsServerError(Exception):
    """
    Exception raised when the server status is 500 (Internal Server Error)
    """
    pass

class DataciteUtilsRequestError(Exception):
    """
    Exception raised when the server status is:
        204 No Content
        400 Bad Request
        401 Unauthorized
        403 Forbidden
        404 Not Found
        410 Gone (deleted)
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def get_url_by_doi(doi, endpoint=ENPOINT, username=USER, password=PASSWORD):
    """
    Returns the URL where the resource pointed by the DOI is located

    @param doi: DOI name of the resource
    @type  doi: string

    @param username: name of the user
    @type  username: str

    @param password: password of the user
    @type  password: str

    @return: URL matching the DOI
    @type: string
    """
    response_buffer = StringIO()
    try:
        c = pycurl.Curl()
        c.setopt(c.URL, ENDPOINT + 'doi/' + doi)
        c.setopt(c.USERPWD, '%s:%s' % (username, password))
        c.setopt(c.WRITEFUNCTION, response_buffer.write)
        # c.setopt(c.VERBOSE, True)
        c.perform()
        code = c.getinfo(pycurl.HTTP_CODE)
    except:
        raise CurlException
    if code == 200:
        return response_buffer.getvalue()
    elif code == 500:
        raise DataciteUtilsServerError
    else:
        raise DataciteUtilsRequestError(code)

def get_metadata_by_doi(doi, endpoint=ENPOINT, username=USER, password=PASSWORD):
    """
    Returns the metadata associated to a DOI name

    @param doi: DOI name of the resource
    @type  doi: string

    @param username: name of the user
    @type  username: str

    @param password: password of the user
    @type  password: str

    @return: metadata xml
    @type: string
    """
    response_buffer = StringIO()
    try:
        c = pycurl.Curl()
        c.setopt(c.URL, ENDPOINT + 'metadata/' + doi)
        c.setopt(c.USERPWD, '%s:%s' % (username, password))
        c.setopt(c.WRITEFUNCTION, response_buffer.write)
        c.perform()
        code = c.getinfo(pycurl.HTTP_CODE)
    except:
        raise CurlException
    if code == 200:
        return response_buffer.getvalue()
    elif code == 500:
        raise DataciteUtilsServerError
    else:
        raise DataciteUtilsRequestError(code)

def post_doi(new_doi, location, endpoint=ENPOINT, username=USER, password=PASSWORD, testing=TESTING):
    """
    Returns the metadata associated to a DOI

    @param new_doi: DOI name for the new resource
    @type  new_doi: string

    @param location: URL where the resource is located
    @type  location: string

    @param username: name of the user
    @type  username: str

    @param password: password of the user
    @type  password: str

    @param testing: flag, no real commitment of the result
    @type  testing: boolean

    @return: OK message
    @type: string
    """
    response_buffer = StringIO()
    try:
        c = pycurl.Curl()
        if (testing == True):
	        c.setopt(c.URL, ENDPOINT + 'doi?testMode=true')
        else:
	        c.setopt(c.URL, ENDPOINT + 'doi')
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPHEADER, ['Content-Type: text/plain'])
        c.setopt(c.HTTPHEADER, ['Charset: UTF-8'])
        c.setopt(c.USERPWD, '%s:%s' % (username, password))
        # Format: doi={doi}&url={url}
        body_content = 'doi=' + new_doi + '&url=' + location
        body_content.encode('utf-8')
        c.setopt(c.POSTFIELDS, body_content)
        c.setopt(c.WRITEFUNCTION, response_buffer.write)
        c.perform()
        code = c.getinfo(pycurl.HTTP_CODE)
    except:
        raise CurlException
    if code == 201:
        return response_buffer.getvalue()
    elif code == 500:
        raise DataciteUtilsServerError
    else:
        raise DataciteUtilsRequestError(code)

def post_metadata(metadata, endpoint=ENPOINT, username=USER, password=PASSWORD, testing=TESTING):
    """
    Sends a new metadata set to complete an existing DOI.
    Metadata should follow the DataCite Metadata Schema 2.2
    http://schema.datacite.org/

    @param metadata: XML format of the metadata
    @type  metadata: str

    @param username: name of the user
    @type  username: str

    @param password: password of the user
    @type  password: str

    @param testing: flag, no real commitment of the result
    @type  testing: boolean

    @return: OK message
    @type: string
    """
    response_buffer = StringIO()
    try:
        c = pycurl.Curl()
        if (testing == True):
	        c.setopt(c.URL, ENDPOINT + 'metadata?testMode=true')
        else:
	        c.setopt(c.URL, ENDPOINT + 'metadata')
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPHEADER, ['Content-Type: application/xml'])
        c.setopt(c.HTTPHEADER, ['Charset: UTF-8'])
        c.setopt(c.USERPWD, '%s:%s' % (username, password))
        body_content = metadata
        body_content.encode('utf-8')
        c.setopt(c.POSTFIELDS, body_content)
        c.setopt(c.WRITEFUNCTION, response_buffer.write)
        c.perform()
        code = c.getinfo(pycurl.HTTP_CODE)
    except:
        raise CurlException
    if code == 201:
        return response_buffer.getvalue()
    elif code == 500:
        raise DataciteUtilsServerError
    else:
        raise DataciteUtilsRequestError(code)

def delete_metadata (doi, endpoint=ENPOINT, username=USER, password=PASSWORD):
    """
    Mark as 'inactive' the metadata set of a DOI resource

    @param doi: DOI name of the resource
    @type  doi: string

    @param username: name of the user
    @type  username: str

    @param password: password of the user
    @type  password: str

    @return: OK message
    @type: string
    """
    response_buffer = StringIO()
    try:
        c = pycurl.Curl()
        c.setopt(c.USERPWD, '%s:%s' % (username, password))
        c.setopt(c.URL, ENDPOINT + 'metadata/' + doi)
        code = c.getinfo(pycurl.HTTP_CODE)
    except:
        raise CurlException
    if code == 200:
        return response_buffer.getvalue()
    elif code == 500:
        raise DataciteUtilsServerError
    else:
        raise DataciteUtilsRequestError(code)

# TODO restrictions and database checking!
def generate_doi(starting='Test.', prefix=PREFIX, check_db=CHECK_DB):
    """
    Generates a random DOI name, given a prefix and a starting string.
    If required, it checks in the database if the DOI was already assigned.

    @param prefix: DOI prefix
    @type  prefix: str

    @param starting: Internal namespace header
    @type  starting: str

    @param check_db: flag, check the name in the database
    @type  check_db: boolean

    @return: DOI name (prefix/header.name)
    @type: string
    """
    import random, string

    rand_string = ''.join(random.choice(string.lowercase + string.digits) \
				    for i in xrange(8))
    doi = prefix + '/' + starting + rand_string[0:4] + '-' + rand_string[4:8]
    # if check_db == True:
    #	not case sensitive...
    #	select * from tabla_doi where tipo=doi, valor=doi
    return doi

