## This file is part of CDS Invenio.
## Copyright (C) 2013 CERN.
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

SUBDIRS = template_context_functions

pylibdir = $(libdir)/python/invenio

pylib_DATA = \
    webtag_blueprint.py \
    webtag_config.py \
    webtag_forms.py \
    webtag_model.py \
    webtag_regression_tests.py \
    webtag_unit_tests.py \
    webtag_user_settings.py \
    webtag_validators.py

jsdir=$(localstatedir)/www/js

js_DATA = webtag_editor.js

EXTRA_DIST = $(pylib_DATA) \
             $(js_DATA)

CLEANFILES = *~ *.tmp *.pyc
