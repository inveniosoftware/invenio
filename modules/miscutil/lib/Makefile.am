## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

SUBDIRS = upgrades

pylibdir = $(libdir)/python/invenio

pylib_DATA = __init__.py \
             errorlib.py \
             errorlib_unit_tests.py \
             errorlib_webinterface.py \
             errorlib_regression_tests.py \
             data_cacher.py \
             dbdump.py \
             web_api_key.py \
             web_api_key_regression_tests.py \
             dbquery.py \
             dbquery_unit_tests.py \
             dbquery_regression_tests.py \
             dataciteutils.py \
             dataciteutils_tester.py \
             logicutils.py \
             logicutils_unit_tests.py \
             mailutils.py \
             miscutil_config.py \
             messages.py \
             messages_unit_tests.py \
             textutils.py \
             textutils_unit_tests.py \
             dateutils.py \
             dateutils_unit_tests.py \
             htmlutils.py \
             htmlutils_unit_tests.py \
             testutils.py \
             testutils_regression_tests.py \
             inveniocfg_upgrader.py \
             inveniocfg_upgrader_unit_tests.py \
             invenio_connector.py \
             invenio_connector_regression_tests.py \
             urlutils.py \
             urlutils_unit_tests.py \
             w3c_validator.py \
             importutils.py \
             importutils_unit_tests.py \
             intbitset_unit_tests.py \
             intbitset_helper.py \
             inveniocfg.py \
             inveniocfg_unit_tests.py \
             shellutils.py \
             shellutils_unit_tests.py \
             pluginutils.py \
             pluginutils_unit_tests.py \
             redisutils.py \
             plotextractor.py \
             plotextractor_converter.py \
             plotextractor_getter.py \
             plotextractor_output_utils.py \
             plotextractor_unit_tests.py \
             plotextractor_regression_tests.py \
             plotextractor_config.py \
             solrutils_bibindex_indexer.py \
             solrutils_bibindex_searcher.py \
             solrutils_bibrank_indexer.py \
             solrutils_bibrank_searcher.py \
             solrutils_config.py \
             solrutils_regression_tests.py \
             solrutils_unit_tests.py \
             xapianutils_bibindex_indexer.py \
             xapianutils_bibindex_searcher.py \
             xapianutils_bibrank_indexer.py \
             xapianutils_bibrank_searcher.py \
             xapianutils_config.py \
             remote_debugger.py \
             remote_debugger_config.py \
             remote_debugger_wsgi_reload.py \
             jsonutils.py \
             jsonutils_unit_tests.py \
             sequtils_cnum.py \
             sequtils.py \
             sequtils_regression_tests.py \
             memoiseutils.py \
             memoiseutils_unit_tests.py \
             crossrefutils.py \
             containerutils.py \
             sequtils_texkey.py \
             hepdatautils.py \
             hepdatadisplayutils.py \
             hepdatautils_unit_tests.py \
             filedownloadutils.py \
             filedownloadutils_unit_tests.py

jsdir=$(localstatedir)/www/js

js_DATA = jquery.mathpreview.js

noinst_DATA = testimport.py \
              kwalitee.py \
              pep8.py

tmpdir = $(prefix)/var/tmp

tmp_DATA = intbitset_example.int

EXTRA_DIST = $(pylib_DATA) \
             $(tmp_DATA) \
             $(js_DATA) \
             testimport.py \
             kwalitee.py \
             pep8.py \
             intbitset.pyx \
             intbitset.c \
             intbitset.h \
             intbitset_impl.c \
             intbitset_setup.py \
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

all:
	$(PYTHON) $(srcdir)/intbitset_setup.py build_ext

install-data-hook:
	$(PYTHON) $(srcdir)/testimport.py ${prefix}
	find ${srcdir} -name intbitset.so -exec cp {} ${pylibdir}/.intbitset.so \;
	mv ${pylibdir}/.intbitset.so ${pylibdir}/intbitset.so

CLEANFILES = *~ *.tmp *.pyc

clean-local:
	rm -rf build
