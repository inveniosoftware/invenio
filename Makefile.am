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

SUBDIRS = config modules

EXTRA_DIST = UNINSTALL .wmlrc configure-tests.py

## submit stuff for demo data link creation
sbmdir = $(WEBDIR)/submit/access/protected
sbmdat = SBITEXT MBITEXT FTTTEXT SRVTEXT TFUTEXT \
	 SBIRTEXT MBIRTEXT FTTRTEXT SRVRTEXT TFURTEXT APPRTEXT \
	 SBIPICT MBIPICT FTTPICT \
         SBIRPICT MBIRPICT FTTRPICT APPRPICT

all:
	@echo "**************************************************************"
	@echo "** CDSware has been successfully built.  Proceed now by     **"
	@echo "** running 'make install'.                                  **"
	@echo "**************************************************************"

install-data-local:
	mkdir -p @prefix@/var
	mkdir -p @prefix@/var/cache
	mkdir -p @prefix@/var/log
	mkdir -p @prefix@/var/tmp
	chmod -R ug=rwx @prefix@/var
	@echo "**************************************************************"
	@echo "** CDSware has been successfully installed!                 **"
	@echo "**                                                          **"
	@echo "** If you are installing CDSware for the first time, we     **"
	@echo "** recommend you to run 'make create-demo-site' now to      **"
	@echo "** to test your installation.                               **"
	@echo "**                                                          **"
	@echo "** If you are reinstalling CDSware because you have been    **"
	@echo "** editing CDSware sources or its WML configuration, you    **"
	@echo "** may want to restart your Apache server now by running    **"
	@echo "** 'apachectl restart'.                                     **"
	@echo "**************************************************************"

uninstall-local:
	rm -rf @prefix@/var

create-tables: local-dbexec local-tabfill
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabcreate.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabfill.sql

drop-tables: local-dbexec 
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabdrop.sql

local-dbexec: ./modules/miscutil/bin/dbexec.wml
	(cd ./modules/miscutil/bin; make)

local-tabfill: ./modules/miscutil/sql/tabfill.sql.wml
	(cd ./modules/miscutil/sql; make)

create-demo-site: install
# 	for f in $(sbmdat); do \
# 	    if [ ! -e $(sbmdir)/$$f.shtml ]; then \
# 		ln -s $(sbmdir)/go.shtml $(sbmdir)/$$f.shtml ; \
# 	    else \
# 		echo "link $(sbmdir)/$$f.shtml already exists"; \
# 	    fi \
# 	done
	./modules/miscutil/bin/dbexec < ./modules/miscutil/demo/democfgdata.sql
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec 
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/webcoll
	${prefix}/bin/webcoll 1
	@echo "***********************************************************************"
	@echo "** The demo site has been successfully created.                      **"
	@echo "**                                                                   **"
	@echo "** Please point your browser to @WEBURL@ "
	@echo "** It should ressemble our 'Atlantis Institute of Fictive Science'   **"
	@echo "** demo site that is available at <http://cdsware.cern.ch/demo/>,    **"
	@echo "** with the exception that no demo records have been loaded yet.     **"
	@echo "**                                                                   **"
	@echo "** To load demo records, you can run 'make load-demo-records'.       **"
	@echo "** To drop the demo site, you can run 'make drop-demo-site'.         **"
	@echo "***********************************************************************"

load-demo-records: install
	${prefix}/bin/dbexec < ./modules/miscutil/sql/tabbibclean.sql
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec 
	${prefix}/bin/bibupload -i ./modules/miscutil/demo/demobibdata.xml
	${prefix}/bin/bibupload 1
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/bibindex
	${prefix}/bin/bibindex 2
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/bibreformat -oHB,HD,HP,HC
	${prefix}/bin/bibreformat 3
	${prefix}/bin/bibupload 4
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/webcoll
	${prefix}/bin/webcoll 5
	@echo "***********************************************************************"
	@echo "** The demo records have been successfully loaded.                   **"
	@echo "**                                                                   **"
	@echo "** Please point your browser to @WEBURL@ "
	@echo "** It should ressemble our 'Atlantis Institute of Fictive Science'   **"
	@echo "** demo site that is available at <http://cdsware.cern.ch/demo/>.    **"
	@echo "**                                                                   **"
	@echo "** To remove demo records, you can run 'make remove-demo-records'.   **"
	@echo "** To drop also the demo site collection etc configurations,         **"
	@echo "** you can run 'make drop-demo-site'.                                **"
	@echo "***********************************************************************"

drop-demo-site: install
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabdrop.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabcreate.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabfill.sql
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec 
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/webcoll
	${prefix}/bin/webcoll 1
#	for f in $(sbmdat); do rm -f $(sbmdir)/$$f.shtml ; done
	@echo "***************************************************************"
	@echo "** The demo site and records have been successfully dropped. **"
	@echo "***************************************************************"

remove-demo-records: install
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabbibclean.sql
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec 
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/webcoll 
	${prefix}/bin/webcoll 1
	@echo "**********************************************************"
	@echo "** The demo records have been successfully removed.     **"
	@echo "** The demo collection and submit configurations        **"
	@echo "** have been preserved.                                 **"
	@echo "**                                                      **"
	@echo "** Note that you can run 'make drop-demo-site' to drop  **"
	@echo "** the demo site fully.                                 **"
	@echo "**********************************************************"

CLEANFILES = *~
