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

EXTRA_DIST = UNINSTALL .wmlrc

## submit stuff for demo data link creation
sbmdir = $(WEBDIR)submit/access/protected
sbmdat = SBITEXT MBITEXT FTTTEXT SRVTEXT TFUTEXT \
	 SBIRTEXT MBIRTEXT FTTRTEXT SRVRTEXT TFURTEXT APPRTEXT \
	 SBIPICT MBIPICT FTTPICT \
         SBIRPICT MBIRPICT FTTRPICT APPRPICT

install-data-local:
	mkdir -p @prefix@/var
	mkdir -p @prefix@/var/cache
	mkdir -p @prefix@/var/log
	chmod -R ug=rwx @prefix@/var

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
	${prefix}/bin/webcoll update-reclist
	${prefix}/bin/webcoll update-webpage
	rm -f index.wml
	@echo "***********************************************************************"
	@echo "** The demo site has been successfully created.                      **"
	@echo "** Please point your browser to @WEBURL@ "
	@echo "** It should ressemble our 'Atlantis Institute of Science' demo site **"
	@echo "** that is available at <http://cdsware.cern.ch/DEMO/>,              **"
	@echo "** with the exception that no demo records have been loaded yet.     **"
	@echo "**                                                                   **"
	@echo "** To load demo records, you can run 'make load-demo-records'.       **"
	@echo "** To destroy the demo site, you can run 'make destroy-demo-site'.   **"
	@echo "***********************************************************************"

load-demo-records: install
	${prefix}/bin/bibupload ./modules/miscutil/demo/demobibdata.xml
	${prefix}/bin/bibwords -ucds.support@cern.ch
	${prefix}/bin/bibwords 1
	@LYNX@ -source '@WEBURL@/search.py?rg=100&of=xm' > z.xml
	${prefix}/bin/bibformat otype=HB,HD,HP,HC < ./z.xml > ./zf.xml
	${prefix}/bin/bibupload -f ./zf.xml
	rm -f z.xml zf.xml
	${prefix}/bin/webcoll update-reclist
	${prefix}/bin/webcoll update-webpage
	rm -f index.wml
	@echo "***********************************************************************"
	@echo "** The demo records have been successfully loaded.                   **"
	@echo "** Please point your browser to @WEBURL@ "
	@echo "** It should ressemble our 'Atlantis Institute of Science' demo site **"
	@echo "** that is available at <http://cdsware.cern.ch/DEMO/>.              **"
	@echo "** You should be able to do some searches, etc.                      **"
	@echo "**                                                                   **"
	@echo "** To remove demo records, you can run 'make remove-demo-records'.   **"
	@echo "** To remove also the demo site collection etc configurations,       **"
	@echo "** you can run 'make destroy-demo-site'.                             **"
	@echo "***********************************************************************"

destroy-demo-site: install
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabdrop.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabcreate.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabfill.sql
	${prefix}/bin/webcoll update-reclist
	${prefix}/bin/webcoll update-webpage
	rm -f index.wml
	for f in $(sbmdat); do rm -f $(sbmdir)/$$f.shtml ; done
	@echo "*****************************************************************"
	@echo "** The demo site and records have been successfully destroyed. **"
	@echo "*****************************************************************"

remove-demo-records: install
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabbibclean.sql
	${prefix}/bin/webcoll update-reclist
	${prefix}/bin/webcoll update-webpage
	rm -f index.wml
	@echo "**************************************************************"
	@echo "** The demo records have been successfully removed.         **"
	@echo "** The demo collection and submit configurations            **"
	@echo "** have been preserved.                                     **"
	@echo "**                                                          **"
	@echo "** Note that you can run 'make destroy-demo-site' to remove **"
	@echo "** the demo site fully.                                     **"
	@echo "**************************************************************"

CLEANFILES = *~ index.wml
