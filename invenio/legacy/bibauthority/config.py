# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

from __future__ import unicode_literals

# CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD
# the authority record field containing the authority record control number
CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD = '035__a'

# the record field for authority control numbers
CFG_BIBAUTHORITY_RECORD_AUTHOR_CONTROL_NUMBER_FIELDS = {
        'AUTHOR' : ['100','700'],
        'INSTITUTE' : ['110','920'],
        'JOURNAL' : ['130'],
        'SUBJECT' : ['150']
}


# Separator to be used in control numbers to separate the authority type
# PREFIX (e.g. "INSTITUTE") from the control_no (e.g. "(CERN)abc123"
CFG_BIBAUTHORITY_PREFIX_SEP = '|'

# the ('980__a') string that identifies an authority record
CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_IDENTIFIER = 'AUTHORITY'

# the name of the authority collection.
# This is needed for searching within the authority record collection.
CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME = 'Authorities'

# CFG_BIBAUTHORITY_TYPE_NAMES
# Some administrators may want to be able to change the names used for the
# authority types. Although the keys of this dictionary are hard-coded into
# Invenio, the values are not and can therefore be changed to match whatever
# values are to be used in the MARC records.
# WARNING: These values shouldn't be changed on a running INVENIO installation
# ... since the same values are hard coded into the MARC data,
# ... including the 980__a subfields of all authority records
# ... and the $0 subfields of the bibliographic fields under authority control
CFG_BIBAUTHORITY_TYPE_NAMES = {
    'INSTITUTE': 'INSTITUTE',
    'AUTHOR': 'AUTHOR',
    'JOURNAL': 'JOURNAL',
    'SUBJECT': 'SUBJECT',
}

# CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC
# 1. tells us which bibliographic subfields are under authority control
# 2. tells us which bibliographic subfields refer to which type of
# ... authority record (must conform to the keys of CFG_BIBAUTHORITY_TYPE_NAMES)
# Note: if you want to add new tag here you should also append appropriate tag
# to the miscellaneous index on the BibIndex Admin Site
CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC = {
    '100__a': 'AUTHOR',
    '100__u': 'INSTITUTE',
    '110__a': 'INSTITUTE',
    '130__a': 'JOURNAL',
    '150__a': 'SUBJECT',
    '260__b': 'INSTITUTE',
    '700__a': 'AUTHOR',
    '700__u': 'INSTITUTE',
}

# CFG_BIBAUTHORITY_CONTROLLED_FIELDS_AUTHORITY
# Tells us which authority record subfields are under authority control
# used by autosuggest feature in BibEdit
# authority record subfields use the $4 field for the control_no (not $0)
CFG_BIBAUTHORITY_CONTROLLED_FIELDS_AUTHORITY = {
    '500__a': 'AUTHOR',
    '510__a': 'INSTITUTE',
    '530__a': 'JOURNAL',
    '550__a': 'SUBJECT',
    '909C1u': 'INSTITUTE', # used in bfe_affiliation
    '920__v': 'INSTITUTE', # used by FZ Juelich demo data
}

# constants for CFG_BIBEDIT_AUTOSUGGEST_TAGS
# CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_ALPHA for alphabetical sorting
# ... of drop-down suggestions
# CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_POPULAR for sorting of drop-down
# ... suggestions according to a popularity ranking
CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_ALPHA = 'alphabetical'
CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_POPULAR = 'by popularity'

# CFG_BIBAUTHORITY_AUTOSUGGEST_CONFIG
# some additional configuration for auto-suggest drop-down
# 'field' : which logical or MARC field field to use for this
# ... auto-suggest type
# 'insert_here_field' : which authority record field to use
# ... for insertion into the auto-completed bibedit field
# 'disambiguation_fields': an ordered list of fields to use
# ... in case multiple suggestions have the same 'insert_here_field' values
# TODO: 'sort_by'. This has not been implemented yet !
CFG_BIBAUTHORITY_AUTOSUGGEST_CONFIG = {
    'AUTHOR': {
        'field': 'authorityauthor',
        'insert_here_field': '100__a',
        'sort_by': CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_POPULAR,
        'disambiguation_fields': ['100__d', '270__m'],
    },
    'INSTITUTE':{
        'field': 'authorityinstitute',
        'insert_here_field': '110__a',
        'sort_by': CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_ALPHA,
        'disambiguation_fields': ['270__b'],
    },
    'JOURNAL':{
        'field': 'authorityjournal',
        'insert_here_field': '130__a',
        'sort_by': CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_POPULAR,
    },
    'SUBJECT':{
        'field': 'authoritysubject',
        'insert_here_field': '150__a',
        'sort_by': CFG_BIBAUTHORITY_AUTOSUGGEST_SORT_ALPHA,
    },
}

# list of authority record fields to index for each authority record type
# R stands for 'repeatable'
# NR stands for 'non-repeatable'
CFG_BIBAUTHORITY_AUTHORITY_SUBFIELDS_TO_INDEX = {
    'AUTHOR': [
        '100__a', #Personal Name (NR, NR)
        '100__d', #Year of birth or other dates (NR, NR)
        '100__q', #Fuller form of name (NR, NR)
        '400__a', #(See From Tracing) (R, NR)
        '400__d', #(See From Tracing) (R, NR)
        '400__q', #(See From Tracing) (R, NR)
    ],
    'INSTITUTE': [
        '110__a', #(NR, NR)
        '410__a', #(R, NR)
    ],
    'JOURNAL': [
        '130__a', #(NR, NR)
        '130__f', #(NR, NR)
        '130__l', #(NR, NR)
        '430__a', #(R, NR)
    ],
    'SUBJECT': [
        '150__a', #(NR, NR)
        '450__a', #(R, NR)
    ],
}
