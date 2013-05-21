## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

SUBDIRS = facets

pylibdir = $(libdir)/python/invenio

pylib_DATA = \
	websearchadminlib.py \
	websearch_blueprint.py \
	websearch_cache.py \
	websearch_facet_builders.py \
	websearch_forms.py \
	websearch_flask_tests.py \
	websearch_fixtures.py \
	websearch_fixtures_demosite.py \
	websearch_model.py \
	websearch_templates.py \
	websearch_user_settings.py \
	websearch_webinterface.py \
	websearch_regression_tests.py \
	websearch_web_tests.py \
	record_blueprint.py \
	search_engine.py \
	search_engine_config.py \
	search_engine_unit_tests.py \
	search_engine_utils.py \
	search_engine_query_parser.py \
	search_engine_query_parser_unit_tests.py \
	websearch_webcoll.py \
	websearchadmin_regression_tests.py \
	websearch_external_collections.py \
	search_engine_summarizer.py \
	search_engine_summarizer_unit_tests.py \
	websearch_external_collections_config.py \
	websearch_external_collections_getter.py \
	websearch_external_collections_getter_unit_tests.py \
	websearch_external_collections_parser.py \
	websearch_external_collections_searcher.py \
	websearch_external_collections_templates.py \
	websearch_external_collections_unit_tests.py \
	websearch_external_collections_utils.py \
	websearch_admin_blueprint.py \
	websearch_admin_forms.py


jsdir=$(localstatedir)/www/js

js_DATA = websearch_facet.js \
          websearch_hotkeys.js \
          websearch_typeahead.js

EXTRA_DIST = $(pylib_DATA) \
             $(js_DATA)

CLEANFILES = *~ *.tmp *.pyc
