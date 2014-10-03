# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

'''Utils for fetching data for ORCID library.'''

from invenio.bibauthorid_backinterface import get_orcid_id_of_author
from invenio.bibauthorid_dbinterface import _get_doi_for_paper, \
    get_all_signatures_of_paper, get_name_by_bibref, \
    get_personid_signature_association_for_paper, \
    get_orcid_id_of_author, get_papers_of_author, get_token, get_all_tokens, \
    delete_token, trigger_aidtoken_change
from invenio.bibauthorid_general_utils import get_doi
from invenio.bibcatalog import BIBCATALOG_SYSTEM
from invenio.bibformat import format_record as bibformat_record
from invenio.bibrecord import record_get_field_value, record_get_field_values, \
    record_get_field_instances
from invenio.config import CFG_SITE_URL
from invenio.dateutils import convert_simple_date_to_array
from invenio.errorlib import get_pretty_traceback
from invenio.orcid_xml_exporter import OrcidXmlExporter
from invenio.search_engine import get_record
from invenio.textutils import encode_for_jinja_and_xml, RE_ALLOWED_XML_1_0_CHARS

from invenio import bibtask

import requests
import re
from requests.exceptions import HTTPError
import sys

try:
    import json
except ImportError:
    import simplejson as json

from invenio.access_control_config import CFG_OAUTH2_CONFIGURATIONS

ORCID_ENDPOINT_PUBLIC = CFG_OAUTH2_CONFIGURATIONS['orcid']['public_url']

ORCID_JSON_TO_XML_EXT_ID = {
    'ARXIV': 'arxiv',
    'DOI': 'doi',
    'ISBN': 'isbn',
    'OTHER_ID': 'other-id'
}

############################### PULLING ########################################

def get_dois_from_orcid_using_pid(pid):

    '''Get dois in case of unknown ORCID.

    @param scope: pid
    @type scope: int

    @return: a pair: ORCID of person indicated by pid and list of his dois
    @rtype: tuple
    '''

    # author should have already an orcid if this method was triggered
    try:
        orcid_id = get_orcid_id_of_author(pid)[0][0]
    except IndexError:
        formatted = get_pretty_traceback()
        BIBCATALOG_SYSTEM.ticket_submit(subject='Wrong response content',
                                        text=formatted)
        orcid_id = None
    return orcid_id, get_dois_from_orcid(orcid_id)

def _read_public_orcid_data(orcid_id):

    '''Get ORCID public profile.

    @param orcid_id: Persons id in xxxx-xxxx-xxxx-xxxx format
    @type orcid_id: str

    @return: the ORCID profile
    @rtype: json dict

    '''

    access_token = _get_access_token_from_orcid('/read-public', \
            extra_params={'grant_type': 'client_credentials'})

    if not access_token:
        return None

     # possible request types: 'orcid-bio', 'orcid-works', 'orcid-profile'
    request_type = 'orcid-profile'
    orcid_response = _get_public_orcids_from_member(orcid_id, access_token,
                                                    request_type)

    if not orcid_response:
        return None

    orcid_profile = json.loads(orcid_response)

    return orcid_profile

def _get_ext_orcids_using_pid(pid):

    '''Get extids in case of unknown ORCID

    @param scope: pid
    @type scope: int

    @return: a dictionary containing all external ids.
    @rtype: tuple
    '''

    # author should have already an orcid if this method was triggered
    try:
        orcid_id = get_orcid_id_of_author(pid)[0][0]
    except IndexError:
        # weird, no orcid id in the database? Let's not do anything...
        orcid_id = None

    return orcid_id, _get_extids_from_orcid(orcid_id)

def _get_extids_from_orcid(orcid_id):

    '''Get all external ids from ORCID database for a given person.

    @param orcid_id: ORCID in format xxxx-xxxx-xxxx-xxxx
    @type orcid_id: str

    @return: a dictionary which contains all external identifiers for given
        person. Identifiers are stored in sets under identifiers names keys.
    @rtype: dictionary

    '''

    orcid_profile = _read_public_orcid_data(orcid_id)

    ext_ids_dict = {
        'DOI' : set(),
        'ARXIV' : set(),
        'ISBN' : set(),
        'OTHER_ID' : set()
    }

    if orcid_profile == None:
        return ext_ids_dict

    try:
        activities = orcid_profile['orcid-profile']['orcid-activities']
        pubs = activities['orcid-works']['orcid-work']
        for pub in pubs:
            try:
                ext_idss = pub['work-external-identifiers']
                ext_ids = ext_idss['work-external-identifier']
                for ext_id_pair in ext_ids:
                    extid_type = ext_id_pair['work-external-identifier-type']
                    value = ext_id_pair['work-external-identifier-id']['value']
                    if extid_type in ext_ids_dict:
                        if extid_type == 'DOI':
                            ext_ids_dict[extid_type].add(get_doi(value))
                        ext_ids_dict[extid_type].add(value)
            except KeyError:
                pass
    except KeyError:
        pass

    return ext_ids_dict

def get_dois_from_orcid(orcid_id):

    '''Get dois in case of know ORCID

    @param scope: orcid_id
    @type scope: string

    @return: dois of a person with ORCID indicated by orcid_id
    @rtype: list
    '''

    orcid_profile = _read_public_orcid_data(orcid_id)

    dois = list()
    if orcid_profile == None:
        return dois

    try:
        activities = orcid_profile['orcid-profile']['orcid-activities']
        pubs = activities['orcid-works']['orcid-work']
        for pub in pubs:
            try:
                ext_ids = pub['work-external-identifiers']
                ext_id_pair = ext_ids['work-external-identifier'][0]
                if ext_id_pair['work-external-identifier-type'] == 'DOI':
                    ext_id = ext_id_pair['work-external-identifier-id']
                    doi = get_doi(ext_id['value'])
                    if doi is not None:
                        dois.append(doi)
            except KeyError:
                pass
    except KeyError:
        pass

    return dois



class OrcidServerError(Exception):
    '''
    Exception raised when the server status is 500 (Internal Server Error).
    '''
    def __str__(self):
        return "Http response code 500. Orcid Internal Server Error."


class OrcidRequestError(Exception):
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
        super(OrcidRequestError, self).__init__(repr(code))
        # TODO: depending on the code we should decide whether to send
        # an email to the system admin or not
        self.code = code
    def __str__(self):
        return "Http response code %s." % repr(self.code)


def _get_access_token_from_orcid(scope, extra_params=None):
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

    payload = {'client_id': CFG_OAUTH2_CONFIGURATIONS['orcid']['consumer_key'],
               'client_secret': \
                    CFG_OAUTH2_CONFIGURATIONS['orcid']['consumer_secret'],
               'scope': scope}

    if extra_params:
        for field, value in extra_params.iteritems():
            payload[field] = value

    request_url = CFG_OAUTH2_CONFIGURATIONS['orcid']['access_token_url']
    headers = {'Accept': 'application/json'}
    response = requests.post(request_url, data=payload, headers=headers)
    code = response.status_code

    res = None
    if code == requests.codes.ok:
        try:
            res = json.loads(response.content)['access_token']
        except KeyError:
            formatted = get_pretty_traceback()
            BIBCATALOG_SYSTEM.ticket_submit(subject='Wrong response content',
                                            text=formatted)
            return None
    return res


def _get_public_orcids_from_public(orcid_id, request_type='orcid-profile',
                                   endpoint=ORCID_ENDPOINT_PUBLIC,
                                   response_format='json'):
    '''
    The API made available to the general public and which can be used without
    any sort of authentication. This API will only return data marked by users
    as “public” and will come with no service level agreement (SLA). The API may
    be throttled at the IP / transaction level in order to discourage
    inadvertent overloading and/or deliberate abuse of the system.

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

    # 'Accept-Charset': 'UTF-8'
    # ATTENTION: it overwrites the response format header
    headers = {'Accept': 'application/orcid+%s' % response_format}
    response = requests.get(request_url, headers=headers)
    code = response.status_code
    res = None
    # response.raise_for_status()
    if code == requests.codes.ok:
        res = response.content
    elif code == 500:
        # raise OrcidServerError()
        res = None
    else:
        # raise OrcidRequestError(code)
        res = None
    return res


def _get_public_orcids_from_member(orcid_id, access_token,
                                   request_type='orcid-profile',
                                   endpoint=ORCID_ENDPOINT_PUBLIC,
                                   response_format='json'):
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
    headers = {'Accept': 'application/orcid+%s' % response_format,
               'Authorization': 'Bearer %s' % access_token}
    # 'Accept-Charset': 'UTF-8'
    # ATTENTION: it overwrites the response format header

    response = requests.get(request_url, headers=headers)
    code = response.status_code
    res = None
    # response.raise_for_status()
    if code == requests.codes.ok:
        res = response.content
    elif code == 500:
        # raise OrcidServerError()
        res = None
    else:
        # raise OrcidRequestError(code)
        res = None

    return res

############################### PUSHING ########################################

class OrcidRecordExisting(Exception):

    '''Indicates that a record is present in ORCID database.'''

    pass

def push_orcid_papers(pid, token):

    '''Pushes papers authored by chosen person.

    Pushes only the papers which were absent previously in ORCID database.

    @param pid: person id of an author.
    @type pid: int
    @param token: the token received from ORCID during authentication step.
    @type token: string
    '''

    return bibtask.task_low_level_submission('orcidpush', 'admin',
                                             '--author_id=' + str(pid),
                                             '--token=' + token,
                                             '-P', '1')

def _orcid_fetch_works(pid):

    '''Get claimed works - only those that are not already put into ORCID.

    @param pid: person id of an author.
    @type pid: int
    @return: a pair: person doid and
        the dictionary with works for OrcidXmlExporter.
    @rtype: tuple (str, dict)
    '''

    doid, existing_papers = _get_ext_orcids_using_pid(pid)
    papers_recs = get_papers_of_author(pid, claimed_only=True)
    orcid_dict = _get_orcid_dictionaries(papers_recs, pid, existing_papers)

    xml_to_push = OrcidXmlExporter.export(orcid_dict, 'works.xml')

    xml_to_push = RE_ALLOWED_XML_1_0_CHARS.sub('', xml_to_push).encode('utf-8')

    return (doid, xml_to_push)


def _orcid_push_with_bibtask():
    '''Push ORCID papers using bibtask scheduling.

    @return: did the task finish successfully
    @rtype: bool
    '''
    pid_tokens = get_all_tokens()
    success = True

    for pid_token in pid_tokens:

        pid = pid_token[0]
        token = pid_token[1]

        if pid_token[2]:
            # pid_token[2] indicates a change in the list of claimed papers
            bibtask.write_message("Fetching works for %s" % (pid,))

            # The order of operations is important here. We need to trigger the
            # record in the database before fetching, as the claims might
            # change when the papers' data is being fetched.
            trigger_aidtoken_change(pid, 1)
            doid, xml_to_push = _orcid_fetch_works(int(pid))

            url = CFG_OAUTH2_CONFIGURATIONS['orcid']['member_url'] + \
                doid + '/orcid-works'

            headers = {'Accept': 'application/vnd.orcid+xml',
                       'Content-Type': 'application/vnd.orcid+xml',
                       'Authorization': 'Bearer ' + token
                       }

            bibtask.write_message("Pushing works for %s. The token is %s" % (
                pid, token))

            response = requests.post(url, xml_to_push, headers=headers)

            code = response.status_code

            if code == 401:
                # The token has expired or the user revoke his token
                delete_token(pid)
                bibtask.write_message("Token deleted for %s" % pid)
                register_exception(subject="The ORCID token expired.")
            elif code == 201:
                trigger_aidtoken_change(pid, 0)
            else:
                try:
                    response.raise_for_status()
                except HTTPError, exc:
                    bibtask.write_message(exc)
                    bibtask.write_message(response.text)
                success = False

    return success


def _get_orcid_dictionaries(papers, personid, old_external_ids):

    '''Returns list of dictionaries which can be used in ORCID library.

    @param papers: list of papers' records ids.
    @type papers: list (tuple(int,))
    @param personid: personid of person who is requesting orcid dictionary of
        his works
    @type personid: int
    @return: a structure which can be passed to ORCID library
    @rtype: list of dictionaries
    '''

    orcid_list = []

    for rec in papers:

        recid = rec[0]

        work_dict = {
            'work_title' : {}
        }

        recstruct = get_record(recid)

        url = CFG_SITE_URL + ('/record/%d' % recid)

        try:
            external_ids = _get_external_ids(recid, url,
                                             recstruct, old_external_ids)
        except OrcidRecordExisting:
            #We will not push this record, skip it.
            continue

        #There always will be some external identifiers.
        work_dict['work_external_identifiers'] = external_ids

        work_dict['work_title']['title'] = \
                encode_for_jinja_and_xml(record_get_field_value(recstruct, '245', '',
                                                      '', 'a'))

        short_description = \
            record_get_field_value(recstruct, '520', '', '', 'a')
        if short_description:
            work_dict['short_description'] = \
                   encode_for_jinja_and_xml(short_description)

        journal_title = record_get_field_value(recstruct, '773', '', '', 'p')
        if journal_title:
            work_dict['journal-title'] = encode_for_jinja_and_xml(journal_title)

        citation = _get_citation(recid)
        if citation:
            work_dict['work_citation'] = citation

        work_dict['work_type'] = _get_work_type(recstruct)

        publication_date = _get_publication_date(recstruct)
        if publication_date:
            work_dict['publication_date'] = publication_date

        work_dict['url'] = url

        work_contributors = _get_work_contributors(recid, personid)
        if len(work_contributors) > 0:
            work_dict['work_contributors'] = work_contributors

        work_source = record_get_field_value(recstruct, '359', '', '', '9')
        if work_source:
            work_dict['work_source']['work-source'] = \
                    encode_for_jinja_and_xml(work_source)

        language = record_get_field_value(recstruct, '041', '', '', 'a')
        if language:
            work_dict['language_code'] = encode_for_jinja_and_xml(language)

        work_dict['visibility'] = 'public'
        orcid_list.append(work_dict)

    bibtask.write_message("I will push "+ str(len(orcid_list)) + \
            " records to ORCID.")

    return orcid_list

def _get_date_from_field_number(recstruct, field, subfield):

    '''Get date dictionary from MARC record.

    The dictionary can have keys 'year', 'month' and 'day'

    @param recstruct: MARC record
    @param field: number of field inside MARC record. The function will extract
                  the date from the field indicated by this field
    @type field: string

    @return: dictionary
    @rtype: dict
    '''

    result = {}

    publication_date = record_get_field_value(recstruct, field, '', '', subfield)
    publication_array = convert_simple_date_to_array(publication_date)
    if len(publication_array) > 0 and \
            re.match(r'[12]\d{3}$', publication_array[0]):
        result['year'] = publication_array[0]
        if len(publication_array) > 1 and \
                re.match(r'[01]\d$', publication_array[1]):
            result['month'] = publication_array[1]
            if len(publication_array) > 2 and \
                    re.match(r'[012]\d{3}$', publication_array[2]):
                result['day'] = publication_array[2]

        return result

    return None


def _get_publication_date(recstruct):

    '''Get work publication date from MARC record.

    @param recstruct: MARC record

    @return: dictionary
    @rtype: dict
    '''

    first_try = _get_date_from_field_number(recstruct, '269', 'c')
    if first_try:
        return first_try

    second_try = _get_date_from_field_number(recstruct, '260', 'c')
    if second_try:
        return second_try

    third_try = _get_date_from_field_number(recstruct, '502', 'd')
    if third_try:
        return third_try

    publication_year = record_get_field_value(recstruct, '773', '', '', 'y')
    if publication_year and re.match(r'[12]\d{3}$', publication_year):
        return {'year' : publication_year}

    return {}

def _get_work_type(recstruct):

    '''Get work type from MARC record.

    @param recstruct: MARC record

    @return: type of given work
    @rtype: str
    '''

    work_type = record_get_field_values(recstruct, '980', '', '', 'a')
    if 'book' in [x.lower() for x in work_type]:
        return 'book'

    work_type_2 = record_get_field_values(recstruct, '502', '', '', 'b')
    if 'phd' in [x.lower() for x in work_type_2]:
        return 'dissertation'

    if 'conferencepaper' in [x.lower() for x in work_type]:
        return 'conference-paper'
    elif 'data' in [x.lower() for x in work_type]:
        return 'dataset'

    published_flag = 'published' in [x.lower() for x in work_type]
    if (published_flag and
            record_get_field_values(recstruct, '773', '', '', 'p')):
        return 'journal-article'

    work_type = record_get_field_instances(recstruct, '035')
    for instance in work_type:
        field_a = False
        field_9 = False
        for tup in instance[0]:
            if tup[0] == '9':
                field_9 = True
            elif tup[0] == 'a':
                field_a = True
        if field_a and field_9 and not published_flag:
            return 'working-paper'

    return 'other'

def _get_citation(recid):

    '''Get citation in BibTeX format.

    Strips down html tags

    @param recid: the id of record
    @type recid: int

    @return: citation in BibTex format
    @rtype: string
    '''

    tex_str = bibformat_record(recid, 'hx')
    bibtex_content = encode_for_jinja_and_xml(tex_str[tex_str.find('@') : \
            tex_str.rfind('}')+1])

    return ('bibtex', bibtex_content)

def _get_external_ids(recid, url, recstruct, old_external_ids):

    '''Get external identifiers used by ORCID.

    Fetches DOI, ISBN, ARXIVID and INSPIREID identifiers.

    @param recid: the id of record
    @type recid: int
    @param url: URL of given paper. It will be used as a spare external id in
            case nothing else is achievable.
    @type url: string
    @param recstruct: the MARC record_get_field_values
    @param old_external_ids: external_ids which are already inside
            ORCID database
    @type old_external_ids: dict

    @return: external ids in form of pairs: name if id, value.
    @rtype: list
    '''

    external_ids = []
    doi = _get_doi_for_paper(recid, recstruct)
    # There are two different fields in MARC records responsiple for ISBN id.
    isbn = record_get_field_value(recstruct, '020', '', '', 'a')
    isbn2 = record_get_field_value(recstruct, '773', '', '', 'z')
    record_ext_ids = record_get_field_instances(recstruct, '037')
    if doi:
        for single_doi in doi:
            if single_doi in old_external_ids['DOI']:
                raise OrcidRecordExisting
            external_ids.append(('doi', encode_for_jinja_and_xml(single_doi)))
    if isbn:
        if isbn in old_external_ids['ISBN']:
            raise OrcidRecordExisting
        external_ids.append(('isbn', encode_for_jinja_and_xml(isbn)))
    if isbn2:
        if isbn2 in old_external_ids['ISBN']:
            raise OrcidRecordExisting
        external_ids.append(('isbn', encode_for_jinja_and_xml(isbn2)))

    for rec in record_ext_ids:
        arxiv = False
        the_id = None
        for field in rec[0]:
            if field[0] == '9' and field[1].lower() == 'arxiv':
                arxiv = True
            elif field[0] == 'a':
                the_id = field[1]
        if arxiv:
            if the_id in old_external_ids['ARXIV']:
                raise OrcidRecordExisting
            external_ids.append(('arxiv', encode_for_jinja_and_xml(the_id)))

    if url in old_external_ids['OTHER_ID']:
        raise OrcidRecordExisting
    if len(external_ids) == 0:
        external_ids.append(('other-id', url))
    return external_ids

def _get_work_contributors(recid, personid):

    '''Get contributors data used by ORCID.

    @param recid: the id of record
    @type recid: int
    @param personid: the id of author
    @type personid: int

    @return: contributors records with fields required by ORCID database.
    @rtype: list
    '''

    work_contributors = []
    signatures = get_all_signatures_of_paper(recid)
    signatures = [([int(y) for y in x['bibref'].split(':')] + \
            [recid]) for x in signatures]
    associations = get_personid_signature_association_for_paper(recid)

    for table, ref, _ in signatures:
        try:
            pid = associations[str(table) + ':' + str(ref)]
        except KeyError:
            pid = None

        if pid == personid:
            #The author himself is not a contributor for his work
            continue

        contributor_dict = {
            'name' : get_name_by_bibref([table, ref]),
            'attributes' : {'role' : 'author'}
        }

        orcid = get_orcid_id_of_author(pid)
        if orcid:
            contributor_dict['orcid'] = orcid[0][0]

        work_contributors.append(contributor_dict)

    return work_contributors


def main():
    '''Daemon responsible for pushing papers to ORCID.'''
    bibtask.task_init(
        authorization_action="orcidpush",
        task_run_fnc=_orcid_push_with_bibtask
    )
