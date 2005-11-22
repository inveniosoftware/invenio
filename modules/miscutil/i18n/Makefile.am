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

LANGUAGES = ca cs de el en es fr it no pt ru sk sv uk

FILES = `find $(top_srcdir)/modules "("  -name "*.py" -or -name "*.wml" ")" -a -not "(" -name '*.php.wml' -o -name '*.html.wml' -o -wholename "*/miscutil/i18n/*" ")"`

MO = $(LANGUAGES:%=%.mo)

localedir = $(prefix)/share/locale

all: $(MO)

install-data-hook: all
	for f in $(LANGUAGES) ; \
	  do $(mkinstalldirs) $(localedir)/$${f}/LC_MESSAGES ; \
	  $(INSTALL_DATA) $${f}.mo \
	  $(localedir)/$${f}/LC_MESSAGES/cdsware.mo ; \
	done

check-translations:
	@echo "** checking if the list of declared languages matches the po files in this directory"
	@rm -f ,,intl-1.tmp
	@for l in $(LANGUAGES) ; do \
	  echo $${l}.po >> ,,intl-1.tmp ; \
	done
	@cat ,,intl-1.tmp | sort > ,,intl-1 && rm -f ,,intl-1.tmp
	@find $(srcdir) -name '??.po' -exec basename {} \; | sort > ,,intl-2
	@diff ,,intl-1 ,,intl-2
	@rm -f ,,intl-1 ,,intl-2
	@echo "** statistics on individual translation files"
	@for f in $(LANGUAGES) ; do \
	  echo "$$f: "`msgfmt --statistics $$f.po -o /dev/null 2>&1` ; \
	done

update-po-files:
	$(PYTHON) $(srcdir)/i18n-import-messages.py $(top_srcdir)/config/messages.wml
	$(PYTHON) $(srcdir)/i18n-update-potfile.py -d cdsware $(FILES)
	for f in $(LANGUAGES) ; do \
		msgmerge -C compendium-$${f}.po -U $(srcdir)/$${f}.po cdsware.pot; \
	done

%.mo: %.po
	$(PYTHON) $(srcdir)/i18n-check-translation.py $<
	msgfmt $< -o $@
