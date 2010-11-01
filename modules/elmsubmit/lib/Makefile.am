## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
pylib_DATA = elmsubmit.py elmsubmit_misc.py elmsubmit_config.py \
             elmsubmit_enriched2txt.py elmsubmit_EZArchive.py elmsubmit_EZEmail.py \
             elmsubmit_field_validation.py elmsubmit_filename_generator.py \
             elmsubmit_html2txt.py elmsubmit_richtext2txt.py \
             elmsubmit_generate_marc.py elmsubmit_submission_parser.py \
             myhtmlentitydefs.py mime.types.edited elmsubmit_tests.py

tmpdir = $(prefix)/var/tmp
tmp_DATA =  elmsubmit_tests_1.mbox elmsubmit_tests_2.mbox

EXTRA_DIST = $(pylib_DATA) $(tmp_DATA) mime.types.edited

CLEANFILES = *~ *.tmp *.pyc