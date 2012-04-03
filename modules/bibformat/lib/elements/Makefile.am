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

pylibdir=$(libdir)/python/invenio/bibformat_elements

pylib_DATA = bfe_field.py bfe_title.py bfe_authors.py bfe_abstract.py bfe_affiliation.py \
	     bfe_imprint.py bfe_fulltext.py bfe_place.py bfe_publisher.py bfe_topbanner.py \
	     bfe_date_rec.py bfe_keywords.py bfe_notes.py bfe_reprints.py bfe_publi_info.py \
	     bfe_cited_by.py bfe_references.py bfe_title_brief.py \
	     bfe_report_numbers.py bfe_additional_report_numbers.py bfe_url.py \
	     bfe_addresses.py bfe_contact.py bfe_photo_resources_brief.py \
	     bfe_collection.py bfe_editors.py bfe_bibtex.py bfe_edit_record.py \
	     bfe_date.py bfe_xml_record.py bfe_external_publications.py __init__.py \
	     bfe_bfx_engine.py bfe_creation_date.py bfe_server_info.py bfe_issn.py \
	     bfe_client_info.py bfe_language.py bfe_record_id.py bfe_comments.py \
	     bfe_pagination.py bfe_fulltext_mini.py bfe_year.py bfe_isbn.py \
	     bfe_appears_in_collections.py bfe_photos.py bfe_record_stats.py \
	     bfe_edit_files.py bfe_plots.py bfe_plots_thumb.py bfe_sword_push.py \
	     bfe_video_sources.py bfe_video_bigthumb.py \
	     bfe_aid_authors.py bfe_doi.py bfe_addthis.py \
	     bfe_duration.py bfe_record_url.py bfe_video_selector.py \
	     bfe_video_platform_downloads.py bfe_video_platform_suggestions.py \
	     bfe_video_platform_sources.py bfe_sciencewise.py bfe_bookmark.py \
	     bfe_oai_marcxml.py bfe_copyright.py

tmpdir = $(prefix)/var/tmp/tests_bibformat_elements

tmp_DATA = test_1.py bfe_test_2.py bfe_test_4.py test3.py test_5.py \
	   test_no_element.test __init__.py

EXTRA_DIST = $(pylib_DATA) $(tmp_DATA)

CLEANFILES = *~ *.tmp *.pyc
