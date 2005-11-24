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

confignicedir = $(sysconfdir)/build
confignice_SCRIPTS=config.nice

SUBDIRS = po m4 config modules

EXTRA_DIST = config.rpath  UNINSTALL RELEASE-NOTES configure-tests.py config.nice.in

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

test:
	@if [ -e @prefix@/bin/testsuite ]; then \
	    @prefix@/bin/testsuite ; \
	else \
	    echo "Hmm, testsuite does not seem to be installed.  Please do 'make install' first."; \
	fi

install-data-local:
	for d in / /cache /log /tmp /data ; do		\
		mkdir -p $(localstatedir)$$d &&		\
		chmod ug=rwx $(localstatedir)$$d ;	\
	done
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


create-tables: local-dbexec local-tabfill
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabfill.sql

update-v0.3.0-tables update-v0.3.1-tables: local-dbexec
	echo "ALTER TABLE idxINDEXNAME CHANGE id_idxINDEX id_idxINDEX mediumint(9) unsigned NOT NULL FIRST;" | ./modules/miscutil/bin/dbexec 
	echo "ALTER TABLE rnkMETHODNAME CHANGE id_rnkMETHOD id_rnkMETHOD mediumint(9) unsigned NOT NULL FIRST;" | ./modules/miscutil/bin/dbexec 
	echo "ALTER TABLE collectionname CHANGE id_collection id_collection mediumint(9) unsigned NOT NULL FIRST;" | ./modules/miscutil/bin/dbexec 
	echo "ALTER TABLE formatname CHANGE id_format id_format mediumint(9) unsigned NOT NULL FIRST;" | ./modules/miscutil/bin/dbexec 
	echo "ALTER TABLE fieldname CHANGE id_field id_field mediumint(9) unsigned NOT NULL FIRST;" | ./modules/miscutil/bin/dbexec 
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runbibrank','run BibRank','','no');" | ./modules/miscutil/bin/dbexec 
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgbibrank','configure BibRank','','no');" | ./modules/miscutil/bin/dbexec 

update-v0.3.2-tables: local-dbexec
	echo "ALTER TABLE sbmCOLLECTION_sbmDOCTYPE CHANGE id_son id_son char(10) NOT NULL default '0';" | ./modules/miscutil/bin/dbexec 

update-v0.3.3-tables: local-dbexec 
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE flxLINKTYPEPARAMS CHANGE pname pname varchar(78) NOT NULL default '';" | ./modules/miscutil/bin/dbexec 
	echo "ALTER TABLE rnkMETHOD DROP star_category_ranges;" | ./modules/miscutil/bin/dbexec
	echo "DROP TABLE rnkSET;" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE arguments arguments LONGTEXT;" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE status status varchar(50);" | ./modules/miscutil/bin/dbexec

update-v0.5.0-tables: local-dbexec 
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE session ADD INDEX uid (uid);" | ./modules/miscutil/bin/dbexec 
	echo "UPDATE idxINDEXNAME SET ln='cs' WHERE ln='cz';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE rnkMETHODNAME SET ln='cs' WHERE ln='cz';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE collectionname SET ln='cs' WHERE ln='cz';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE collection_portalbox SET ln='cs' WHERE ln='cz';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE formatname SET ln='cs' WHERE ln='cz';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE fieldname SET ln='cs' WHERE ln='cz';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE idxINDEXNAME SET ln='sv' WHERE ln='se';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE rnkMETHODNAME SET ln='sv' WHERE ln='se';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE collectionname SET ln='sv' WHERE ln='se';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE collection_portalbox SET ln='sv' WHERE ln='se';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE formatname SET ln='sv' WHERE ln='se';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE fieldname SET ln='sv' WHERE ln='se';" | ./modules/miscutil/bin/dbexec

update-v0.7.1-tables: local-dbexec
	echo "DROP TABLE oaiHARVEST;" | ./modules/miscutil/bin/dbexec 
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runoaiharvest','run BibHarvest oaiharvest','','no');" | ./modules/miscutil/bin/dbexec 
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgbibharvest','configure BibHarvest','','no');" | ./modules/miscutil/bin/dbexec 

drop-tables: local-dbexec 
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabdrop.sql

local-dbexec: 
	(cd ./modules/miscutil/bin; make)

local-tabfill: $(srcdir)/modules/miscutil/sql/tabfill.sql.wml
	(cd ./modules/miscutil/sql; make)

create-demo-site: 
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

load-demo-records: 
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec 
	${prefix}/bin/bibupload -i $(srcdir)/modules/miscutil/demo/demobibdata.xml
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
	@echo ""
	@echo "***********************************************************************"
	@echo "** You will be asked for a username, please enter admin email below. **"
	@echo "***********************************************************************"
	@echo ""
	${prefix}/bin/bibrank
	${prefix}/bin/bibrank 6
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

drop-demo-site: 
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabdrop.sql
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabcreate.sql
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

remove-demo-records: 
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabbibclean.sql
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

ACLOCAL_AMFLAGS = -I m4
