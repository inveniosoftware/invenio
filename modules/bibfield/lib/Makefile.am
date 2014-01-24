## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013 CERN.
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

SUBDIRS = functions

pylibdir = $(libdir)/python/invenio

pylib_DATA = bibfield.py \
			 bibfield_reader.py \
             bibfield_config_engine.py \
             bibfield_config_engine_unit_tests.py \
             bibfield_jsonreader.py \
             bibfield_marcreader.py \
             bibfield_marcreader_unit_tests.py \
             bibfield_regression_tests.py \
             bibfield_utils.py

EXTRA_DIST = $(pylib_DATA)

CLEANFILES = *~ *.tmp *.pyc
