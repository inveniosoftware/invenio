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

SUBDIRS = admin hacking

docdir = $(WEBDIR)/help/search

doc_DATA=index.en.html index.fr.html index.de.html index.es.html index.ca.html index.pl.html index.pt.html index.it.html index.ja.html index.ru.html index.sk.html index.cs.html index.no.html index.sv.html index.el.html index.uk.html \
	tips.en.html tips.fr.html tips.de.html tips.pl.html tips.pt.html tips.es.html tips.ca.html tips.it.html tips.ja.html tips.ru.html tips.sk.html tips.cs.html tips.no.html tips.sv.html tips.el.html tips.uk.html \
	guide.en.html guide.fr.html guide.de.html guide.pl.html guide.pt.html guide.es.html guide.ca.html guide.it.html guide.ja.html guide.ru.html guide.sk.html guide.cs.html guide.no.html guide.sv.html guide.el.html guide.uk.html

FILESWML   = $(wildcard $(srcdir)/*.wml)
EXTRA_DIST = $(FILESWML:$(srcdir)/%=%)

CLEANFILES = $(doc_DATA) *~ *.tmp

LINGUAS = $(shell grep -v '^\#' $(top_srcdir)/po/LINGUAS)
MO = $(LINGUAS:%=$(top_builddir)/po/%.gmo)

%.en.html %.fr.html %.de.html %.es.html %.ca.html %.pl.html %.pt.html %.it.html %.ja.html %.ru.html %.sk.html %.cs.html %.no.html %.sv.html %.el.html %.uk.html: %.html.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml $(MO)
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$*.en.html \
	       -o\(ALL-LANG_*\)+LANG_FR:$*.fr.html \
	       -o\(ALL-LANG_*\)+LANG_DE:$*.de.html \
	       -o\(ALL-LANG_*\)+LANG_ES:$*.es.html \
	       -o\(ALL-LANG_*\)+LANG_CA:$*.ca.html \
	       -o\(ALL-LANG_*\)+LANG_PT:$*.pt.html \
	       -o\(ALL-LANG_*\)+LANG_PL:$*.pl.html \
	       -o\(ALL-LANG_*\)+LANG_IT:$*.it.html \
	       -o\(ALL-LANG_*\)+LANG_JA:$*.ja.html \
	       -o\(ALL-LANG_*\)+LANG_RU:$*.ru.html \
	       -o\(ALL-LANG_*\)+LANG_SK:$*.sk.html \
	       -o\(ALL-LANG_*\)+LANG_CS:$*.cs.html \
	       -o\(ALL-LANG_*\)+LANG_NO:$*.no.html \
	       -o\(ALL-LANG_*\)+LANG_SV:$*.sv.html \
	       -o\(ALL-LANG_*\)+LANG_EL:$*.el.html \
	       -o\(ALL-LANG_*\)+LANG_UK:$*.uk.html $<
	for lang in $(LINGUAS); do \
		$(PYTHON) $(top_srcdir)/po/i18n_update_wml.py $${lang} "$*.$${lang}.html" ; \
	done

