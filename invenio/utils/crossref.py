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

""" API to fetch metadata in MARCXML format from crossref site using DOI """

import urllib2

from invenio.config import CFG_ETCDIR, CFG_CROSSREF_USERNAME, \
 CFG_CROSSREF_PASSWORD
from invenio.bibconvert_xslt_engine import convert


# Exceptions classes
class CrossrefError(Exception):
    """Crossref errors"""
    def __init__(self, code):
        """Initialisation"""
        self.code = code

    def __str__(self):
        """Returns error code"""
        return repr(self.code)

def get_marcxml_for_doi(doi):
    """
    Send doi to the http://www.crossref.org/openurl page.
    Attaches parameters: username, password, doi and noredirect.
    Returns the MARCXML code or throws an exception, when
    1. DOI is malformed
    2. Record not found
    """
    if not CFG_CROSSREF_USERNAME and not CFG_CROSSREF_PASSWORD:
        raise CrossrefError("error_crossref_no_account")

    # Clean the DOI
    doi = doi.strip()

    # Getting the data from external source
    url = "http://www.crossref.org/openurl/?pid=" +  CFG_CROSSREF_USERNAME \
        + ":" + CFG_CROSSREF_PASSWORD + "&noredirect=tru&id=doi:" + doi
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    header = response.info().getheader('Content-Type')
    content = response.read()

    # Check if the returned page is html - this means the DOI is malformed
    if "text/html" in header:
        raise CrossrefError("error_crossref_malformed_doi")
    if 'status="unresolved"' in content:
        raise CrossrefError("error_crossref_record_not_found")

    # Convert xml to marc using convert function
    # from bibconvert_xslt_engine file
    # Seting the path to xsl template
    xsl_crossref2marc_config = "%s/bibconvert/config/%s" % \
    (CFG_ETCDIR, "crossref2marcxml.xsl")

    output = convert(xmltext=content, \
                    template_filename=xsl_crossref2marc_config)
    return output
