## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
webdir=$(localstatedir)/www/img
jsdir=$(localstatedir)/www/js

pylib_DATA = bibedit_config.py \
             bibedit_dblayer.py \
             bibedit_engine.py \
             bibedit_unit_tests.py \
             bibedit_regression_tests.py \
             bibedit_templates.py \
             bibeditcli.py \
             bibedit_utils.py \
             bibedit_webinterface.py \
             bibedit_web_tests.py \
             bibeditmulti_templates.py \
             bibeditmulti_webinterface.py \
             bibeditmulti_engine.py

js_DATA = bibedit_display.js \
          bibedit_engine.js \
          bibedit_keys.js \
          bibedit_menu.js \
          bibeditmulti.js \
          bibedit_holdingpen.js \
          marcxml.js \
          bibedit_clipboard.js \
          bibedit_template_interface.js \
          bibedit_engine_unit_tests.js \
          bibedit_engine_unit_tests.conf \
          bibedit_refextract.js

web_DATA = bibedit.css

install-data-hook:
	## Let's initialize an empty jquery.min.js, so that if the admin does not
	## run make install-jquery-plugins, at least when jquery.min.js is
	## downloaded by the client browser, no 404 error is raised.
	@touch $(jsdir)/jquery.min.js


EXTRA_DIST = $(pylib_DATA) \
             $(js_DATA) \
             $(web_DATA)

CLEANFILES = *~ *.tmp *.pyc
