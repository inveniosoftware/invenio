# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""RefExtract configuration."""

__revision__ = "$Id$"

from invenio.config import CFG_VERSION, CFG_ETCDIR

# pylint: disable=C0301

# version number:
CFG_REFEXTRACT_VERSION = "Invenio/%s refextract/%s" % (CFG_VERSION, CFG_VERSION)

# periodicals knowledge base:
CFG_REFEXTRACT_KB_JOURNAL_TITLES = "%s/refextract/refextract-journal-titles.kb" % CFG_ETCDIR
# report numbers knowledge base:
CFG_REFEXTRACT_KB_REPORT_NUMBERS = "%s/refextract/refextract-report-numbers.kb" % CFG_ETCDIR
# authors which should be recognised as such
CFG_REFEXTRACT_KB_AUTHORS = "%s/refextract/refextract-authors.kb" % CFG_ETCDIR

## Lines holding key matches will be replaced with the value at extraction time
CFG_REFEXTRACT_INSTITUTION_REPLACEMENTS = {r'^Livermore' : 'LLNL, Livermore', \
                                               r'.*?Stanford Linear Accelerator Center.*?' : 'SLAC', \
                                               r'^Fermi National Accelerator Laboratory' : 'Fermilab'}

## Lines holding these institutions will be reduced solely to the institution at extraction time
CFG_REFEXTRACT_INSTITUTION_REDUCTIONS = ['CERN', 'DESY', 'Rutherford', 'Fermilab', 'SLAC', \
                                             'TRIUMF', 'Brookhaven Livermore', 'Argonne']

## The allowable distance between consecutively numerated affiliations
## A small distance value could limit the number of numerated affiliations obtained (default: 2)
CFG_REFEXTRACT_AFFILIATION_NUMERATION_ALLOWABLE_GAP = 2

## MARC Fields and subfields used by refextract:

## reference fields:
CFG_REFEXTRACT_CTRL_FIELD_RECID          = "001" ## control-field recid
CFG_REFEXTRACT_TAG_ID_REFERENCE          = "999" ## ref field tag
CFG_REFEXTRACT_IND1_REFERENCE            = "C"   ## ref field ind1
CFG_REFEXTRACT_IND2_REFERENCE            = "5"   ## ref field ind2
CFG_REFEXTRACT_SUBFIELD_MARKER           = "o"   ## ref marker subfield
CFG_REFEXTRACT_SUBFIELD_MISC             = "m"   ## ref misc subfield
CFG_REFEXTRACT_SUBFIELD_DOI              = "a"   ## ref DOI subfield (NEW)
CFG_REFEXTRACT_SUBFIELD_REPORT_NUM       = "r"   ## ref reportnum subfield
CFG_REFEXTRACT_SUBFIELD_TITLE            = "s"   ## ref title subfield
CFG_REFEXTRACT_SUBFIELD_URL              = "u"   ## ref url subfield
CFG_REFEXTRACT_SUBFIELD_URL_DESCR        = "z"   ## ref url-text subfield
CFG_REFEXTRACT_SUBFIELD_AUTH             = "h"   ## ref author subfield

## refextract statistics fields:
CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS   = "999" ## ref-stats tag
CFG_REFEXTRACT_IND1_EXTRACTION_STATS     = "C"   ## ref-stats ind1
CFG_REFEXTRACT_IND2_EXTRACTION_STATS     = "6"   ## ref-stats ind2
CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS = "a"   ## ref-stats subfield

## refextract author-extraction fields:
CFG_REFEXTRACT_AE_TAG_ID_HEAD_AUTHOR     = "100" ## first author-aff details
CFG_REFEXTRACT_AE_TAG_ID_TAIL_AUTHOR     = "700" ## remaining author-affs
CFG_REFEXTRACT_AE_SUBFIELD_AUTHOR        = "a"   ## authors subfield
CFG_REFEXTRACT_AE_SUBFIELD_AFFILIATION   = "u"   ## affiliations subfield

## Internal tags are used by refextract to mark-up recognised citation
## information. These are the "closing tags:
CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM = r"</cds.REPORTNUMBER>"
CFG_REFEXTRACT_MARKER_CLOSING_TITLE      = r"</cds.TITLE>"
CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID = r"</cds.TITLEibid>"
CFG_REFEXTRACT_MARKER_CLOSING_SERIES     = r"</cds.SER>"
CFG_REFEXTRACT_MARKER_CLOSING_VOLUME     = r"</cds.VOL>"
CFG_REFEXTRACT_MARKER_CLOSING_YEAR       = r"</cds.YR>"
CFG_REFEXTRACT_MARKER_CLOSING_PAGE       = r"</cds.PG>"

## Of the form '</cds.AUTHxxxx>' only
CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND= r"</cds.AUTHstnd>"
CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL= r"</cds.AUTHetal>"
CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL= r"</cds.AUTHincl>"

CFG_REFEXTRACT_MARKER_CLOSING_AFFILIATION= r"</cds.AFF>"

## XML Record and collection opening/closing tags:
CFG_REFEXTRACT_XML_VERSION          = u"""<?xml version="1.0" encoding="UTF-8"?>"""
CFG_REFEXTRACT_XML_COLLECTION_OPEN  = u"""<collection xmlns="http://www.loc.gov/MARC21/slim">"""
CFG_REFEXTRACT_XML_COLLECTION_CLOSE = u"""</collection>\n"""
CFG_REFEXTRACT_XML_RECORD_OPEN      = u"<record>"
CFG_REFEXTRACT_XML_RECORD_CLOSE     = u"</record>"

## Job task file valid parameters
CFG_REFEXTRACT_JOB_FILE_PARAMS = ('collection', 'recid', 'raw-references',
                                  'output-raw-refs', 'xmlfile', 'dictfile',
                                  'inspire', 'kb-journal', 'kb-report-number', 'verbose')
