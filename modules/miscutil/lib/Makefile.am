## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

pylibdir = $(libdir)/python/invenio
pylib_DATA = __init__.py \
             errorlib.py \
             errorlib_tests.py \
             errorlib_webinterface.py \
             errorlib_regression_tests.py \
             config.py \
             data_cacher.py \
             dbquery.py \
             dbquery_tests.py \
             mailutils.py \
	     miscutil_config.py \
             messages.py \
             textutils.py \
             dateutils.py \
             dateutils_tests.py \
             htmlutils.py \
	     htmlutils_tests.py \
	     testutils.py \
	     testutils_regression_tests.py \
	     urlutils.py \
	     w3c_validator.py \
             intbitset_tests.py

noinst_DATA = testimport.py \
              kwalitee.py \
              api_migration_kit.sh

phplibdir = $(libdir)/php/invenio/errors
phplib_DATA = errorHandling.php

EXTRA_DIST = __init__.py \
             errorlib.py \
             errorlib_tests.py \
             errorlib_webinterface.py \
             errorlib_regression_tests.py \
	     miscutil_config.py \
             config.py.wml \
             dbquery.py.wml \
             dbquery_tests.py \
             messages.py.wml \
             errorHandling.php.wml \
             textutils.py \
             dateutils.py \
             dateutils_tests.py \
             htmlutils.py \
	     htmlutils_tests.py \
	     testutils.py \
	     testutils_regression_tests.py \
             urlutils.py \
             testimport.py \
             kwalitee.py \
             intbitset.pyx \
             intbitset.h \
             intbitset_impl.c \
             intbitset_setup.py \
             intbitset_tests.py

all:
	$(PYTHON) $(srcdir)/intbitset_setup.py build_ext

install-data-hook:
	$(PYTHON) $(srcdir)/testimport.py ${prefix}
	$(PYTHON) $(srcdir)/intbitset_setup.py install

CLEANFILES = config.py dbquery.py messages.py $(phplib_DATA) intbitset.c *~ *.tmp *.pyc

clean-local:
	rm -rf build

config.py: config.py.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
      $(top_srcdir)/config/cdswmllib.wml
	$(WML) -o $@ $<

dbquery.py: dbquery.py.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
      $(top_srcdir)/config/cdswmllib.wml
	$(WML) -o $@ $<

messages.py: messages.py.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
      $(top_srcdir)/config/cdswmllib.wml
	$(WML) -o $@ $<

mailutils.py: mailutils.py.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
      $(top_srcdir)/config/cdswmllib.wml
	$(WML) -o $@ $<

errorHandling.php: errorHandling.php.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
      $(top_srcdir)/config/cdswmllib.wml
	$(WML) -o $@ $<
