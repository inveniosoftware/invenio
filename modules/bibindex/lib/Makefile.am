## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012, 2013 CERN.
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

SUBDIRS = tokenizers

pylibdir = $(libdir)/python/invenio
pylib_DATA = bibindex_engine.py bibindex_engine_config.py bibindex_engine_unit_tests.py \
             bibindexadminlib.py bibindex_engine_stemmer.py bibindex_engine_stopwords.py \
             bibindex_engine_stemmer_unit_tests.py bibindex_engine_stemmer_greek.py \
             bibindex_engine_tokenizer_unit_tests.py \
             bibindex_engine_tokenizer_regression_tests.py \
             bibindexadmin_regression_tests.py bibindex_engine_washer.py \
             bibindex_regression_tests.py bibindex_engine_utils.py \
             bibindex_termcollectors.py bibindex_termcollectors_regression_tests.py
EXTRA_DIST = $(pylib_DATA)

CLEANFILES = *~ *.tmp *.pyc
