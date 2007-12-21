## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

etcdir = $(sysconfdir)/bibformat/format_templates

etc_DATA = Default_HTML_captions.bft Picture_HTML_brief.bft \
	   Default_HTML_detailed.bft Default_HTML_portfolio.bft \
	   Picture_HTML_detailed.bft Default_HTML_brief.bft \
	   BibTeX.bft MARCXML.bft Excel.bft \
	   Default_HTML_similarity.bft \
	   EndNote.bft EndNote.bfx \
	   DC.bft DC.bfx \
	   NLM.bft NLM.bfx \
	   NLM.xsl \
	   RSS.bft RSS.bfx \
	   MARCXML.bfx \
	   OAI_DC.xsl DC.xsl EndNote.xsl \
	   Default_HTML_references.bft Default_HTML_files.bft \
	   Default_HTML_actions.bft

tmpdir = $(prefix)/var/tmp

tmp_DATA = Test1.bft Test3.bft Test_2.bft Test_no_template.test

EXTRA_DIST = $(etc_DATA) $(tmp_DATA)

CLEANFILES = *.tmp
