# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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

# pylint: disable=C0301

"""External collection configuration file."""

from __future__ import unicode_literals

__revision__ = "$Id$"

from invenio.config import CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_TIMEOUT, \
     CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_MAXRESULTS

# if we want to define a parser for an external collection directly using the following dictionary
# we have to import them here instead of the searcher
from .parser import InvenioHTMLExternalCollectionResultsParser
from .parser import InvenioXMLExternalCollectionResultsParser


CFG_EXTERNAL_COLLECTION_TIMEOUT = CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_TIMEOUT

CFG_HOSTED_COLLECTION_TIMEOUT_NBRECS = 1

CFG_HOSTED_COLLECTION_TIMEOUT_ANTE_SEARCH = 1

CFG_HOSTED_COLLECTION_TIMEOUT_POST_SEARCH = 10

CFG_EXTERNAL_COLLECTION_MAXRESULTS = CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_MAXRESULTS

CFG_EXTERNAL_COLLECTION_MAXRESULTS_ALERTS = 100

CFG_EXTERNAL_COLLECTIONS = {
    'Amazon':
        {'engine': 'Amazon'},
    'CERN Indico':
        {'engine': 'CDSIndico'},
    'CERN Intranet':
        {'base_url': "http://www.iso.org", 'search_url': "http://search.cern.ch/query.html?qt="},
    'CERN EDMS':
        {'engine': 'CERNEDMS'},
    'CiteSeer':
        {'engine': 'Citeseer'},
    'Google Web':
        {'engine': 'Google'},
    'Google Books':
        {'engine': 'GoogleBooks'},
    'Google Scholar':
        {'engine': 'GoogleScholar'},
    'IEC':
        {'base_url': "http://www.iec.ch",
         'search_url': "http://www.iec.ch/cgi-bin/procgi.pl/www/iecwww.p?wwwlang=E&wwwprog=sea22.p&search=text&searchfor="},
    'IHS':
        {'base_url': "http://global.ihs.com",
         'search_url': "http://global.ihs.com/search_res.cfm?&input_doc_title="},
    'ISO':
        {'base_url': "http://www.iso.org",
         'search_url': "http://www.iso.org/iso/en/StandardsQueryFormHandler.StandardsQueryFormHandler?languageCode=en" + \
            "&lastSearch=false&title=true&isoNumber=&isoPartNumber=&isoDocType=ALL&isoDocElem=ALL&ICS=&stageCode=&stages" + \
            "cope=Current&repost=1&stagedatepredefined=&stageDate=&committee=ALL&subcommittee=&scopecatalogue=CATALOGUE&" + \
            "scopeprogramme=PROGRAMME&scopewithdrawn=WITHDRAWN&scopedeleted=DELETED&sortOrder=ISO&keyword="},
    'INSPEC':
        {'engine': 'INSPEC'},
    'KISS Preprints':
        {'engine': 'KissForPreprints'},
    'KISS Books/Journals':
        {'engine': 'KissForBooksAndJournals'},
    'NEBIS':
        {'engine': 'NEBIS'},
    'Scirus':
        {'engine': 'Scirus'},
    'SLAC Library Catalog':
        {'engine': 'SPIRESBooks'},
    'INSPIRE':
        {'engine': 'Invenio',
         'base_url': 'http://inspirehep.net/',
         'parser_params':
            {'host': 'inspirehep.net',
             'path': '',
             'parser': InvenioHTMLExternalCollectionResultsParser,
             'fetch_format': 'hb',
             'num_results_regex_str': r'<strong>([0-9,]+?)</strong> records found',
             'nbrecs_regex_str': r'<!-- Search-Engine-Total-Number-Of-Results: ([0-9,]+?) -->',
             'nbrecs_url': 'http://inspirehep.net/search?rg=0&of=xm'},
         'search_url': 'http://inspirehep.net/search?p=',
         'record_url': 'http://inspirehep.net/record/'},
    'ScienceCinema':
        {'engine': 'ScienceCinema'},
    'Atlantis Institute Books':
        {'engine': 'Invenio',
         'base_url': 'http://demo.invenio-software.org/',
         'parser_params':
            {'host': 'demo.invenio-software.org',
             'path': '',
             'parser': InvenioHTMLExternalCollectionResultsParser,
             'fetch_format': 'hb',
             'num_results_regex_str': r'<strong>([0-9,]+?)</strong> records found',
             'nbrecs_regex_str': r'<!-- Search-Engine-Total-Number-Of-Results: ([0-9,]+?) -->',
             'nbrecs_url': 'http://demo.invenio-software.org/search?c=Books&rg=0&of=xm'},
         'search_url': 'http://demo.invenio-software.org/search?cc=Books&p=',
         'record_url': 'http://demo.invenio-software.org/record/',
         'selected_by_default': False},
    'Atlantis Institute Articles':
        {'engine': 'Invenio',
         'base_url': 'http://demo.invenio-software.org/',
         'parser_params':
            {'host': 'demo.invenio-software.org',
             'path': '',
             'parser': InvenioXMLExternalCollectionResultsParser,
             'fetch_format': 'xm',
             'num_results_regex_str': r'<!-- Search-Engine-Total-Number-Of-Results: ([0-9,]+?) -->',
             'nbrecs_regex_str': r'<!-- Search-Engine-Total-Number-Of-Results: ([0-9,]+?) -->',
             'nbrecs_url': 'http://demo.invenio-software.org/search?cc=Articles&rg=0&of=xm'},
         'search_url': 'http://demo.invenio-software.org/search?cc=Articles&p=',
         'record_url': 'http://demo.invenio-software.org/record/',
         'selected_by_default': True},
}

CFG_EXTERNAL_COLLECTION_STATES_NAME = {0: 'Disabled', 1: 'See also', 2: 'External search', 3:'External search checked'}
