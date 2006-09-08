# -*- coding: utf-8 -*-
## $Id$

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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""External collection configuration file."""

__lastupdated__ = """$Date$"""

__version__ = "$Id$"

__revision__ = "0.0.1"

# pylint: disable-msg=C0301

cfg_external_collection_timeout = 10
cfg_external_collection_maxresults = 25
cfg_external_collections = {
    'Amazon': 
        {'engine': 'Amazon'},
    'CERN - CDS Indico': 
        {'engine': 'CDSIndico'},
    'CERN - Intranet':
        {'base_url': "http://www.iso.org", 'search_url': "http://search.cern.ch/query.html?qt="},
    'CERN - EDMS':
        {'engine': 'CERNEDMS'},
    'CiteSeer': 
        {'engine': 'Citeseer'},
    'Google':
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
    'KEK KISS Preprints':
        {'engine': 'KissForPreprints'},
    'KEK Library Books':
        {'engine': 'KissForBooks'},
    'KEK Library Journals':
        {'engine': 'KissForJournals'},
    'NEBIS':
        {'engine': 'NEBIS'},
    'Scirus':
        {'engine': 'Scirus'},
    'SLAC SPIRES HEP':
        {'engine': 'SPIRES'},
    'SLAC Library Books':
        {'engine': 'SPIRESBooks'},
}

cfg_external_collection_states_name = {0: 'Disabled', 1: 'See also', 2: 'External search', 3:'External search checked'}
