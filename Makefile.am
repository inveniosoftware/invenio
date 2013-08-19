## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2011, 2012, 2013 CERN.
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

EXTRA_DIST = UNINSTALL THANKS RELEASE-NOTES configure-tests.py config.nice.in \
             config.rpath

# current jsMath version and packages
JSMV = v3.5
JSMFV = 1.3
JSMATH = jsMath-$(JSMV).zip
JSMATHFONTS = jsMath-fonts-$(JSMFV).zip

# git-version-get stuff:
BUILT_SOURCES = $(top_srcdir)/.version
$(top_srcdir)/.version:
	echo $(VERSION) > $@-t && mv $@-t $@
dist-hook:
	echo $(VERSION) > $(distdir)/.tarball-version

check-custom-templates:
	$(PYTHON) $(top_srcdir)/modules/webstyle/lib/template.py --check-custom-templates $(top_srcdir)

kwalitee-check:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py $(top_srcdir)

kwalitee-check-errors-only:
	@find $(top_srcdir) -name '*.py' -exec pylint -e {} \; 2> /dev/null

kwalitee-check-variables:
	@find $(top_srcdir) -name '*.py' -exec pylint --reports=n --enable-checker=variables {} \; 2> /dev/null

kwalitee-check-indentation:
	@find $(top_srcdir) -name '*.py' -exec pylint --reports=n --enable-checker=format {} 2> /dev/null \; | grep -E '(^\*|indentation)'

kwalitee-check-sql-queries:
	@echo "* Listing potentially dangerous SQL queries:"
	@echo "** SQL SELECT queries without explicit column list:"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'SELECT \* FROM' {} \; 2> /dev/null
	@echo "** SQL INSERT queries without explicit column list:"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'INSERT INTO ([[:alnum:]]|_)+[[:space:]]*VALUES' {} \; 2> /dev/null
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'INSERT INTO ([[:alnum:]]|_)+[[:space:]]*$$' {} \; 2> /dev/null
	@echo "** SQL queries using charset-ignorant escape_string():"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'escape_string' {} \; 2> /dev/null
	@echo "** SQL queries using literal '%s':"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin "run_sql.*'%[dfis]'" {} \; 2> /dev/null
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'run_sql.*"%[dfis]"' {} \; 2> /dev/null
	@echo "** SQL queries with potentially unescaped arguments:"
	@find $(top_srcdir) -name '*.py' -exec grep -HEin 'run_sql.* % ' {} \; 2> /dev/null
	@echo "* Done."

etags:
	\rm -f $(top_srcdir)/TAGS
	(cd $(top_srcdir) && find $(top_srcdir) -name "*.py" -print | xargs etags)

install-data-local:
	for d in / /cache /log /tmp /data /run ; do	\
		mkdir -p $(localstatedir)$$d ;		\
	done
	@echo "************************************************************"
	@echo "** CDS Invenio software has been successfully installed!  **"
	@echo "**                                                        **"
	@echo "** You may proceed to customizing your installation now.  **"
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
	@echo "** Please do not forget to properly set the option       **"
	@echo "** CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS in invenio.conf. **"
	@echo "***********************************************************"

uninstall-jsmath-plugin:
	@rm -rvf ${prefix}/var/www/jsMath
	@echo "***********************************************************"
	@echo "** The jsMath plugin was successfully removed.           **"
	@echo "***********************************************************"

update-v0.3.0-tables update-v0.3.1-tables:
	echo "ALTER TABLE idxINDEXNAME CHANGE id_idxINDEX id_idxINDEX mediumint(9) unsigned NOT NULL FIRST;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkMETHODNAME CHANGE id_rnkMETHOD id_rnkMETHOD mediumint(9) unsigned NOT NULL FIRST;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE collectionname CHANGE id_collection id_collection mediumint(9) unsigned NOT NULL FIRST;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE formatname CHANGE id_format id_format mediumint(9) unsigned NOT NULL FIRST;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE fieldname CHANGE id_field id_field mediumint(9) unsigned NOT NULL FIRST;" | ${prefix}/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runbibrank','run BibRank','','no');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgbibrank','configure BibRank','','no');" | ${prefix}/bin/dbexec

update-v0.3.2-tables:
	echo "ALTER TABLE sbmCOLLECTION_sbmDOCTYPE CHANGE id_son id_son char(10) NOT NULL default '0';" | ${prefix}/bin/dbexec

update-v0.3.3-tables:
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE flxLINKTYPEPARAMS CHANGE pname pname varchar(78) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkMETHOD DROP star_category_ranges;" | ${prefix}/bin/dbexec
	echo "DROP TABLE rnkSET;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE arguments arguments LONGTEXT;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE status status varchar(50);" | ${prefix}/bin/dbexec

update-v0.5.0-tables:
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE session ADD INDEX uid (uid);" | ${prefix}/bin/dbexec
	echo "UPDATE idxINDEXNAME SET ln='cs' WHERE ln='cz';" | ${prefix}/bin/dbexec
	echo "UPDATE rnkMETHODNAME SET ln='cs' WHERE ln='cz';" | ${prefix}/bin/dbexec
	echo "UPDATE collectionname SET ln='cs' WHERE ln='cz';" | ${prefix}/bin/dbexec
	echo "UPDATE collection_portalbox SET ln='cs' WHERE ln='cz';" | ${prefix}/bin/dbexec
	echo "UPDATE formatname SET ln='cs' WHERE ln='cz';" | ${prefix}/bin/dbexec
	echo "UPDATE fieldname SET ln='cs' WHERE ln='cz';" | ${prefix}/bin/dbexec
	echo "UPDATE idxINDEXNAME SET ln='sv' WHERE ln='se';" | ${prefix}/bin/dbexec
	echo "UPDATE rnkMETHODNAME SET ln='sv' WHERE ln='se';" | ${prefix}/bin/dbexec
	echo "UPDATE collectionname SET ln='sv' WHERE ln='se';" | ${prefix}/bin/dbexec
	echo "UPDATE collection_portalbox SET ln='sv' WHERE ln='se';" | ${prefix}/bin/dbexec
	echo "UPDATE formatname SET ln='sv' WHERE ln='se';" | ${prefix}/bin/dbexec
	echo "UPDATE fieldname SET ln='sv' WHERE ln='se';" | ${prefix}/bin/dbexec

update-v0.7.1-tables:
	echo "DROP TABLE oaiHARVEST;" | ${prefix}/bin/dbexec
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgbibharvest','configure BibHarvest','','no');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runoaiharvest','run BibHarvest oaiharvest','','no');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'cfgwebcomment','configure WebComment','','no');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runoaiarchive','run BibHarvest oaiarchive','','no');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accACTION (id,name,description,allowedkeywords,optional) VALUES (NULL,'runbibedit','run BibEdit','','no');" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user ADD nickname varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user ADD last_login datetime NOT NULL default '0000-00-00 00:00:00';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user ADD INDEX nickname (nickname);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmFIELD CHANGE subname subname varchar(13) default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user_query_basket CHANGE alert_name alert_name varchar(30) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "TRUNCATE TABLE session;" | ${prefix}/bin/dbexec
	@echo "**********************************************************"
	@echo "** Do not forget to run the basket migration now:       **"
	@echo "**    @PYTHON@ modules/webbasket/lib/webbasket_migration_kit.py "
	@echo "** Please see the RELEASE-NOTES for details.           **"
	@echo "**********************************************************"
	@echo "INSERT INTO oaiARCHIVE (id, setName, setSpec, setDescription, setDefinition, setRecList) SELECT id, setName, setSpec, CONCAT_WS('', setDescription), setDefinition, setRecList FROM oaiSET;"

update-v0.90.0-tables:
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE format ADD COLUMN (description varchar(255) default '');" | ${prefix}/bin/dbexec
	echo "ALTER TABLE format ADD COLUMN (content_type varchar(255) default '');" | ${prefix}/bin/dbexec

update-v0.90.1-tables:
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE schTASK ADD INDEX status (status);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK ADD INDEX runtime (runtime);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmCATEGORIES ADD COLUMN score TINYINT UNSIGNED NOT NULL DEFAULT 0;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmCATEGORIES ADD PRIMARY KEY (doctype, sname);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmCATEGORIES ADD KEY doctype (doctype);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiHARVEST ADD COLUMN setspecs TEXT NOT NULL DEFAULT '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE setDescription setDescription text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE p1 p1 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE f1 f1 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE m1 m1 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE p2 p2 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE f2 f2 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE m2 m2 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE p3 p3 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE f3 f3 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiARCHIVE CHANGE m3 m3 text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "UPDATE bibdoc SET status=0 WHERE status='';" | ${prefix}/bin/dbexec
	echo "UPDATE bibdoc SET status=1 WHERE status='deleted';" | ${prefix}/bin/dbexec

update-v0.92.0-tables:
	echo "UPDATE bibdoc SET status=0 WHERE status='';" | ${prefix}/bin/dbexec
	echo "UPDATE bibdoc SET status=1 WHERE status='deleted';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE arguments arguments mediumblob;" | ${prefix}/bin/dbexec
	echo "UPDATE user SET note=1 WHERE nickname='admin' AND note IS NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE usergroup CHANGE name name varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE usergroup ADD login_method varchar(255) NOT NULL default 'INTERNAL';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE usergroup ADD UNIQUE KEY login_method_name (login_method(70), name);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user CHANGE settings settings blob default NULL;" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Get_Recid', 'This function gets the recid for a document with a given report-number (as stored in the global variable rn).');" | ${prefix}/bin/dbexec

update-v0.92.1-tables:
	echo "DROP TABLE rnkCITATIONDATA;" | ${prefix}/bin/dbexec
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "UPDATE bibdoc SET status='DELETED' WHERE status='1';" | ${prefix}/bin/dbexec
	echo "UPDATE bibdoc SET status='' WHERE status='0';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibrec ADD KEY creation_date (creation_date);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibrec ADD KEY modification_date (modification_date);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc ADD KEY creation_date (creation_date);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc ADD KEY modification_date (modification_date);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc ADD KEY docname (docname);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiHARVEST CHANGE postprocess postprocess varchar(20) NOT NULL default 'h';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiHARVEST ADD COLUMN bibfilterprogram varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE idxINDEXNAME CHANGE ln ln char(5) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE idxINDEX ADD COLUMN stemming_language VARCHAR(10) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkMETHODNAME CHANGE ln ln char(5) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkDOWNLOADS CHANGE id_bibdoc id_bibdoc mediumint(9) unsigned default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkDOWNLOADS CHANGE file_format file_format varchar(10) NULL default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE collectionname CHANGE ln ln char(5) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE collection_portalbox CHANGE ln ln char(5) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE format ADD COLUMN visibility TINYINT NOT NULL default 1;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE formatname CHANGE ln ln char(5) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE fieldname CHANGE ln ln char(5) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE accROLE ADD COLUMN firerole_def_ser blob NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE accROLE ADD COLUMN firerole_def_src text NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user_accROLE ADD COLUMN expiration datetime NOT NULL default '9999-12-31 23:59:59';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user DROP INDEX id, ADD PRIMARY KEY id (id);" | ${prefix}/bin/dbexec
	echo -e 'from invenio.dbquery import run_sql;\
	map(lambda index_id: run_sql("ALTER TABLE idxPHRASE%02dF CHANGE term term TEXT NULL DEFAULT NULL, DROP INDEX term, ADD INDEX term (term (50))" % index_id[0]), run_sql("select id from idxINDEX"))' | $(PYTHON)
	echo "INSERT INTO rnkCITATIONDATA VALUES (1,'citationdict','','');" | ${prefix}/bin/dbexec
	echo "INSERT INTO rnkCITATIONDATA VALUES (2,'reversedict','','');" | ${prefix}/bin/dbexec
	echo "INSERT INTO rnkCITATIONDATA VALUES (3,'selfcitdict','','');" | ${prefix}/bin/dbexec

update-v0.99.0-tables:
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "ALTER TABLE bibdoc ADD COLUMN more_info mediumblob NULL default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK ADD COLUMN priority tinyint(4) NOT NULL default 0;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK ADD KEY priority (priority);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkCITATIONDATA DROP PRIMARY KEY;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkCITATIONDATA ADD PRIMARY KEY (id);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkCITATIONDATA CHANGE id id mediumint(8) unsigned NOT NULL auto_increment;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE rnkCITATIONDATA ADD UNIQUE KEY object_name (object_name);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmPARAMETERS CHANGE value value text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmAPPROVAL ADD note text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE hstDOCUMENT CHANGE docsize docsize bigint(15) unsigned NOT NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtACTIONHISTORY CHANGE client_host client_host int(10) unsigned default NULL;" | ${prefix}/bin/dbexec

update-v0.99.1-tables:
	@echo "Nothing to do; table structure did not change between v0.99.1 and v0.99.2."

update-v0.99.2-tables:
	@echo "Nothing to do; table structure did not change between v0.99.2 and v0.99.3."

update-v0.99.3-tables:
	@echo "Nothing to do; table structure did not change between v0.99.3 and v0.99.4."

update-v0.99.4-tables:
	@echo "Nothing to do; table structure did not change between v0.99.4 and v0.99.5."

update-v0.99.5-tables:
	@echo "Nothing to do; table structure did not change between v0.99.5 and v0.99.6."

update-v0.99.6-tables:
	@echo "Nothing to do; table structure did not change between v0.99.6 and v0.99.7."

update-v0.99.7-tables:
	@echo "Nothing to do; table structure did not change between v0.99.7 and v0.99.8."

CLEANFILES = *~
