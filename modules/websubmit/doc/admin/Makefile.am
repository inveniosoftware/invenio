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

doc_DATA=actionimplement.en.php actionimplement.fr.php actionimplement.de.php actionimplement.es.php actionimplement.pt.php actionimplement.it.php actionimplement.ru.php actionimplement.sk.php actionimplement.cz.php  \
        actionmodify.en.php actionmodify.fr.php actionmodify.de.php actionmodify.es.php actionmodify.pt.php actionmodify.it.php actionmodify.ru.php actionmodify.sk.php actionmodify.cz.php  \
        actionnew.en.php actionnew.fr.php actionnew.de.php actionnew.es.php actionnew.pt.php actionnew.it.php actionnew.ru.php actionnew.sk.php actionnew.cz.php  \
        actionremove.en.php actionremove.fr.php actionremove.de.php actionremove.es.php actionremove.pt.php actionremove.it.php actionremove.ru.php actionremove.sk.php actionremove.cz.php  \
        actions.en.php actions.fr.php actions.de.php actions.es.php actions.pt.php actions.it.php actions.ru.php actions.sk.php actions.cz.php  \
        catalogues.en.php catalogues.fr.php catalogues.de.php catalogues.es.php catalogues.pt.php catalogues.it.php catalogues.ru.php catalogues.sk.php catalogues.cz.php  \
        description.en.php description.fr.php description.de.php description.es.php description.pt.php description.it.php description.ru.php description.sk.php description.cz.php  \
        documentmodify.en.php documentmodify.fr.php documentmodify.de.php documentmodify.es.php documentmodify.pt.php documentmodify.it.php documentmodify.ru.php documentmodify.sk.php documentmodify.cz.php  \
        documentnew.en.php documentnew.fr.php documentnew.de.php documentnew.es.php documentnew.pt.php documentnew.it.php documentnew.ru.php documentnew.sk.php documentnew.cz.php  \
        documentremove.en.php documentremove.fr.php documentremove.de.php documentremove.es.php documentremove.pt.php documentremove.it.php documentremove.ru.php documentremove.sk.php documentremove.cz.php  \
        documents.en.php documents.fr.php documents.de.php documents.es.php documents.pt.php documents.it.php documents.ru.php documents.sk.php documents.cz.php  \
        example.en.php example.fr.php example.de.php example.es.php example.pt.php example.it.php example.ru.php example.sk.php example.cz.php  \
        faq.en.php faq.fr.php faq.de.php faq.es.php faq.pt.php faq.it.php faq.ru.php faq.sk.php faq.cz.php  \
        functiondelete.en.php functiondelete.fr.php functiondelete.de.php functiondelete.es.php functiondelete.pt.php functiondelete.it.php functiondelete.ru.php functiondelete.sk.php functiondelete.cz.php  \
        functiondescription.en.php functiondescription.fr.php functiondescription.de.php functiondescription.es.php functiondescription.pt.php functiondescription.it.php functiondescription.ru.php functiondescription.sk.php functiondescription.cz.php  \
        functionnew.en.php functionnew.fr.php functionnew.de.php functionnew.es.php functionnew.pt.php functionnew.it.php functionnew.ru.php functionnew.sk.php functionnew.cz.php  \
        functions.en.php functions.fr.php functions.de.php functions.es.php functions.pt.php functions.it.php functions.ru.php functions.sk.php functions.cz.php  \
        httpprotection.en.php httpprotection.fr.php httpprotection.de.php httpprotection.es.php httpprotection.pt.php httpprotection.it.php httpprotection.ru.php httpprotection.sk.php httpprotection.cz.php  \
        implementfunctions.en.php implementfunctions.fr.php implementfunctions.de.php implementfunctions.es.php implementfunctions.pt.php implementfunctions.it.php implementfunctions.ru.php implementfunctions.sk.php implementfunctions.cz.php  \
        implementwebform.en.php implementwebform.fr.php implementwebform.de.php implementwebform.es.php implementwebform.pt.php implementwebform.it.php implementwebform.ru.php implementwebform.sk.php implementwebform.cz.php  \
        index.en.php index.fr.php index.de.php index.es.php index.pt.php index.it.php index.ru.php index.sk.php index.cz.php  \
        introduction.en.php introduction.fr.php introduction.de.php introduction.es.php introduction.pt.php introduction.it.php introduction.ru.php introduction.sk.php introduction.cz.php  \
        protection.en.php protection.fr.php protection.de.php protection.es.php protection.pt.php protection.it.php protection.ru.php protection.sk.php protection.cz.php  \
        uploader.en.php uploader.fr.php uploader.de.php uploader.es.php uploader.pt.php uploader.it.php uploader.ru.php uploader.sk.php uploader.cz.php        
EXTRA_DIST = $(wildcard *.wml)

CLEANFILES = $(doc_DATA) *~ *.tmp

%.en.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_EN:$@ $<

%.fr.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_FR:$@ $<

%.de.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_DE:$@ $<

%.es.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_ES:$@ $<

%.pt.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_PT:$@ $<

%.it.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_IT:$@ $<

%.ru.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_RU:$@ $<

%.sk.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_SK:$@ $<

%.cz.php: %.php.wml ../../../../config/config.wml ../../../../config/configbis.wml \
           ../../../../config/messages.wml
	$(WML) -o\(ALL-LANG_*\)+LANG_CZ:$@ $<