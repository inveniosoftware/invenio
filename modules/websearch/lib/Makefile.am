## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2014 CERN.
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

SUBDIRS = services

pylibdir = $(libdir)/python/invenio
jsdir=$(localstatedir)/www/js
webdir=$(localstatedir)/www/img

pylib_DATA = \
	websearchadminlib.py \
	websearch_templates.py \
	websearch_webinterface.py \
	websearch_regression_tests.py \
	websearch_web_tests.py \
	search_engine.py \
	search_engine_config.py \
	search_engine_cvifier.py \
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
	websearch_services.py \
	websearch_services_unit_tests.py \
	websearch_services_regression_tests.py \
    search_engine_summarizer_regression_tests.py


js_DATA = hepdata.js

web_DATA = hepdata.css

EXTRA_DIST = $(pylib_DATA) $(js_DATA) $(web_DATA)

CLEANFILES = *~ *.tmp *.pyc
