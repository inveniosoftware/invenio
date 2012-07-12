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

"""RefExtract configuration"""


from invenio.config import CFG_VERSION, CFG_ETCDIR

# pylint: disable=C0301

# Version number:
CFG_REFEXTRACT_VERSION = "Invenio/%s refextract/%s" % (CFG_VERSION, '1.3')
# Module config directory
CFG_CONF_DIR = '%s/docextract' % CFG_ETCDIR

CFG_REFEXTRACT_KBS = {
   'journals'        : "%s/journal-titles.kb" % CFG_CONF_DIR,
   'journals-re'     : "%s/journal-titles-re.kb" % CFG_CONF_DIR,
   'report-numbers'  : "%s/report-numbers.kb" % CFG_CONF_DIR,
   'authors'         : "%s/authors.kb" % CFG_CONF_DIR,
   'collaborations'  : "%s/collaborations.kb" % CFG_CONF_DIR,
   'books'           : "%s/books.kb" % CFG_CONF_DIR,
   'conferences'     : "%s/conferences.kb" % CFG_CONF_DIR,
   'publishers'      : "%s/publishers.kb" % CFG_CONF_DIR,
   'special-journals': "%s/special-journals.kb" % CFG_CONF_DIR,
}

# Prefix for temp files
CFG_REFEXTRACT_FILENAME = "refextract"

## MARC Fields and subfields used by refextract:

# Reference fields:
CFG_REFEXTRACT_CTRL_FIELD_RECID          = "001"    # control-field recid
CFG_REFEXTRACT_TAG_ID_REFERENCE          = "999"    # ref field tag
CFG_REFEXTRACT_IND1_REFERENCE            = "C"      # ref field ind1
CFG_REFEXTRACT_IND2_REFERENCE            = "5"      # ref field ind2
CFG_REFEXTRACT_SUBFIELD_MARKER           = "o"      # ref marker subfield
CFG_REFEXTRACT_SUBFIELD_MISC             = "m"      # ref misc subfield
CFG_REFEXTRACT_SUBFIELD_DOI              = "a"      # ref DOI subfield (NEW)
CFG_REFEXTRACT_SUBFIELD_REPORT_NUM       = "r"      # ref reportnum subfield
CFG_REFEXTRACT_SUBFIELD_TITLE            = "s"      # ref journal subfield
CFG_REFEXTRACT_SUBFIELD_URL              = "u"      # ref url subfield
CFG_REFEXTRACT_SUBFIELD_URL_DESCR        = "z"      # ref url-text subfield
CFG_REFEXTRACT_SUBFIELD_AUTH             = "h"      # ref author subfield
CFG_REFEXTRACT_SUBFIELD_QUOTED           = "t"      # ref title subfield
CFG_REFEXTRACT_SUBFIELD_ISBN             = "i"      # ref isbn subfield
CFG_REFEXTRACT_SUBFIELD_PUBLISHER        = "p"      # ref publisher subfield
CFG_REFEXTRACT_SUBFIELD_BOOK             = "xbook"  # ref book subfield

## refextract statistics fields:
CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS   = "999"  # ref-stats tag
CFG_REFEXTRACT_IND1_EXTRACTION_STATS     = "C"    # ref-stats ind1
CFG_REFEXTRACT_IND2_EXTRACTION_STATS     = "6"    # ref-stats ind2
CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS = "a"    # ref-stats subfield


## Internal tags are used by refextract to mark-up recognised citation
## information. These are the "closing tags:
CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM = r"</cds.REPORTNUMBER>"
CFG_REFEXTRACT_MARKER_CLOSING_TITLE      = r"</cds.JOURNAL>"
CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID = r"</cds.JOURNALibid>"
CFG_REFEXTRACT_MARKER_CLOSING_SERIES     = r"</cds.SER>"
CFG_REFEXTRACT_MARKER_CLOSING_VOLUME     = r"</cds.VOL>"
CFG_REFEXTRACT_MARKER_CLOSING_YEAR       = r"</cds.YR>"
CFG_REFEXTRACT_MARKER_CLOSING_PAGE       = r"</cds.PG>"
CFG_REFEXTRACT_MARKER_CLOSING_QUOTED     = r"</cds.QUOTED>"
CFG_REFEXTRACT_MARKER_CLOSING_ISBN       = r"</cds.ISBN>"
CFG_REFEXTRACT_MARKER_CLOSING_ISBN       = r"</cds.PUBLISHER>"

## Of the form '</cds.AUTHxxxx>' only
CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND = r"</cds.AUTHstnd>"
CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL = r"</cds.AUTHetal>"
CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL = r"</cds.AUTHincl>"

## XML Record and collection opening/closing tags:
CFG_REFEXTRACT_XML_VERSION          = u"""<?xml version="1.0" encoding="UTF-8"?>"""
CFG_REFEXTRACT_XML_COLLECTION_OPEN  = u"""<collection xmlns="http://www.loc.gov/MARC21/slim">"""
CFG_REFEXTRACT_XML_COLLECTION_CLOSE = u"""</collection>"""
CFG_REFEXTRACT_XML_RECORD_OPEN      = u"<record>"
CFG_REFEXTRACT_XML_RECORD_CLOSE     = u"</record>"

## The minimum length of a reference's misc text to be deemed insignificant.
## when comparing misc text with semi-colon defined sub-references.
## Values higher than this value reflect meaningful misc text.
## Hence, upon finding a correct semi-colon, but having current misc text
## length less than this value (without other meaningful reference objects:
## report numbers, titles...) then no split will occur.
## (A higher value will increase splitting strictness. i.e. Fewer splits)
CGF_REFEXTRACT_SEMI_COLON_MISC_TEXT_SENSITIVITY = 60

## The length of misc text between two adjacent authors which is
## deemed as insignificant. As such, when misc text of a length less
## than this value is found, then the latter author group is dumped into misc.
## (A higher value will increase splitting strictness. i.e. Fewer splits)
CGF_REFEXTRACT_ADJACENT_AUTH_MISC_SEPARATION = 10
