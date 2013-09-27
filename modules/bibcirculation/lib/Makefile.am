## $Id: Makefile.am,v 1.4 2008/08/25 13:23:38 joaquim Exp $

## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2013 CERN.
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

pylib_DATA = bibcirculation.py \
             bibcirculation_cern_ldap.py \
             bibcirculation_config.py \
             bibcirculation_daemon.py \
             bibcirculation_dblayer.py \
             bibcirculation_regression_tests.py \
             bibcirculation_templates.py \
             bibcirculation_utils.py \
             bibcirculation_webinterface.py \
             bibcirculationadmin_webinterface.py \
             bibcirculationadminlib.py

EXTRA_DIST = $(pylib_DATA)

CLEANFILES = *~ *.tmp *.pyc
