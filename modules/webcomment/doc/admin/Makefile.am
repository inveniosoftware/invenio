## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

docdir = $(WEBDIR)/admin/webcomment

doc_DATA = guide.html

FILESWML   = $(wildcard $(srcdir)/*.wml)
EXTRA_DIST = $(FILESWML:$(srcdir)/%=%)

CLEANFILES = $(doc_DATA) *~ *.tmp

%.html: %.html.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml $(top_srcdir)/config/cdsnavbar.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$@ $<
	$(PYTHON) $(top_srcdir)/po/i18n_update_wml_target.py en $@