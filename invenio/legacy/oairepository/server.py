# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014, 2015 CERN.
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

"""Receive OAI-PMH 2.0 requests and responds"""

__revision__ = "$Id$"

from six.moves import cPickle
import os
import re
import time
import tempfile
import sys
import datetime
if sys.hexversion < 0x2050000:
    from glob import glob as iglob
else:
    from glob import iglob
from flask import url_for, abort
from flask_login import current_user
from intbitset import intbitset
from six import iteritems

from invenio.config import \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
     CFG_CACHEDIR, \
     CFG_CERN_SITE, \
     CFG_OAI_DELETED_POLICY, \
     CFG_OAI_EXPIRE, \
     CFG_OAI_FRIENDS, \
     CFG_OAI_IDENTIFY_DESCRIPTION, \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_ID_PREFIX, \
     CFG_OAI_LOAD, \
     CFG_OAI_METADATA_FORMATS, \
     CFG_OAI_PREVIOUS_SET_FIELD, \
     CFG_OAI_PROVENANCE_ALTERED_SUBFIELD, \
     CFG_OAI_PROVENANCE_BASEURL_SUBFIELD, \
     CFG_OAI_PROVENANCE_DATESTAMP_SUBFIELD, \
     CFG_OAI_PROVENANCE_HARVESTDATE_SUBFIELD, \
     CFG_OAI_PROVENANCE_METADATANAMESPACE_SUBFIELD, \
     CFG_OAI_PROVENANCE_ORIGINDESCRIPTION_SUBFIELD, \
     CFG_OAI_SAMPLE_IDENTIFIER, \
     CFG_OAI_SET_FIELD, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL, \
     CFG_WEBSTYLE_HTTP_USE_COMPRESSION

from invenio.base.globals import cfg
from invenio.ext.logging import register_exception
from invenio.legacy.bibrecord import record_get_field_instances
from invenio.legacy.dbquery import run_sql, wash_table_column_name
from invenio.legacy.oairepository.config import CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC
from invenio.legacy.search_engine import record_exists, get_all_restricted_recids, \
    search_unit_in_bibxxx, get_record
from invenio.modules.formatter import format_record
from invenio.modules.search.api import Query
from invenio.utils.date import localtime_to_utc, utc_to_localtime
from invenio.utils.html import X, EscapedXMLString

CFG_VERBS = {
    'GetRecord'          : ['identifier', 'metadataPrefix'],
    'Identify'           : [],
    'ListIdentifiers'    : ['from', 'until',
                            'metadataPrefix',
                            'set',
                            'resumptionToken'],
    'ListMetadataFormats': ['identifier'],
    'ListRecords'        : ['from', 'until',
                            'metadataPrefix',
                            'set',
                            'resumptionToken'],
    'ListSets'           : ['resumptionToken']
    }

CFG_ERRORS = {
    "badArgument": "The request includes illegal arguments, is missing required arguments, includes a repeated argument, or values for arguments have an illegal syntax:",
    "badResumptionToken": "The value of the resumptionToken argument is invalid or expired:",
    "badVerb": "Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb argument is repeated:",
    "cannotDisseminateFormat": "The metadata format identified by the value given for the metadataPrefix argument is not supported by the item or by the repository:",
    "idDoesNotExist": "The value of the identifier argument is unknown or illegal in this repository:",
    "noRecordsMatch": "The combination of the values of the from, until, set and metadataPrefix arguments results in an empty list:",
    "noMetadataFormats": "There are no metadata formats available for the specified item:",
    "noSetHierarchy": "The repository does not support sets:"
}

CFG_MIN_DATE = "1970-01-01T00:00:00Z"
CFG_MAX_DATE = "9999-12-31T23:59:59Z"


def get_all_field_values(tag):
    """
    Return all existing values stored for a given tag.
    @param tag: the full tag, e.g. 909C0b
    @type tag: string
    @return: the list of values
    @rtype: list of strings
    """
    table = 'bib%02dx' % int(tag[:2])
    return [row[0] for row in run_sql("SELECT DISTINCT(value) FROM %s WHERE tag=%%s" % table, (tag, ))]


def oai_error(argd, errors):
    """
    Return a well-formatted OAI-PMH error
    """
    out = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
         http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">"""
    out += X.responseDate()(get_utc_now())
    for error_code, error_msg in errors:
        assert(error_code in CFG_ERRORS)
        if error_code in ("badArgument", "badVerb"):
            out += X.request()(oai_get_request_url())
            break
    else:
        ## There are no badArgument or badVerb errors so we can
        ## return the whole request information
        out += X.request(**argd)(oai_get_request_url())
    for error_code, error_msg in errors:
        if error_msg is None:
            error_msg = CFG_ERRORS[error_code]
        else:
            error_msg = "%s %s" % (CFG_ERRORS[error_code], error_msg)
        out += X.error(code=error_code)(error_msg)
    out += "</OAI-PMH>"
    return out

def oai_header(argd, verb):
    """
    Return OAI header
    """

    out = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + "\n"
    out += "<?xml-stylesheet type=\"text/xsl\" href=\"%s\" ?>\n" % (
        url_for('oairepository.static',
                filename='xsl/oairepository/oai2.xsl.v1.0'))
    out += "<OAI-PMH xmlns=\"http://www.openarchives.org/OAI/2.0/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd\">\n"

    #out += "<responseDate>%s</responseDate>" % get_utc_now()
    out += X.responseDate()(get_utc_now())

    if verb:
        out += X.request(**argd)(oai_get_request_url())
        out += "<%s>\n" % verb
    else:
        out += X.request()(oai_get_request_url())

    return out

def oai_footer(verb):
    """
    @return: the OAI footer.
    """
    out = ""
    if verb:
        out += "</%s>\n" % (verb)
    out += "</OAI-PMH>\n"
    return out

def get_field(recid, field):
    """
    Gets list of field 'field' for the record with 'recid' system number.
    """

    digit = field[0:2]

    bibbx = "bib%sx" % digit
    bibx  = "bibrec_bib%sx" % digit
    query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec=%%s AND bx.id=bibx.id_bibxxx AND bx.tag=%%s" % (wash_table_column_name(bibbx), wash_table_column_name(bibx))

    return [row[0] for row in run_sql(query, (recid, field))]

def get_modification_date(recid):
    """Returns the date of last modification for the record 'recid'.
    Return empty string if no record or modification date in UTC.
    """
    out = ""
    res = run_sql("SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (recid,), 1)
    if res and res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_earliest_datestamp():
    """Get earliest datestamp in the database
    Return empty string if no records or earliest datestamp in UTC.
    """
    out = CFG_MIN_DATE
    res = run_sql("SELECT DATE_FORMAT(MIN(creation_date),'%Y-%m-%d %H:%i:%s') FROM bibrec", n=1)
    if res and res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_latest_datestamp():
    """Get latest datestamp in the database
    Return empty string if no records or latest datestamp in UTC.
    """
    out = CFG_MAX_DATE
    res = run_sql("SELECT DATE_FORMAT(MAX(modification_date),'%Y-%m-%d %H:%i:%s') FROM bibrec", n=1)
    if res and res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def check_date(date):
    """Check if given date has a correct format, complying to "Complete date" or
    "Complete date plus hours, minutes and seconds" formats defined in ISO8601."""

    if(re.match("\d\d\d\d-\d\d-\d\d(T\d\d:\d\d:\d\dZ)?\Z", date) is not None):
        return date
    else:
        return ""

def normalize_date(date, dtime="T00:00:00Z"):
    """
    Normalize the given date to the
    "Complete date plus hours, minutes and seconds" format defined in ISO8601
    (If "hours, minutes and seconds" part is missing, append 'dtime' to date).
    'date' must be checked before with check_date(..).

    Returns empty string if cannot be normalized
    """
    if len(date) == 10:
        date = date + dtime
    elif len(date) != 20:
        date = ""

    return date

def get_record_provenance(recid):
    """
    Return the provenance XML representation of a record, suitable to be put
    in the about tag.
    """
    record = get_record(recid)
    provenances = record_get_field_instances(record, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4])
    out = ""
    for provenance in provenances:
        base_url = identifier = datestamp = metadata_namespace = origin_description = harvest_date = altered = ""
        for (code, value) in provenance[0]:
            if code == CFG_OAI_PROVENANCE_BASEURL_SUBFIELD:
                base_url = value
            elif code == CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5]:
                identifier = value
            elif code == CFG_OAI_PROVENANCE_DATESTAMP_SUBFIELD:
                datestamp = value
            elif code == CFG_OAI_PROVENANCE_METADATANAMESPACE_SUBFIELD:
                metadata_namespace = value
            elif code == CFG_OAI_PROVENANCE_ORIGINDESCRIPTION_SUBFIELD:
                origin_description = value
            elif code == CFG_OAI_PROVENANCE_HARVESTDATE_SUBFIELD:
                harvest_date = value
            elif code == CFG_OAI_PROVENANCE_ALTERED_SUBFIELD:
                altered = value
        if base_url:
            out += """<provenance xmlns="http://www.openarchives.org/OAI/2.0/provenance" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/provenance http://www.openarchives.org/OAI/2.0/provenance.xsd">"""
            out += X.originDescription(harvestDate=harvest_date, altered=altered)(
                X.baseURL()(base_url),
                X.identifier()(identifier),
                X.datestamp()(datestamp),
                X.metadataNamespace()(metadata_namespace),
                origin_description and X.originDescription(origin_description) or '' ## This is already XML
            )
            out += """</provenance>"""
    return out

def get_record_rights(dummy):
    """
    Return the record rights parts, suitable to be put in the about tag.
    """
    return ""
    ## FIXME: This need to be thought in a good way. What shall we really
    ## put in the rights parts?
    #record = get_record(recid)
    #rights = record_get_field_instances(record, CFG_OAI_RIGHTS_FIELD[:3], CFG_OAI_RIGHTS_FIELD[3], CFG_OAI_RIGHTS_FIELD[4])
    #license = record_get_field_instances(record, CFG_OAI_LICENSE_FIELD[:3], CFG_OAI_LICENSE_FIELD[3], CFG_OAI_LICENSE_FIELD[4])

    #holder = date = rights_uri = contact = statement = terms = publisher = license_uri = ''
    #if rights:
        #for code, value in rights[0][0]:
            #if code == CFG_OAI_RIGHTS_HOLDER_SUBFIELD:
                #holder = value
            #elif code == CFG_OAI_RIGHTS_DATE_SUBFIELD:
                #date = value
            #elif code == CFG_OAI_RIGHTS_URI_SUBFIELD:
                #rights_uri = value
            #elif code == CFG_OAI_RIGHTS_CONTACT_SUBFIELD:
                #contact = value
            #elif CFG_OAI_RIGHTS_STATEMENT_SUBFIELD:
                #statement = value
    #if license:
        #for code, value in license[0][0]:
            #if code == CFG_OAI_LICENSE_TERMS_SUBFIELD:
                #terms = value
            #elif code == CFG_OAI_LICENSE_PUBLISHER_SUBFIELD:
                #publisher = value
            #elif code == CFG_OAI_LICENSE_URI_SUBFIELD:
                #license_uri = value

def print_record(recid, prefix='marcxml', verb='ListRecords', set_spec=None, set_last_updated=None):
    """Prints record 'recid' formatted according to 'prefix'.

    - if record does not exist, return nothing.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is
      'transient' or 'deleted', then return only header, with status
      'deleted'.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is 'no',
      then return nothing.

    """

    record_exists_result = record_exists(recid) == 1
    if record_exists_result:
        sets = get_field(recid, CFG_OAI_SET_FIELD)
        if set_spec is not None and not set_spec in sets and not [set_ for set_ in sets if set_.startswith("%s:" % set_spec)]:
            ## the record is not in the requested set, and is not
            ## in any subset
            record_exists_result = False

    if record_exists_result:
        status = None
    else:
        status = 'deleted'

    if not record_exists_result and CFG_OAI_DELETED_POLICY not in ('persistent', 'transient'):
        return ""

    idents = get_field(recid, CFG_OAI_ID_FIELD)
    if not idents:
        return ""
    ## FIXME: Move these checks in a bibtask
    #try:
        #assert idents, "No OAI ID for record %s, please do your checks!" % recid
    #except AssertionError as err:
        #register_exception(alert_admin=True)
        #return ""
    #try:
        #assert len(idents) == 1, "More than OAI ID found for recid %s. Considering only the first one, but please do your checks: %s" % (recid, idents)
    #except AssertionError as err:
        #register_exception(alert_admin=True)
    ident = idents[0]

    header_body = EscapedXMLString('')
    header_body += X.identifier()(ident)
    if set_last_updated:
        header_body += X.datestamp()(max(get_modification_date(recid), set_last_updated))
    else:
        header_body += X.datestamp()(get_modification_date(recid))
    for set_spec in get_field(recid, CFG_OAI_SET_FIELD):
        if set_spec and set_spec != CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC:
            # Print only if field not empty
            header_body += X.setSpec()(set_spec)

    header = X.header(status=status)(header_body)

    if verb == 'ListIdentifiers':
        return header
    else:
        if record_exists_result:
            metadata_body = format_record(recid, CFG_OAI_METADATA_FORMATS[prefix][0])
            metadata = X.metadata(body=metadata_body)
            provenance_body = get_record_provenance(recid)
            if provenance_body:
                provenance = X.about(body=provenance_body)
            else:
                provenance = ''
            rights_body = get_record_rights(recid)
            if rights_body:
                rights = X.about(body=rights_body)
            else:
                rights = ''
        else:
            metadata = ''
            provenance = ''
            rights = ''
        return X.record()(header, metadata, provenance, rights)

def oai_list_metadata_formats(argd):
    """Generates response to oai_list_metadata_formats verb."""

    if argd.get('identifier'):
        recid = oai_get_recid(argd['identifier'])
        _record_exists = record_exists(recid)
        if _record_exists != 1 and (_record_exists != -1 or CFG_OAI_DELETED_POLICY == "no"):
            return oai_error(argd, [("idDoesNotExist", "invalid record Identifier: %s" % argd['identifier'])])

    out = ""
    for prefix, (dummy, schema, namespace) in CFG_OAI_METADATA_FORMATS.items():
        out += X.metadataFormat()(
            X.metadataPrefix(prefix),
            X.schema(schema),
            X.metadataNamespace(namespace)
        )

    return oai_header(argd, "ListMetadataFormats") + out + oai_footer("ListMetadataFormats")

def oai_list_records_or_identifiers(req, argd):
    """Generates response to oai_list_records verb."""

    verb = argd['verb']
    resumption_token_was_specified = False

    # check if the resumption_token did not expire
    if argd.get('resumptionToken'):
        resumption_token_was_specified = True
        try:
            cache = oai_cache_load(argd['resumptionToken'])
            last_recid = cache['last_recid']
            argd = cache['argd']
            complete_list = cache['complete_list']
            complete_list = filter_out_based_on_date_range(complete_list, argd.get('from', ''), argd.get('until', ''))
        except Exception, e:
            # Ignore cache not found errors
            if not isinstance(e, IOError) or e.errno != 2:
                register_exception(alert_admin=True)
            req.write(oai_error(argd, [("badResumptionToken", "ResumptionToken expired or invalid: %s" % argd['resumptionToken'])]))
            return
    else:
        last_recid = 0
        complete_list = oai_get_recid_list(argd.get('set', ""), argd.get('from', ""), argd.get('until', ""))

        if not complete_list: # noRecordsMatch error
            req.write(oai_error(argd, [("noRecordsMatch", "no records correspond to the request")]))
            return

    cursor = 0
    for cursor, recid in enumerate(complete_list):
        ## Let's fast-forward the cursor to point after the last recid that was
        ## disseminated successfully
        if recid > last_recid:
            break

    set_last_updated = get_set_last_update(argd.get('set', ""))

    req.write(oai_header(argd, verb))
    for recid in list(complete_list)[cursor:cursor+CFG_OAI_LOAD]:
        req.write(print_record(recid, argd['metadataPrefix'], verb=verb, set_spec=argd.get('set'), set_last_updated=set_last_updated))

    if list(complete_list)[cursor+CFG_OAI_LOAD:]:
        resumption_token = oai_generate_resumption_token(argd.get('set', ''))
        cache = {
            'argd': argd,
            'last_recid': recid,
            # FIXME introduce IP check if you use fireroles for guests
            'id_user': current_user.get_id(),
            'complete_list': complete_list.fastdump(),
        }
        oai_cache_dump(resumption_token, cache)
        expdate = oai_get_response_date(CFG_OAI_EXPIRE)
        req.write(X.resumptionToken(expirationDate=expdate, cursor=cursor, completeListSize=len(complete_list))(resumption_token))
    elif resumption_token_was_specified:
        ## Since a resumptionToken was used we shall put a last empty resumptionToken
        req.write(X.resumptionToken(cursor=cursor, completeListSize=len(complete_list))(""))
    req.write(oai_footer(verb))
    oai_cache_gc()

def oai_list_sets(argd):
    """
    Lists available sets for OAI metadata harvesting.
    """

    out = ""

    # note: no flow control in ListSets
    sets = get_all_sets().values()
    if not sets:
        return oai_error(argd, [("noSetHierarchy", "No sets have been configured for this repository")])
    for set_ in sets:
        out += "  <set>\n"
        out += X.setSpec()(set_[0]) + X.setName()(set_[1])
        if set_[2]:
            out += X.setDescription()(set_[2])
        out = out + "   </set>\n"

    return oai_header(argd, "ListSets") + out + oai_footer("ListSets")


def oai_get_record(argd):
    """Returns record 'identifier' according to 'metadataPrefix' format for OAI metadata harvesting.

    - if record does not exist, return oai_error 'idDoesNotExist'.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is
      'transient' or 'deleted', then return only header, with status
      'deleted'.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is 'no',
      then return oai_error 'idDoesNotExist'.
    """

    recid = oai_get_recid(argd['identifier'])
    _record_exists = record_exists(recid)
    if _record_exists == 1 or \
           (_record_exists == -1 and CFG_OAI_DELETED_POLICY != 'no'):
        out = print_record(recid, argd['metadataPrefix'], _record_exists)
        out = oai_header(argd, "GetRecord") + out + oai_footer("GetRecord")
    else:
        return oai_error(argd, [("idDoesNotExist", "invalid record Identifier: %s" % argd['identifier'])])
    return out



def oai_identify(argd):
    """Generates a response to oai_identify verb.

     script_url - *str* URL of the script used to access the
                  service. This is made necessary since the gateway
                  can be accessed either via /oai2d or /oai2d/ (or for
                  backward compatibility: oai2d.py or oai2d.py/), and
                  that the base URL must be returned in the Identify
                  response
    """

    out = X.repositoryName()(CFG_SITE_NAME)
    out += X.baseURL()(CFG_SITE_URL + '/oai2d')
    out += X.protocolVersion()("2.0")
    out += X.adminEmail()(CFG_SITE_SUPPORT_EMAIL)
    out += X.earliestDatestamp()(get_earliest_datestamp())
    out += X.deletedRecord()(CFG_OAI_DELETED_POLICY)
    out += X.granularity()("YYYY-MM-DDThh:mm:ssZ")
    if CFG_WEBSTYLE_HTTP_USE_COMPRESSION:
        out += X.compression()('deflate')
    out += X.description("""<oai-identifier xmlns="http://www.openarchives.org/OAI/2.0/oai-identifier"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai-identifier
                                       http://www.openarchives.org/OAI/2.0/oai-identifier.xsd">""" +
                X.scheme()("oai") +
                X.repositoryIdentifier()(CFG_OAI_ID_PREFIX) +
                X.delimiter()(":") +
                X.sampleIdentifier()(CFG_OAI_SAMPLE_IDENTIFIER) +
                """</oai-identifier>""")
    out += CFG_OAI_IDENTIFY_DESCRIPTION % {'CFG_SITE_URL': EscapedXMLString(CFG_SITE_URL)}
    if CFG_OAI_FRIENDS:
        friends = """<friends xmlns="http://www.openarchives.org/OAI/2.0/friends/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/friends/
      http://www.openarchives.org/OAI/2.0/friends.xsd">"""
        for baseurl in CFG_OAI_FRIENDS:
            friends += X.baseURL()(baseurl)
        friends += """</friends>"""
        out += X.description(friends)

    out = oai_header(argd, "Identify") + out + oai_footer("Identify")

    return out

def get_utc_now():
    """
    Return current UTC time in the OAI-PMH format.
    """
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def oai_build_request_element(argd=None):
    """
    Build the request tag.
    """
    if argd is None:
        argd = {}
    return X.responseDate()(get_utc_now()) + X.request(**argd)("%s/oai2d" % CFG_SITE_URL)

def oai_get_request_url():
    """Generates requesturl tag for OAI."""
    requesturl = CFG_SITE_URL + "/oai2d"
    return requesturl

def oai_get_response_date(delay=0):
    """Generates responseDate tag for OAI."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + delay))

def oai_get_recid(identifier):
    """Returns the recid corresponding to the OAI identifier. Prefer a non deleted
    record if multiple recids matches but some of them are deleted (e.g. in
    case of merging). Returns None if no record matches."""
    if identifier:
        recids = Query('{f}:"{p}"'.format(
            f=CFG_OAI_ID_FIELD, p=identifier)
        ).search()
        if recids:
            for recid in recids:
                if record_exists(recid) > 0:
                    return recid
    return None


def get_set_last_update(set_spec=""):
    """
    Returns the last_update of a given set (or of all sets) in UTC
    """
    if set_spec:
        last_update = run_sql("SELECT DATE_FORMAT(MAX(last_updated),'%%Y-%%m-%%d %%H:%%i:%%s') FROM oaiREPOSITORY WHERE setSpec=%s", (set_spec, ))[0][0]
    else:
        last_update = run_sql("SELECT DATE_FORMAT(MAX(last_updated),'%Y-%m-%d %H:%i:%s') FROM oaiREPOSITORY")[0][0]
    if last_update:
        return localtime_to_utc(last_update)
    else:
        return None


def filter_out_based_on_date_range(recids, fromdate="", untildate="", set_spec=None):
    """ Filter out recids based on date range."""
    if fromdate:
        fromdate = normalize_date(fromdate, "T00:00:00Z")
    else:
        fromdate = get_earliest_datestamp()
    fromdate = utc_to_localtime(fromdate)

    if untildate:
        untildate = normalize_date(untildate, "T23:59:59Z")
    else:
        untildate = get_latest_datestamp()
    untildate = utc_to_localtime(untildate)

    if set_spec is not None: ## either it has a value or it empty, thus meaning all records
        last_updated = get_set_last_update(set_spec)
        if last_updated is not None:
            last_updated = utc_to_localtime(last_updated)
            if last_updated > fromdate:
                fromdate = utc_to_localtime(get_earliest_datestamp())

    recids = intbitset(recids) ## Let's clone :-)

    if fromdate and untildate:
        recids &= intbitset(run_sql("SELECT id FROM bibrec WHERE modification_date BETWEEN %s AND %s", (fromdate, untildate)))
    elif fromdate:
        recids &= intbitset(run_sql("SELECT id FROM bibrec WHERE modification_date >= %s", (fromdate, )))
    elif untildate:
        recids &= intbitset(run_sql("SELECT id FROM bibrec WHERE modification_date <= %s", (untildate, )))

    if cfg.get('CFG_OAI_FILTER_RESTRICTED_RECORDS', True):
        recids = recids - get_all_restricted_recids()

    return recids

def oai_get_recid_list(set_spec="", fromdate="", untildate=""):
    """
    Returns list of recids for the OAI set 'set', modified from 'fromdate' until 'untildate'.
    """
    ret = intbitset()
    if not set_spec:
        ret |= search_unit_in_bibxxx(p='*', f=CFG_OAI_SET_FIELD, m='e')
        if CFG_OAI_DELETED_POLICY != 'no':
            ret |= search_unit_in_bibxxx(p='*', f=CFG_OAI_PREVIOUS_SET_FIELD, m='e')
    else:
        ret |= search_unit_in_bibxxx(p=set_spec, f=CFG_OAI_SET_FIELD, m='e')
        ret |= search_unit_in_bibxxx(p='%s:*' % set_spec, f=CFG_OAI_SET_FIELD, m='e')
        if CFG_OAI_DELETED_POLICY != 'no':
            ret |= search_unit_in_bibxxx(p=set_spec, f=CFG_OAI_PREVIOUS_SET_FIELD, m='e')
            ret |= search_unit_in_bibxxx(p='%s:*' % set_spec, f=CFG_OAI_PREVIOUS_SET_FIELD, m='e')
    if CFG_OAI_DELETED_POLICY == 'no':
        ret -= search_unit_in_bibxxx(p='DELETED', f='980__%', m='e')
        if CFG_CERN_SITE:
            ret -= search_unit_in_bibxxx(p='DUMMY', f='980__%', m='e')
    return filter_out_based_on_date_range(ret, fromdate, untildate, set_spec)

def oai_generate_resumption_token(set_spec):
    """Generates unique ID for resumption token management."""
    fd, name = tempfile.mkstemp(dir=os.path.join(CFG_CACHEDIR, 'RTdata'), prefix='%s___' % set_spec)
    os.close(fd)
    return os.path.basename(name)

def oai_delete_resumption_tokens_for_set(set_spec):
    """
    In case a set is modified by the admin interface, this will delete
    any resumption token that is now invalid.
    """
    aset = set_spec
    while aset:
        for name in iglob(os.path.join(CFG_CACHEDIR, 'RTdata', '%s___*' % set_spec)):
            os.remove(name)
        aset = aset.rsplit(":", 1)[0]
    for name in iglob(os.path.join(CFG_CACHEDIR, 'RTdata', '___*')):
        os.remove(name)

def oai_cache_dump(resumption_token, cache):
    """
    Given a resumption_token and the cache, stores the cache.
    """
    cPickle.dump(cache, open(os.path.join(CFG_CACHEDIR, 'RTdata', resumption_token), 'w'), -1)


def oai_cache_load(resumption_token):
    """Restore the cache from the resumption_token."""
    fullpath = os.path.join(CFG_CACHEDIR, 'RTdata', resumption_token)
    if os.path.dirname(os.path.abspath(fullpath)) != os.path.abspath(
            os.path.join(CFG_CACHEDIR, 'RTdata')):
        raise ValueError("Invalid path")
    cache = cPickle.load(open(fullpath))

    if cache.get('id_user', 0) == current_user.get_id():
        return cache
    abort(401)


def oai_cache_gc():
    """
    OAI Cache Garbage Collector.
    """
    cache_dir = os.path.join(CFG_CACHEDIR, 'RTdata')

    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    for file_ in os.listdir(cache_dir):
        filename = os.path.join(cache_dir, file_)
        # cache entry expires when not modified during a specified period of time
        if ((time.time() - os.path.getmtime(filename)) > CFG_OAI_EXPIRE):
            try:
                os.remove(filename)
            except OSError as e:
                # Most probably the cache was already deleted
                pass

def get_all_sets():
    """
    Return all the sets.
    """
    res = run_sql("SELECT setSpec, setName, setDescription FROM oaiREPOSITORY")
    ret = {}
    for row in res:
        ret[row[0]] = row

    ## Let's expand with all the set that exist in the DB
    for a_set in get_all_field_values(CFG_OAI_SET_FIELD):
        if a_set not in ret:
            ret[a_set] = (a_set, a_set, '')

    ## Let's expand with all the supersets
    for a_set in ret.keys():
        while ':' in a_set:
            try:
                a_set = a_set.rsplit(":", 1)[0]
            except AttributeError:
                a_set = ':'.join(a_set.split(":")[:-1])
            if a_set not in ret:
                ret[a_set] = (a_set, a_set, '')

    if CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC in ret:
        ## Let's remove the special global set
        del ret[CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC]

    if '' in ret:
        ## '' is not a valid setSpec but might be in the MARC
        del ret['']

    return ret

def check_argd(argd):
    """
    Check OAI arguments
    Also transform them from lists to strings.
    """
    errors = []

    ## no several times the same argument
    bad_arguments_error = False
    for param, value in iteritems(argd):
        if len(value) > 1 and not bad_arguments_error:
            errors.append(("badArgument", "More than one value specified for the %s argument: %s" % (param, value)))
            bad_arguments_error = True ## This is needed only once
        if len(value) > 0:
            argd[param] = value[0]
        else:
            argd[param] = ''

    ## principal argument required
    if argd['verb'] not in CFG_VERBS:
        errors.append(("badVerb", "Illegal OAI verb: %s" % argd['verb']))

    ## defined argd
    for param in argd.keys():
        if not param in CFG_VERBS.get(argd['verb'], []) and param != 'verb' \
               and not bad_arguments_error:
            errors.append(("badArgument", "The request includes illegal arguments for the given verb: %s" % param))
            bad_arguments_error = True
            break # Indicate only once

    ## resumptionToken exclusive
    if argd.get('resumptionToken', '') != "" and \
           len(argd.keys()) != 2 and not bad_arguments_error:
        errors.append(("badArgument", "The resumptionToken was specified together with other arguments"))
        bad_arguments_error = True

    if argd.get('resumptionToken', None) == '':
        errors.append(("badResumptionToken", "ResumptionToken invalid: %s" % argd.get('resumptionToken', None)))

    ## datestamp formats
    if 'from' in argd and \
           'from' in CFG_VERBS.get(argd['verb'], []):
        from_length = len(argd['from'])
        if check_date(argd['from']) == "":
            errors.append(("badArgument", "Bad datestamp format in from: %s" % argd['from']))
    else:
        from_length = 0

    if 'until' in argd and \
           'until' in CFG_VERBS.get(argd['verb'], []):
        until_length = len(argd['until'])
        if check_date(argd['until']) == "":
            errors.append(("badArgument", "Bad datestamp format in until: %s" % argd['until']))
    else:
        until_length = 0

    if from_length != 0:
        if until_length != 0:
            if from_length != until_length:
                errors.append(("badArgument", "From and until have two different formats: %s Vs. %s" % (from_length, until_length)))

    if 'from' in argd and 'until' in argd \
           and argd['from'] > argd['until'] and \
           'from' in CFG_VERBS.get(argd['verb'], []) and \
           'until' in CFG_VERBS.get(argd['verb'], []):
        errors.append(("badArgument", "from argument comes after until argument: %s > %s" % (argd['from'], argd['until'])))

    ## Identify exclusive
    if argd['verb'] == "Identify" and \
           len(argd.keys()) != 1:
        if not bad_arguments_error: # Do not repeat this error
            errors.append(("badArgument", "The request includes illegal arguments"))
            bad_arguments_error = True

    ## parameters for GetRecord
    if argd['verb'] == "GetRecord" and \
           'identifier' not in argd:
        errors.append(("badArgument", "Record identifier missing"))

    if argd['verb'] == "GetRecord" and \
           'metadataPrefix' not in argd:
        errors.append(("badArgument", "Missing metadataPrefix"))

    ## parameters for ListRecords and ListIdentifiers
    if (argd['verb'] == "ListRecords" or argd['verb'] == "ListIdentifiers") and \
           ('resumptionToken' not in argd and 'metadataPrefix' not in argd):
        errors.append(("badArgument", "Missing metadataPrefix"))

    ## Metadata prefix defined and valid
    if 'metadataPrefix' in argd and \
           not argd['metadataPrefix'] in CFG_OAI_METADATA_FORMATS:
        errors.append(("cannotDisseminateFormat", "Chosen format is not supported. Valid formats are: %s" % ', '.join(CFG_OAI_METADATA_FORMATS.keys())))

    return errors

def oai_profile():
    """
    Runs a benchmark
    """
    from six import StringIO
    oai_list_records_or_identifiers(StringIO(), argd={"metadataPrefix": "oai_dc", "verb": "ListRecords"})
    oai_list_records_or_identifiers(StringIO(), argd={"metadataPrefix": "marcxml", "verb" :"ListRecords"})
    oai_list_records_or_identifiers(StringIO(), argd={"metadataPrefix": "oai_dc", "verb": "ListIdentifiers"})
    return

if __name__ == "__main__":
    import profile
    import pstats
    profile.run('oai_profile()', "oai_profile")
    p = pstats.Stats("oai_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()
