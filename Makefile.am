## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

confignicedir = $(sysconfdir)/build
confignice_SCRIPTS=config.nice

SUBDIRS = po config modules

EXTRA_DIST = UNINSTALL THANKS RELEASE-NOTES configure-tests.py config.nice.in \
             config.rpath


# current MathJax version and packages
# See also modules/miscutil/lib/htmlutils.py (get_mathjax_header)
MJV = 1.1
MATHJAX = https://github.com/mathjax/MathJax/zipball/v$(MJV)

# current CKeditor version
CKV = 3.6.2
CKEDITOR = ckeditor_$(CKV).zip

# current MediaElement.js version
MEV = master
MEDIAELEMENT = http://github.com/johndyer/mediaelement/zipball/$(MEV)

#for solrutils
INVENIO_JAVA_PATH = org/invenio_software/solr
solrdirname = apache-solr-3.1.0
solrdir = $(prefix)/lib/$(solrdirname)
solrutils_dir=$(CURDIR)/modules/miscutil/lib/solrutils

CLASSPATH=.:${solrdir}/dist/solrj-lib/commons-io-1.4.jar:${solrdir}/dist/apache-solr-core-*jar:${solrdir}/contrib/jzlib-1.0.7.jar:${solrdir}/dist/apache-solr-solrj-3.1.0.jar:${solrdir}/dist/solrj-lib/slf4j-api-1.5.5.jar:${solrdir}/dist/*:${solrdir}/contrib/basic-lucene-libs/*:${solrdir}/contrib/analysis-extras/lucene-libs/*:${solrdir}/dist/solrj-lib/*

# git-version-get stuff:
BUILT_SOURCES = $(top_srcdir)/.version
$(top_srcdir)/.version:
	echo $(VERSION) > $@-t && mv $@-t $@
dist-hook:
	echo $(VERSION) > $(distdir)/.tarball-version

check-custom-templates:
	$(PYTHON) $(top_srcdir)/modules/webstyle/lib/template.py --check-custom-templates $(top_srcdir)

kwalitee-check:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py --stats $(top_srcdir)

kwalitee-check-errors-only:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py --check-errors $(top_srcdir)

kwalitee-check-variables:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py --check-variables $(top_srcdir)

kwalitee-check-indentation:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py --check-indentation $(top_srcdir)

kwalitee-check-sql-queries:
	@$(PYTHON) $(top_srcdir)/modules/miscutil/lib/kwalitee.py --check-sql $(top_srcdir)

etags:
	\rm -f $(top_srcdir)/TAGS
	(cd $(top_srcdir) && find $(top_srcdir) -name "*.py" -print | xargs etags)

install-data-local:
	for d in / /cache /log /tmp /tmp-shared /data /run /tmp-shared/bibencode/jobs/done ; do	\
		mkdir -p $(localstatedir)$$d ;		\
	done
	@echo "************************************************************"
	@echo "** Invenio software has been successfully installed!      **"
	@echo "**                                                        **"
	@echo "** You may proceed to customizing your installation now.  **"
	@echo "************************************************************"

install-mathjax-plugin:
	@echo "***********************************************************"
	@echo "** Installing MathJax plugin, please wait...             **"
	@echo "***********************************************************"
	rm -rf /tmp/invenio-mathjax-plugin
	mkdir /tmp/invenio-mathjax-plugin
	mkdir -p ${prefix}/var/www/MathJax
	(cd /tmp/invenio-mathjax-plugin && \
	wget '$(MATHJAX)' -O mathjax.zip --no-check-certificate && \
	unzip -q mathjax.zip && cd mathjax-MathJax-* && cp -ur * \
	${prefix}/var/www/MathJax)
	rm -fr /tmp/invenio-mathjax-plugin
	@echo "************************************************************"
	@echo "** The MathJax plugin was successfully installed.         **"
	@echo "** Please do not forget to properly set the option        **"
	@echo "** CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS in invenio.conf. **"
	@echo "************************************************************"

uninstall-mathjax-plugin:
	@rm -rvf ${prefix}/var/www/MathJax
	@echo "***********************************************************"
	@echo "** The MathJax plugin was successfully uninstalled.      **"
	@echo "***********************************************************"

install-jscalendar-plugin:
	@echo "***********************************************************"
	@echo "** Installing jsCalendar plugin, please wait...          **"
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
	@echo "** The jsCalendar plugin was successfully uninstalled.   **"
	@echo "***********************************************************"

install-jquery-plugins:
	@echo "***********************************************************"
	@echo "** Installing various jQuery plugins, please wait...     **"
	@echo "***********************************************************"
	mkdir -p ${prefix}/var/www/js
	mkdir -p $(prefix)/var/www/css
	(cd ${prefix}/var/www/js && \
	wget http://code.jquery.com/jquery-1.7.1.min.js && \
	mv jquery-1.7.1.min.js jquery.min.js && \
	wget http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.17/jquery-ui.min.js && \
        wget http://invenio-software.org/download/jquery/v1.5/js/jquery.jeditable.mini.js && \
	wget https://raw.github.com/malsup/form/master/jquery.form.js --no-check-certificate && \
	wget http://jquery-multifile-plugin.googlecode.com/svn/trunk/jquery.MultiFile.pack.js && \
	wget -O jquery.tablesorter.zip http://invenio-software.org/download/jquery/jquery.tablesorter.20111208.zip && \
	wget http://invenio-software.org/download/jquery/uploadify-v2.1.4.zip -O uploadify.zip && \
	wget http://www.datatables.net/download/build/jquery.dataTables.min.js && \
	wget http://keith-wood.name/zip/jquery.bookmark.package-1.4.0.zip && \
	unzip jquery.tablesorter.zip && \
	rm jquery.tablesorter.zip && \
	rm -rf uploadify && \
	unzip -u uploadify.zip -d uploadify && \
	wget http://flot.googlecode.com/files/flot-0.6.zip && \
        wget http://trentrichardson.com/examples/timepicker/js/jquery-ui-timepicker-addon.js && \
	unzip -u flot-0.6.zip && \
	mv flot/jquery.flot.selection.min.js flot/jquery.flot.min.js flot/excanvas.min.js ./ && \
	rm flot-0.6.zip && rm -r flot && \
	mv uploadify/swfobject.js ./ && \
	mv uploadify/cancel.png uploadify/uploadify.css uploadify/uploadify.allglyphs.swf uploadify/uploadify.fla uploadify/uploadify.swf ../img/ && \
	mv uploadify/jquery.uploadify.v2.1.4.min.js ./jquery.uploadify.min.js && \
	rm uploadify.zip && rm -r uploadify && \
	wget --no-check-certificate https://github.com/douglascrockford/JSON-js/raw/master/json2.js && \
	wget https://raw.github.com/jeresig/jquery.hotkeys/master/jquery.hotkeys.js && \
	wget http://jquery.bassistance.de/treeview/jquery.treeview.zip && \
	unzip jquery.treeview.zip -d jquery-treeview && \
	rm jquery.treeview.zip && \
	wget http://invenio-software.org/download/jquery/v1.5/js/jquery.ajaxPager.js && \
	unzip jquery.bookmark.package-1.4.0.zip && \
	rm -f jquery.bookmark.ext.* bookmarks-big.png bookmarkBasic.html jquery.bookmark.js jquery.bookmark.pack.js && \
	mv bookmarks.png ../img/ && \
	mv jquery.bookmark.css ../css/ && \
	rm -f jquery.bookmark.package-1.4.0.zip && \
	mkdir -p ${prefix}/var/www/img && \
	cd ${prefix}/var/www/img && \
	wget -r -np -nH --cut-dirs=4 -A "png,css" -P jquery-ui/themes http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/base/ && \
	wget -r -np -nH --cut-dirs=4 -A "png,css" -P jquery-ui/themes http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/smoothness/ && \
	wget -r -np -nH --cut-dirs=4 -A "png,css" -P jquery-ui/themes http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/redmond/ && \
	wget --no-check-certificate -O datatables_jquery-ui.css https://github.com/DataTables/DataTables/raw/master/media/css/demo_table_jui.css && \
	wget http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/redmond/jquery-ui.css && \
	wget http://jquery-ui.googlecode.com/svn/tags/1.8.17/demos/images/calendar.gif && \
	wget -r -np -nH --cut-dirs=5 -A "png" http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/redmond/images/)
	@echo "***********************************************************"
	@echo "** The jQuery plugins were successfully installed.       **"
	@echo "***********************************************************"

uninstall-jquery-plugins:
	(cd ${prefix}/var/www/js && \
	rm -f jquery.min.js && \
	rm -f jquery.MultiFile.pack.js && \
	rm -f jquery.jeditable.mini.js && \
	rm -f jquery.flot.selection.min.js && \
	rm -f jquery.flot.min.js && \
	rm -f excanvas.min.js && \
	rm -f jquery-ui-timepicker-addon.min.js && \
	rm -f jquery.tablesorter.js && \
	rm -f jquery.tablesorter.pager.js && \
	rm -f json2.js && \
	rm -f jquery.uploadify.min.js && \
	rm -rf tablesorter && \
	rm -rf jquery-treeview && \
	rm -f jquery.ajaxPager.js && \
	rm -f jquery.form.js && \
	rm -f jquery.dataTables.min.js && \
	rm -f ui.core.js && \
	rm -f jquery.bookmark.min.js && \
        rm -f jquery.hotkeys.js && \
        rm -f jquery.tablesorter.min.js && \
        rm -f jquery-ui-1.7.3.custom.min.js && \
        rm -f jquery.metadata.js && \
        rm -f jquery-latest.js && \
        rm -f jquery-ui.min.js)
	(cd ${prefix}/var/www/img && \
	rm -f cancel.png uploadify.css uploadify.swf uploadify.allglyphs.swf uploadify.fla && \
	rm -f datatables_jquery-ui.css \
	rm -f bookmarks.png) && \
	(cd ${prefix}/var/www/css && \
	rm -f jquery.bookmark.css)
	@echo "***********************************************************"
	@echo "** The jquery plugins were successfully uninstalled.     **"
	@echo "***********************************************************"

install-ckeditor-plugin:
	@echo "***********************************************************"
	@echo "** Installing CKeditor plugin, please wait...           **"
	@echo "***********************************************************"
	rm -rf ${prefix}/lib/python/invenio/ckeditor/
	rm -rf /tmp/invenio-ckeditor-plugin
	mkdir /tmp/invenio-ckeditor-plugin
	(cd /tmp/invenio-ckeditor-plugin && \
	wget 'http://download.cksource.com/CKEditor/CKEditor/CKEditor%20$(CKV)/$(CKEDITOR)' && \
	unzip -u -d ${prefix}/var/www $(CKEDITOR)) && \
	find ${prefix}/var/www/ckeditor/ -depth -name '_*' -exec rm -rf {} \; && \
	find ${prefix}/var/www/ckeditor/ckeditor* -maxdepth 0 ! -name "ckeditor.js" -exec rm -r {} \; && \
	rm -fr /tmp/invenio-ckeditor-plugin
	@echo "* Installing Invenio-specific CKeditor config..."
	(cd $(top_srcdir)/modules/webstyle/etc && make install)
	@echo "***********************************************************"
	@echo "** The CKeditor plugin was successfully installed.      **"
	@echo "** Please do not forget to properly set the option       **"
	@echo "** CFG_WEBCOMMENT_USE_RICH_TEXT_EDITOR in invenio.conf.  **"
	@echo "***********************************************************"

uninstall-ckeditor-plugin:
	@rm -rvf ${prefix}/var/www/ckeditor
	@rm -rvf ${prefix}/lib/python/invenio/ckeditor
	@echo "***********************************************************"
	@echo "** The CKeditor plugin was successfully uninstalled.    **"
	@echo "***********************************************************"

install-pdfa-helper-files:
	@echo "***********************************************************"
	@echo "** Installing PDF/A helper files, please wait...         **"
	@echo "***********************************************************"
	wget 'http://invenio-software.org/download/invenio-demo-site-files/ISOCoatedsb.icc' -O ${prefix}/etc/websubmit/file_converter_templates/ISOCoatedsb.icc
	@echo "***********************************************************"
	@echo "** The PDF/A helper files were successfully installed.   **"
	@echo "***********************************************************"

install-mediaelement:
	@echo "***********************************************************"
	@echo "** MediaElement.js, please wait...                       **"
	@echo "***********************************************************"
	rm -rf /tmp/mediaelement
	mkdir /tmp/mediaelement
	wget 'http://github.com/johndyer/mediaelement/zipball/master' -O '/tmp/mediaelement/mediaelement.zip' --no-check-certificate
	unzip -u -d '/tmp/mediaelement' '/tmp/mediaelement/mediaelement.zip'
	rm -rf ${prefix}/var/www/mediaelement
	mkdir ${prefix}/var/www/mediaelement
	mv /tmp/mediaelement/johndyer-mediaelement-*/build/* ${prefix}/var/www/mediaelement
	rm -rf /tmp/mediaelement
	@echo "***********************************************************"
	@echo "** MediaElement.js was successfully installed.           **"
	@echo "***********************************************************"

uninstall-pdfa-helper-files:
	rm -f ${prefix}/etc/websubmit/file_converter_templates/ISOCoatedsb.icc
	@echo "***********************************************************"
	@echo "** The PDF/A helper files were successfully uninstalled. **"
	@echo "***********************************************************"

#Solrutils allows automatic installation, running and searching of an external Solr index.
install-solrutils:
	@echo "***********************************************************"
	@echo "** Installing Solrutils and solr, please wait...         **"
	@echo "***********************************************************"
	cd $(prefix)/lib && \
	if test -d apache-solr*; then echo A solr directory already exists in `pwd` . \
	Please remove it manually, if you are sure it is not needed; exit 2; fi ; \
        if test -f apache-solr*; then echo solr tarball already exists in `pwd` . \
        Please remove it manually.; exit 2; fi ; \
	wget http://www.apache.org/dist//lucene/solr/3.1.0/apache-solr-3.1.0.tgz && \
	tar -xzf apache-solr-3.1.0.tgz && \
	rm apache-solr-3.1.0.tgz
	cd $(solrdir)/contrib/ ;\
	wget http://mirrors.ibiblio.org/pub/mirrors/maven2/com/jcraft/jzlib/1.0.7/jzlib-1.0.7.jar && \
	cd $(solrdir)/contrib/ ;\
	jar -xf ../example/webapps/solr.war WEB-INF/lib/lucene-core-3.1.0.jar ; \
        if test -d basic-lucene-libs; then rm -rf basic-lucene-libs; fi ; \
        mv WEB-INF/lib/ basic-lucene-libs ; \
        cp $(solrutils_dir)/schema.xml $(solrdir)/example/solr/conf/
	cp $(solrutils_dir)/solrconfig.xml $(solrdir)/example/solr/conf/
	cd $(solrutils_dir) && \
	javac -classpath $(CLASSPATH) -d $(solrdir)/contrib @$(solrutils_dir)/java_sources.txt && \
	cd $(solrdir)/contrib/ && \
	jar -cf invenio-solr.jar org/invenio_software/solr/*class

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
	@echo "** Please see the RELEASE-NOTES for details.            **"
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
	@echo "Nothing to do; table structure did not change between v0.99.1 and v0.99.2."

update-v0.99.2-tables:
	@echo "Nothing to do; table structure did not change between v0.99.2 and v0.99.3."

update-v0.99.3-tables:
	@echo "Nothing to do; table structure did not change between v0.99.3 and v0.99.4."

update-v0.99.4-tables:
	@echo "Nothing to do; table structure did not change between v0.99.4 and v0.99.5."

update-v0.99.5-tables: # from v0.99.5 to v1.0.0-rc0
	echo "RENAME TABLE oaiARCHIVE TO oaiREPOSITORY;" | ${prefix}/bin/dbexec
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "INSERT INTO knwKB (id,name,description,kbtype) SELECT id,name,description,'' FROM fmtKNOWLEDGEBASES;" | ${prefix}/bin/dbexec
	echo "INSERT INTO knwKBRVAL (id,m_key,m_value,id_knwKB) SELECT id,m_key,m_value,id_fmtKNOWLEDGEBASES FROM fmtKNOWLEDGEBASEMAPPINGS;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE sbmPARAMETERS CHANGE name name varchar(40) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc CHANGE docname docname varchar(250) COLLATE utf8_bin NOT NULL default 'file';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc CHANGE status status text NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bibdoc ADD COLUMN text_extraction_date datetime NOT NULL default '0000-00-00';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE collection DROP COLUMN restricted;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE host host varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE hstTASK CHANGE host host varchar(255) NOT NULL default '';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bib85x DROP INDEX kv, ADD INDEX kv (value(100));" | ${prefix}/bin/dbexec
	echo "UPDATE clsMETHOD SET location='http://invenio-software.org/download/invenio-demo-site-files/HEP.rdf' WHERE name='HEP' AND location='';" | ${prefix}/bin/dbexec
	echo "UPDATE clsMETHOD SET location='http://invenio-software.org/download/invenio-demo-site-files/NASA-subjects.rdf' WHERE name='NASA-subjects' AND location='';" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET name='runoairepository', description='run oairepositoryupdater task' WHERE name='runoaiarchive';" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET name='cfgoaiharvest', description='configure OAI Harvest' WHERE name='cfgbibharvest';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE accARGUMENT CHANGE value value varchar(255);" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET allowedkeywords='doctype,act,categ' WHERE name='submit';" | ${prefix}/bin/dbexec
	echo "INSERT INTO accARGUMENT(keyword,value) VALUES ('categ','*');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accROLE_accACTION_accARGUMENT(id_accROLE,id_accACTION,id_accARGUMENT,argumentlistid) SELECT DISTINCT raa.id_accROLE,raa.id_accACTION,accARGUMENT.id,raa.argumentlistid FROM accROLE_accACTION_accARGUMENT as raa JOIN accACTION on id_accACTION=accACTION.id,accARGUMENT WHERE accACTION.name='submit' and accARGUMENT.keyword='categ' and accARGUMENT.value='*';" | ${prefix}/bin/dbexec
	echo "UPDATE accACTION SET allowedkeywords='name,with_editor_rights' WHERE name='cfgwebjournal';" | ${prefix}/bin/dbexec
	echo "INSERT INTO accARGUMENT(keyword,value) VALUES ('with_editor_rights','yes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO accROLE_accACTION_accARGUMENT(id_accROLE,id_accACTION,id_accARGUMENT,argumentlistid) SELECT DISTINCT raa.id_accROLE,raa.id_accACTION,accARGUMENT.id,raa.argumentlistid FROM accROLE_accACTION_accARGUMENT as raa JOIN accACTION on id_accACTION=accACTION.id,accARGUMENT WHERE accACTION.name='cfgwebjournal' and accARGUMENT.keyword='with_editor_rights' and accARGUMENT.value='yes';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskEXTREC CHANGE id id int(15) unsigned NOT NULL auto_increment;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskEXTREC ADD external_id int(15) NOT NULL default '0';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskEXTREC ADD collection_id int(15) unsigned NOT NULL default '0';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskEXTREC ADD original_url text;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD status char(2) NOT NULL default 'ok';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD KEY status (status);" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Move_Photos_to_Storage','Attach/edit the pictures uploaded with the \"create_photos_manager_interface()\" function');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFIELDDESC VALUES ('Upload_Photos',NULL,'','R',NULL,NULL,NULL,NULL,NULL,'\"\"\"\r\nThis is an example of element that creates a photos upload interface.\r\nClone it, customize it and integrate it into your submission. Then add function \r\n\'Move_Photos_to_Storage\' to your submission functions list, in order for files \r\nuploaded with this interface to be attached to the record. More information in \r\nthe WebSubmit admin guide.\r\n\"\"\"\r\n\r\nfrom invenio.websubmit_functions.ParamFile import ParamFromFile\r\nfrom invenio.websubmit_functions.Move_Photos_to_Storage import read_param_file, create_photos_manager_interface, get_session_id\r\n\r\n# Retrieve session id\r\ntry:\r\n    # User info is defined only in MBI/MPI actions...\r\n    session_id = get_session_id(None, uid, user_info) \r\nexcept:\r\n    session_id = get_session_id(req, uid, {})\r\n\r\n# Retrieve context\r\nindir = curdir.split(\'/\')[-3]\r\ndoctype = curdir.split(\'/\')[-2]\r\naccess = curdir.split(\'/\')[-1]\r\n\r\n# Get the record ID, if any\r\nsysno = ParamFromFile(\"%s/%s\" % (curdir,\'SN\')).strip()\r\n\r\n\"\"\"\r\nModify below the configuration of the photos manager interface.\r\nNote: \'can_reorder_photos\' parameter is not yet fully taken into consideration\r\n\r\nDocumentation of the function is available by running:\r\necho -e \'from invenio.websubmit_functions.Move_Photos_to_Storage import create_photos_manager_interface as f\\nprint f.__doc__\' | python\r\n\"\"\"\r\ntext += create_photos_manager_interface(sysno, session_id, uid,\r\n                                        doctype, indir, curdir, access,\r\n                                        can_delete_photos=True,\r\n                                        can_reorder_photos=True,\r\n                                        can_upload_photos=True,\r\n                                        editor_width=700,\r\n                                        editor_height=400,\r\n                                        initial_slider_value=100,\r\n                                        max_slider_value=200,\r\n                                        min_slider_value=80)','0000-00-00','0000-00-00',NULL,NULL,0);"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Photos_to_Storage','iconsize');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFIELDDESC VALUES ('Upload_Files',NULL,'','R',NULL,NULL,NULL,NULL,NULL,'\"\"\"\r\nThis is an example of element that creates a file upload interface.\r\nClone it, customize it and integrate it into your submission. Then add function \r\n\'Move_Uploaded_Files_to_Storage\' to your submission functions list, in order for files \r\nuploaded with this interface to be attached to the record. More information in \r\nthe WebSubmit admin guide.\r\n\"\"\"\r\nfrom invenio.websubmit_managedocfiles import create_file_upload_interface\r\nfrom invenio.websubmit_functions.Shared_Functions import ParamFromFile\r\n\r\nindir = ParamFromFile(os.path.join(curdir, \'indir\'))\r\ndoctype = ParamFromFile(os.path.join(curdir, \'doctype\'))\r\naccess = ParamFromFile(os.path.join(curdir, \'access\'))\r\ntry:\r\n    sysno = int(ParamFromFile(os.path.join(curdir, \'SN\')).strip())\r\nexcept:\r\n    sysno = -1\r\nln = ParamFromFile(os.path.join(curdir, \'ln\'))\r\n\r\n\"\"\"\r\nRun the following to get the list of parameters of function \'create_file_upload_interface\':\r\necho -e \'from invenio.websubmit_managedocfiles import create_file_upload_interface as f\\nprint f.__doc__\' | python\r\n\"\"\"\r\ntext = create_file_upload_interface(recid=sysno,\r\n                                 print_outside_form_tag=False,\r\n                                 include_headers=True,\r\n                                 ln=ln,\r\n                                 doctypes_and_desc=[(\'main\',\'Main document\'),\r\n                                                    (\'additional\',\'Figure, schema, etc.\')],\r\n                                 can_revise_doctypes=[\'*\'],\r\n                                 can_describe_doctypes=[\'main\'],\r\n                                 can_delete_doctypes=[\'additional\'],\r\n                                 can_rename_doctypes=[\'main\'],\r\n                                 sbm_indir=indir, sbm_doctype=doctype, sbm_access=access)[1]\r\n','0000-00-00','0000-00-00',NULL,NULL,0);"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Uploaded_Files_to_Storage','forceFileRevision');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Create_Upload_Files_Interface','Display generic interface to add/revise/delete files. To be used before function \"Move_Uploaded_Files_to_Storage\"');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Move_Uploaded_Files_to_Storage','Attach files uploaded with \"Create_Upload_Files_Interface\"')" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Revised_Files_to_Storage','elementNameToDoctype');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Revised_Files_to_Storage','createIconDoctypes');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Revised_Files_to_Storage','createRelatedFormats');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Revised_Files_to_Storage','iconsize');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Revised_Files_to_Storage','keepPreviousVersionDoctypes');"  | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Move_Revised_Files_to_Storage','Revise files initially uploaded with \"Move_Files_to_Storage\"')" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','maxsize');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','minsize');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','doctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','restrictions');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canDeleteDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canReviseDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canDescribeDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canCommentDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canKeepDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canAddFormatDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canRestrictDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canRenameDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','canNameNewFiles');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','createRelatedFormats');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','keepDefault');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','showLinks');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','fileLabel');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','filenameLabel');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','descriptionLabel');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','commentLabel');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','restrictionLabel');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','startDoc');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','endDoc');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','defaultFilenameDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Create_Upload_Files_Interface','maxFilesDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Uploaded_Files_to_Storage','iconsize');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Uploaded_Files_to_Storage','createIconDoctypes');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Report_Number_Generation','nblength');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Second_Report_Number_Generation','2nd_nb_length');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Get_Recid','record_search_pattern');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Move_FCKeditor_Files_to_Storage','Transfer files attached to the record with the FCKeditor');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_FCKeditor_Files_to_Storage','input_fields');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Stamp_Uploaded_Files','layer');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Stamp_Replace_Single_File_Approval','layer');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Stamp_Replace_Single_File_Approval','switch_file');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Stamp_Uploaded_Files','switch_file');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Files_to_Storage','paths_and_restrictions');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Files_to_Storage','paths_and_doctypes');" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD round_name varchar(255) NOT NULL default ''" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD restriction varchar(50) NOT NULL default ''" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD in_reply_to_id_cmtRECORDCOMMENT int(15) unsigned NOT NULL default '0'" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD KEY in_reply_to_id_cmtRECORDCOMMENT (in_reply_to_id_cmtRECORDCOMMENT);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskRECORDCOMMENT ADD in_reply_to_id_bskRECORDCOMMENT int(15) unsigned NOT NULL default '0'" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskRECORDCOMMENT ADD KEY in_reply_to_id_bskRECORDCOMMENT (in_reply_to_id_bskRECORDCOMMENT);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD reply_order_cached_data blob NULL default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskRECORDCOMMENT ADD reply_order_cached_data blob NULL default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE cmtRECORDCOMMENT ADD INDEX (reply_order_cached_data(40));" | ${prefix}/bin/dbexec
	echo "ALTER TABLE bskRECORDCOMMENT ADD INDEX (reply_order_cached_data(40));" | ${prefix}/bin/dbexec
	echo -e 'from invenio.webcommentadminlib import migrate_comments_populate_threads_index;\
	migrate_comments_populate_threads_index()' | $(PYTHON)
	echo -e 'from invenio.access_control_firerole import repair_role_definitions;\
	repair_role_definitions()' | $(PYTHON)

update-v1.0.0-rc0-tables: # from v1.0.0-rc0 to v1.0.0
	@echo "Nothing to do; table structure did not change between v1.0.0-rc0 and v1.0.0."

update-db-from-v1.0-to-v1.1: # update DB from v1.0 release series to v1.1 release series
	${prefix}/bin/dbexec < $(top_srcdir)/modules/miscutil/sql/tabcreate.sql
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Set_Embargo','Set an embargo on all the documents of a given record.');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Set_Embargo','date_file');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Set_Embargo','date_format');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('User_is_Record_Owner_or_Curator','curator_role');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('User_is_Record_Owner_or_Curator','curator_flag');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Move_Photos_to_Storage','iconformat');" | ${prefix}/bin/dbexec
	echo "INSERT INTO format (name, code, description, content_type, visibility) VALUES ('Podcast', 'xp', 'Sample format suitable for multimedia feeds, such as podcasts', 'application/rss+xml', 0);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE accMAILCOOKIE ADD INDEX expiration (expiration);" | ${prefix}/bin/dbexec
	echo "UPDATE sbmFUNDESC SET function='Move_CKEditor_Files_to_Storage' WHERE function='Move_FCKeditor_Files_to_Storage';" | ${prefix}/bin/dbexec
	echo "UPDATE sbmALLFUNCDESCR SET function='Move_CKEditor_Files_to_Storage', description='Transfer files attached to the record with the CKEditor' WHERE function='Move_FCKeditor_Files_to_Storage';" | ${prefix}/bin/dbexec
	echo "UPDATE sbmFUNCTIONS SET function='Move_CKEditor_Files_to_Storage' WHERE function='Move_FCKeditor_Files_to_Storage';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK CHANGE proc proc varchar(255) NOT NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK ADD sequenceid int(8) NULL default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE schTASK ADD INDEX sequenceid (sequenceid);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE hstTASK CHANGE proc proc varchar(255) NOT NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE hstTASK ADD sequenceid int(8) NULL default NULL;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE hstTASK ADD INDEX sequenceid (sequenceid);" | ${prefix}/bin/dbexec
	echo "ALTER TABLE session CHANGE session_object session_object longblob;" | ${prefix}/bin/dbexec
	echo "ALTER TABLE session CHANGE session_expiry session_expiry datetime NOT NULL default '0000-00-00 00:00:00';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE oaiREPOSITORY CHANGE setSpec setSpec varchar(255) NOT NULL default 'GLOBAL_SET';" | ${prefix}/bin/dbexec
	echo "UPDATE oaiREPOSITORY SET setSpec='GLOBAL_SET' WHERE setSpec='';" | ${prefix}/bin/dbexec
	echo "ALTER TABLE user_query_basket ADD COLUMN alert_desc TEXT DEFAULT NULL AFTER alert_name;" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Link_Records','Link two records toghether via MARC');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Video_Processing',NULL);" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Link_Records','edsrn');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Link_Records','edsrn2');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Link_Records','directRelationship');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Link_Records','reverseRelationship');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Video_Processing','aspect');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Video_Processing','batch_template');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Video_Processing','title');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmALLFUNCDESCR VALUES ('Set_RN_From_Sysno', 'Set the value of global rn variable to the report number identified by sysno (recid)');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Set_RN_From_Sysno','edsrn');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Set_RN_From_Sysno','rep_tags');" | ${prefix}/bin/dbexec
	echo "INSERT INTO sbmFUNDESC VALUES ('Set_RN_From_Sysno','record_search_pattern');" | ${prefix}/bin/dbexec

CLEANFILES = *~ *.pyc *.tmp
