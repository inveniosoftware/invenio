## $Id$
## OAI interface for CDSware/MySQL written in Python compliant with OAI-PMH2.0

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAI interface for CDSware/MySQL written in Python compliant with OAI-PMH2.0"""

import cPickle
import string
from string import split
import os
import re
import urllib
import sys
import time
import md5

from oai_repository_config import *
from config import *
from dbquery import run_sql

verbs = {
    "Identify"            : [""],
    "ListSets"            : ["resumptionToken"],
    "ListMetadataFormats" : ["resumptionToken"],
    "ListRecords"         : ["resumptionToken"],
    "ListIdentifiers"     : ["resumptionToken"],
    "GetRecord"	          : [""]
}

params = {
    "verb" : ["Identify","ListIdentifiers","ListSets","ListMetadataFormats","ListRecords","GetRecord"],
    "metadataPrefix" : ["","oai_dc","marcxml"],
    "from" :[""],
    "until":[""],
    "set" :[""],
    "identifier": [""]
}

def encode_for_xml(strxml):
    "Encode special chars in string for XML-compliancy."

    if strxml == None:
        return strxml
    else:
        strxml = string.replace(strxml, '&', '&amp;')
        strxml = string.replace(strxml, '<', '&lt;')
        return strxml

def escape_space(strxml):
    "Encode special chars in string for URL-compliancy."

    strxml = string.replace(strxml, ' ', '%20')
    return strxml

def encode_for_url(strxml):
    "Encode special chars in string for URL-compliancy."

    strxml = string.replace(strxml, '%', '%25')
    strxml = string.replace(strxml, ' ', '%20')
    strxml = string.replace(strxml, '?', '%3F')
    strxml = string.replace(strxml, '#', '%23')
    strxml = string.replace(strxml, '=', '%3D')
    strxml = string.replace(strxml, '&', '%26')
    strxml = string.replace(strxml, '/', '%2F')
    strxml = string.replace(strxml, ':', '%3A')
    strxml = string.replace(strxml, ';', '%3B')
    strxml = string.replace(strxml, '+', '%2B')

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
    query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag='%s'" % (bibbx, bibx, sysno, field)

    res = run_sql(query)

    for row in res:

        out.append(row[0])

    return out

def utc_to_localtime(date):
    "Convert UTC to localtime"

    ldate = date.split("T")[0]
    ltime = date.split("T")[1]

    lhour   = ltime.split(":")[0]
    lminute = ltime.split(":")[1]
    lsec    = ltime.split(":")[2]

    lyear   = ldate.split("-")[0]
    lmonth  = ldate.split("-")[1]
    lday    = ldate.split("-")[2]
    
    timetoconvert = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime((string.atoi(lyear), string.atoi(lmonth), string.atoi(lday), string.atoi(lhour), string.atoi(lminute), string.atoi(lsec[:-1]), 0, 0, -1)) - time.timezone + (time.daylight)*3600))

    return timetoconvert

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

    timetoconvert = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.mktime((string.atoi(lyear), string.atoi(lmonth), string.atoi(lday), string.atoi(lhour), string.atoi(lminute), string.atoi(lsec), 0, 0, -1))))

    return timetoconvert

def get_creation_date(sysno):
    "Returns the creation date of the record 'sysno'."
    out   = ""
    res = run_sql("SELECT DATE_FORMAT(creation_date, '%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_modification_date(sysno):
    "Returns the date of last modification for the record 'sysno'."
    out = ""
    res = run_sql("SELECT DATE_FORMAT(modification_date,'%%Y-%%m-%%d %%H:%%i:%%s') FROM bibrec WHERE id=%s", (sysno,), 1)
    if res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def get_earliest_datestamp():
    "Get earliest datestamp in the database"
    out = ""
    res = run_sql("SELECT MIN(DATE_FORMAT(creation_date,'%%Y-%%m-%%d %%H:%%i:%%s')) FROM bibrec", (), 1)
    if res[0][0]:
        out = localtime_to_utc(res[0][0])
    return out

def check_date(date, dtime="T00:00:00Z"):
    "Check if the date has a correct format"

    if(re.sub("[0123456789\-:TZ]", "", date) == ""):
        if len(date) == 10:
            date = date + dtime
        if len(date) == 20:
            date = utc_to_localtime(date)
        else:
            date = ""
    else:
        date = ""
    
    return date

def record_exists(sysno):
    "Returns 1 if record with SYSNO 'sysno' exists.  Returns 0 otherwise."

    out = 0
    query = "SELECT id FROM bibrec WHERE id='%s'" % (sysno)

    res = run_sql(query)
    
    for row in res:
        if row[0] != "":
            out = 1

    return out

def print_record(sysno, format='marcxml'):
    "Prints record 'sysno' formatted accoding to 'format'."

    out = ""

    # sanity check:
    if not record_exists(sysno):
        return

    if (format == "dc") or (format == "oai_dc"):
        format = "xd"

    # print record opening tags:
    
    out = out + "  <record>\n"

    if is_deleted(sysno) and oaideleted != "no":
        out = out + "    <header status=\"deleted\">\n"
    else:
        out = out + "   <header>\n"

    for ident in get_field(sysno, oaiidfield):
        out = "%s    <identifier>%s</identifier>\n" % (out, escape_space(ident))
    out = "%s    <datestamp>%s</datestamp>\n" % (out, get_modification_date(sysno))
    for set in get_field(sysno, oaisetfield):
        out = "%s    <setSpec>%s</setSpec>\n" % (out, set)
    out = out + "   </header>\n"

    if is_deleted(sysno) and oaideleted != "no":
        pass
    else:
        out = out + "   <metadata>\n"

        if format == "marcxml":
            out = out + "    <record xmlns=\"http://www.loc.gov/MARC21/slim\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\" type=\"Bibliographic\">"
            out = out + "     <leader>00000coc  2200000uu 4500</leader>"
            ## MARC21 and XML formats, possibley OAI -- they are not in "bibfmt" table; so fetch all the data from "bibXXx" tables:

            if format == "marcxml":

                out = "%s     <controlfield tag=\"001\">%d</controlfield>\n" % (out, int(sysno))

            for digit1 in range(0, 10):
                for digit2 in range(0, 10):
                    bibbx = "bib%d%dx" % (digit1, digit2)
                    bibx = "bibrec_bib%d%dx" % (digit1, digit2)
                    query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                            "WHERE bb.id_bibrec='%s' AND b.id=bb.id_bibxxx AND b.tag LIKE '%s%%' "\
                            "ORDER BY bb.field_number, b.tag ASC" % (bibbx, bibx, sysno, str(digit1)+str(digit2))
                    res = run_sql(query)
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
                                    out = out + "     </datafield>\n"

                                out = "%s     <datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">\n" % (out, encode_for_xml(field[0:3]), encode_for_xml(ind1).lower(), encode_for_xml(ind2).lower())

                            field_number_old = field_number
                            field_old = field
                        # print subfield value
                        if format == "marcxml":
                            value = encode_for_xml(value)
                            out = "%s      <subfield code=\"%s\">%s</subfield>\n" % (out, encode_for_xml(field[-1:]), value)
   
                        # fetch next subfield
                    # all fields/subfields printed in this run, so close the tag:
                    if (format == "marcxml") and field_number_old != -999:
                        out = out + "     </datafield>\n"
            out = out + "    </record>\n"

        elif format == "xd":
        # XML Dublin Core format, possibly OAI -- select only some bibXXx fields:
            out = out + "       <oaidc:dc xmlns=\"http://purl.org/dc/elements/1.1/\" xmlns:oaidc=\"http://www.openarchives.org/OAI/2.0/oai_dc/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd\">\n"

            for field_ in get_field(sysno, "041__a"):
                out =  "%s         <language>%s</language>\n" % (out, field_)

            for field_ in get_field(sysno, "100__a"):
                out =  "%s         <creator>%s</creator>\n" % (out, encode_for_xml(field_))
 
            for field_ in get_field(sysno, "700__a"):
                out =  "%s         <creator>%s</creator>\n" % (out, encode_for_xml(field_))

            for field_ in get_field(sysno, "245__a"):
                out =  "%s         <title>%s</title>\n" % (out, encode_for_xml(field_))

            for field_ in get_field(sysno, "111__a"):
                out =  "%s         <title>%s</title>\n" % (out, encode_for_xml(field_))

            for field_ in get_field(sysno, "65017a"):
                out =  "%s         <subject>%s</subject>\n" % (out, encode_for_xml(field_))

            for field_ in get_field(sysno, "8564_u"):
                out =  "%s         <identifier>%s</identifier>\n" % (out, encode_for_xml(escape_space(field_)))
        
            for field_ in get_field(sysno, "520__a"):
                out = "%s         <description>%s</description>\n" % (out, encode_for_xml(field_))

            date = get_creation_date(sysno)
 
            out = "%s         <date>%s</date>\n" % (out, date)
            out = out + "    </oaidc:dc>\n"

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

        if record_exists(sysno):

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

    sysnos = []
    sysno  = []

    # check if the resumptionToken did not expire
    if arg['resumptionToken']:
        filename = "%s/RTdata/%s" % (logdir, arg['resumptionToken'])
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
        
        out = out + oai_error("noRecordsMatch", "no_ records correspond to the request")
        out = oai_error_header(args, "ListRecords") + out + oai_error_footer("ListRecords")
        return out

    i = 0
    for sysno_ in sysnos:
        if sysno_:
            i = i + 1
            if i > nb_records_in_resume:          # cache or write?
                if i == nb_records_in_resume + 1: # resumptionToken?
                    arg['resumptionToken'] = oaigenresumptionToken()
                    extdate = oaigetresponsedate(oai_rt_expire)
                    if extdate:
                        out = "%s <resumptionToken expirationDate=\"%s\">%s</resumptionToken>\n" % (out, extdate, arg['resumptionToken'])
                    else:
                        out = "%s <resumptionToken>%s</resumptionToken>\n" % (out, arg['resumptionToken'])
                sysno.append(sysno_)
            else:
                done = 0
                for field_ in get_field(sysno_, "245__a"):
                    if done == 0:
                        out = out + print_record(sysno_, arg['metadataPrefix'])

    if i > nb_records_in_resume:
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
    """Returns record 'identifier' according to 'metadataPrefix' format for OAI metadata harvesting."""
    
    arg = parse_args(args)
    out = ""
    sysno = oaigetsysno(arg['identifier'])

    if record_exists(sysno):
        datestamp = get_modification_date(sysno)
        out = out + print_record(sysno, arg['metadataPrefix'])
    else:
        out = out + oai_error("idDoesNotExist", "invalid record Identifier")
        out = oai_error_header(args, "GetRecord") + out + oai_error_footer("GetRecord")
        return out

    out = oai_header(args, "GetRecord") + out + oai_footer("GetRecord")

    return out


def oailistidentifiers(args):
    "Prints OAI response to the ListIdentifiers verb."

    arg = parse_args(args)

    out = ""

    sysno  = []
    sysnos = []

    if arg['resumptionToken']:
        filename = "%s/RTdata/%s" % (logdir, arg['resumptionToken'])
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
            i = i + 1
            if i > nb_identifiers_in_resume:           # cache or write?
                if i ==  nb_identifiers_in_resume + 1: # resumptionToken?
                    arg['resumptionToken'] = oaigenresumptionToken()
                    extdate = oaigetresponsedate(oai_rt_expire)
                    if extdate:
                        out = "%s  <resumptionToken expirationDate=\"%s\">%s</resumptionToken>\n" % (out, extdate, arg['resumptionToken'])
                    else:
                        out = "%s  <resumptionToken>%s</resumptionToken>\n" % (out, arg['resumptionToken'])
                sysno.append(sysno_)
            else:
                done = 0
                for field_ in get_field(sysno_, "245__a"):
                    if done == 0:
                        for ident in get_field(sysno_, oaiidfield): 
                            if is_deleted(sysno_) and oaideleted != "no":
                                out = out + "    <header status=\"deleted\">\n"
                            else:
                                out = out + "    <header>\n"
                            out = "%s      <identifier>%s</identifier>\n" % (out, escape_space(ident))
                            out = "%s      <datestamp>%s</datestamp>\n" % (out, get_modification_date(oaigetsysno(ident)))
                            for set in get_field(sysno_, oaisetfield):
                                out = "%s      <setSpec>%s</setSpec>\n" % (out, set)
                            out = out + "    </header>\n"
                        done = 1

    if i > nb_identifiers_in_resume:
        oaicacheclean() # clean cache from expired resumptionTokens
        oaicachein(arg['resumptionToken'], sysno)

    out = oai_header(args, "ListIdentifiers") + out + oai_footer("ListIdentifiers")

    return out


def oaiidentify(args):
    "Generates response to oaiidentify verb."
        
    out = ""

    repositoryname        = "  <repositoryName>" + cdsname + "</repositoryName>\n"
    baseurl               = "  <baseURL>%s/oai2d.py/</baseURL>\n" % weburl
    protocolversion       = "  <protocolVersion>2.0</protocolVersion>\n"
    adminemail            = "  <adminEmail>%s</adminEmail>\n" % supportemail
    earliestdst		  = "  <earliestDatestamp>%s</earliestDatestamp>\n" % get_earliest_datestamp()               
    deletedrecord         = "  <deletedRecord>%s</deletedRecord>\n" % oaideleted
    repositoryidentifier  = "%s" % oaiidprefix
    sampleidentifier      = oaisampleidentifier
    identifydescription   = oaiidentifydescription + "\n"

    out = out + repositoryname
    out = out + baseurl
    out = out + protocolversion
    out = out + adminemail
    out = out + earliestdst
    out = out + deletedrecord
    out = out + "  <granularity>YYYY-MM-DDThh:mm:ssZ</granularity>\n"
    #    print "  <compression></compression>\n"
    out = out + oaiidentifydescription

    out = oai_header(args, "Identify") + out + oai_footer("Identify")

    return out

     
def oaigetrequesturl(args):
    "Generates requesturl tag for OAI."

    # re_amp = re.compile('&')

    requesturl = weburl + "/" + "oai2d.py/"# + "?" + re_amp.sub("&amp;", args)

    return requesturl

def oaigetresponsedate(delay=0):
    "Generates responseDate tag for OAI."
    
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + delay))


def oai_error(code, msg):
    "OAI error occured"

    return "<error code=\"%s\">%s</error>\n" % (code, msg)


def oaigetsysno(identifier):
    "Returns the first MySQL BIB ID for the OAI identifier 'identifier', if it exists."
    sysno = None
    if identifier:
        query = "SELECT DISTINCT(bb.id_bibrec) FROM bib%sx AS bx, bibrec_bib%sx AS bb WHERE bx.tag='%s' AND bb.id_bibxxx=bx.id AND bx.value='%s'" % (oaiidfield[0:2], oaiidfield[0:2], oaiidfield, identifier)
        res = run_sql(query)
        for row in res:
            sysno = row[0]
    return sysno


def oaigetsysnolist(set, fromdate, untildate):
    "Returns list of system numbers for the OAI set 'set', modified from 'date_from' until 'date_until'."

    out_dict = {} # dict to hold list of out sysnos as its keys

    if set:
        query = "SELECT DISTINCT bibx.id_bibrec FROM bib%sx AS bx LEFT JOIN bibrec_bib%sx AS bibx ON bx.id=bibx.id_bibxxx LEFT JOIN bibrec AS b ON b.id=bibx.id_bibrec WHERE bx.tag='%s' AND bx.value='%s'" % (oaiidfield[0:2], oaiidfield[0:2], oaisetfield, set)
    else:
        query = "SELECT DISTINCT bibx.id_bibrec FROM bib%sx AS bx LEFT JOIN bibrec_bib%sx AS bibx ON bx.id=bibx.id_bibxxx LEFT JOIN bibrec AS b ON b.id=bibx.id_bibrec WHERE bx.tag='%s'" % (oaiidfield[0:2], oaiidfield[0:2], oaiidfield)

    if untildate:
        query = query + " AND b.modification_date <= '%s'" % untildate
    if fromdate:
        query = query + " AND b.modification_date >= '%s'" % fromdate

    res = run_sql(query)

    for row in res:
        out_dict[row[0]] = 1
         
    return out_dict.keys()

def is_deleted(recid):
    "Check if record with recid has been deleted. Return 1 if deleted."

    query = "select a.id from bibrec as a left join bibrec_bib98x as b on a.id=b.id_bibrec left join bib98x as c on b.id_bibxxx=c.id where c.value='DELETED' and a.id=%s" % recid

    res = run_sql(query)

    for item in res:
        if item == None:
            return 0
        else:
            return 1
    
def oaigenresumptionToken():
    "Generates unique ID for resumption token management."

    return md5.new(str(time.time())).hexdigest()


def oaicachein(resumptionToken, sysnos):
    "Stores or adds sysnos in cache.  Input is a string of sysnos separated by commas."

    filename = "%s/RTdata/%s" % (logdir, resumptionToken)

    fil = open(filename, "w")
    cPickle.dump(sysnos, fil)
    fil.close()
    return 1


def oaicacheout(resumptionToken):
    "Restores string of comma-separated system numbers from cache."
    
    sysnos = []

    filename = "%s/RTdata/%s" % (logdir, resumptionToken)

    if oaicachestatus(resumptionToken):
        fil = open(filename, "r")
        sysnos = cPickle.load(fil)
        fil.close()
    else:
        return 0
    return sysnos


def oaicacheclean():
    "Removes cached resumptionTokens older than specified"
    
    directory = "%s/RTdata" % logdir

    files = os.listdir(directory)

    for file_ in files:
        filename = directory + "/" + file_
        # cache entry expires when not modified during a specified period of time
        if ((time.time() - os.path.getmtime(filename)) > oai_rt_expire):
            os.remove(filename)

    return 1


def oaicachestatus(resumptionToken):
    "Checks cache status.  Returns 0 for empty, 1 for full."
    
    filename = "%s/RTdata/%s" % (logdir, resumptionToken)
    
    if os.path.exists(filename):
        if os.path.getsize(filename) > 0:
            return 1
        else:
            return 0
    else:
        return 0


def get_sets():
    "Returns list of sets."

    out = []
    row = ['', '']

    query = "SELECT setSpec,setName,setDescription FROM oaiSET"
    res = run_sql(query)
    for row in res:
        row_bis = [row[0], row[1], row[2]]
        out.append(row_bis)
            
    return out


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

    if args == "" or args == None:
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

def check_args(arguments):
    "Check OAI arguments"

    out_args = {
        "verb"             : "",
        "metadataPrefix"   : "",
        "from"             : "",
        "until"            : "",
        "set"              : "",
        "identifier"       : "",
        "resumptionToken"  : ""
    }

    out = ""

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
        if out_args.has_key(param):
            pass
        else:
            out = out + oai_error("badArgument", "The request includes illegal arguments")

## unique args
#
#
    for param in arguments.keys():
        if (arguments[param] == "Error"):
            out = out + oai_error("badArgument", "The request includes illegal arguments")

## resumptionToken exclusive
#
#
    if ((arguments['from'] != "" or arguments['until'] != "" or arguments['metadataPrefix'] != "" or arguments['identifier'] != "" or arguments['set'] != "") and arguments['resumptionToken'] != ""):

        out = out + oai_error("badArgument", "The request includes illegal arguments")

## datestamp formats
#
#
    if arguments['from'] != "" and arguments['from'] != "":
        from_length = len(arguments['from'])
        if check_date(arguments['from'], "T00:00:00Z") == "":
            out = out + oai_error("badArgument", "Bad datestamp format in from")
    else:
        from_length = 0

    if arguments['until'] != "" and arguments['until'] != "":
        until_length = len(arguments['until'])
        if check_date(arguments['until'], "T23:59:59Z") == "":
            out = out + oai_error("badArgument", "Bad datestamp format in until")
    else:
        until_length = 0 

    if from_length != 0:
        if until_length != 0:
            if from_length != until_length:
                out = out + oai_error("badArgument", "Bad datestamp format")

    if arguments['from'] != "" and arguments['until'] != "" and arguments['from'] > arguments['until']:
        out = out + oai_error("badArgument", "Wrong date")

## Identify exclusive
#
#
    if (arguments['verb'] =="Identify" and (arguments['metadataPrefix'] != "" or arguments['identifier'] != "" or arguments['set'] != "" or arguments['from'] != "" or arguments['until'] != "" or arguments['resumptionToken'] != "")):
        out = out + oai_error("badArgument", "The request includes illegal arguments")

## parameters for GetRecord
#
#
    if arguments['verb'] =="GetRecord" and arguments['identifier'] == "":
        out = out + oai_error("badArgument", "Record identifier missing")

    if arguments['verb'] =="GetRecord" and arguments['metadataPrefix'] == "":
        out = out + oai_error("badArgument", "Missing metadataPrefix")


## parameters for ListRecords and ListIdentifiers
#
#
    if (arguments['verb'] =="ListRecords" or arguments['verb'] =="ListIdentifiers") and (arguments['metadataPrefix'] == "" and arguments['resumptionToken'] == ""):
        out = out + oai_error("badArgument", "Missing metadataPrefix")

## Metadata prefix defined
#
#
    if arguments.has_key('metadataPrefix'):
        if ((arguments['metadataPrefix'] in params['metadataPrefix']) or (params['metadataPrefix'] == "")):
            pass
        else:
            out = out + oai_error("badArgument", "Missing metadataPrefix")

    return out


