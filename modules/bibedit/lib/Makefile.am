## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

pylib_DATA = bibrecord_config.py \
             bibrecord.py \
             bibrecord_tests.py \
             refextract_config.py \
             refextract.py \
             xmlmarc2textmarc.py \
             textmarc2xmlmarc.py \
             bibedit_config.py \
             bibedit_dblayer.py \
             bibedit_engine.py \
             bibedit_regression_tests.py \
             bibedit_templates.py \
             bibeditcli.py \
             bibedit_utils.py \
             bibedit_webinterface.py \
             bibeditmulti_templates.py \
             bibeditmulti_webinterface.py \
             bibeditmulti_engine.py

jsdir=$(localstatedir)/www/js

js_DATA = bibedit_display.js \
          bibedit_engine.js \
          bibedit_keys.js \
          bibedit_menu.js \
          bibeditmulti.js \
          bibedit_holdingpen.js \
	  marcxml.js \
	  bibedit_clipboard.js

EXTRA_DIST = $(pylib_DATA) \
             $(js_DATA)

CLEANFILES = *~ *.tmp *.pyc
