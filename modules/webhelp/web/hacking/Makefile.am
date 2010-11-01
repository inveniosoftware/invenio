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

docdir = $(localstatedir)/www/hacking
doc_DATA = cdsware.el

imgdir = $(localstatedir)/www/img/hacking
img_DATA = modules-overview-diagram.jpeg

webdoclibdir = $(libdir)/webdoc/invenio/hacking
webdoclib_DATA = \
	hacking.webdoc \
	modules-overview.webdoc \
	coding-style.webdoc \
	common-concepts.webdoc \
	directory-organization.webdoc \
	release-numbering.webdoc \
	test-suite.webdoc \
	fckeditor.webdoc

EXTRA_DIST = $(webdoclib_DATA) $(doc_DATA) $(img_DATA)

CLEANFILES = *~ *.tmp
