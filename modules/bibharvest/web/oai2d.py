## $Id$ 
##
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

__lastupdated__ = """$Date$"""
__version__ = "$Id$"

import sys
import urllib
from mod_python import apache

from cdsware.dbquery import run_sql
from cdsware.oai_repository_config import *
from cdsware import oai_repository
from cdsware.config import logdir

def index (req):
    "OAI repository interface"

## check availability

    if os.path.exists("%s/RTdata/last_harvest_date" % logdir):
        req.err_headers_out["Status-Code"] = "503"
        req.err_headers_out["Retry-After"] = "60"
        req.status = apache.HTTP_SERVICE_UNAVAILABLE
        return "%s" % apache.OK
    command = "date > %s/RTdata/last_harvest_date" % logdir   
    os.system(command)

## parse input parameters

    args = ""

    if req.method == "GET":
        args = req.args

    elif req.method == "POST":
        params = {}
        for key in req.form.keys():
            params[key] = req.form[key]
        args = urllib.urlencode(params)    

    arg = oai_repository.parse_args(args)


## check request for OAI compliancy

    oai_error = oai_repository.check_args(arg)


## create OAI response

    req.content_type = "text/xml"
    req.send_http_header()

    if oai_error == "":

## OAI Identify 

        if arg['verb']   == "Identify":
            req.write(oai_repository.oaiidentify(args))


## OAI ListSets

        elif arg['verb'] == "ListSets":
            req.write(oai_repository.oailistsets(args))


## OAI ListIdentifiers

        elif arg['verb'] == "ListIdentifiers":
            req.write(oai_repository.oailistidentifiers(args))


## OAI ListRecords

        elif arg['verb'] == "ListRecords":  
            req.write(oai_repository.oailistrecords(args))


## OAI GetRecord

        elif arg['verb'] == "GetRecord": 
            req.write(oai_repository.oaigetrecord(args))


## OAI ListMetadataFormats

        elif arg['verb'] == "ListMetadataFormats":
            req.write(oai_repository.oailistmetadataformats(args))


## Unknown verb

        else:
            req.write(oai_repository.oai_error("badVerb","Illegal OAI verb"))


## OAI error

    else: 
        req.write(oai_repository.oai_header(args,""))
        req.write(oai_error)
        req.write(oai_repository.oai_footer(""))

    command = "rm %s/RTdata/last_harvest_date" % logdir
    os.system(command)
    return "\n"
