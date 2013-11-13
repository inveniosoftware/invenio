## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

bibdocfilepluginsdir = $(libdir)/python/invenio/bibdocfile_plugins

bibdocfileplugins_DATA = bom_*.py

pylibdir = $(libdir)/python/invenio

pylib_DATA = bibdocfile_config.py file.py \
             bibdocfile_templates.py \
             bibdocfile_managedocfiles.py \
             bibdocfile.py \
             bibdocfilecli.py \
             bibdocfile_regression_tests.py

noinst_DATA = fulltext_files_migration_kit.py icon_migration_kit.py

EXTRA_DIST = $(pylib_DATA) $(noinst_DATA) $(bibdocfileplugins)

CLEANFILES = *~ *.tmp *.pyc
