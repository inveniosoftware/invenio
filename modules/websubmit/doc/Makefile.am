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

SUBDIRS = admin

docdir = $(WEBDIR)/help/submit

doc_DATA=access.en.html access.fr.html access.de.html access.es.html access.pt.html access.it.html access.ru.html access.sk.html access.cz.html access.no.html access.se.html \
         actions.en.html actions.fr.html actions.de.html actions.es.html actions.pt.html actions.it.html actions.ru.html actions.sk.html actions.cz.html actions.no.html actions.se.html \
         approval.en.html approval.fr.html approval.de.html approval.pt.html approval.es.html approval.it.html approval.ru.html approval.sk.html approval.cz.html approval.no.html approval.se.html \
         bibliographic_fields.en.html bibliographic_fields.fr.html bibliographic_fields.de.html bibliographic_fields.es.html bibliographic_fields.pt.html bibliographic_fields.it.html bibliographic_fields.ru.html bibliographic_fields.sk.html bibliographic_fields.cz.html bibliographic_fields.no.html bibliographic_fields.se.html \
         description.en.html description.fr.html description.de.html description.pt.html description.es.html description.it.html description.ru.html description.sk.html description.cz.html description.no.html description.se.html \
         file_transfer.en.html file_transfer.fr.html file_transfer.de.html file_transfer.es.html file_transfer.pt.html file_transfer.it.html file_transfer.ru.html file_transfer.sk.html file_transfer.cz.html file_transfer.no.html file_transfer.se.html \
         index.en.html index.fr.html index.de.html index.pt.html index.es.html index.it.html index.ru.html index.sk.html index.cz.html index.no.html index.se.html \
         introduction.en.html introduction.fr.html introduction.de.html introduction.es.html introduction.pt.html introduction.it.html introduction.ru.html introduction.sk.html introduction.cz.html introduction.no.html introduction.se.html \
         login.en.html login.fr.html login.de.html login.pt.html login.es.html login.it.html login.ru.html login.sk.html login.cz.html login.no.html login.se.html \
         modification.en.html modification.fr.html modification.de.html modification.es.html modification.pt.html modification.it.html modification.ru.html modification.sk.html modification.cz.html modification.no.html modification.se.html \
         password.en.html password.fr.html password.de.html password.es.html password.pt.html password.it.html password.ru.html password.sk.html password.cz.html password.no.html password.se.html \
         pending.en.html pending.fr.html pending.de.html pending.es.html pending.pt.html pending.it.html pending.ru.html pending.sk.html pending.cz.html pending.no.html pending.se.html \
         approvals.en.html approvals.fr.html approvals.de.html approvals.es.html approvals.pt.html approvals.it.html approvals.ru.html approvals.sk.html approvals.cz.html approvals.no.html approvals.se.html \
         revised_version.en.html revised_version.fr.html revised_version.de.html revised_version.es.html revised_version.pt.html revised_version.it.html revised_version.ru.html revised_version.sk.html revised_version.cz.html revised_version.no.html revised_version.se.html \
         submission.en.html submission.fr.html submission.de.html submission.es.html submission.pt.html submission.it.html submission.ru.html submission.sk.html submission.cz.html submission.no.html submission.se.html \
         subnumber.en.html subnumber.fr.html subnumber.de.html subnumber.es.html subnumber.pt.html subnumber.it.html subnumber.ru.html subnumber.sk.html subnumber.cz.html subnumber.no.html subnumber.se.html

EXTRA_DIST = $(wildcard *.wml)

CLEANFILES = $(doc_DATA) *~ *.tmp *.php

%.en.html %.fr.html %.de.html %.es.html %.pt.html %.it.html %.ru.html %.sk.html %.cz.html %.no.html %.se.html: %.html.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
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
