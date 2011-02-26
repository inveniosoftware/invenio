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

pylib_DATA = session.py webuser.py webuser_tests.py \
	websession_templates.py websession_webinterface.py \
	webgroup.py webgroup_dblayer.py websession_config.py \
	webaccount.py websession_regression_tests.py \
	webgroup_regression_tests.py webuser_regression_tests.py \
	webgroup_tests.py inveniogc.py webuser_config.py \
	websession_web_tests.py

noinst_DATA = password_migration_kit.py

EXTRA_DIST = $(pylib_DATA) $(noinst_DATA)

CLEANFILES = *~ *.tmp *.pyc
