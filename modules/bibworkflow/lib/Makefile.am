## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

SUBDIRS = workers

pylibdir = $(libdir)/python/invenio

jsdir=$(localstatedir)/www/js

js_DATA = bibworkflow_workflows.js \
          bibworkflow_index.js \
          bibworkflow_entry_details.js

pylib_DATA = bibworkflow_admin_blueprint.py \
			 bibworkflow_api.py \
			 bibworkflow_client.py \
			 bibworkflow_config.py \
			 bibworkflow_engine.py \
			 bibworkflow_model.py \
			 bibworkflow_object.py \
			 bibworkflow_unit_tests.py \
			 bibworkflow_utils.py \
			 bibworkflow_worker_engine.py \
			 bibworkflow_workflow_definition.py

EXTRA_DIST = $(pylib_DATA) \
			 $(js_DATA)

CLEANFILES = *~ *.tmp *.pyc
