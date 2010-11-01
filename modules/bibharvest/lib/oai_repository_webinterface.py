## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio OAI provider interface, compliant with OAI-PMH/2.0"""

__revision__ = "$Id$"

import os
import urllib
import time
from invenio import webinterface_handler_config as apache

from invenio import oai_repository_server
from invenio.config import CFG_CACHEDIR, CFG_OAI_SLEEP
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory

class WebInterfaceOAIProviderPages(WebInterfaceDirectory):
    """Defines the set of /oai2d OAI provider pages."""

    _exports = ['']

    def __call__(self, req, form):
        "OAI repository interface"

        # Clean input arguments. The protocol specifies that an error
        # has to be returned if the same argument is specified several
        # times. Eg:
        # oai2d?verb=ListIdentifiers&metadataPrefix=marcxml&metadataPrefix=marcxml
        # So keep the arguments as list for now so that check_argd can
        # return an error if needed (check_argd also transforms these
        # lists into strings)
        argd = wash_urlargd(form, {'verb': (list, []),
                                   'metadataPrefix': (list, []),
                                   'from': (list, []),
                                   'until': (list, []),
                                   'set': (list, []),
                                   'identifier': (list, []),
                                   'resumptionToken': (list, []),
                                   })

        ## wash_urlargd(..) function cleaned everything, but also added
        ## unwanted parameters. Remove them now
        for param in argd.keys():
            if not param in form and param != 'verb':
                del argd[param]

        ## wash_urlargd(..) function also removed unknown parameters
        ## that we would like to keep in order to send back an error
        ## as required by the protocol. But we do not need that value,
        ## so set it to empty string.
        for param in form.keys():
            if param not in argd.keys():
                argd[param] = ''

        ## But still remove 'ln' parameter that was automatically added.
        if argd.has_key('ln'):
            del argd['ln']

        ## check request for OAI compliancy
        ## also transform all the list arguments into string
        oai_error = oai_repository_server.check_argd(argd)

        ## check availability (OAI requests for Identify, ListSets and
        ## ListMetadataFormats are served immediately, otherwise we
        ## shall wait for CFG_OAI_SLEEP seconds between requests):
        if os.path.exists("%s/RTdata/RTdata" % CFG_CACHEDIR) and (argd['verb'] not in ["Identify", "ListMetadataFormats", "ListSets"]):
            time_gap = int(time.time() - os.path.getmtime("%s/RTdata/RTdata" % CFG_CACHEDIR))
            if(time_gap < CFG_OAI_SLEEP):
                req.headers_out["Status-Code"] = "503"
                req.headers_out["Retry-After"] = "%d" % (CFG_OAI_SLEEP - time_gap)
                req.status = apache.HTTP_SERVICE_UNAVAILABLE
                return "Retry after %d seconds" % (CFG_OAI_SLEEP - time_gap)
        command = "touch %s/RTdata/RTdata" % CFG_CACHEDIR
        os.system(command)

        ## construct args (argd string equivalent) for the
        ## oai_repository_server business logic (later it may be good if it
        ## takes argd directly):
        args = urllib.urlencode(argd)

        ## create OAI response

        req.content_type = "text/xml"
        req.send_http_header()

        if oai_error == "":

            ## OAI Identify

            if argd['verb']   == "Identify":
                req.write(oai_repository_server.oaiidentify(args, script_url=req.uri))


            ## OAI ListSets

            elif argd['verb'] == "ListSets":
                req.write(oai_repository_server.oailistsets(args))


            ## OAI ListIdentifiers

            elif argd['verb'] == "ListIdentifiers":
                req.write(oai_repository_server.oailistidentifiers(args))


            ## OAI ListRecords

            elif argd['verb'] == "ListRecords":
                req.write(oai_repository_server.oailistrecords(args))


            ## OAI GetRecord

            elif argd['verb'] == "GetRecord":
                req.write(oai_repository_server.oaigetrecord(args))


            ## OAI ListMetadataFormats

            elif argd['verb'] == "ListMetadataFormats":
                req.write(oai_repository_server.oailistmetadataformats(args))


            ## Unknown verb

            else:
                req.write(oai_repository_server.oai_error("badVerb","Illegal OAI verb"))


        ## OAI error

        else:
            req.write(oai_repository_server.oai_header(args,""))
            req.write(oai_error)
            req.write(oai_repository_server.oai_footer(""))

        return "\n"

    ## Return the same page wether we ask for /oai2d?verb or /oai2d/?verb
    index = __call__
