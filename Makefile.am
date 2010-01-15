## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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
JSMV = 3.6b
JSMFV = 1.3
JSMATH = jsMath-$(JSMV).zip
JSMATHFONTS = jsMath-fonts-$(JSMFV).zip

# current FCKeditor version
FCKV = 2.6.5
FCKEDITOR = FCKeditor_$(FCKV).zip

all:
	@echo "****************************************************"
	@echo "** CDS Invenio has been successfully built.       **"
	@echo "**                                                **"
	@echo "** You may proceed to 'make install' now.         **"
	@echo "****************************************************"

check-custom-templates:
	$(PYTHON) $(top_srcdir)/modules/webstyle/lib/template.py --check-custom-templates $(top_srcdir)

kwalitee-check:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py --stats $(top_srcdir)

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
	@echo "** The jsMath plugin was successfully uninstalled.       **"
	@echo "***********************************************************"

install-jscalendar-plugin:
	@echo "***********************************************************"
	@echo "** Installing jsCalendar plugin, please wait...              **"
	@echo "***********************************************************"
	rm -rf /tmp/invenio-jscalendar-plugin
	mkdir /tmp/invenio-jscalendar-plugin
	(cd /tmp/invenio-jscalendar-plugin && \
	wget 'http://www.dynarch.com/static/jscalendar-1.0.zip' && \
	unzip -u jscalendar-1.0.zip && \
	mkdir -p ${prefix}/var/www/jsCalendar && \
	cp jscalendar-1.0/img.gif ${prefix}/var/www/jsCalendar/jsCalendar.gif && \
	cp jscalendar-1.0/calendar.js ${prefix}/var/www/jsCalendar/ && \
	cp jscalendar-1.0/calendar-setup.js ${prefix}/var/www/jsCalendar/ && \
	cp jscalendar-1.0/lang/calendar-en.js ${prefix}/var/www/jsCalendar/ && \
	cp jscalendar-1.0/calendar-blue.css ${prefix}/var/www/jsCalendar/)
	rm -fr /tmp/invenio-jscalendar-plugin
	@echo "***********************************************************"
	@echo "** The jsCalendar plugin was successfully installed.     **"
	@echo "***********************************************************"

uninstall-jscalendar-plugin:
	@rm -rvf ${prefix}/var/www/jsCalendar
	@echo "***********************************************************"
	@echo "** The jsCalendar plugin was successfully uninstalled.       **"
	@echo "***********************************************************"

install-jquery-plugins: uninstall-jquery-plugins
	@echo "***********************************************************"
	@echo "** Installing various jQuery plugins, please wait...     **"
	@echo "***********************************************************"
	mkdir -p ${prefix}/var/www/js
	(cd ${prefix}/var/www/js && \
	wget http://jqueryjs.googlecode.com/files/jquery-1.3.1.min.js && \
	mv jquery-1.3.1.min.js jquery.min.js && \
	wget http://jquery-ui.googlecode.com/svn/tags/latest/ui/minified/effects.core.min.js && \
	wget http://jquery-ui.googlecode.com/svn/tags/latest/ui/minified/effects.highlight.min.js && \
	wget http://www.appelsiini.net/download/jquery.jeditable.mini.js && \
	wget http://tablesorter.com/jquery.tablesorter.js && \
	wget http://tablesorter.com/addons/pager/jquery.tablesorter.pager.js && \
	wget http://plugins.jquery.com/files/jquery.autogrow-1.2.2.zip && \
	unzip jquery.autogrow-1.2.2.zip jquery.autogrow.js && \
	rm jquery.autogrow-1.2.2.zip && \
	wget http://json.org/json2.js && \
	wget -O jquery.hotkeys.min.js http://js-hotkeys.googlecode.com/files/jquery.hotkeys-0.7.8-packed.js)
	@echo "***********************************************************"
	@echo "** The jQuery plugins were successfully installed.       **"
	@echo "***********************************************************"

uninstall-jquery-plugins:
	(cd ${prefix}/var/www/js && \
	rm -f jquery.min.js && \
	rm -f effects.core.min.js && \
	rm -f effects.highlight.min.js && \
	rm -f jquery.jeditable.mini.js && \
	rm -f jquery.tablesorter.js && \
	rm -f jquery.tablesorter.pager.js && \
	rm -f jquery.autogrow.js && \
	rm -f json2.js && \
	rm -f jquery.hotkeys.min.js)
	@echo "***********************************************************"
	@echo "** The jquery plugins were successfully uninstalled.     **"
	@echo "***********************************************************"

install-fckeditor-plugin:
	@echo "***********************************************************"
	@echo "** Installing FCKeditor plugin, please wait...           **"
	@echo "***********************************************************"
	rm -rf ${prefix}/lib/python/invenio/fckeditor/
	rm -rf /tmp/invenio-fckeditor-plugin
	mkdir /tmp/invenio-fckeditor-plugin
	(cd /tmp/invenio-fckeditor-plugin && \
	wget 'http://downloads.sourceforge.net/fckeditor/$(FCKEDITOR)' && \
	unzip -u -d ${prefix}/var/www $(FCKEDITOR)) && \
	mkdir -p ${prefix}/lib/python/invenio/fckeditor/editor/filemanager/connectors/py && \
	mv -f ${prefix}/var/www/fckeditor/fckeditor.py ${prefix}/lib/python/invenio/fckeditor/ && \
	mv -f ${prefix}/var/www/fckeditor/editor/filemanager/connectors/py/*.py ${prefix}/lib/python/invenio/fckeditor/editor/filemanager/connectors/py/ && \
	rm -f ${prefix}/var/www/fckeditor/editor/filemanager/connectors/py/upload.py && \
	rm -f ${prefix}/var/www/fckeditor/editor/filemanager/connectors/py/zope.py && \
	find ${prefix}/lib/python/invenio/fckeditor -type d -exec touch {}/__init__.py \; && \
	find ${prefix}/var/www/fckeditor/ -depth -name '_*' -exec rm -rf {} \; && \
	rm -r ${prefix}/var/www/fckeditor/editor/filemanager/connectors && \
	find ${prefix}/var/www/fckeditor/fckeditor* -maxdepth 0 -exec rm -r {} \; && \
	rm -fr /tmp/invenio-fckeditor-plugin
	@echo "* Installing Invenio-specific FCKeditor config..."
	(cd $(top_srcdir)/modules/webstyle/etc && make install)
	@echo "***********************************************************"
	@echo "** The FCKeditor plugin was successfully installed.      **"
	@echo "** Please do not forget to properly set the option       **"
	@echo "** CFG_WEBCOMMENT_USE_RICH_TEXT_EDITOR in invenio.conf.  **"
	@echo "***********************************************************"

uninstall-fckeditor-plugin:
	@rm -rvf ${prefix}/var/www/fckeditor
	@rm -rvf ${prefix}/lib/python/invenio/fckeditor
	@echo "***********************************************************"
	@echo "** The FCKeditor plugin was successfully uninstalled.    **"
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
	echo "ALTER TABLE fmtKNOWLEDGEBASES add COLUMN kbtype char default NULL;" | ${prefix}/bin/dbexec

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
	echo "RENAME TABLE oaiARCHIVE TO oaiREPOSITORY;" | ${prefix}/bin/dbexec
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "INSERT INTO knwKB (id,name,description,kbtype) SELECT id,name,description,'' FROM fmtKNOWLEDGEBASES;" | ${prefix}/bin/dbexec
	echo "INSERT INTO knwKBRVAL (id,m_key,m_value,id_knwKB) SELECT id,m_key,m_value,id_fmtKNOWLEDGEBASES FROM fmtKNOWLEDGEBASEMAPPINGS;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmPARAMETERS CHANGE name name varchar(40) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc CHANGE docname docname varchar(250) COLLATE utf8_bin NOT NULL default 'file';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE collection DROP COLUMN restricted;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE host host varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE hstTASK CHANGE host host varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bib85x DROP INDEX kv, ADD INDEX kv (value(100));" | ${prefix}/bin/dbexec
	echo "UPDATE clsMETHOD SET location='http://cdsware.cern.ch/download/invenio-demo-site-files/HEP.rdf' WHERE name='HEP' AND location='';" | ${prefix}/bin/dbexec
	echo "UPDATE clsMETHOD SET location='http://cdsware.cern.ch/download/invenio-demo-site-files/NASA-subjects.rdf' WHERE name='NASA-subjects' AND location='';" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET name='runoairepository', description='run oairepositoryupdater task' WHERE name='runoaiarchive';" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET name='cfgoaiharvest', description='configure OAI Harvest' WHERE name='cfgbibharvest';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE accARGUMENT CHANGE value value varchar(255);" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET allowedkeywords='doctype,act,categ' WHERE name='submit';" | ${prefix}/bin/dbexec
	echo "INSERT INTO accARGUMENT(keyword,value) VALUES ('categ','*');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accROLE_accACTION_accARGUMENT(id_accROLE,id_accACTION,id_accARGUMENT,argumentlistid) SELECT DISTINCT raa.id_accROLE,raa.id_accACTION,accARGUMENT.id,raa.argumentlistid FROM accROLE_accACTION_accARGUMENT as raa JOIN accACTION on id_accACTION=accACTION.id,accARGUMENT WHERE accACTION.name='submit' and accARGUMENT.keyword='categ' and accARGUMENT.value='*';" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET allowedkeywords='name,with_editor_rights' WHERE name='cfgwebjournal';" | ${prefix}/bin/dbexec
	echo "INSERT INTO accARGUMENT(keyword,value) VALUES ('with_editor_rights','yes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accROLE_accACTION_accARGUMENT(id_accROLE,id_accACTION,id_accARGUMENT,argumentlistid) SELECT DISTINCT raa.id_accROLE,raa.id_accACTION,accARGUMENT.id,raa.argumentlistid FROM accROLE_accACTION_accARGUMENT as raa JOIN accACTION on id_accACTION=accACTION.id,accARGUMENT WHERE accACTION.name='cfgwebjournal' and accARGUMENT.keyword='with_editor_rights' and accARGUMENT.value='yes';" | ${prefix}/bin/dbexec

CLEANFILES = *~ *.pyc *.tmp
