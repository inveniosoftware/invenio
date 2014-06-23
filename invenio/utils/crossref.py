# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2014 CERN.
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

import urllib, urllib2
from xml.dom.minidom import parse
from time import sleep

from invenio.config import CFG_ETCDIR, CFG_CROSSREF_USERNAME, \
 CFG_CROSSREF_PASSWORD, CFG_CROSSREF_EMAIL
from invenio.legacy.bibconvert.xslt_engine import convert
from invenio.legacy.bibrecord import record_get_field_value

FIELDS_JOURNAL = 'issn,title,author,volume,issue,page,year,type,doi'.split(',')
FIELDS_BOOK = ('isbn,ser_title,vol_title,author,volume,edition_number,'
               + 'page,year,component_number,type,doi').split(',')

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
    xsl_crossref2marc_config = templates.get('crossref2marcxml.xsl', '')

    output = convert(xmltext=content, \
                    template_filename=xsl_crossref2marc_config)
    return output

def get_doi_for_records(records):
    """
    Query crossref to obtain the DOI of a set of records

    @params records: List of records
    @returns dict {record_id : doi}
    """
    from itertools import islice, chain

    def batch(iterable, size):
        sourceiter = iter(iterable)
        while True:
            batchiter = islice(sourceiter, size)
            yield chain([batchiter.next()], batchiter)

    pipes = []
    for record in records:
        data = [
            "", # ISSN
            "", # JOURNAL TITLE (773__p)
            "", # AUTHOR (Family name of 100__a)
            "", # VOLUME (773__v)
            "", # ISSUE (773__n)
            "", # PAGE (773__c)
            "", # YEAR  (773__y)
            "", # RESOURCE TYPE
            "", # KEY
            ""  # DOI
        ]

        full_author = record_get_field_value(record, "100", "", "", "a").split(",")
        if len(full_author) > 0:
            data[2] = full_author[0]

        data[8] = str(record["001"][0][3])

        for subfield, position in ("p", 1), ("v", 3), ("n", 4), ("c", 5), ("y", 6):
            for tag, ind1, ind2 in [("773", "", "")]:
                val = record_get_field_value(record, tag, ind1, ind2, subfield)
                if val:
                    data[position] = val
                    break

        if not data[1] or not data[3] or not data[5]:
            continue  # We need journal title, volume and page

        pipes.append("|".join(data))

    dois = {}
    if len(pipes) > 0:
        for batchpipes in batch(pipes, 10):
            params = {
                "usr": CFG_CROSSREF_USERNAME,
                "pwd": CFG_CROSSREF_PASSWORD,
                "format": "unixref",
                "qdata": "\n".join(batchpipes)
            }
            url = "http://doi.crossref.org/servlet/query"
            data = urllib.urlencode(params)

            retry_attempt = 0

            while retry_attempt < 10:
                try:
                    document = parse(urllib2.urlopen(url, data))
                    break
                except (urllib2.URLError, urllib2.HTTPError):
                    sleep(5)
                    retry_attempt += 1

            results = document.getElementsByTagName("doi_record")

            for result in results:
                record_id = result.getAttribute("key")
                doi_tags = result.getElementsByTagName("doi")
                if len(doi_tags) == 1:
                    dois[record_id] = doi_tags[0].firstChild.nodeValue

            # Avoid sending too many requests
            sleep(0.5)
    return dois


def get_metadata_for_dois(dois):
    """
    Get the metadata associated with
    """
    pipes = []
    for doi in dois:
        pipes.append("|".join([doi, doi]))

    metadata = {}
    if len(pipes) > 0:
        params = {
            "usr": CFG_CROSSREF_EMAIL,
            "format": "piped",
            "qdata": "\n".join(pipes)
        }
        url = "http://doi.crossref.org/servlet/query"
        data = urllib.urlencode(params)

        for line in urllib2.urlopen(url, data):
            line = line.split("|")
            if len(line) == 1:
                pass
            elif len(line) in (10, 12):
                is_book = len(line) == 12
                if is_book:
                    record_data = dict(zip(FIELDS_BOOK, line))
                else:
                    record_data = dict(zip(FIELDS_JOURNAL, line))
                record_data["is_book"] = is_book
                metadata[record_data["doi"]] = record_data
            else:
                raise CrossrefError("Crossref response not understood")

    return metadata

