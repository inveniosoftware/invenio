## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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

"""Receive OAI-PMH 2.0 requests and responds"""

__revision__ = "$Id$"

import cPickle
import os
import re
import cgi
import urllib
import time
import sys
if sys.hexversion < 0x2060000:
    from md5 import md5
else:
    from hashlib import md5

from invenio.config import \
     CFG_OAI_DELETED_POLICY, \
     CFG_OAI_EXPIRE, \
     CFG_OAI_IDENTIFY_DESCRIPTION, \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_LOAD, \
     CFG_OAI_SET_FIELD, \
     CFG_CACHEDIR, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL

from invenio.intbitset import intbitset
from invenio.dbquery import run_sql
from invenio.search_engine import record_exists, perform_request_search, \
    get_all_restricted_recids
from invenio.bibformat_dblayer import get_preformatted_record
from invenio.bibformat import format_record
from invenio.textutils import encode_for_xml

verbs = {
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
params = {
    "verb" : ["Identify","ListIdentifiers","ListSets","ListMetadataFormats","ListRecords","GetRecord"],
    "metadataPrefix" : ["oai_dc","marcxml"],
    "from" :[""],
    "until":[""],
    "set" :[""],
    "identifier": [""]
}

def escape_space(strxml):
    "Encode special chars in string for URL-compliancy."

    strxml = strxml.replace(' ', '%20')
    return strxml

def encode_for_url(strxml):
    "Encode special chars in string for URL-compliancy."

    strxml = strxml.replace('%', '%25')
    strxml = strxml.replace(' ', '%20')
    strxml = strxml.replace('?', '%3F')
    strxml = strxml.replace('#', '%23')
    strxml = strxml.replace('=', '%3D')
    strxml = strxml.replace('&', '%26')
    strxml = strxml.replace('/', '%2F')
    strxml = strxml.replace(':', '%3A')
    strxml = strxml.replace(';', '%3B')
    strxml = strxml.replace('+', '%2B')

    return strxml

def oai_header(args, verb):
    "Print OAI header"

    out = ""

    out = out + "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + "\n"
    out = out + "<OAI-PMH xmlns=\"http://www.openarchives.org/OAI/2.0/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd\">\n"

    out = out + " <responseDate>" + oaigetresponsedate() + "</responseDate>\n"

    if verb:
        out = out + " <request verb=\"%s\">%s</request>\n" % (verb, oaigetrequesturl(args))
        out = out + " <%s>\n" % verb
    else:
        out = out + " <request>%s</request>\n" % (oaigetrequesturl(args))

    return out

def oai_footer(verb):
    "Print OAI footer"

    out = ""

    if verb:
        out = "%s </%s>\n" % (out, verb)
    out = out + "</OAI-PMH>\n"

    return out

def oai_error_header(args, verb):
    "Print OAI header"

    out = ""

###    out = "Content-Type: text/xml\n\n"
    out = out + "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + "\n"
    out = out + "<OAI-PMH xmlns=\"http://www.openarchives.org/OAI/2.0/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd\">\n"

    out = out + " <responseDate>" + oaigetresponsedate() + "</responseDate>\n"
    out = out + " <request verb=\"%s\">%s</request>\n" % (verb, oaigetrequesturl(args))

    return out

def oai_error_footer(verb):
    "Print OAI footer"

    out  = verb
    out  = "</OAI-PMH>\n"
    return out

def get_field(sysno, field):
    "Gets list of field 'field' for the record with 'sysno' system number."

    out   = []
    digit = field[0:2]

    bibbx = "bib%sx" % digit
    bibx  = "bibrec_bib%sx" % digit
    query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec=%%s AND bx.id=bibx.id_bibxxx AND bx.tag=%%s" % (bibbx, bibx)

    res = run_sql(query, (sysno, field))

    for row in res:

        out.append(row[0])

    return out

def utc_to_localtime(date):
    """
    Convert UTC to localtime

    Reference:
     - (1) http://www.openarchives.org/OAI/openarchivesprotocol.html#Dates
     - (2) http://www.w3.org/TR/NOTE-datetime

    This function works only with dates complying with the
    "Complete date plus hours, minutes and seconds" profile of
    ISO 8601 defined by (2), and linked from (1).

    Eg:    1994-11-05T13:15:30Z
    """
    ldate = date.split("T")[0]
    ltime = date.split("T")[1]

    lhour   = ltime.split(":")[0]
    lminute = ltime.split(":")[1]
    lsec    = ltime.split(":")[2]
    lsec    = lsec[:-1] # Remove trailing "Z"

    lyear   = ldate.split("-")[0]
    lmonth  = ldate.split("-")[1]
    lday    = ldate.split("-")[2]


    # 1: Build a time as UTC. Since time.mktime() expect a local time :
    ## 1a: build it without knownledge of dst
    ## 1b: substract timezone to get a local time, with possibly wrong dst
    utc_time = time.mktime((int(lyear), int(lmonth), int(lday), int(lhour), int(lminute), int(lsec), 0, 0, -1))
    local_time = utc_time - time.timezone

    # 2: Fix dst for local_time
    # Find out the offset for daily saving time of the local
    # timezone at the time of the given 'date'
    if time.localtime(local_time)[-1] == 1:
        local_time = local_time + 3600

    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(local_time))

def localtime_to_utc(date):
    "Convert localtime to UTC"

    ldate = date.split(" ")[0]
    ltime = date.split(" ")[1]

    lhour   = ltime.split(":")[0]
    lminute = ltime.split(":")[1]
    lsec    = ltime.split(":")[2]

    lyear   = ldate.split("-")[0]
    lmonth  = ldate.split("-")[1]
    lday    = ldate.split("-")[2]

    # Find out the offset for daily saving time of the local
    # timezone at the time of the given 'date'
    #
    # 1: build time that correspond to local date, without knowledge of dst
    # 2: determine if dst is locally enabled at this time
    tmp_date = time.mktime((int(lyear), int(lmonth), int(lday), int(lhour), int(lminute), int(lsec), 0, 0, -1))
    if time.localtime(tmp_date)[-1] == 1:
        dst = time.localtime(tmp_date)[-1]
    else:
        dst = 0

    # 3: Build a new time with knowledge of the dst
    local_time = time.mktime((int(lyear), int(lmonth), int(lday), int(lhour), int(lminute), int(lsec), 0, 0, dst))
    # 4: Get the time as UTC
    utc_time = time.gmtime(local_time)

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", utc_time)

def get_modification_date(sysno):
    "Returns the date of last modification for the record 'sysno'."
    out = ""
    res = run_sql("SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res and res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_earliest_datestamp():
    "Get earliest datestamp in the database"
    out = ""
    res = run_sql("SELECT MIN(DATE_FORMAT(creation_date,'%%Y-%%m-%%d %%H:%%i:%%s')) FROM bibrec", (), 1)
    if res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_latest_datestamp():
    "Get latest datestamp in the database"
    out = ""
    res = run_sql("SELECT MAX(DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s')) FROM bibrec", (), 1)
    if res[0][0]:
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

def print_record(sysno, format='marcxml', record_exists_result=None):
    """Prints record 'sysno' formatted according to 'format'.

    - if record does not exist, return nothing.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is
      'transient' or 'deleted', then return only header, with status
      'deleted'.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is 'no',
      then return nothing.

    Optional parameter 'record_exists_result' has the value of the result
    of the record_exists(sysno) function (in order not to call that function
    again if already done.)
    """

    out = ""

    # sanity check:
    if record_exists_result is not None:
        _record_exists = record_exists_result
    else:
        _record_exists = record_exists(sysno)

    if not _record_exists:
        return

    if (format == "dc") or (format == "oai_dc"):
        format = "xd"

    # print record opening tags:

    out = out + "  <record>\n"

    if _record_exists == -1: # Deleted?
        if CFG_OAI_DELETED_POLICY == "persistent" or \
               CFG_OAI_DELETED_POLICY == "transient":
            out = out + "    <header status=\"deleted\">\n"
        else:
            return
    else:
        out = out + "   <header>\n"

    for ident in get_field(sysno, CFG_OAI_ID_FIELD):
        out = "%s    <identifier>%s</identifier>\n" % (out, escape_space(ident))
    out = "%s    <datestamp>%s</datestamp>\n" % (out, get_modification_date(sysno))
    for set in get_field(sysno, CFG_OAI_SET_FIELD):
        if set:
            # Print only if field not empty
            out = "%s    <setSpec>%s</setSpec>\n" % (out, set)
    out = out + "   </header>\n"

    if _record_exists == -1: # Deleted?
        pass
    else:
        out = out + "   <metadata>\n"

        if format == "marcxml":
            formatted_record = get_preformatted_record(sysno, 'xm')
            if formatted_record is not None:
                ## MARCXML is already preformatted. Adapt it if needed
                formatted_record = formatted_record.replace("<record>", "<marc:record xmlns:marc=\"http://www.loc.gov/MARC21/slim\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\" type=\"Bibliographic\">\n     <marc:leader>00000coc  2200000uu 4500</marc:leader>")
                formatted_record = formatted_record.replace("<record xmlns=\"http://www.loc.gov/MARC21/slim\">", "<marc:record xmlns:marc=\"http://www.loc.gov/MARC21/slim\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\" type=\"Bibliographic\">\n     <marc:leader>00000coc  2200000uu 4500</marc:leader>")
                formatted_record = formatted_record.replace("</record", "</marc:record")
                formatted_record = formatted_record.replace("<controlfield", "<marc:controlfield")
                formatted_record = formatted_record.replace("</controlfield", "</marc:controlfield")
                formatted_record = formatted_record.replace("<datafield", "<marc:datafield")
                formatted_record = formatted_record.replace("</datafield", "</marc:datafield")
                formatted_record = formatted_record.replace("<subfield", "<marc:subfield")
                formatted_record = formatted_record.replace("</subfield", "</marc:subfield")
                out += formatted_record
            else:
                ## MARCXML is not formatted in the database, so produce it.
                out = out + "    <marc:record xmlns:marc=\"http://www.loc.gov/MARC21/slim\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\" type=\"Bibliographic\">"
                out = out + "     <marc:leader>00000coc  2200000uu 4500</marc:leader>"
                out = "%s     <marc:controlfield tag=\"001\">%d</marc:controlfield>\n" % (out, int(sysno))

                for digit1 in range(0, 10):
                    for digit2 in range(0, 10):
                        bibbx = "bib%d%dx" % (digit1, digit2)
                        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
                        query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                                "WHERE bb.id_bibrec=%%s AND b.id=bb.id_bibxxx AND b.tag LIKE %%s "\
                                "ORDER BY bb.field_number, b.tag ASC" % (bibbx, bibx)
                        res = run_sql(query, (sysno, '%d%d%%' % (digit1, digit2)))
                        field_number_old = -999
                        field_old = ""
                        for row in res:
                            field, value, field_number = row[0], row[1], row[2]
                            ind1, ind2 = field[3], field[4]
                            if ind1 == "_":
                                ind1 = " "
                            if ind2 == "_":
                                ind2 = " "
                            # print field tag
                            if field_number != field_number_old or field[:-1] != field_old[:-1]:
                                if format == "marcxml":

                                    if field_number_old != -999:
                                        if field_old[0:2] == "00":
                                            out = out + "     </marc:controlfield>\n"
                                        else:
                                            out = out + "     </marc:datafield>\n"

                                    if field[0:2] == "00":
                                        out = "%s     <marc:controlfield tag=\"%s\">\n" % (out, encode_for_xml(field[0:3]))
                                    else:
                                        out = "%s     <marc:datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">\n" % (out, encode_for_xml(field[0:3]), encode_for_xml(ind1).lower(), encode_for_xml(ind2).lower())


                                field_number_old = field_number
                                field_old = field
                            # print subfield value
                            if format == "marcxml":
                                value = encode_for_xml(value)

                                if(field[0:2] == "00"):
                                    out = "%s      %s\n" % (out, value)
                                else:
                                    out = "%s      <marc:subfield code=\"%s\">%s</marc:subfield>\n" % (out, encode_for_xml(field[-1:]), value)


                            # fetch next subfield
                        # all fields/subfields printed in this run, so close the tag:
                        if (format == "marcxml") and field_number_old != -999:
                            if field_old[0:2] == "00":
                                out = out + "     </marc:controlfield>\n"
                            else:
                                out = out + "     </marc:datafield>\n"

                out = out + "    </marc:record>\n"

        elif format == "xd":
            out += format_record(sysno, 'xoaidc')

    # print record closing tags:

        out = out + "   </metadata>\n"

    out = out + "  </record>\n"

    return out

def oailistmetadataformats(args):
    "Generates response to oailistmetadataformats verb."

    arg = parse_args(args)

    out = ""

    flag = 1 # list or not depending on identifier

    if arg['identifier'] != "":

        flag = 0

        sysno = oaigetsysno(arg['identifier'])
        _record_exists = record_exists(sysno)
        if _record_exists == 1 or \
               (_record_exists == -1 and CFG_OAI_DELETED_POLICY != "no"):

            flag = 1

        else:

            out = out + oai_error("idDoesNotExist","invalid record Identifier")
            out = oai_error_header(args, "ListMetadataFormats") + out + oai_error_footer("ListMetadataFormats")
            return out

    if flag:
        out = out + "   <metadataFormat>\n"
        out = out + "    <metadataPrefix>oai_dc</metadataPrefix>\n"
        out = out + "    <schema>http://www.openarchives.org/OAI/1.1/dc.xsd</schema>\n"
        out = out + "    <metadataNamespace>http://purl.org/dc/elements/1.1/</metadataNamespace>\n"
        out = out + "   </metadataFormat>\n"
        out = out + "   <metadataFormat>\n"
        out = out + "    <metadataPrefix>marcxml</metadataPrefix>\n"
        out = out + "    <schema>http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd</schema>\n"
        out = out + "    <metadataNamespace>http://www.loc.gov/MARC21/slim</metadataNamespace>\n"
        out = out + "   </metadataFormat>\n"

    out = oai_header(args, "ListMetadataFormats") + out + oai_footer("ListMetadataFormats")
    return out


def oailistrecords(args):
    "Generates response to oailistrecords verb."

    arg = parse_args(args)

    out = ""
    resumptionToken_printed = False

    sysnos = []
    sysno  = []
    # check if the resumptionToken did not expire
    if arg['resumptionToken']:
        filename = os.path.join(CFG_CACHEDIR, 'RTdata', arg['resumptionToken'])
        if os.path.exists(filename) == 0:
            out = oai_error("badResumptionToken", "ResumptionToken expired")
            out = oai_error_header(args, "ListRecords") + out + oai_error_footer("ListRecords")
            return out

    if arg['resumptionToken'] != "":
        sysnos = oaicacheout(arg['resumptionToken'])
        arg['metadataPrefix'] = sysnos.pop()
    else:
        sysnos = oaigetsysnolist(arg['set'], arg['from'], arg['until'])

    if len(sysnos) == 0: # noRecordsMatch error

        out = out + oai_error("noRecordsMatch", "no records correspond to the request")
        out = oai_error_header(args, "ListRecords") + out + oai_error_footer("ListRecords")
        return out

    i = 0
    for sysno_ in sysnos:
        if sysno_:
            if i >= CFG_OAI_LOAD:          # cache or write?
                if not resumptionToken_printed: # resumptionToken?
                    arg['resumptionToken'] = oaigenresumptionToken()
                    extdate = oaigetresponsedate(CFG_OAI_EXPIRE)
                    if extdate:
                        out = "%s <resumptionToken expirationDate=\"%s\">%s</resumptionToken>\n" % (out, extdate, arg['resumptionToken'])
                    else:
                        out = "%s <resumptionToken>%s</resumptionToken>\n" % (out, arg['resumptionToken'])
                    resumptionToken_printed = True
                sysno.append(sysno_)
            else:
                _record_exists = record_exists(sysno_)
                if not (_record_exists == -1 and CFG_OAI_DELETED_POLICY == "no"):
                    #Produce output only if record exists and had to be printed
                    i = i + 1 # Increment limit only if record is returned
                    res = print_record(sysno_, arg['metadataPrefix'], _record_exists)
                    if res:
                        out += res

    if resumptionToken_printed:
        oaicacheclean()
        sysno.append(arg['metadataPrefix'])
        oaicachein(arg['resumptionToken'], sysno)

    out = oai_header(args, "ListRecords") + out + oai_footer("ListRecords")
    return out

def oailistsets(args):
    "Lists available sets for OAI metadata harvesting."

    out = ""

    # note: no flow control in ListSets

    sets = get_sets()

    for set_ in sets:

        out = out + "  <set>\n"
        out = "%s    <setSpec>%s</setSpec>\n" % (out, set_[0])
        out = "%s    <setName>%s</setName>\n" % (out, set_[1])
        if set_[2]:
            out = "%s    <setDescription>%s</setDescription>\n" % (out, set_[2])
        out = out + "   </set>\n"

    out = oai_header(args, "ListSets") + out + oai_footer("ListSets")

    return out


def oaigetrecord(args):
    """Returns record 'identifier' according to 'metadataPrefix' format for OAI metadata harvesting.

    - if record does not exist, return oai_error 'idDoesNotExist'.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is
      'transient' or 'deleted', then return only header, with status
      'deleted'.

    - if record has been deleted and CFG_OAI_DELETED_POLICY is 'no',
      then return oai_error 'idDoesNotExist'.
    """

    arg = parse_args(args)
    out = ""
    sysno = oaigetsysno(arg['identifier'])
    _record_exists = record_exists(sysno)
    if _record_exists == 1 or \
           (_record_exists == -1 and CFG_OAI_DELETED_POLICY != 'no'):
        out = print_record(sysno, arg['metadataPrefix'], _record_exists)
        out = oai_header(args, "GetRecord") + out + oai_footer("GetRecord")
    else:
        out = oai_error("idDoesNotExist", "invalid record Identifier")
        out = oai_error_header(args, "GetRecord") + out + oai_error_footer("GetRecord")
    return out

def oailistidentifiers(args):
    "Prints OAI response to the ListIdentifiers verb."

    arg = parse_args(args)

    out = ""
    resumptionToken_printed = False

    sysno  = []
    sysnos = []

    if arg['resumptionToken']:
        filename = os.path.join(CFG_CACHEDIR, 'RTdata', arg['resumptionToken'])
        if os.path.exists(filename) == 0:
            out = out + oai_error("badResumptionToken", "ResumptionToken expired")
            out = oai_error_header(args, "ListIdentifiers") + out + oai_error_footer("ListIdentifiers")
            return out

    if arg['resumptionToken']:
        sysnos = oaicacheout(arg['resumptionToken'])
    else:
        sysnos = oaigetsysnolist(arg['set'], arg['from'], arg['until'])

    if len(sysnos) == 0: # noRecordsMatch error
        out = out + oai_error("noRecordsMatch", "no records correspond to the request")
        out = oai_error_header(args, "ListIdentifiers") + out + oai_error_footer("ListIdentifiers")
        return out

    i = 0
    for sysno_ in sysnos:
        if sysno_:
            if i >= CFG_OAI_LOAD:           # cache or write?
                if not resumptionToken_printed: # resumptionToken?
                    arg['resumptionToken'] = oaigenresumptionToken()
                    extdate = oaigetresponsedate(CFG_OAI_EXPIRE)
                    if extdate:
                        out = "%s  <resumptionToken expirationDate=\"%s\">%s</resumptionToken>\n" % (out, extdate, arg['resumptionToken'])
                    else:
                        out = "%s  <resumptionToken>%s</resumptionToken>\n" % (out, arg['resumptionToken'])
                    resumptionToken_printed = True
                sysno.append(sysno_)
            else:
                _record_exists = record_exists(sysno_)
                if (not _record_exists == -1 and CFG_OAI_DELETED_POLICY == "no"):
                    i = i + 1 # Increment limit only if record is returned
                for ident in get_field(sysno_, CFG_OAI_ID_FIELD):
                    if ident != '':
                        if _record_exists == -1: #Deleted?
                            if CFG_OAI_DELETED_POLICY == "persistent" \
                                   or CFG_OAI_DELETED_POLICY == "transient":
                                out = out + "    <header status=\"deleted\">\n"
                            else:
                                # In that case, print nothing (do not go further)
                                break
                        else:
                            out = out + "    <header>\n"
                        out = "%s      <identifier>%s</identifier>\n" % (out, escape_space(ident))
                        out = "%s      <datestamp>%s</datestamp>\n" % (out, get_modification_date(oaigetsysno(ident)))
                        for set in get_field(sysno_, CFG_OAI_SET_FIELD):
                            if set:
                                # Print only if field not empty
                                out = "%s      <setSpec>%s</setSpec>\n" % (out, set)
                        out = out + "    </header>\n"

    if resumptionToken_printed:
        oaicacheclean() # clean cache from expired resumptionTokens
        oaicachein(arg['resumptionToken'], sysno)

    out = oai_header(args, "ListIdentifiers") + out + oai_footer("ListIdentifiers")

    return out


def oaiidentify(args, script_url):
    """Generates a response to oaiidentify verb.

    Parameters:
           args - *dict* query parameters

     script_url - *str* URL of the script used to access the
                  service. This is made necessary since the gateway
                  can be accessed either via /oai2d or /oai2d/ (or for
                  backward compatibility: oai2d.py or oai2d.py/), and
                  that the base URL must be returned in the Identify
                  response
    """

    out = """  <repositoryName>%(CFG_SITE_NAME)s</repositoryName>
    <baseURL>%(CFG_SITE_URL)s%(script_url)s</baseURL>
    <protocolVersion>2.0</protocolVersion>
    <adminEmail>%(CFG_SITE_SUPPORT_EMAIL)s</adminEmail>
    <earliestDatestamp>%(earliest_datestamp)s</earliestDatestamp>
    <deletedRecord>%(CFG_OAI_DELETED_POLICY)s</deletedRecord>
    <granularity>%(granularity)s</granularity>
    %(CFG_OAI_IDENTIFY_DESCRIPTION)s\n""" % \
        {"CFG_SITE_NAME": cgi.escape(CFG_SITE_NAME),
         "CFG_SITE_URL": cgi.escape(CFG_SITE_URL),
         "earliest_datestamp": cgi.escape(get_earliest_datestamp()),
         "granularity": "YYYY-MM-DDThh:mm:ssZ",
         "CFG_OAI_DELETED_POLICY": cgi.escape(CFG_OAI_DELETED_POLICY),
         "CFG_SITE_SUPPORT_EMAIL": cgi.escape(CFG_SITE_SUPPORT_EMAIL),
         "CFG_OAI_IDENTIFY_DESCRIPTION": CFG_OAI_IDENTIFY_DESCRIPTION,
         "script_url": script_url}

    out = oai_header(args, "Identify") + out + oai_footer("Identify")

    return out

def oaigetrequesturl(args):
    "Generates requesturl tag for OAI."

    # re_amp = re.compile('&')

    requesturl = CFG_SITE_URL + "/" + "oai2d/"# + "?" + re_amp.sub("&amp;", args)

    return requesturl

def oaigetresponsedate(delay=0):
    "Generates responseDate tag for OAI."

    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + delay))


def oai_error(code, msg):
    "OAI error occured"

    return "<error code=\"%s\">%s</error>\n" % (code, msg)


def oaigetsysno(identifier):
    "Returns the first database BIB ID for the OAI identifier 'identifier', if it exists."
    sysno = None
    if identifier:
        query = "SELECT DISTINCT(bb.id_bibrec) FROM bib%sx AS bx, bibrec_bib%sx AS bb WHERE bx.tag=%%s AND bb.id_bibxxx=bx.id AND bx.value=%%s" % (CFG_OAI_ID_FIELD[0:2], CFG_OAI_ID_FIELD[0:2])
        res = run_sql(query, (CFG_OAI_ID_FIELD, identifier))
        for row in res:
            sysno = row[0]
    return sysno


def oaigetsysnolist(set="", fromdate="", untildate=""):
    "Returns list of system numbers for the OAI set 'set', modified from 'fromdate' until 'untildate'."
    from invenio.oai_repository_updater import get_set_definitions

    if fromdate != "":
        fromdate = normalize_date(fromdate, "T00:00:00Z")
    else:
        fromdate = get_earliest_datestamp()

    if untildate != "":
        untildate = normalize_date(untildate, "T23:59:59Z")
    else:
        untildate = get_latest_datestamp()

    collections = []
    for set_definition in get_set_definitions(set):
        collections.extend(coll.strip() for coll in set_definition['c'].split(','))
    recids = perform_request_search(f1=CFG_OAI_ID_FIELD, p1="oai:*", m1="e", op1='a',
                                    f2=((set and CFG_OAI_SET_FIELD) or ""), p2=set, m2="e",
                                    d1=utc_to_localtime(fromdate),
                                    d2=utc_to_localtime(untildate),
                                    c=collections,
                                    dt='m',
                                    ap=0)
    ## Let's discard non public records
    return list(intbitset(recids) - get_all_restricted_recids())

def oaigenresumptionToken():
    "Generates unique ID for resumption token management."

    return md5(str(time.time())).hexdigest()


def oaicachein(resumptionToken, sysnos):
    "Stores or adds sysnos in cache.  Input is a string of sysnos separated by commas."

    filename = os.path.join(CFG_CACHEDIR, 'RTdata', resumptionToken)

    fil = open(filename, "w")
    cPickle.dump(sysnos, fil)
    fil.close()
    return 1


def oaicacheout(resumptionToken):
    "Restores string of comma-separated system numbers from cache."

    sysnos = []

    filename = os.path.join(CFG_CACHEDIR, 'RTdata', resumptionToken)

    if oaicachestatus(resumptionToken):
        fil = open(filename, "r")
        sysnos = cPickle.load(fil)
        fil.close()
    else:
        return 0
    return sysnos


def oaicacheclean():
    "Removes cached resumptionTokens older than specified"

    directory = os.path.join(CFG_CACHEDIR, 'RTdata')

    files = os.listdir(directory)

    for file_ in files:
        filename = os.path.join(directory, file_)
        # cache entry expires when not modified during a specified period of time
        if ((time.time() - os.path.getmtime(filename)) > CFG_OAI_EXPIRE):
            try:
                os.remove(filename)
            except OSError, e:
                # Most probably the cache was already deleted
                pass
    return 1


def oaicachestatus(resumptionToken):
    "Checks cache status.  Returns 0 for empty, 1 for full."

    filename = os.path.join(CFG_CACHEDIR, 'RTdata', resumptionToken)

    if os.path.exists(filename):
        if os.path.getsize(filename) > 0:
            return 1
        else:
            return 0
    else:
        return 0


def get_sets():
    "Returns list of sets."
    # TODO: Try to remove dependency on oaiREPOSITORY table, by
    # determining available sets from data.

    out = {}
    row = ['', '']

    query = "SELECT setSpec,setName,setDescription FROM oaiREPOSITORY"
    res = run_sql(query)
    for row in res:
        row_bis = [row[0], row[1], row[2]]
        out[row[0]] = row_bis

    return out.values()


def parse_args(args=""):
    "Parse input args"

    out_args = {
       "verb"             : "",
       "metadataPrefix"   : "",
       "from"             : "",
       "until"            : "",
       "set"              : "",
       "identifier"       : "",
       "resumptionToken"  : ""
    }

    if args == "" or args is None:
        pass
    else:

        list_of_arguments = args.split('&')

        for item in list_of_arguments:
            keyvalue = item.split('=')
            if len(keyvalue) == 2:
                if (out_args.has_key(keyvalue[0])):
                    if(out_args[keyvalue[0]] != ""):
                        out_args[keyvalue[0]] = "Error"
                    else:
                        out_args[keyvalue[0]] = urllib.unquote(keyvalue[1])
                else:
                    out_args[keyvalue[0]] = urllib.unquote(keyvalue[1])
            else:
                out_args['verb'] = ""

    return out_args

def check_argd(arguments):
    """
    Check OAI arguments
    Also transform them from lists to strings.
    """

    out = ""

## no several times the same argument
#
#
    for param, value in arguments.iteritems():
        if len(value) > 1 and not 'The request includes illegal arguments' in out:
            out = out + oai_error("badArgument", "The request includes illegal arguments")
            bad_arguments_error = True
        if len(value) > 0:
            arguments[param] = value[0]
        else:
            arguments[param] = ''

## principal argument required
#
#
    if verbs.has_key(arguments['verb']):
        pass
    else:
        out = out + oai_error("badVerb", "Illegal OAI verb")

## defined args
#
#
    for param in arguments.keys():
        if not param in verbs.get(arguments['verb'], []) and param != 'verb' \
               and not 'The request includes illegal arguments' in out:
            out = out + oai_error("badArgument", "The request includes illegal arguments")
            break # Indicate only once

## resumptionToken exclusive
#
#
    if arguments.get('resumptionToken', '') != "" and \
           len(arguments.keys()) != 2 and \
           not 'The request includes illegal arguments' in out:
        out = out + oai_error("badArgument",
                              "The request includes illegal arguments")

## datestamp formats
#
#
    if arguments.has_key('from') and \
           'from' in verbs.get(arguments['verb'], []):
        from_length = len(arguments['from'])
        if check_date(arguments['from']) == "":
            out = out + oai_error("badArgument",
                                  "Bad datestamp format in from")
    else:
        from_length = 0

    if arguments.has_key('until') and \
           'until' in verbs.get(arguments['verb'], []):
        until_length = len(arguments['until'])
        if check_date(arguments['until']) == "":
            out = out + oai_error("badArgument",
                                  "Bad datestamp format in until")
    else:
        until_length = 0

    if from_length != 0:
        if until_length != 0:
            if from_length != until_length:
                out = out + oai_error("badArgument",
                                      "Bad datestamp format")

    if arguments.has_key('from') and arguments.has_key('until') \
           and arguments['from'] > arguments['until'] and \
           'from' in verbs.get(arguments['verb'], []) and \
           'until' in verbs.get(arguments['verb'], []):
        out = out + oai_error("badArgument", "Wrong date")

## Identify exclusive
#
#
    if arguments['verb'] == "Identify" and \
           len(arguments.keys()) != 1:
        if not 'The request includes illegal arguments' in out: # Do not repeat this error
            out = out + oai_error("badArgument",
                                  "The request includes illegal arguments")

## parameters for GetRecord
#
#
    if arguments['verb'] == "GetRecord" and \
           not arguments.has_key('identifier'):
        out = out + oai_error("badArgument",
                              "Record identifier missing")

    if arguments['verb'] == "GetRecord" and \
           not arguments.has_key('metadataPrefix'):
        out = out + oai_error("badArgument",
                              "Missing metadataPrefix")

## parameters for ListRecords and ListIdentifiers
#
#
    if (arguments['verb'] == "ListRecords" or arguments['verb'] == "ListIdentifiers") and \
           (not arguments.has_key('resumptionToken') and not arguments.has_key('metadataPrefix')):
        out = out + oai_error("badArgument", "Missing metadataPrefix")

## Metadata prefix defined and valid
#
#
    if arguments.has_key('metadataPrefix') and \
           not arguments['metadataPrefix'] in params['metadataPrefix']:
        out = out + oai_error("cannotDisseminateFormat", "Chosen format is not supported")

    return out

def oai_profile():
    """
    Runs a benchmark
    """
    oailistrecords('set=&from=&metadataPrefix=oai_dc&verb=ListRecords&resumptionToken=&identifier=&until=')
    #oailistrecords('set=&from=&metadataPrefix=marcxml&verb=ListRecords&resumptionToken=&identifier=&until=')
    #oailistidentifiers('set=&from=&metadataPrefix=oai_dc&verb=ListIdentifiers&resumptionToken=&identifier=&until=')

    return

if __name__ == "__main__":
    import profile
    import pstats
    profile.run('oai_profile()', "oai_profile")
    p = pstats.Stats("oai_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()
