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

docdir = $(WEBDIR)/help/submit

doc_DATA=access.en.html access.fr.html access.de.html access.es.html access.pt.html access.it.html access.ru.html access.sk.html access.cs.html access.no.html access.sv.html access.el.html \
         actions.en.html actions.fr.html actions.de.html actions.es.html actions.pt.html actions.it.html actions.ru.html actions.sk.html actions.cs.html actions.no.html actions.sv.html actions.el.html \
         approval.en.html approval.fr.html approval.de.html approval.pt.html approval.es.html approval.it.html approval.ru.html approval.sk.html approval.cs.html approval.no.html approval.sv.html approval.el.html \
         bibliographic_fields.en.html bibliographic_fields.fr.html bibliographic_fields.de.html bibliographic_fields.es.html bibliographic_fields.pt.html bibliographic_fields.it.html bibliographic_fields.ru.html bibliographic_fields.sk.html bibliographic_fields.cs.html bibliographic_fields.no.html bibliographic_fields.sv.html bibliographic_fields.el.html \
         description.en.html description.fr.html description.de.html description.pt.html description.es.html description.it.html description.ru.html description.sk.html description.cs.html description.no.html description.sv.html description.el.html \
         file_transfer.en.html file_transfer.fr.html file_transfer.de.html file_transfer.es.html file_transfer.pt.html file_transfer.it.html file_transfer.ru.html file_transfer.sk.html file_transfer.cs.html file_transfer.no.html file_transfer.sv.html file_transfer.el.html \
         index.en.html index.fr.html index.de.html index.pt.html index.es.html index.it.html index.ru.html index.sk.html index.cs.html index.no.html index.sv.html index.el.html \
         introduction.en.html introduction.fr.html introduction.de.html introduction.es.html introduction.pt.html introduction.it.html introduction.ru.html introduction.sk.html introduction.cs.html introduction.no.html introduction.sv.html introduction.el.html \
         login.en.html login.fr.html login.de.html login.pt.html login.es.html login.it.html login.ru.html login.sk.html login.cs.html login.no.html login.sv.html login.el.html \
         modification.en.html modification.fr.html modification.de.html modification.es.html modification.pt.html modification.it.html modification.ru.html modification.sk.html modification.cs.html modification.no.html modification.sv.html modification.el.html \
         password.en.html password.fr.html password.de.html password.es.html password.pt.html password.it.html password.ru.html password.sk.html password.cs.html password.no.html password.sv.html password.el.html  \
         pending.en.html pending.fr.html pending.de.html pending.es.html pending.pt.html pending.it.html pending.ru.html pending.sk.html pending.cs.html pending.no.html pending.sv.html pending.el.html \
         approvals.en.html approvals.fr.html approvals.de.html approvals.es.html approvals.pt.html approvals.it.html approvals.ru.html approvals.sk.html approvals.cs.html approvals.no.html approvals.sv.html approvals.el.html \
         revised_version.en.html revised_version.fr.html revised_version.de.html revised_version.es.html revised_version.pt.html revised_version.it.html revised_version.ru.html revised_version.sk.html revised_version.cs.html revised_version.no.html revised_version.sv.html revised_version.el.html \
         submission.en.html submission.fr.html submission.de.html submission.es.html submission.pt.html submission.it.html submission.ru.html submission.sk.html submission.cs.html submission.no.html submission.sv.html submission.el.html \
         subnumber.en.html subnumber.fr.html subnumber.de.html subnumber.es.html subnumber.pt.html subnumber.it.html subnumber.ru.html subnumber.sk.html subnumber.cs.html subnumber.no.html subnumber.sv.html subnumber.el.html

FILESWML   = $(wildcard $(srcdir)/*.wml)
EXTRA_DIST = $(FILESWML:$(srcdir)/%=%)

CLEANFILES = $(doc_DATA) *~ *.tmp *.php

%.en.html %.fr.html %.de.html %.es.html %.pt.html %.it.html %.ru.html %.sk.html %.cs.html %.no.html %.sv.html %.el.html: %.html.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml \
           $(top_srcdir)/config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$*.en.html \
	       -o\(ALL-LANG_*\)+LANG_FR:$*.fr.html \
	       -o\(ALL-LANG_*\)+LANG_DE:$*.de.html \
	       -o\(ALL-LANG_*\)+LANG_ES:$*.es.html \
	       -o\(ALL-LANG_*\)+LANG_PT:$*.pt.html \
	       -o\(ALL-LANG_*\)+LANG_IT:$*.it.html \
	       -o\(ALL-LANG_*\)+LANG_RU:$*.ru.html \
	       -o\(ALL-LANG_*\)+LANG_SK:$*.sk.html \
	       -o\(ALL-LANG_*\)+LANG_CS:$*.cs.html \
	       -o\(ALL-LANG_*\)+LANG_NO:$*.no.html \
	       -o\(ALL-LANG_*\)+LANG_SV:$*.sv.html \
	       -o\(ALL-LANG_*\)+LANG_EL:$*.el.html $<
