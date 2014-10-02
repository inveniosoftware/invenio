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

import sys
import urllib
import urllib2
import datetime
from xml.dom.minidom import parse
from time import sleep

from invenio.config import (CFG_ETCDIR,
                            CFG_CROSSREF_USERNAME,
                            CFG_CROSSREF_PASSWORD,
                            CFG_CROSSREF_EMAIL)
from invenio.bibconvert_xslt_engine import convert
from invenio.bibrecord import record_get_field_value
from invenio.urlutils import make_invenio_opener
from invenio.jsonutils import json, json_unicode_to_utf8

CROSSREF_OPENER = make_invenio_opener('crossrefutils')

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
    response = CROSSREF_OPENER.open(request)
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
            "",  # ISSN
            "",  # JOURNAL TITLE (773__p)
            "",  # AUTHOR (Family name of 100__a)
            "",  # VOLUME (773__v)
            "",  # ISSUE (773__n)
            "",  # PAGE (773__c)
            "",  # YEAR  (773__y)
            "",  # RESOURCE TYPE
            "",  # KEY
            ""   # DOI
        ]

        full_author = record_get_field_value(record, "100", "", "", "a").split(",")
        if len(full_author) > 0:
            data[2] = full_author[0]

        data[8] = str(record["001"][0][3])

        for subfield, position in ("p", 1), ("v", 3), ("n", 4), ("c", 5), ("y", 6):
            for tag, ind1, ind2 in [("773", "", "")]:
                val = record_get_field_value(record, tag, ind1, ind2, subfield)
                if val:
                    if subfield == "c":
                        # strip page range to send only starting page
                        if '-' in val:
                            val = val.split('-')[0]
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
                    document = parse(CROSSREF_OPENER.open(url, data))
                    break
                except (urllib2.URLError, urllib2.HTTPError):
                    sleep(5)
                    retry_attempt += 1
            else:
                # Executed if retries are maxed out. We skip this record.
                continue

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

        for line in CROSSREF_OPENER.open(url, data):
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


def get_all_modified_dois(publisher, from_date=None, re_match=None, debug=False):
    """
    Get all the DOIs from a given publisher (e.g. Elsevier has 10.1016
    that were registered or updated in Crossref since from_date.
    By default from_date is today - 3 days.
    re_match is an optional argument where a compiled reguar expression
    can be passed in order to match only given DOI structures.
    """
    if from_date is None:
        from_date = (datetime.datetime.today() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    res = query_fundref_api("/publishers/%s/works" % publisher, rows=0, filter="from-update-date:%s" % from_date)
    total_results = res['total-results']
    if debug:
        print >> sys.stderr, "total modified DOIs for publisher %s since %s: %s" % (publisher, from_date, total_results)
    ret = {}
    for offset in range(0, total_results, 1000):
        if debug:
            print >> sys.stderr, "Fetching %s/%s..." % (offset, total_results)
        res = query_fundref_api("/publishers/%s/works" % publisher, rows=1000, offset=offset, filter="from-update-date:%s" % from_date)
        if re_match:
            ret.update([(item['DOI'], item) for item in res['items'] if re_match.match(item['DOI'])])
        else:
            ret.update([(item['DOI'], item) for item in res['items']])
    return ret

def query_fundref_api(query, **kwargs):
    """
    Perform a request to the Fundref API.
    """
    sleep(1)
    req = urllib2.Request("http://api.crossref.org%s?%s" % (query, urllib.urlencode(kwargs)), headers={'content-type': 'application/vnd.crossref-api-message+json; version=1.0'})
    res = json_unicode_to_utf8(json.load(CROSSREF_OPENER.open(req)))
    return res['message']
