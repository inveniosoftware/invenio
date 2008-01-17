## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

confignicedir = $(sysconfdir)/build
confignice_SCRIPTS=config.nice

SUBDIRS = po config modules

EXTRA_DIST = UNINSTALL THANKS RELEASE-NOTES configure-tests.py config.nice.in

# current jsMath version and packages
JSMV = 3.4f
JSMFV = 1.3
JSMATH = jsMath-$(JSMV).zip
JSMATHFONTS = jsMath-fonts-$(JSMFV).zip

## submit stuff for demo data link creation
sbmdir = $(localstatedir)/www/submit/access/protected
sbmdat = SBITEXT MBITEXT FTTTEXT SRVTEXT TFUTEXT \
	 SBIRTEXT MBIRTEXT FTTRTEXT SRVRTEXT TFURTEXT APPRTEXT \
	 SBIPICT MBIPICT FTTPICT \
         SBIRPICT MBIRPICT FTTRPICT APPRPICT

all:
	@echo "**************************************************************"
	@echo "** CDS Invenio has been successfully built.                 **"
	@echo "**                                                          **"
	@echo "** If you are upgrading and you have previously customized  **"
	@echo "** page templates (see WebStyle Admin guide), please        **"
	@echo "** run now 'make check-custom-templates' in order to ensure **"
	@echo "** that they are still valid.                               **"
	@echo "**                                                          **"
	@echo "** Otherwise you can proceed to do 'make install' now.      **"
	@echo "**************************************************************"

test:
	@if [ -e @prefix@/bin/testsuite ]; then \
	    @prefix@/bin/testsuite ; \
	else \
	    echo "Hmm, testsuite does not seem to be installed.  Please do 'make install' first."; \
	fi

regression-test:
	@if [ -e @prefix@/bin/regressiontestsuite ]; then \
	    @prefix@/bin/regressiontestsuite ; \
	else \
	    echo "Hmm, regressiontestsuite does not seem to be installed.  Please do 'make install' first."; \
	fi

check-custom-templates:
	$(PYTHON) $(top_srcdir)/modules/webstyle/lib/template.py --check-custom-templates $(top_srcdir)

kwalitee-check:
	$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py $(top_srcdir)

kwalitee-check-errors-only:
	find $(top_srcdir) -name '*.py' -exec pylint -e {} \; 2> /dev/null

kwalitee-check-variables:
	find $(top_srcdir) -name '*.py' -exec pylint --reports=n --enable-checker=variables {} \; 2> /dev/null

kwalitee-check-sql-queries:
	@echo "* Listing potentially dangerous SQL queries:"
	@echo "* 1) SQL INSERT queries without explicit column list:"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'INSERT INTO ([[:alnum:]]|_)+[[:space:]]*VALUES' {} \; 2> /dev/null
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'INSERT INTO ([[:alnum:]]|_)+[[:space:]]*$$' {} \; 2> /dev/null
	@echo "* 2) SQL queries using charset-ignorant escape_string():"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'escape_string' {} \; 2> /dev/null
	@echo "* 3) SQL queries using literal '%s':"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin "run_sql.*'%[dfis]'" {} \; 2> /dev/null
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'run_sql.*"%[dfis]"' {} \; 2> /dev/null
	@echo "* 4) SQL queries with potentially unescaped arguments:"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'run_sql.* % ' {} \; 2> /dev/null
	@echo "* Done."

etags:
	\rm -f $(top_srcdir)/TAGS
	(cd $(top_srcdir) && find $(top_srcdir) -name "*.py" -print | xargs etags)

install-data-local:
	for d in / /cache /log /tmp /data /run ; do	\
		mkdir -p $(localstatedir)$$d &&		\
		chmod ug=rwx $(localstatedir)$$d ;	\
	done
	@echo "************************************************************"
	@echo "** CDS Invenio has been successfully installed!           **"
	@echo "**                                                        **"
	@echo "** If you are installing CDS Invenio for the first time,  **"
	@echo "** please continue with the Apache httpd configuration    **"
	@echo "** step, as described in the INSTALL file.                **"
	@echo "** Afterwards you may want to run 'make create-demo-site' **"
	@echo "** to test your new installation.                         **"
	@echo "**                                                        **"
	@echo "** If you are reinstalling CDS Invenio because you have   **"
	@echo "** edited CDS Invenio sources or its WML configuration,   **"
	@echo "** you may want to restart your Apache server now by      **"
	@echo "** running 'sudo apachectl restart'.                      **"
	@echo "************************************************************"

install-jsmath-plugin:
	@echo "***********************************************************"
	@echo "** Installing jsMath plugin, please wait...              **"
	@echo "***********************************************************"
	rm -rf /tmp/invenio-jsmath-plugin
	mkdir /tmp/invenio-jsmath-plugin
	(cd /tmp/invenio-jsmath-plugin && \
	wget 'http://downloads.sourceforge.net/jsmath/$(JSMATH)' && \
	wget 'http://downloads.sourceforge.net/jsmath/$(JSMATHFONTS)' && \
	wget 'http://www.math.union.edu/~dpvc/jsMath/download/extra-fonts/msam10/msam10.zip' && \
	wget 'http://www.math.union.edu/~dpvc/jsMath/download/extra-fonts/msbm10/msbm10.zip' && \
	unzip -u -d ${prefix}/var/www $(JSMATH) && \
	unzip -u -d ${prefix}/var/www $(JSMATHFONTS) && \
	unzip -u -d ${prefix}/var/www/jsMath/fonts msam10.zip && \
	unzip -u -d ${prefix}/var/www/jsMath/fonts msbm10.zip)
	rm -fr /tmp/invenio-jsmath-plugin
	@echo "* Installing Invenio-specific jsMath config..."
	(cd $(top_srcdir)/modules/webstyle/etc && make install)
	@echo "***********************************************************"
	@echo "** The jsMath plugin was successfully installed.         **"
	@echo "** Please do not forget to properly set the              **"
	@echo "** CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS in config.wml.   **"
	@echo "***********************************************************"

uninstall-jsmath-plugin:
	@rm -rvf ${prefix}/var/www/jsMath
	@echo "***********************************************************"
	@echo "** The jsMath plugin was successfully removed.           **"
	@echo "***********************************************************"

create-tables: local-dbexec local-tabfill
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabfill.sql
	@echo "**************************************************************"
	@echo "** The database tables were successfully created.           **"
	@echo "**************************************************************"

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
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgbibharvest','configure BibHarvest','','no');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runoaiharvest','run BibHarvest oaiharvest','','no');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgwebcomment','configure WebComment','','no');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runoaiarchive','run BibHarvest oaiarchive','','no');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runbibedit','run BibEdit','','no');" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user ADD nickname varchar(255) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user ADD last_login datetime NOT NULL default '0000-00-00 00:00:00';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user ADD INDEX nickname (nickname);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE sbmFIELD CHANGE subname subname varchar(13) default NULL;" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user_query_basket CHANGE alert_name alert_name varchar(30) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "TRUNCATE TABLE session;" | ./modules/miscutil/bin/dbexec
	@echo "**********************************************************"
	@echo "** Do not forget to run the basket migration now:       **"
	@echo "**    @PYTHON@ modules/webbasket/lib/webbasket_migration_kit.py "
	@echo "** Please see the RELEASE-NOTES for details.           **"
	@echo "**********************************************************"
	@echo "INSERT INTO oaiARCHIVE (id, setName, setSpec, setDescription, setDefinition, setRecList) SELECT id, setName, setSpec, CONCAT_WS('', setDescription), setDefinition, setRecList FROM oaiSET;"

update-v0.90.0-tables: local-dbexec
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE format ADD COLUMN (description varchar(255) default '');" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE format ADD COLUMN (content_type varchar(255) default '');" | ./modules/miscutil/bin/dbexec

update-v0.90.1-tables: local-dbexec
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE schTASK ADD INDEX status (status);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE schTASK ADD INDEX runtime (runtime);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE sbmCATEGORIES ADD COLUMN score TINYINT UNSIGNED NOT NULL DEFAULT 0;" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE sbmCATEGORIES ADD PRIMARY KEY (doctype, sname);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE sbmCATEGORIES ADD KEY doctype (doctype);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiHARVEST ADD COLUMN setspecs TEXT NOT NULL DEFAULT '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE setDescription setDescription text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE p1 p1 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE f1 f1 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE m1 m1 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE p2 p2 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE f2 f2 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE m2 m2 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE p3 p3 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE f3 f3 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE m3 m3 text NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE bibdoc SET status=0 WHERE status='';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE bibdoc SET status=1 WHERE status='deleted';" | ./modules/miscutil/bin/dbexec

update-v0.92.0-tables: local-dbexec
	echo "UPDATE bibdoc SET status=0 WHERE status='';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE bibdoc SET status=1 WHERE status='deleted';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE arguments arguments mediumblob;" | ./modules/miscutil/bin/dbexec
	echo "UPDATE user SET note=1 WHERE nickname='admin' AND note IS NULL;" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE usergroup CHANGE name name varchar(255) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE usergroup ADD login_method varchar(255) NOT NULL default 'INTERNAL';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE usergroup ADD UNIQUE KEY login_method_name (login_method(70), name);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user CHANGE settings settings blob default NULL;" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Get_Recid', 'This function gets the recid for a document with a given report-number (as stored in the global variable rn).');" | ./modules/miscutil/bin/dbexec

update-v0.92.1-tables: local-dbexec
	./modules/miscutil/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "UPDATE bibdoc SET status='DELETED' WHERE status='1';" | ./modules/miscutil/bin/dbexec
	echo "UPDATE bibdoc SET status='' WHERE status='0';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiHARVEST CHANGE postprocess postprocess varchar(20) NOT NULL default 'h';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE oaiHARVEST ADD COLUMN bibfilterprogram varchar(255) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE idxINDEXNAME CHANGE ln ln char(5) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE rnkMETHODNAME CHANGE ln ln char(5) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE collectionname CHANGE ln ln char(5) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE collection_portalbox CHANGE ln ln char(5) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE formatname CHANGE ln ln char(5) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE fieldname CHANGE ln ln char(5) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE accROLE ADD COLUMN firerole_def_ser tinyblob NULL;" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE accROLE ADD COLUMN firerole_def_src tinytext NULL;" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION VALUES (NULL,'accrestrcoll','view restricted collection','collection','no');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION VALUES (NULL,'runsessiongc','run SessionGC','','no');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION VALUES (NULL,'viewrestrcoll','view restricted document','status','no');" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user_accROLE ADD COLUMN expiration datetime NOT NULL default '9999-12-31 23:59:59';" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE user DROP INDEX id, ADD PRIMARY KEY id (id);" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE format ADD COLUMN visibility TINYINT NOT NULL default 1;" | ./modules/miscutil/bin/dbexec
	echo "drop table rnkCITATIONDATA" | ./modules/miscutil/bin/dbexec
	echo "CREATE table rnkCITATIONDATA (id mediumint(8) unsigned default NULL, object_name varchar(255) NOT NULL, object_value longblob, last_updated datetime NOT NULL default '0000-00-00') TYPE=MyISAM;" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO rnkCITATIONDATA VALUES (1,'citationdict','','');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO rnkCITATIONDATA VALUES (2,'reversedict','','');" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO rnkCITATIONDATA VALUES (3,'selfcitdict','','');" | ./modules/miscutil/bin/dbexec
	echo "ALTER TABLE idxINDEX ADD COLUMN stemming_language VARCHAR(10) NOT NULL default '';" | ./modules/miscutil/bin/dbexec
	echo "INSERT INTO accACTION VALUES (NULL,'cfgoairepository','Configure OAI Repository','','no');" | ./modules/miscutil/bin/dbexec


drop-tables: local-dbexec
	@if [ "$(FORCE)" != "yes" ]; then \
	    echo "***********************************************************************"; \
	    echo "** WARNING: You are going to destroy your database tables!           **"; \
	    echo "** Press Ctrl-C if you want to abort this action.                    **"; \
	    echo "** Press ENTER to proceed to destroy your tables.                    **"; \
	    echo "***********************************************************************"; \
	    read; \
	fi
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabdrop.sql
	@echo "**************************************************************"
	@echo "** The database tables were successfully dropped.           **"
	@echo "**************************************************************"

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
	./modules/webaccess/bin/webaccessadmin -u admin -c
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec
	${prefix}/bin/webcoll -uadmin
	${prefix}/bin/webcoll 1
	@echo "***********************************************************************"
	@echo "** The demo site has been successfully created.                      **"
	@echo "**                                                                   **"
	@echo "** Please point your browser to @WEBURL@ "
	@echo "** It should ressemble our 'Atlantis Institute of Fictive Science'   **"
	@echo "** demo site that is available at <http://cdsware.cern.ch:8000/>,    **"
	@echo "** with the exception that no demo records have been loaded yet.     **"
	@echo "**                                                                   **"
	@echo "** To load demo records, you can run 'make load-demo-records'.       **"
	@echo "** To drop the demo site, you can run 'make drop-demo-site'.         **"
	@echo "***********************************************************************"

load-demo-records:
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec
	${prefix}/bin/bibupload -i $(srcdir)/modules/miscutil/demo/demobibdata.xml
	${prefix}/bin/bibupload 1
	${prefix}/bin/bibindex -uadmin
	${prefix}/bin/bibindex 2
	${prefix}/bin/bibreformat -uadmin -oHB
	${prefix}/bin/bibreformat 3
	${prefix}/bin/bibupload 4
	${prefix}/bin/webcoll -uadmin
	${prefix}/bin/webcoll 5
	${prefix}/bin/bibrank -uadmin
	${prefix}/bin/bibrank 6
	@echo "***********************************************************************"
	@echo "** The demo records have been successfully loaded.                   **"
	@echo "**                                                                   **"
	@echo "** Please point your browser to @WEBURL@ "
	@echo "** It should ressemble our 'Atlantis Institute of Fictive Science'   **"
	@echo "** demo site that is available at <http://cdsware.cern.ch:8000/>.    **"
	@echo "**                                                                   **"
	@echo "** To remove demo records, you can run 'make remove-demo-records'.   **"
	@echo "** To drop also the demo site collection etc configurations,         **"
	@echo "** you can run 'make drop-demo-site'.                                **"
	@echo "***********************************************************************"

drop-demo-site:
	@if [ "$(FORCE)" != "yes" ]; then \
	    echo "***********************************************************************"; \
	    echo "** WARNING: You are going to destroy your site and documents!        **"; \
	    echo "** Press Ctrl-C if you want to abort this action.                    **"; \
	    echo "** Press ENTER to proceed to destroy your site.                      **"; \
	    echo "***********************************************************************"; \
	    read; \
	fi
	rm -rf ${prefix}/var/data/files/*
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabdrop.sql
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabcreate.sql
	./modules/miscutil/bin/dbexec < ./modules/miscutil/sql/tabfill.sql
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec
	${prefix}/bin/webcoll -uadmin
	${prefix}/bin/webcoll 1
#	for f in $(sbmdat); do rm -f $(sbmdir)/$$f.shtml ; done
	@echo "***************************************************************"
	@echo "** The demo site and records have been successfully dropped. **"
	@echo "***************************************************************"

remove-demo-records:
	@if [ "$(FORCE)" != "yes" ]; then \
	    echo "***********************************************************************"; \
	    echo "** WARNING: You are going to destroy your records and documents!     **"; \
	    echo "** Press Ctrl-C if you want to abort this action.                    **"; \
	    echo "** Press ENTER to proceed to destroy your records.                   **"; \
	    echo "***********************************************************************"; \
	    read; \
	fi
	rm -rf ${prefix}/var/data/files/*
	./modules/miscutil/bin/dbexec < $(srcdir)/modules/miscutil/sql/tabbibclean.sql
	echo "TRUNCATE schTASK;" | ${prefix}/bin/dbexec
	${prefix}/bin/webcoll -uadmin
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
