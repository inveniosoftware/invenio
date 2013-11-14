## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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
             webaccessadmin_lib.py \
             external_authentication_cern.py \
             external_authentication.py \
             external_authentication_ldap.py \
             external_authentication_cern_wrapper.py \
             external_authentication_cern_unit_tests.py \
             external_authentication_sso.py \
             external_authentication_robot.py \
             webaccess_regression_tests.py \
             external_authentication_oauth1.py \
             external_authentication_oauth2.py \
             external_authentication_openid.py

noinst_DATA = collection_restrictions_migration_kit.py

EXTRA_DIST = $(pylib_DATA) $(noinst_DATA)

CLEANFILES = *~ *.tmp *.pyc
