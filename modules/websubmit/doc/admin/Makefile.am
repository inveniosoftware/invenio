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

docdir = $(WEBDIR)/admin/websubmit/guide

doc_DATA=actionimplement.en.html actionimplement.fr.html actionimplement.de.html actionimplement.es.html actionimplement.pt.html actionimplement.it.html actionimplement.ru.html actionimplement.sk.html actionimplement.cz.html actionimplement.no.html  \
        actionmodify.en.html actionmodify.fr.html actionmodify.de.html actionmodify.es.html actionmodify.pt.html actionmodify.it.html actionmodify.ru.html actionmodify.sk.html actionmodify.cz.html actionmodify.no.html  \
        actionnew.en.html actionnew.fr.html actionnew.de.html actionnew.es.html actionnew.pt.html actionnew.it.html actionnew.ru.html actionnew.sk.html actionnew.cz.html actionnew.no.html  \
        actionremove.en.html actionremove.fr.html actionremove.de.html actionremove.es.html actionremove.pt.html actionremove.it.html actionremove.ru.html actionremove.sk.html actionremove.cz.html actionremove.no.html  \
        actions.en.html actions.fr.html actions.de.html actions.es.html actions.pt.html actions.it.html actions.ru.html actions.sk.html actions.cz.html actions.no.html  \
        catalogues.en.html catalogues.fr.html catalogues.de.html catalogues.es.html catalogues.pt.html catalogues.it.html catalogues.ru.html catalogues.sk.html catalogues.cz.html catalogues.no.html  \
        description.en.html description.fr.html description.de.html description.es.html description.pt.html description.it.html description.ru.html description.sk.html description.cz.html description.no.html  \
        documentmodify.en.html documentmodify.fr.html documentmodify.de.html documentmodify.es.html documentmodify.pt.html documentmodify.it.html documentmodify.ru.html documentmodify.sk.html documentmodify.cz.html documentmodify.no.html  \
        documentnew.en.html documentnew.fr.html documentnew.de.html documentnew.es.html documentnew.pt.html documentnew.it.html documentnew.ru.html documentnew.sk.html documentnew.cz.html documentnew.no.html  \
        documentremove.en.html documentremove.fr.html documentremove.de.html documentremove.es.html documentremove.pt.html documentremove.it.html documentremove.ru.html documentremove.sk.html documentremove.cz.html documentremove.no.html  \
        documents.en.html documents.fr.html documents.de.html documents.es.html documents.pt.html documents.it.html documents.ru.html documents.sk.html documents.cz.html documents.no.html  \
        example.en.html example.fr.html example.de.html example.es.html example.pt.html example.it.html example.ru.html example.sk.html example.cz.html example.no.html  \
        faq.en.html faq.fr.html faq.de.html faq.es.html faq.pt.html faq.it.html faq.ru.html faq.sk.html faq.cz.html faq.no.html  \
        functiondelete.en.html functiondelete.fr.html functiondelete.de.html functiondelete.es.html functiondelete.pt.html functiondelete.it.html functiondelete.ru.html functiondelete.sk.html functiondelete.cz.html functiondelete.no.html  \
        functionedit.en.html functionedit.fr.html functionedit.de.html functionedit.es.html functionedit.pt.html functionedit.it.html functionedit.ru.html functionedit.sk.html functionedit.cz.html functionedit.no.html  \
        functiondescription.en.html functiondescription.fr.html functiondescription.de.html functiondescription.es.html functiondescription.pt.html functiondescription.it.html functiondescription.ru.html functiondescription.sk.html functiondescription.cz.html functiondescription.no.html  \
        functionnew.en.html functionnew.fr.html functionnew.de.html functionnew.es.html functionnew.pt.html functionnew.it.html functionnew.ru.html functionnew.sk.html functionnew.cz.html functionnew.no.html  \
        functions.en.html functions.fr.html functions.de.html functions.es.html functions.pt.html functions.it.html functions.ru.html functions.sk.html functions.cz.html functions.no.html  \
        implementfunctions.en.html implementfunctions.fr.html implementfunctions.de.html implementfunctions.es.html implementfunctions.pt.html implementfunctions.it.html implementfunctions.ru.html implementfunctions.sk.html implementfunctions.cz.html implementfunctions.no.html  \
        implementwebform.en.html implementwebform.fr.html implementwebform.de.html implementwebform.es.html implementwebform.pt.html implementwebform.it.html implementwebform.ru.html implementwebform.sk.html implementwebform.cz.html implementwebform.no.html  \
        index.en.html index.fr.html index.de.html index.es.html index.pt.html index.it.html index.ru.html index.sk.html index.cz.html index.no.html  \
        protection.en.html protection.fr.html protection.de.html protection.es.html protection.pt.html protection.it.html protection.ru.html protection.sk.html protection.cz.html protection.no.html  \
        bibconvert.en.html bibconvert.fr.html bibconvert.de.html bibconvert.es.html bibconvert.pt.html bibconvert.it.html bibconvert.ru.html bibconvert.sk.html bibconvert.cz.html bibconvert.no.html   \
        introduction.en.html introduction.fr.html introduction.de.html introduction.es.html introduction.pt.html introduction.it.html introduction.ru.html introduction.sk.html introduction.cz.html introduction.no.html
EXTRA_DIST = $(wildcard *.wml)

CLEANFILES = $(doc_DATA) *~ *.tmp *.php

%.fr.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_FR:$@ $<

%.en.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$@ $<

%.de.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_DE:$@ $<

%.es.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_ES:$@ $<

%.pt.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_PT:$@ $<

%.it.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_IT:$@ $<

%.ru.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_RU:$@ $<

%.sk.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_SK:$@ $<

%.cz.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_CZ:$@ $<

%.no.html: %.html.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_NO:$@ $<