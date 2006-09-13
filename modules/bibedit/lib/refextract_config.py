# -*- coding: utf-8 -*-
##
## $Id$
##
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

"""RefExtract configuration."""

__revision__ = "$Id$"

from invenio.config import version, etcdir, pdftotext

# pylint: disable-msg=C0301

# version number:
CFG_REFEXTRACT_VERSION = "CDS Invenio/%s refextract/%s" % (version, version)

# periodicals knowledge base:
CFG_REFEXTRACT_KB_JOURNAL_TITLES = "%s/bibedit/refextract-journal-titles.kb" % etcdir
# report numbers knowledge base:
CFG_REFEXTRACT_KB_REPORT_NUMBERS = "%s/bibedit/refextract-report-numbers.kb" % etcdir

# path to pdftotext executable:
CFG_REFEXTRACT_PDFTOTEXT = pdftotext

### FIXME.  The following are not used in this early release. Do not change them.

# Not important in this version:
CFG_REFEXTRACT_CAT = "LD_LIBRARY_PATH='/opt/SUNWspro/lib:/usr/openwin/lib:/usr/dt/lib:/usr/local/lib'; export LD_LIBRARY_PATH; /bin/cat"

# Again, not important in this version:
CFG_REFEXTRACT_GUNZIP = "LD_LIBRARY_PATH='/opt/SUNWspro/lib:/usr/openwin/lib:/usr/dt/lib:/usr/local/lib'; export LD_LIBRARY_PATH; /bin/gunzip"

# Again not important in this version:
CFG_REFEXTRACT_GS = "/usr/bin/gs" 

# CFG_REFEXTRACT_NO_CITATION_TREATMENT:
#   If no usable citations are found in a line, there are 2 options:
#   1) If this flag is set to 0, DO NOT use the standardised version of the line.  Instead, strip off the line marker and
#   mark up the original UNTOUCHED line as miscellaneous text.
#   2) If this flag is set to 1, mark up the "standardised" version of the line
#   as Miscellaneous text.  This could result in a better formed reference line as titles could be
#   standardised and corrected, BUT, there is a risk that the line could also be corrupted by
#   partial title identification for example.
CFG_REFEXTRACT_NO_CITATION_TREATMENT = 0
