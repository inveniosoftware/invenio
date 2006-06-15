## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio OAI provider interface, compliant with OAI-PMH/2.0"""

__lastupdated__ = """$Date$"""
__version__ = "$Id$"

import os
import sys
import urllib
import time
from mod_python import apache

from invenio.dbquery import run_sql
from invenio.oai_repository_config import *
from invenio import oai_repository
from invenio.config import cachedir
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceOAIProviderPages(WebInterfaceDirectory):
    """Defines the set of /oai2d OAI provider pages."""

    _exports = ['']

    def __call__(self, req, form):
        "OAI repository interface"

        argd = wash_urlargd(form, {'verb': (str, ""),
                                   'metadataPrefix': (str, ""),
                                   'from': (str, ""),
                                   'until': (str, ""),
                                   'set': (str, ""),
                                   'identifier': (str, ""),
                                   'resumptionToken': (str, ""),
                                   })

        ## oai_repository business logic does not like to see the
        ## language parameter, so take it out now:        
        if argd['ln']:
            del argd['ln']

        ## construct args (argd string equivalent) for the
        ## oai_repository business logic (later it may be good if it
        ## takes argd directly):
        args = urllib.urlencode(argd)

        ## check availability

        if os.path.exists("%s/RTdata/RTdata" % cachedir):
            time_gap = int(time.time() - os.path.getmtime("%s/RTdata/RTdata" % cachedir))
            if(time_gap < cfg_oai_sleep):
                req.err_headers_out["Status-Code"] = "503"
                req.err_headers_out["Retry-After"] = "%d" % (cfg_oai_sleep - time_gap)
                req.status = apache.HTTP_SERVICE_UNAVAILABLE
                return "Retry after %d seconds" % (cfg_oai_sleep - time_gap)
        command = "touch %s/RTdata/RTdata" % cachedir   
        os.system(command)

        ## check request for OAI compliancy

        oai_error = oai_repository.check_args(argd)


        ## create OAI response

        req.content_type = "text/xml"
        req.send_http_header()

        if oai_error == "":

            ## OAI Identify 

            if argd['verb']   == "Identify":
                req.write(oai_repository.oaiidentify(args))


            ## OAI ListSets

            elif argd['verb'] == "ListSets":
                req.write(oai_repository.oailistsets(args))


            ## OAI ListIdentifiers

            elif argd['verb'] == "ListIdentifiers":
                req.write(oai_repository.oailistidentifiers(args))


            ## OAI ListRecords

            elif argd['verb'] == "ListRecords":  
                req.write(oai_repository.oailistrecords(args))


            ## OAI GetRecord

            elif argd['verb'] == "GetRecord": 
                req.write(oai_repository.oaigetrecord(args))


            ## OAI ListMetadataFormats

            elif argd['verb'] == "ListMetadataFormats":
                req.write(oai_repository.oailistmetadataformats(args))


            ## Unknown verb

            else:
                req.write(oai_repository.oai_error("badVerb","Illegal OAI verb"))


        ## OAI error

        else: 
            req.write(oai_repository.oai_header(args,""))
            req.write(oai_error)
            req.write(oai_repository.oai_footer(""))

        return "\n"

    ## Return the same page wether we ask for /oai2d?verb or /oai2d/?verb
    index = __call__
