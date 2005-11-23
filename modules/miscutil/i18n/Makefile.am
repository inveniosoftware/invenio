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

ALL_LINGUAS = @ALL_LINGUAS@

MO = $(ALL_LINGUAS:%=%.mo)
PO = $(ALL_LINGUAS:%=%.po)

CLEANFILES = $(MO)
EXTRA_DIST = $(PO) i18n-check-translation.py

localedir = $(prefix)/share/locale

all: $(MO)

%.mo: %.po
	$(PYTHON) $(srcdir)/i18n-check-translation.py $<
	msgfmt $< -o $@

install-data-hook: all
	for f in $(LANGUAGES) ; \
	  do $(mkinstalldirs) $(localedir)/$${f}/LC_MESSAGES ; \
	  $(INSTALL_DATA) $${f}.mo \
	  $(localedir)/$${f}/LC_MESSAGES/cdsware.mo ; \
	done

# The following targets are for developpers and translators

PYFILES = `find $(top_srcdir)/modules "("  -name "*.py" -o -name "*.wml" -o -name "*.in" ")" -a -not "(" -name '*.php.wml' -o -name '*.html.wml' -o -wholename "*/miscutil/i18n/*" -o -name "Makefile.in" ")"`

WMLFILES = `find $(top_srcdir)/modules -name "*.html.wml"`

check-translations:
	@echo "** checking if the list of declared languages matches the po files in this directory"
	@rm -f ,,intl-1.tmp
	@for l in $(ALL_LINGUAS) ; do \
	  echo $${l}.po >> ,,intl-1.tmp ; \
	done
	@cat ,,intl-1.tmp | sort > ,,intl-1 && rm -f ,,intl-1.tmp
	@find $(srcdir) -name '??.po' -exec basename {} \; | sort > ,,intl-2
	@diff ,,intl-1 ,,intl-2
	@rm -f ,,intl-1 ,,intl-2
	@echo "** statistics on individual translation files"
	@for f in $(ALL_LINGUAS) ; do \
	  echo "$$f: "`msgfmt --statistics $$f.po -o /dev/null 2>&1` ; \
	done

update-po-files:
	$(PYTHON) $(srcdir)/i18n-import-messages.py $(top_srcdir)/config/messages.wml
	$(PYTHON) $(srcdir)/i18n-update-potfile.py -d python $(PYFILES)
	$(PYTHON) $(srcdir)/i18n-extract-from-wml.py $(WMLFILES) > wml.pot
	msgcat wml.pot python.pot > cdsware.pot
	for f in $(ALL_LINGUAS) ; do \
		msgmerge -C compendium-$${f}.po -U $(srcdir)/$${f}.po cdsware.pot; \
	done

