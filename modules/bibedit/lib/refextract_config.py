# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from config import version, etcdir, pdftotext

# version number:
cfg_refextract_version = "CDSware/%s refextract/%s" % (version, version)

# periodicals knowledge base:
cfg_refextract_kb_journal_titles = "%s/bibedit/refextract-journal-titles.kb" % etcdir
# report numbers knowledge base:
cfg_refextract_kb_report_numbers = "%s/bibedit/refextract-report-numbers.kb" % etcdir

# path to pdftotext executable:
cfg_refextract_pdftotext = pdftotext

### FIXME.  The following are not used in this early release. Do not change them.

# Not important in this version:
cfg_refextract_cat = "LD_LIBRARY_PATH='/opt/SUNWspro/lib:/usr/openwin/lib:/usr/dt/lib:/usr/local/lib'; export LD_LIBRARY_PATH; /bin/cat"

# Again, not important in this version:
cfg_refextract_gunzip = "LD_LIBRARY_PATH='/opt/SUNWspro/lib:/usr/openwin/lib:/usr/dt/lib:/usr/local/lib'; export LD_LIBRARY_PATH; /bin/gunzip"

# Again not important in this version:
cfg_refextract_gs = "/usr/bin/gs" 

# cfg_refextract_no_citation_treatment:
#   If no usable citations are found in a line, there are 2 options:
#   1) If this flag is set to 0, DO NOT use the standardised version of the line.  Instead, strip off the line marker and
#   mark up the original UNTOUCHED line as miscellaneous text.
#   2) If this flag is set to 1, mark up the "standardised" version of the line
#   as Miscellaneous text.  This could result in a better formed reference line as titles could be
#   standardised and corrected, BUT, there is a risk that the line could also be corrupted by
#   partial title identification for example.
cfg_refextract_no_citation_treatment = 0
