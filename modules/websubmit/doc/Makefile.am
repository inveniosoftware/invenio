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

doc_DATA=access.en.php access.fr.php access.de.php access.es.php access.pt.php access.it.php access.ru.php access.sk.php access.cz.php access.no.php \
         actions.en.php actions.fr.php actions.de.php actions.es.php actions.pt.php actions.it.php actions.ru.php actions.sk.php actions.cz.php actions.no.php \
         approval.en.php approval.fr.php approval.de.php approval.pt.php approval.es.php approval.it.php approval.ru.php approval.sk.php approval.cz.php approval.no.php \
         bibliographic_fields.en.php bibliographic_fields.fr.php bibliographic_fields.de.php bibliographic_fields.es.php bibliographic_fields.pt.php bibliographic_fields.it.php bibliographic_fields.ru.php bibliographic_fields.sk.php bibliographic_fields.cz.php bibliographic_fields.no.php \
         completed.en.php completed.fr.php completed.de.php completed.es.php completed.pt.php completed.it.php completed.ru.php completed.sk.php completed.cz.php completed.no.php \
         cookies.en.php cookies.fr.php cookies.de.php cookies.es.php cookies.pt.php cookies.it.php cookies.ru.php cookies.sk.php cookies.cz.php cookies.no.php \
         description.en.php description.fr.php description.de.php description.pt.php description.es.php description.it.php description.ru.php description.sk.php description.cz.php description.no.php \
         file_transfer.en.php file_transfer.fr.php file_transfer.de.php file_transfer.es.php file_transfer.pt.php file_transfer.it.php file_transfer.ru.php file_transfer.sk.php file_transfer.cz.php file_transfer.no.php \
         index.en.php index.fr.php index.de.php index.pt.php index.es.php index.it.php index.ru.php index.sk.php index.cz.php index.no.php \
         introduction.en.php introduction.fr.php introduction.de.php introduction.es.php introduction.pt.php introduction.it.php introduction.ru.php introduction.sk.php introduction.cz.php introduction.no.php \
         link.en.php link.fr.php link.de.php link.es.php link.pt.php link.it.php link.ru.php link.sk.php link.cz.php link.no.php \
         login.en.php login.fr.php login.de.php login.pt.php login.es.php login.it.php login.ru.php login.sk.php login.cz.php login.no.php \
         modification.en.php modification.fr.php modification.de.php modification.es.php modification.pt.php modification.it.php modification.ru.php modification.sk.php modification.cz.php modification.no.php \
         password.en.php password.fr.php password.de.php password.es.php password.pt.php password.it.php password.ru.php password.sk.php password.cz.php password.no.php \
         pending.en.php pending.fr.php pending.de.php pending.es.php pending.pt.php pending.it.php pending.ru.php pending.sk.php pending.cz.php pending.no.php \
         revised_version.en.php revised_version.fr.php revised_version.de.php revised_version.es.php revised_version.pt.php revised_version.it.php revised_version.ru.php revised_version.sk.php revised_version.cz.php revised_version.no.php \
         submission.en.php submission.fr.php submission.de.php submission.es.php submission.pt.php submission.it.php submission.ru.php submission.sk.php submission.cz.php submission.no.php \
         subnumber.en.php subnumber.fr.php subnumber.de.php subnumber.es.php subnumber.pt.php subnumber.it.php subnumber.ru.php subnumber.sk.php subnumber.cz.php subnumber.no.php

EXTRA_DIST = $(wildcard *.wml)

CLEANFILES = $(doc_DATA) *~ *.tmp

%.en.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$@ $<

%.fr.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_FR:$@ $<

%.de.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_DE:$@ $<

%.es.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_ES:$@ $<

%.pt.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_PT:$@ $<

%.it.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_IT:$@ $<

%.ru.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_RU:$@ $<

%.sk.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_SK:$@ $<

%.cz.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_CZ:$@ $<

%.no.php: %.php.wml ../../../config/config.wml ../../../config/configbis.wml \
           ../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_NO:$@ $<