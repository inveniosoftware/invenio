##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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

pylibdir = $(libdir)/python/invenio

pylib_DATA = \
	bibauthorid_cli.py \
	bibauthorid_daemon.py \
	bibauthorid_least_squares.py \
	bibauthorid_personid_maintenance.py \
	bibauthorid_scheduler.py \
	bibauthorid_tortoise.py \
	bibauthorid_cluster_set.py \
	bibauthorid_dbinterface.py \
	bibauthorid_matrix_optimization.py \
	bibauthorid_prob_matrix.py \
	bibauthorid_searchinterface.py \
	bibauthorid_webapi.py \
	bibauthorid_comparison.py \
	bibauthorid_frontinterface.py \
	bibauthorid_merge.py \
	bibauthorid_rabbit.py \
	bibauthorid_string_utils.py \
	bibauthorid_webinterface.py \
	bibauthorid_backinterface.py \
	bibauthorid_config.py \
	bibauthorid_general_utils.py \
	bibauthorid_name_utils.py \
	bibauthorid_search_engine.py \
	bibauthorid_name_utils_unit_tests.py \
	bibauthorid_recipes.py \
	bibauthorid_templates.py \
	bibauthorid_wedge.py \
	bibauthorid_webauthorprofileinterface.py \
	bibauthorid_bib_matrix.py \
	bibauthorid_meld_edges.pyx \
	bibauthorid_bib_matrix_unit_tests.py \
	bibauthorid_cluster_set_unit_tests.py \
	bibauthorid_dbinterface_unit_tests.py \
	bibauthorid_affiliations.py \
	bibauthorid_affiliations_regression_tests.py \
	bibauthorid_prob_matrix_unit_tests.py

jsdir=$(localstatedir)/www/js

js_DATA = bibauthorid.js bootstrap.min.js underscore-min.js backbone.js handlebars.js hepname_update.js

EXTRA_DIST = $(pylib_DATA) \
             $(js_DATA)

CLEANFILES = *~ *.tmp *.pyc
