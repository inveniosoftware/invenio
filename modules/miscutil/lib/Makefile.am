## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
##
# Invenio is free software; you can redistribute it and/or
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
             crossrefutils.py \
             dataciteutils_tester.py \
             dbdump.py \
             dbquery_regression_tests.py \
             dbquery_unit_tests.py \
             errorlib_regression_tests.py \
             errorlib_webinterface.py \
             flaskshell.py \
             invenio_connector.py \
             invenio_connector_regression_tests.py \
             inveniocfg_unit_tests.py \
             inveniomanage_unit_tests.py \
             miscutil_model.py \
             plotextractor.py \
             plotextractor_config.py \
             plotextractor_converter.py \
             plotextractor_getter.py \
             plotextractor_output_utils.py \
             plotextractor_regression_tests.py \
             plotextractor_unit_tests.py \
             pluginutils.py \
             pluginutils_unit_tests.py \
             remote_debugger.py \
             remote_debugger_config.py \
             remote_debugger_wsgi_reload.py \
             sequtils.py \
             sequtils_cnum.py \
             sequtils_regression_tests.py \
             sherpa_romeo_testing.py \
             solrutils_bibrank_indexer.py \
             solrutils_regression_tests.py \
             testutils_regression_tests.py \
             w3c_validator.py \
             xapianutils_bibrank_indexer.py

noinst_DATA = testimport.py \
              kwalitee.py \
              pep8.py

tmpdir = $(prefix)/var/tmp

EXTRA_DIST = $(pylib_DATA) \
             $(tmp_DATA) \
             testimport.py \
             kwalitee.py \
             pep8.py \
             solrutils \
             solrutils/schema.xml \
             solrutils/java_sources.txt \
             solrutils/org \
             solrutils/org/invenio_software \
             solrutils/org/invenio_software/solr \
             solrutils/org/invenio_software/solr/BitSetFieldCollector.java \
             solrutils/org/invenio_software/solr/InvenioFacetComponent.java \
             solrutils/org/invenio_software/solr/FieldCollectorBase.java \
             solrutils/org/invenio_software/solr/IntFieldCollector.java \
             solrutils/org/invenio_software/solr/FieldCollector.java \
             solrutils/org/invenio_software/solr/InvenioQueryComponent.java \
             solrutils/org/invenio_software/solr/InvenioBitsetStreamResponseWriter.java \
             solrutils/org/invenio_software/solr/InvenioBitSet.java \
             solrutils/org/invenio_software/solr/StringFieldCollector.java \
             solrutils/solrconfig.xml

install-data-hook:
	$(PYTHON) $(srcdir)/testimport.py ${prefix}

CLEANFILES = *~ *.tmp *.pyc

clean-local:
	rm -rf build
