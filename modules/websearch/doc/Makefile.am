## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

doc_DATA=index.en.html index.fr.html index.de.html index.es.html index.pt.html index.it.html index.ru.html index.sk.html index.cz.html index.no.html index.se.html \
         tips.en.html tips.fr.html tips.de.html tips.pt.html tips.es.html tips.it.html tips.ru.html tips.sk.html tips.cz.html tips.no.html tips.se.html 

EXTRA_DIST = $(wildcard *.wml)

CLEANFILES = $(doc_DATA) *~ *.tmp

%.en.html %.fr.html %.de.html %.es.html %.pt.html %.it.html %.ru.html %.sk.html %.cz.html %.no.html %.se.html: %.html.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
           $(top_srcdir)/config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$*.en.html \
	       -o\(ALL-LANG_*\)+LANG_FR:$*.fr.html \
	       -o\(ALL-LANG_*\)+LANG_DE:$*.de.html \
	       -o\(ALL-LANG_*\)+LANG_ES:$*.es.html \
	       -o\(ALL-LANG_*\)+LANG_PT:$*.pt.html \
	       -o\(ALL-LANG_*\)+LANG_IT:$*.it.html \
	       -o\(ALL-LANG_*\)+LANG_RU:$*.ru.html \
	       -o\(ALL-LANG_*\)+LANG_SK:$*.sk.html \
	       -o\(ALL-LANG_*\)+LANG_CZ:$*.cz.html \
	       -o\(ALL-LANG_*\)+LANG_NO:$*.no.html \
	       -o\(ALL-LANG_*\)+LANG_SE:$*.se.html $<
