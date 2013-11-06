## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

pylib_DATA = \
             websubmit_dblayer.py \
             websubmit_webinterface.py \
             websubmit_templates.py \
             websubmit_regression_tests.py \
             websubmitadmin_config.py \
             websubmitadmin_dblayer.py \
             websubmitadmin_engine.py \
             websubmitadmin_templates.py \
             websubmitadmin_regression_tests.py \
             websubmit_file_stamper.py \
             websubmit_icon_creator.py \
             websubmit_file_converter.py \
             hocrlib.py \
             websubmit_file_metadata.py \
             websubmit_web_tests.py \
             websubmitadmincli.py

metadataplugindir = $(libdir)/python/invenio/websubmit_file_metadata_plugins
metadataplugin_DATA = __init__.py \
                      wsm_extractor_plugin.py \
                      wsm_pyexiv2_plugin.py \
                      wsm_pdftk_plugin.py

EXTRA_DIST = $(pylib_DATA) $(metadataplugin_DATA)

CLEANFILES = *~ *.tmp *.pyc
