# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

import requests
from invenio.bibauthorid_general_utils import get_doi

try:
    import json
except ImportError:
    import simplejson as json
from invenio.webauthorprofile_config import CFG_WEBAUTHORPROFILE_ORCID_ENDPOINT_PUBLIC as ENDPOINT_PUBLIC


def get_dois_from_orcid(orcid_id):
    access_token = _get_access_token_from_orcid('/read-public', extra_params={'grant_type': 'client_credentials'})

    if not access_token:
        return None

    request_type = 'orcid-profile'   # possible request types: 'orcid-bio', 'orcid-works', 'orcid-profile'
    orcid_response = _get_public_data_from_orcid_member(orcid_id, access_token, request_type)

    if not orcid_response:
        return None

    orcid_profile = json.loads(orcid_response)

    dois = list()
    try:
        for pub in orcid_profile['orcid-profile']['orcid-activities']['orcid-works']['orcid-work']:
            try:
                if pub['work-external-identifiers']['work-external-identifier'][0]['work-external-identifier-type'] == 'DOI':
                    doi = get_doi(pub['work-external-identifiers']['work-external-identifier'][0]['work-external-identifier-id']['value'])
                    if doi is not None:
                        dois.append(doi)
            except KeyError:
                pass
    except KeyError:
        pass

    return dois


class Orcid_server_error(Exception):
    '''
    Exception raised when the server status is 500 (Internal Server Error).
    '''
    def __str__(self):
        return "Http response code 500. Orcid Internal Server Error."


class Orcid_request_error(Exception):
    '''
    Exception raised when the server status is:
    204 No Content
    400 Bad Request
    401 Unauthorized
    403 Forbidden
    404 Not Found
    410 Gone (deleted)
    '''
    def __init__(self, code):
        # TODO: depending on the code we should decide whether to send an email to the system admin
        self.code = code
    def __str__(self):
        return "Http response code %s." % repr(self.code)


def _get_access_token_from_orcid(scope, extra_params=None, response_format='json'):
    '''
    Returns a multi-use access token using the client credentials. With the
    specific access token we can retreive public data of the given scope.

    @param scope: scope
    @type scope: str
    @param extra_data: additional parameters {field: value}
    @type extra_data: dict {str: str}

    @return: access token
    @rtype: str
    '''
    # TODO: when we already have a valid access token return that instead of creating a new one
    from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS

    payload = {'client_id': CFG_OAUTH2_CONFIGURATIONS['orcid']['consumer_key'],
               'client_secret': CFG_OAUTH2_CONFIGURATIONS['orcid']['consumer_secret'],
               'scope': scope }

    if extra_params:
        for field, value in extra_params.iteritems():
            payload[field] = value

    request_url = '%s' % (CFG_OAUTH2_CONFIGURATIONS['orcid']['access_token_url'])
    headers = {'Accept': 'application/json'}
    response = requests.post(request_url, data=payload, headers=headers)
    code = response.status_code
    res = None
    # response.raise_for_status()
    if code == requests.codes.ok:
        try:
            res = json.loads(response.content)['access_token']
        except ValueError:
            #TODO: don't fail silently but gently report an error somehow
            return None
    return res


def _get_public_data_from_orcid_public(orcid_id, request_type='orcid-profile', endpoint=ENDPOINT_PUBLIC, response_format='json'):
    '''
    The API made available to the general public and which can be used without any sort of authentication.
    This API will only return data marked by users as “public” and will come with no service level agreement (SLA).
    The API may be throttled at the IP / transaction level in order to discourage inadvertent overloading and/or
    deliberate abuse of the system.

    @param orcid_id: orcid identifier
    @type orcid_id: str
    @param request_type: type of request
    @type request_type: str
    @param endpoint: domain of the orcid server
    @type endpoint: str
    @param response_format: format of the orcid response
    @type response_format: str

    @return: the specified public orcid data
    @rtype: dict
    '''
    request_url = '%s%s/%s' % (endpoint, orcid_id, request_type)
    headers = {'Accept': 'application/orcid+%s' % response_format}   # 'Accept-Charset': 'UTF-8'   # ATTENTION: it overwrites the response format header
    response = requests.get(request_url, headers=headers)
    code = response.status_code
    res = None
    # response.raise_for_status()
    if code == requests.codes.ok:
        res = response.content
    elif code == 500:
        # raise Orcid_server_error()
        res = None
    else:
        # raise Orcid_request_error(code)
        res = None

    return res


def _get_public_data_from_orcid_member(orcid_id, access_token, request_type='orcid-profile', endpoint=ENDPOINT_PUBLIC, response_format='json'):
    '''
    Returns the public data for the specific request query given an orcid id.

    @param orcid_id: orcid identifier
    @type orcid_id: str
    @param access_token: access token
    @type access_token: str
    @param request_type: type of request
    @type request_type: str
    @param endpoint: domain of the orcid server
    @type endpoint: str
    @param response_format: format of the orcid response
    @type response_format: str

    @return: the specified public orcid data
    @rtype: dict
    '''
    request_url = '%s%s/%s' % (endpoint, orcid_id, request_type)
    headers = {'Accept': 'application/orcid+%s' % response_format, 'Authorization': 'Bearer %s' % access_token}   # 'Accept-Charset': 'UTF-8'   # ATTENTION: it overwrites the response format header
    response = requests.get(request_url, headers=headers)
    code = response.status_code
    res = None
    # response.raise_for_status()
    if code == requests.codes.ok:
        res = response.content
    elif code == 500:
        # raise Orcid_server_error()
        res = None
    else:
        # raise Orcid_request_error(code)
        res = None

    return res
