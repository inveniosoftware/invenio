## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

pylib_DATA = __init__.py \
             errorlib.py \
             errorlib_tests.py \
             errorlib_webinterface.py \
             errorlib_regression_tests.py \
             data_cacher.py \
             dbdump.py \
             dbquery.py \
             dbquery_tests.py \
             logicutils.py \
             logicutils_tests.py \
             mailutils.py \
             miscutil_config.py \
             messages.py \
             messages_tests.py \
             textutils.py \
             textutils_tests.py \
             dateutils.py \
             dateutils_tests.py \
             htmlutils.py \
             htmlutils_tests.py \
             testutils.py \
             testutils_regression_tests.py \
             invenio_connector.py \
             invenio_connector_regression_tests.py \
             urlutils.py \
             urlutils_tests.py \
             w3c_validator.py \
             intbitset_tests.py \
             inveniocfg.py \
             shellutils.py \
             shellutils_tests.py \
             pluginutils.py \
             pluginutils_tests.py \
             plotextractor.py \
             plotextractor_converter.py \
             plotextractor_getter.py \
             plotextractor_output_utils.py \
             plotextractor_tests.py \
             plotextractor_regression_tests.py \
             plotextractor_config.py \
             solrutils.py \
             remote_debugger.py \
             remote_debugger_config.py \
             remote_debugger_wsgi_reload.py

noinst_DATA = testimport.py \
              kwalitee.py \
              pep8.py

tmpdir = $(prefix)/var/tmp

tmp_DATA = intbitset_example.int

EXTRA_DIST = $(pylib_DATA) \
             testimport.py \
             kwalitee.py \
             pep8.py \
             intbitset.pyx \
             intbitset.c \
             intbitset.h \
             intbitset_impl.c \
             intbitset_setup.py \
             intbitset.pyx \
             $(tmp_DATA)


all:
	$(PYTHON) $(srcdir)/intbitset_setup.py build_ext

install-data-hook:
	$(PYTHON) $(srcdir)/testimport.py ${prefix}
	@find ${srcdir} -name intbitset.so -exec cp {} ${pylibdir} \;

CLEANFILES = *~ *.tmp *.pyc

clean-local:
	rm -rf build
