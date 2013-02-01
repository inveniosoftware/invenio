## This file is part of Invenio.
## Copyright (C) 2003, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

SUBDIRS = elements

pylibdir = $(libdir)/python/invenio

pylib_DATA = bibformat_config.py bibformat_templates.py \
             bibformatadminlib.py bibformat_engine.py bibformat_dblayer.py \
             bibformat_utils.py bibformat.py \
             bibformat_manager.py \
             bibformatadmin_regression_tests.py bibformat_engine_unit_tests.py \
             bibformat_bfx_engine.py bibformat_bfx_engine_config.py \
             bibformat_regression_tests.py bibformat_xslt_engine.py bibreformat.py \
             bibformat_web_tests.py bibformat_utils_unit_tests.py

EXTRA_DIST = $(pylib_DATA)

CLEANFILES = *~ *.tmp *.pyc
