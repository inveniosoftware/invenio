## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
jsdir=$(localstatedir)/www/js

pylib_DATA = authorlist_config.py \
             authorlist_dblayer.py \
             authorlist_engine.py \
             authorlist_templates.py \
             authorlist_webinterface.py \
             authorlist_web_tests.py


js_DATA = authorlist.js \
          authorlist.spreadSheet.js \
          authorlist.select.js

install-data-hook:
	## Let's initialize an empty jquery.min.js, so that if the admin does not
	## run make install-jquery-plugins, at least when jquery.min.js is
	## downloaded by the client browser, no 404 error is raised.
	@touch $(jsdir)/jquery.min.js

EXTRA_DIST = $(pylib_DATA) \
             $(js_DATA)

CLEANFILES = *~ *.tmp *.pyc
