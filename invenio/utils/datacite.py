# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

CFG_DATACITE_USERNAME
CFG_DATACITE_PASSWORD
CFG_DATACITE_TESTMODE
CFG_DATACITE_DOI_PREFIX
CFG_DATACITE_URL

Example of usage:
    doc = '''
    <resource xmlns="http://datacite.org/schema/kernel-2.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://datacite.org/schema/kernel-2.2 http://schema.datacite.org/meta/kernel-2.2/metadata.xsd">
    <identifier identifierType="DOI">10.5072/invenio.test.1</identifier>
    <creators>
        <creator>
            <creatorName>Simko, T</creatorName>
        </creator>
    </creators>
    <titles>
        <title>Invenio Software</title>
    </titles>
    <publisher>CERN</publisher>
    <publicationYear>2002</publicationYear>
    </resource>
    '''

    d = DataCite(test_mode=True)

    # Set metadata for DOI
    d.metadata_post(doc)

    # Mint new DOI
    d.doi_post('10.5072/invenio.test.1', 'http://invenio-software.org/')

    # Get DOI location
    location = d.doi_get("10.5072/invenio.test.1")

    # Get metadata for DOI
    d.metadata_get("10.5072/invenio.test.1")

    # Make DOI inactive
    d.metadata_delete("10.5072/invenio.test.1")
"""

from invenio.base.globals import cfg
from urllib import urlencode
import httplib
import urllib2
import base64
import socket
try:
    import ssl
    HAS_SSL = True
except ImportError:
    HAS_SSL = False

if not HAS_SSL:
    from warnings import warn
    warn("Module ssl not installed. Please install with e.g. 'pip install ssl'. Required for HTTPS connections to DataCite.", RuntimeWarning)

import urllib2
import re
from invenio.xmlDict import XmlDictConfig, ElementTree

# Uncomment to enable debugging of HTTP connection and uncomment line in
# DataCiteRequest.request()
# import logging
# import sys
# logger = logging.getLogger()
# logger.addHandler(logging.StreamHandler(sys.stdout))
# logger.setLevel(logging.NOTSET)

if HAS_SSL:
    # OpenSSL 1.0.0 has a reported bug with SSLv3/TLS handshake.
    # Python libs affected are httplib2 and urllib2. Eg:
    # httplib2.SSLHandshakeError: [Errno 1] _ssl.c:497:
    # error:14077438:SSL routines:SSL23_GET_SERVER_HELLO:tlsv1 alert internal error
    # custom HTTPS opener, banner's oracle 10g server supports SSLv3 only
    class HTTPSConnectionV3(httplib.HTTPSConnection):
        def __init__(self, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)

        def connect(self):
            try:
                sock = socket.create_connection((self.host, self.port), self.timeout)
            except AttributeError:
                # Python 2.4 compatibility (does not deal with IPv6)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))

            try:
                if self._tunnel_host:
                    self.sock = sock
                    self._tunnel()
            except AttributeError:
                # Python 2.4 compatibility (_tunnel_host not defined)
                pass

            try:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv3)
            except ssl.SSLError:
                self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)

    class HTTPSHandlerV3(urllib2.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(HTTPSConnectionV3, req)


#
# Exceptions
#
class HttpError(Exception):
    """
    Exception raised when there's a technical problem.
    """
    pass


class DataCiteError(Exception):
    """
    Exception raised when the server status is:
        204 No Content
        400 Bad Request
        401 Unauthorized
        403 Forbidden
        404 Not Found
        410 Gone (deleted)
    """
    @staticmethod
    def factory(err_code):
        if err_code == 204:
            return DataCiteNoContentError()
        elif err_code == 400:
            return DataCiteBadRequestError()
        elif err_code == 401:
            return DataCiteUnauthorizedError()
        elif err_code == 403:
            return DataCiteForbiddenError()
        elif err_code == 404:
            return DataCiteNotFoundError()
        elif err_code == 410:
            return DataCiteGoneError()
        elif err_code == 412:
            return DataCitePreconditionError()
        else:
            return DataCiteServerError()


class DataCiteServerError(DataCiteError):
    """ An internal server error happend on the DataCite end. Try later. """
    pass


class DataCiteRequestError(DataCiteError):
    """ A DataCite request error. You made an invalid request.  """
    pass


class DataCiteNoContentError(DataCiteRequestError):
    """ DOI is known to MDS, but is not resolvable (might be due to handle's latency) """
    pass


class DataCiteBadRequestError(DataCiteRequestError):
    """
    invalid XML, wrong domain, wrong prefix,
    request body must be exactly two lines: DOI and URL
    one or more of the specified mime-types or urls are invalid (e.g. non
        supported mime-type, not allowed url domain, etc.)
    """
    pass


class DataCiteUnauthorizedError(DataCiteRequestError):
    """ no login """
    pass


class DataCiteForbiddenError(DataCiteRequestError):
    """ Login problem, dataset belongs to another party or quota exceeded"""
    pass


class DataCiteNotFoundError(DataCiteRequestError):
    """ DOI does not exist in our database """
    pass


class DataCiteGoneError(DataCiteRequestError):
    """ the requested dataset was marked inactive (using DELETE method) """
    pass


class DataCitePreconditionError(DataCiteRequestError):
    """ metadata must be uploaded first """
    pass


#
# Classes
#
class DataCiteRequest(object):
    """
    Helper class to make requests

    @param base_url: Base URL for all requests.
    @type  base_url: str

    @param username: HTTP Basic Authentication Username
    @type  username: str

    @param password: HTTP Basic Authentication Passsword
    @type  password: str

    @param default_params: A key/value-mapping which will be converted into a
                           query string on all requests.
    @type  default_params: dict
    """
    def __init__(self, base_url=None, username=None, password=None, default_params={}):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.default_params = default_params

    def request(self, url, method='GET', body=None, params={}, headers={}):
        """
        Make a request. If the request was successful (i.e no exceptions),
        you can find the HTTP response code in self.code and the response
        body in self.value.

        @param url: Request URL (relative to base_url if set)
        @type  url: str

        @param method: Request method (GET, POST, DELETE) supported
        @type  method: str

        @param body: Request body
        @type  body: str (UTF8 encoded)

        @param params: Request parameters
        @type  params: dict

        @param headers: Request headers
        @type  headers: dict
        """
        self.data = None
        self.code = None

        headers['Authorization'] = 'Basic ' + base64.encodestring(self.username + ':' + self.password)
        if headers['Authorization'][-1] == '\n':
            headers['Authorization'] = headers['Authorization'][:-1]

        if self.default_params:
            params.update(self.default_params)

        if self.base_url:
            url = self.base_url + url

        if method == 'POST':
            if not body and params:
                body = urlencode(params)
            elif params:
                url = "%s?%s" % (url, urlencode(params))
            if body:
                # HTTP client requests must end with double newline (not added
                # by urllib2)
                body += '\r\n\r\n'
                if isinstance(body, unicode):
                    body = body.encode('utf-8')
        else:
            if params:
                url = "%s?%s" % (url, urlencode(params))

        try:
            if HAS_SSL:
                httpsv3_handler = HTTPSHandlerV3()
                #httpsv3_handler.set_http_debuglevel(1)
                opener = urllib2.build_opener(httpsv3_handler)
            else:
                opener = urllib2.build_opener()
            request = urllib2.Request(url, data=body, headers=headers)
            request.get_method = lambda: method
            res = opener.open(request)
            self.code = res.code
            self.data = res.read()
        except urllib2.HTTPError, e:
            self.code = e.code
            self.data = e.msg
        except urllib2.URLError, e:
            raise HttpError(e)

    def get(self, url, params={}, headers={}):
        """ Make a GET request """
        return self.request(url, params=params, headers=headers)

    def post(self, url, body=None, params={}, headers={}):
        """ Make a POST request """
        return self.request(url, method='POST', body=body, params=params, headers=headers)

    def delete(self, url, params={}, headers={}):
        """ Make a DELETE request """
        return self.request(url, method="DELETE", params=params, headers=headers)


class DataCite(object):
    """
    DataCite API wrapper
    """

    def __init__(self, username=None, password=None, url=None, prefix=None, test_mode=None, api_ver="2"):
        """
        Initialize DataCite API. In case parameters are not specified via keyword
        arguments, they will be read from the Invenio configuration.

        @param username: DataCite username (or CFG_DATACITE_USERNAME)
        @type  username: str

        @param password: DataCite password (or CFG_DATACITE_PASSWORD)
        @type  password: str

        @param url: DataCite API base URL (or CFG_DATACITE_URL). Defaults to https://mds.datacite.org/.
        @type  url: str

        @param prefix: DOI prefix (or CFG_DATACITE_DOI_PREFIX). Defaults to 10.5072 (DataCite test prefix).
        @type  prefix: str

        @param test_mode: Set to True to enable test mode (or CFG_DATACITE_TESTMODE). Defaults to False.
        @type  test_mode: boolean

        @param api_ver: DataCite API version. Currently has no effect. Default to 2.
        @type  api_ver: str
        """
        if not HAS_SSL:
            warn("Module ssl not installed. Please install with e.g. 'pip install ssl'. Required for HTTPS connections to DataCite.")

        self.username = username or cfg.get('CFG_DATACITE_USERNAME', '')
        self.password = password or cfg.get('CFG_DATACITE_PASSWORD', '')
        self.prefix = prefix or cfg.get('CFG_DATACITE_DOI_PREFIX', '10.5072')
        self.api_ver = api_ver  # Currently not used

        self.api_url = url or cfg.get('CFG_DATACITE_URL', 'https://mds.datacite.org/')
        if self.api_url[-1] != '/':
            self.api_url = self.api_url + "/"

        if test_mode is not None:
            self.test_mode = test_mode
        else:
            self.test_mode = cfg.get('CFG_DATACITE_TESTMODE', False)

        # If in test mode, set prefix to 10.5072, the default DataCite test
        # prefix.
        if self.test_mode:
            self.prefix = "10.5072"

    def __repr__(self):
        return '<DataCite: %s>' % self.username

    def _request_factory(self):
        """
        Create a new CulRequest object
        """
        params = {}
        if self.test_mode:
            params['testMode'] = '1'

        return DataCiteRequest(
            base_url=self.api_url,
            username=self.username,
            password=self.password,
            default_params=params,
        )

    def doi_get(self, doi):
        """
        Returns the URL where the resource pointed by the DOI is located

        @param doi: DOI name of the resource
        @type  doi: string

        @return: URL matching the DOI
        @type: string
        """

        r = self._request_factory()
        r.get("doi/" + doi)
        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code)

    def doi_post(self, new_doi, location):
        """
        Mint new DOI

        @param new_doi: DOI name for the new resource
        @type  new_doi: string

        @param location: URL where the resource is located
        @type  location: string

        @return: CREATED, HANDLE_ALREADY_EXISTS
        @type: string
        """
        headers = {'Content-Type': 'text/plain', 'Charset': 'UTF-8'}
        # Use \r\n for HTTP client data.
        body = "\r\n".join(["doi=%s" % new_doi, "url=%s" % location])

        r = self._request_factory()
        r.post("doi", body=body, headers=headers)

        if r.code == 201:
            return r.data
        else:
            raise DataCiteError.factory(r.code)

    def metadata_get(self, doi):
        """
        Returns the metadata associated to a DOI name

        @param doi: DOI name of the resource
        @type  doi: string

        @return: metadata xml
        @type: string
        """
        headers = {'Accept': 'application/xml', 'Accept-Encoding': 'UTF-8'}
        r = self._request_factory()
        r.get("metadata/" + doi, headers=headers)

        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code)

    def metadata_post(self, metadata):
        """
        Sends a new metadata set to complete an existing DOI.
        Metadata should follow the DataCite Metadata Schema 2.2
        http://schema.datacite.org/

        @param metadata: XML format of the metadata
        @type  metadata: str

        @return: OK message
        @type: string
        """
        headers = {'Content-Type': 'application/xml', 'Charset': 'UTF-8'}

        r = self._request_factory()
        r.post("metadata", body=metadata, headers=headers)

        if r.code == 201:
            return r.data
        else:
            raise DataCiteError.factory(r.code)

    def metadata_delete(self, doi):
        """
        Mark as 'inactive' the metadata set of a DOI resource

        @param doi: DOI name of the resource
        @type  doi: string

        @return: OK message
        @type: string
        """
        r = self._request_factory()
        r.delete("metadata/" + doi)

        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code)

    def media_get(self, doi):
        """
        This request returns list of pairs of media type and URLs associated
        with a given DOI.

        @param doi: DOI name of the resource
        @type  doi: string

        @return: metadata xml
        @type: string
        """
        r = self._request_factory()
        r.get("media/" + doi)

        if r.code == 200:
            values = {}
            for line in r.data.splitlines():
                mimetype, url = line.split("=", 1)
                values[mimetype] = url
            return values
        else:
            raise DataCiteError.factory(r.code)

    def media_post(self, doi, media):
        """
        POST will add/update media type/urls pairs to a DOI. Standard domain
        restrictions check will be performed.

        @param media: List of (mime-type, URL)-tuples.
        @type  media: list of 2-tuples

        @return: OK message
        @type: string
        """
        headers = {'Content-Type': 'text/plain', 'Charset': 'UTF-8'}
        # Use \r\n for HTTP client data.
        body = "\r\n".join(["%s=%s" % (k, v) for k, v in media.items()])

        r = self._request_factory()
        r.post("media/" + doi, body=body, headers=headers)

        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code)

class DataciteMetadata(object):

    def __init__(self, doi):

        self.url = "http://data.datacite.org/application/x-datacite+xml/"
        self.error = False
        try:
            data = urllib2.urlopen(self.url + doi).read()
        except urllib2.HTTPError:
            self.error = True

        if not self.error:
            # Clean the xml for parsing
            data = re.sub('<\?xml.*\?>', '', data, count=1)

            # Remove the resource tags
            data = re.sub('<resource .*xsd">', '', data)
            self.data = '<?xml version="1.0"?><datacite>' + data[0:len(data) - 11] + '</datacite>'
            self.root = ElementTree.XML(self.data)
            self.xml = XmlDictConfig(self.root)

    def get_creators(self, attribute='creatorName'):
        if 'creators' in self.xml:
            if isinstance(self.xml['creators']['creator'], list):
                return [c[attribute] for c in self.xml['creators']['creator']]
            else:
                return self.xml['creators']['creator'][attribute]

        return None

    def get_titles(self):
        if 'titles' in self.xml:
            return self.xml['titles']['title']
        return None

    def get_publisher(self):
        if 'publisher' in self.xml:
            return self.xml['publisher']
        return None

    def get_dates(self):
        if 'dates' in self.xml:
            if isinstance(self.xml['dates']['date'], dict):
                return self.xml['dates']['date'].values()[0]
            return self.xml['dates']['date']
        return None

    def get_publication_year(self):
        if 'publicationYear' in self.xml:
            return self.xml['publicationYear']
        return None

    def get_language(self):
        if 'language' in self.xml:
            return self.xml['language']
        return None

    def get_related_identifiers(self):
        pass

    def get_description(self, description_type='Abstract'):
        if 'descriptions' in self.xml:
            if isinstance(self.xml['descriptions']['description'], list):
                for description in self.xml['descriptions']['description']:
                    if description_type in description:
                        return description[description_type]
            elif isinstance(self.xml['descriptions']['description'], dict):
                description = self.xml['descriptions']['description']
                if description_type in description:
                    return description[description_type]
                elif len(description) == 1:
                    # return the only description
                    return description.values()[0]

        return None

    def get_rights(self):
        if 'titles' in self.xml:
            return self.xml['rights']
        return None

