## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

etcdir = $(sysconfdir)/bibformat/format_templates

etc_DATA = Default_HTML_captions.bft Picture_HTML_brief.bft \
	   Default_HTML_detailed.bft Default_HTML_portfolio.bft \
	   Picture_HTML_detailed.bft Default_HTML_brief.bft \
	   BibTeX.bft MARCXML.bft Excel.bft \
	   Default_HTML_similarity.bft NLM.xsl \
	   OAI_DC.xsl OAI_MARC.bft DC.xsl EndNote.xsl RSS.xsl \
	   RefWorks.xsl MODS.xsl \
	   Default_HTML_references.bft Default_HTML_files.bft \
	   Default_HTML_actions.bft Journal_HTML_detailed.bft \
	   Journal_HTML_brief.bft \
	   Poetry_HTML_brief.bft Poetry_HTML_detailed.bft \
	   AID_HTML_very_brief.bft Podcast.xsl \
	   Video_HTML_brief.bft Video_HTML_detailed.bft \
	   Basket_Search_Result.bft Default_HTML_meta.bft
	   WebAuthorProfile_affiliations_helper.bft

tmpdir = $(prefix)/var/tmp

tmp_DATA = Test1.bft Test3.bft Test_2.bft Test_no_template.test

EXTRA_DIST = $(etc_DATA) $(tmp_DATA)

CLEANFILES = *.tmp
