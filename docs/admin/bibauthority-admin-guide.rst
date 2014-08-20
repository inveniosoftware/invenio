..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _bibauthority-admin-guide:

BibAuthority Admin Guide
========================

Introduction
------------

The INVENIO admin can configure the various ways in which authority
control works for INVENIO by means of the
``invenio.legacy.bibauthority.config``
file. The location and full contents of this configuration file with a
commented example configuration are shown at the bottom of this page.
Their functionality is explained in the following paragraphs.

*For examples of how Authority Control works in Invenio from a user's
perspective, cf. `HOWTO Manage Authority Records <howto-authority>`_.*

Enforcing types of authority records
------------------------------------

INVENIO is originally agnostic about the types of authority records it
contains. Everything it needs to know about authority records comes, on
the one hand, from the authority record types that are contained within
the '980\_\_a' fields, and from the configurations related to these
types on the other hand. Whereas the '980\_\_a' values are usually
edited by the librarians, the INVENIO configuration is the
responsibility of the administrator. It is important for librarians and
administrators to communicate the exact authority record types as well
as the desired functionality relative to the types for the various
INVENIO modules.

BibEdit
-------

As admin of an INVENIO instance, you have the possibility of configuring
which fields are under authority control. In the “Configuration File
Overview” at the end of this page you will find an example of a
configuration which will enable the auto-complete functionality for the
'100\_\_a', '100\_\_u', '110\_\_a', '130\_\_a', '150\_\_a', '700\_\_a'
and '700\_\_u' fields of a bibliographic record in BibEdit. The keys of
the “CFG BIBAUTHORITY CONTROLLED FIELDS” dictionary indicate which
bibliographic fields are under authority control. If the user types
Ctrl-Shift-A while typing within one of these fields, they will propose
an auto-complete dropdown list in BibEdit. The user still has the option
to enter values manually without use of the drop-down list. The values
associated with each key of the dictionary indicate which kind of
authority record is to be associated with this field. In the example
given, the '100\_\_a' field is associated with the authority record type
'AUTHOR'.

The “CFG BIBAUTHORITY AUTOSUGGEST OPTIONS” dictionary gives us the
remaining configurations, specific only to the auto-suggest
functionality. The value for the 'index' key determines which index type
will be used find the authority records that will populate the drop-down
with a list of suggestions (cf. the following paragraph on configuring
the BibIndex for authority records). The value of the
'insert\_here\_field' determines which authority record field contains
the value that should be used both for constructing the strings of the
entries in the drop-down list as well as the value to be inserted
directly into the edited subfield if the user clicks on one of the
drop-down entries. Finally, the value for the 'disambiguation\_fields'
key is an ordered list of authority record fields that are used, in the
order in which they appear in the list, to disambiguate between
authority records with exactly the same value in their
'insert\_here\_field'.

BibIndex
--------

As an admin of INVENIO, you have the possibility of configuring how
indexing works in regards to authority records that are referenced by
bibliographic records. When a bibliographic record is indexed for a
particular index type, and if that index type contains MARC fields which
are under authority control in this particular INVENIO instance (as
configured by the, “CFG BIBAUTHORITY CONTROLLED FIELDS” dictionary in
the bibauthority\_config.py configuration file, mentioned above), then
the indexer will include authority record data from specific MARC fields
of these authority records in the same index. Which authority record
fields are to be used to enrich the indexes for bibliographic records
can be configured by the “CFG BIBAUTHORITY AUTHORITY SUBFIELDS TO INDEX”
dictionary. In the example below each of the 4 authority record types
('AUTHOR', 'INSTITUTION', 'JOURNAL' and 'SUBJECT') is given a list of
authority record MARC fields which are to be scanned for data that is to
be included in the indexed terms of the dependent bibliographic records.
For the 'AUTHOR' authority records, the example specifies that the
values of the fields '100\_\_a', '100\_\_d', '100\_\_q', '400\_\_a',
'400\_\_d', and '400\_\_q' (i.e. name, alternative names, and year of
birth) should all be included in the data to be indexed for any
bibliographic records referencing these authority records in their
authority-controlled subfields.

Configuration File Overview
---------------------------

The configuration file for the BibAuthority module can be found at
``invenio/legacy/bibauthority/config.py``. Below is a
commented example configuration to show how one would typically
configure the parameters for BibAuthority. The details of how this works
were explained in the paragraphs above.

::

    # CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD
    # the authority record field containing the authority record control number
    CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD = '035__a'

    # Separator to be used in control numbers to separate the authority type
    # PREFIX (e.g. "INSTITUTION") from the control_no (e.g. "(CERN)abc123"
    CFG_BIBAUTHORITY_PREFIX_SEP = '|'

    # the ('980__a') string that identifies an authority record
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_IDENTIFIER = 'AUTHORITY'

    # the name of the authority collection.
    # This is needed for searching within the authority record collection.
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_NAME = 'Authority Records'

    # used in log file and regression tests
    CFG_BIBAUTHORITY_BIBINDEX_UPDATE_MESSAGE = \
        "Indexing records dependent on modified authority records"

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
        'INSTITUTION': 'INSTITUTION',
        'AUTHOR': 'AUTHOR',
        'JOURNAL': 'JOURNAL',
        'SUBJECT': 'SUBJECT',
    }

    # CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC
    # 1. tells us which bibliographic subfields are under authority control
    # 2. tells us which bibliographic subfields refer to which type of
    # ... authority record (must conform to the keys of CFG_BIBAUTHORITY_TYPE_NAMES)
    CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC = {
        '100__a': 'AUTHOR',
        '100__u': 'INSTITUTION',
        '110__a': 'INSTITUTION',
        '130__a': 'JOURNAL',
        '150__a': 'SUBJECT',
        '260__b': 'INSTITUTION',
        '700__a': 'AUTHOR',
        '700__u': 'INSTITUTION',
    }

    # CFG_BIBAUTHORITY_CONTROLLED_FIELDS_AUTHORITY
    # Tells us which authority record subfields are under authority control
    # used by autosuggest feature in BibEdit
    # authority record subfields use the $4 field for the control_no (not $0)
    CFG_BIBAUTHORITY_CONTROLLED_FIELDS_AUTHORITY = {
        '500__a': 'AUTHOR',
        '510__a': 'INSTITUTION',
        '530__a': 'JOURNAL',
        '550__a': 'SUBJECT',
        '909C1u': 'INSTITUTION', # used in bfe_affiliation
        '920__v': 'INSTITUTION', # used by FZ Juelich demo data
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
        'INSTITUTION':{
            'field': 'authorityinstitution',
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
        'INSTITUTION': [
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

