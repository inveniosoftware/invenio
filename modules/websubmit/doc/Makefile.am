## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

SUBDIRS = admin hacking

docdir = $(localstatedir)/www/help/submit

doc_DATA = access.en.html access.fr.html access.de.html access.es.html access.ca.html access.pl.html access.pt.html access.hr.html access.it.html access.ja.html access.ru.html access.sk.html access.cs.html access.no.html access.sv.html access.el.html access.bg.html access.uk.html \
         actions.en.html actions.fr.html actions.de.html actions.es.html actions.ca.html actions.pl.html actions.pt.html actions.hr.html actions.it.html actions.ja.html actions.ru.html actions.sk.html actions.cs.html actions.no.html actions.sv.html actions.el.html actions.bg.html actions.uk.html \
         approval.en.html approval.fr.html approval.de.html approval.pl.html approval.pt.html approval.es.html approval.ca.html approval.hr.html approval.it.html approval.ja.html approval.ru.html approval.sk.html approval.cs.html approval.no.html approval.sv.html approval.el.html approval.bg.html approval.uk.html \
         bibliographic_fields.en.html bibliographic_fields.fr.html bibliographic_fields.de.html bibliographic_fields.es.html bibliographic_fields.ca.html bibliographic_fields.pl.html bibliographic_fields.pt.html bibliographic_fields.hr.html bibliographic_fields.it.html bibliographic_fields.ja.html bibliographic_fields.ru.html bibliographic_fields.sk.html bibliographic_fields.cs.html bibliographic_fields.no.html bibliographic_fields.sv.html bibliographic_fields.el.html bibliographic_fields.bg.html bibliographic_fields.uk.html \
         description.en.html description.fr.html description.de.html description.pl.html description.pt.html description.es.html description.ca.html description.hr.html description.it.html description.ja.html description.ru.html description.sk.html description.cs.html description.no.html description.sv.html description.el.html description.bg.html description.uk.html \
         file_transfer.en.html file_transfer.fr.html file_transfer.de.html file_transfer.es.html file_transfer.ca.html file_transfer.pl.html file_transfer.pt.html file_transfer.hr.html file_transfer.it.html file_transfer.ja.html file_transfer.ru.html file_transfer.sk.html file_transfer.cs.html file_transfer.no.html file_transfer.sv.html file_transfer.el.html file_transfer.bg.html file_transfer.uk.html \
         index.en.html index.fr.html index.de.html index.pl.html index.pt.html index.es.html index.ca.html index.hr.html index.it.html index.ja.html index.ru.html index.sk.html index.cs.html index.no.html index.sv.html index.el.html index.bg.html index.uk.html \
         introduction.en.html introduction.fr.html introduction.de.html introduction.es.html introduction.ca.html introduction.pl.html introduction.pt.html introduction.hr.html introduction.it.html introduction.ja.html introduction.ru.html introduction.sk.html introduction.cs.html introduction.no.html introduction.sv.html introduction.el.html introduction.bg.html introduction.uk.html \
         login.en.html login.fr.html login.de.html login.pl.html login.pt.html login.es.html login.ca.html login.hr.html login.it.html login.ja.html login.ru.html login.sk.html login.cs.html login.no.html login.sv.html login.el.html login.bg.html login.uk.html \
         modification.en.html modification.fr.html modification.de.html modification.es.html modification.ca.html modification.pl.html modification.pt.html modification.hr.html modification.it.html modification.ja.html modification.ru.html modification.sk.html modification.cs.html modification.no.html modification.sv.html modification.el.html modification.bg.html modification.uk.html \
         password.en.html password.fr.html password.de.html password.es.html password.ca.html password.pl.html password.pt.html password.hr.html password.it.html password.ja.html password.ru.html password.sk.html password.cs.html password.no.html password.sv.html password.el.html password.bg.html password.uk.html  \
         pending.en.html pending.fr.html pending.de.html pending.es.html pending.ca.html pending.pl.html pending.pt.html pending.hr.html pending.it.html pending.ja.html pending.ru.html pending.sk.html pending.cs.html pending.no.html pending.sv.html pending.el.html pending.bg.html pending.uk.html \
         approvals.en.html approvals.fr.html approvals.de.html approvals.es.html approvals.ca.html approvals.pl.html approvals.pt.html approvals.hr.html approvals.it.html approvals.ja.html approvals.ru.html approvals.sk.html approvals.cs.html approvals.no.html approvals.sv.html approvals.el.html approvals.bg.html approvals.uk.html \
         revised_version.en.html revised_version.fr.html revised_version.de.html revised_version.es.html revised_version.ca.html revised_version.pl.html revised_version.pt.html revised_version.hr.html revised_version.it.html revised_version.ja.html revised_version.ru.html revised_version.sk.html revised_version.cs.html revised_version.no.html revised_version.sv.html revised_version.el.html revised_version.bg.html revised_version.uk.html \
         submission.en.html submission.fr.html submission.de.html submission.es.html submission.ca.html submission.pl.html submission.pt.html submission.hr.html submission.it.html submission.ja.html submission.ru.html submission.sk.html submission.cs.html submission.no.html submission.sv.html submission.el.html submission.bg.html submission.uk.html \
         subnumber.en.html subnumber.fr.html subnumber.de.html subnumber.es.html subnumber.ca.html subnumber.pl.html subnumber.pt.html subnumber.hr.html subnumber.it.html subnumber.ja.html subnumber.ru.html subnumber.sk.html subnumber.cs.html subnumber.no.html subnumber.sv.html subnumber.el.html subnumber.bg.html subnumber.uk.html

FILESWML   = $(wildcard $(srcdir)/*.wml)
EXTRA_DIST = $(FILESWML:$(srcdir)/%=%)

CLEANFILES = $(doc_DATA) *~ *.tmp *.php

LINGUAS = $(shell grep -v '^\#' $(top_srcdir)/po/LINGUAS)
MO = $(LINGUAS:%=$(top_builddir)/po/%.gmo)

%.en.html %.fr.html %.de.html %.es.html %.ca.html %.pl.html %.pt.html %.hr.html %.it.html %.ja.html %.ru.html %.sk.html %.cs.html %.no.html %.sv.html %.el.html %.bg.html %.uk.html: %.html.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml $(MO)
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$*.en.html \
	       -o\(ALL-LANG_*\)+LANG_FR:$*.fr.html \
	       -o\(ALL-LANG_*\)+LANG_DE:$*.de.html \
	       -o\(ALL-LANG_*\)+LANG_ES:$*.es.html \
	       -o\(ALL-LANG_*\)+LANG_CA:$*.ca.html \
	       -o\(ALL-LANG_*\)+LANG_PL:$*.pl.html \
	       -o\(ALL-LANG_*\)+LANG_PT:$*.pt.html \
	       -o\(ALL-LANG_*\)+LANG_HR:$*.hr.html \
	       -o\(ALL-LANG_*\)+LANG_IT:$*.it.html \
	       -o\(ALL-LANG_*\)+LANG_JA:$*.ja.html \
	       -o\(ALL-LANG_*\)+LANG_RU:$*.ru.html \
	       -o\(ALL-LANG_*\)+LANG_SK:$*.sk.html \
	       -o\(ALL-LANG_*\)+LANG_CS:$*.cs.html \
	       -o\(ALL-LANG_*\)+LANG_NO:$*.no.html \
	       -o\(ALL-LANG_*\)+LANG_SV:$*.sv.html \
	       -o\(ALL-LANG_*\)+LANG_EL:$*.el.html \
	       -o\(ALL-LANG_*\)+LANG_BG:$*.bg.html \
	       -o\(ALL-LANG_*\)+LANG_UK:$*.uk.html $<
	for lang in $(LINGUAS); do \
		$(PYTHON) $(top_srcdir)/po/i18n_update_wml_target.py $${lang} "$*.$${lang}.html" ; \
	done
