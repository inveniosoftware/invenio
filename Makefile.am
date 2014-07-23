## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

SUBDIRS = config

EXTRA_DIST = UNINSTALL THANKS RELEASE-NOTES configure-tests.py config.nice.in \
             config.rpath


# current MathJax version and packages
# See also modules/miscutil/lib/htmlutils.py (get_mathjax_header)
MJV = 2.3
MATHJAX = http://invenio-software.org/download/mathjax/MathJax-v$(MJV).zip

# current CKeditor version
CKV = 3.6.6
CKEDITOR = ckeditor_$(CKV).zip

# current MediaElement.js version
MEV = master
MEDIAELEMENT = http://github.com/johndyer/mediaelement/zipball/$(MEV)

#for solrutils
INVENIO_JAVA_PATH = org/invenio_software/solr
solrdirname = apache-solr-3.1.0
solrdir = $(prefix)/lib/$(solrdirname)
solrutils_dir=$(CURDIR)/modules/miscutil/lib/solrutils

# for recline.js
RECLINEVER=master

CLASSPATH=.:${solrdir}/dist/solrj-lib/commons-io-1.4.jar:${solrdir}/dist/apache-solr-core-*jar:${solrdir}/contrib/jzlib-1.0.7.jar:${solrdir}/dist/apache-solr-solrj-3.1.0.jar:${solrdir}/dist/solrj-lib/slf4j-api-1.5.5.jar:${solrdir}/dist/*:${solrdir}/contrib/basic-lucene-libs/*:${solrdir}/contrib/analysis-extras/lucene-libs/*:${solrdir}/dist/solrj-lib/*

# git-version-get stuff:
BUILT_SOURCES = $(top_srcdir)/.version
$(top_srcdir)/.version:
	echo $(VERSION) > $@-t && mv $@-t $@
dist-hook:
	echo $(VERSION) > $(distdir)/.tarball-version

# Bootstrap version
BOOTSTRAPV = 3.0.2

# Hogan.js version
HOGANVER = 2.0.0

check-custom-templates:
	$(PYTHON) $(top_srcdir)/modules/webstyle/lib/template.py --check-custom-templates $(top_srcdir)

kwalitee-check:
	@$(PYTHON) $(top_srcdir)/scripts/kwalitee.py --stats $(top_srcdir)

kwalitee-check-errors-only:
	@$(PYTHON) $(top_srcdir)/scripts/kwalitee.py --check-errors $(top_srcdir)

kwalitee-check-variables:
	@$(PYTHON) $(top_srcdir)/scripts/kwalitee.py --check-variables $(top_srcdir)

kwalitee-check-indentation:
	@$(PYTHON) $(top_srcdir)/scripts/kwalitee.py --check-indentation $(top_srcdir)

kwalitee-check-sql-queries:
	@$(PYTHON) $(top_srcdir)/scripts/kwalitee.py --check-sql $(top_srcdir)

etags:
	\rm -f $(top_srcdir)/TAGS
	(cd $(top_srcdir) && find $(top_srcdir) -name "*.py" -print | xargs etags)

install-data-local:
	for d in / /cache /cache/RTdata /log /tmp /tmp-shared /data /run /tmp-shared/bibencode/jobs/done /tmp-shared/bibedit-cache; do	\
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
	rm -fr ${prefix}/var/www/MathJax
	mkdir -p ${prefix}/var/www/MathJax
	(cd /tmp/invenio-mathjax-plugin && \
	wget '$(MATHJAX)' -O mathjax.zip && \
	unzip -q mathjax.zip && cd mathjax-MathJax-* && cp -r * \
	${prefix}/var/www/MathJax)
	rm -fr /tmp/invenio-mathjax-plugin
	@echo "************************************************************"
	@echo "** The MathJax plugin was successfully installed.         **"
	@echo "** Please do not forget to properly set the option        **"
	@echo "** CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS and              **"
	@echo "** CFG_WEBSUBMIT_USE_MATHJAX in invenio.conf.             **"
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

install-js-test-driver:
	@echo "*******************************************************"
	@echo "** Installing js-test-driver, please wait...         **"
	@echo "*******************************************************"
	mkdir -p $(prefix)/lib/java/js-test-driver && \
	cd $(prefix)/lib/java/js-test-driver && \
	wget http://invenio-software.org/download/js-test-driver/JsTestDriver-1.3.5.jar -O JsTestDriver.jar

uninstall-js-test-driver:
	@rm -rvf ${prefix}/lib/java/js-test-driver
	@echo "*********************************************************"
	@echo "** The js-test-driver was successfully uninstalled.    **"
	@echo "*********************************************************"

install-jquery-plugins:
	@echo "***********************************************************"
	@echo "** Installing various jQuery plugins, please wait...     **"
	@echo "***********************************************************"
	mkdir -p ${prefix}/var/www/js
	mkdir -p $(prefix)/var/www/css
	mkdir -p $(prefix)/var/www/img
	(cd ${prefix}/var/www/js && \
	wget http://invenio-software.org/download/jquery/jquery-1.7.1.min.js && \
	mv jquery-1.7.1.min.js jquery.min.js && \
	wget http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.17/jquery-ui.min.js && \
    wget http://invenio-software.org/download/jquery/jquery.jeditable.custom.min.js -O jquery.jeditable.mini.js && \
	wget https://raw.github.com/malsup/form/master/jquery.form.js --no-check-certificate && \
	wget http://jquery-multifile-plugin.googlecode.com/svn/trunk/jquery.MultiFile.pack.js && \
	wget -O jquery.tablesorter.zip http://invenio-software.org/download/jquery/jquery.tablesorter.20111208.zip && \
	wget http://invenio-software.org/download/jquery/uploadify-v2.1.4.zip -O uploadify.zip && \
	wget http://www.datatables.net/download/build/jquery.dataTables.min.js && \
	rm -rf /tmp/invenio-dt-bootstrap && \
	mkdir /tmp/invenio-dt-bootstrap && \
	(cd /tmp/invenio-dt-bootstrap && \
	 git clone 'https://github.com/DataTables/Plugins.git' && \
	 cp Plugins/integration/bootstrap/2/dataTables.bootstrap.css ${prefix}/var/www/css/dataTables.bootstrap.css && \
	 cp Plugins/integration/bootstrap/2/dataTables.bootstrap.js ${prefix}/var/www/js/dataTables.bootstrap.js && \
	 cp Plugins/integration/bootstrap/images/*.png ${prefix}/var/www/img/ && \
	 ln -s ${prefix}/var/www/img/ ${prefix}/var/www/images) && \
	rm -rf /tmp/invenio-dt-bootstrap/plugins && \
	mkdir /tmp/invenio-dt-bootstrap/plugins && \
	(cd /tmp/invenio-dt-bootstrap/plugins && \
	 git clone 'https://github.com/DataTables/ColVis' && \
	 cp ColVis/media/css/ColVis.css ${prefix}/var/www/css/ColVis.css && \
	 cp ColVis/media/js/ColVis.js ${prefix}/var/www/js/ColVis.js && \
	 cp ColVis/media/images/*.png ${prefix}/var/www/img/) && \
	cd ${prefix}/var/www/js && \
	rm -rf /tmp/invenio-dt-bootstrap/plugins && \
	mkdir /tmp/invenio-dt-bootstrap/plugins && \
	(cd /tmp/invenio-dt-bootstrap/plugins && \
	 git clone 'https://github.com/LeaVerou/prism' && \
	 cp prism/themes/prism.css ${prefix}/var/www/css/prism.css && \
	 cp prism/prism.js ${prefix}/var/www/js/prism.js) && \
	rm -rf /tmp/invenio-dt-bootstrap/plugins && \
	wget http://invenio-software.org/download/jquery/jquery.bookmark.package-1.4.0.zip && \
	unzip jquery.tablesorter.zip -d tablesorter && \
	wget http://invenio-software.org/download/jquery/jquery.fileTree-1.01.zip && \
	unzip jquery.fileTree-1.01.zip && \
	rm jquery.fileTree-1.01.zip && \
	wget http://invenio-software.org/download/jquery/ColVis.min.js && \
	mv ColVis.min.js jquery.dataTables.ColVis.min.js && \
	rm jquery.tablesorter.zip && \
	rm -rf uploadify && \
	unzip -u uploadify.zip -d uploadify && \
	wget http://invenio-software.org/download/jquery/flot-0.6.zip && \
	wget http://www.csspace.net/tmp/jquery-lightbox-0.5.zip && \
	rm -rf jquery-lightbox && \
	unzip -u jquery-lightbox-0.5.zip -d jquery-lightbox && \
	sed -i 's/images\//\/js\/jquery-lightbox\/images\//g' jquery-lightbox/js/jquery.lightbox-0.5.js && \
	rm -rf jquery-lightbox-0.5.zip && \
	wget -O jquery-ui-timepicker-addon.js http://invenio-software.org/download/jquery/jquery-ui-timepicker-addon-1.0.3.js && \
	unzip -u flot-0.6.zip && \
	mv flot/jquery.flot.selection.min.js flot/jquery.flot.min.js flot/excanvas.min.js ./ && \
	rm flot-0.6.zip && rm -r flot && \
	mv uploadify/swfobject.js ./ && \
	mv uploadify/cancel.png uploadify/uploadify.css uploadify/uploadify.allglyphs.swf uploadify/uploadify.fla uploadify/uploadify.swf ../img/ && \
	mv uploadify/jquery.uploadify.v2.1.4.min.js ./jquery.uploadify.min.js && \
	rm uploadify.zip && rm -r uploadify && \
	wget --no-check-certificate https://github.com/douglascrockford/JSON-js/raw/master/json2.js && \
	wget http://invenio-software.org/download/jquery/jquery.hotkeys-0.8.js -O jquery.hotkeys.js && \
	wget http://invenio-software.org/download/jquery/jquery.treeview.zip && \
	unzip jquery.treeview.zip -d jquery-treeview && \
	rm jquery.treeview.zip && \
	wget http://invenio-software.org/download/jquery/v1.5/js/jquery.ajaxPager.js && \
	unzip jquery.bookmark.package-1.4.0.zip && \
	rm -f jquery.bookmark.ext.* bookmarks-big.png bookmarkBasic.html jquery.bookmark.js jquery.bookmark.pack.js && \
	mv bookmarks.png ../img/ && \
	mv jquery.bookmark.css ../css/ && \
	wget --no-check-certificate http://invenio-software.org/download/jquery/jquery.omniwindow.js && \
	wget --no-check-certificate http://invenio-software.org/download/jquery/jquery.blockUI.js && \
	wget --no-check-certificate http://invenio-software.org/download/jquery/sly.min.js &&\
	wget --no-check-certificate http://invenio-software.org/download/jquery/parsley.js &&\
	wget --no-check-certificate http://invenio-software.org/download/jquery/spin.min.js &&\
	rm -f jquery.bookmark.package-1.4.0.zip && \
	mkdir -p ${prefix}/var/www/img && \
	cd ${prefix}/var/www/img && \
	wget -r -np -nH --cut-dirs=4 -A "png,css" -P jquery-ui/themes http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/base/ && \
	wget -r -np -nH --cut-dirs=4 -A "png,css" -P jquery-ui/themes http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/smoothness/ && \
	wget -r -np -nH --cut-dirs=4 -A "png,css" -P jquery-ui/themes http://jquery-ui.googlecode.com/svn/tags/1.8.17/themes/redmond/ && \
	wget --no-check-certificate -O datatables_jquery-ui.css https://raw.githubusercontent.com/DataTables/DataTables/1.10.0/media/css/demo_table_jui.css && \
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
	rm -f json2.js && \
	rm -f jquery.uploadify.min.js && \
	rm -rf tablesorter && \
	rm -rf jquery-treeview && \
	rm -f jquery.ajaxPager.js && \
	rm -f jquery.form.js && \
	rm -f jquery.dataTables.min.js && \
	rm -f ui.core.js && \
	rm -f jquery.bookmark.min.js && \
		rm -f jquery.dataTables.ColVis.min.js && \
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
	wget 'http://invenio-software.org/download/ckeditor/$(CKEDITOR)' && \
	unzip -u -d ${prefix}/var/www $(CKEDITOR)) && \
	find ${prefix}/var/www/ckeditor/ -depth -name '_*' -exec rm -rf {} \; && \
	find ${prefix}/var/www/ckeditor/ckeditor* -maxdepth 0 ! -name "ckeditor.js" -exec rm -r {} \; && \
	touch ${prefix}/var/www/ckeditor/invenio-ckeditor-config.js && \
	rm -fr /tmp/invenio-ckeditor-plugin
	@echo "* Installing Invenio-specific CKeditor config..."
	@echo "Ignored: (cd $(top_srcdir)/modules/webstyle/etc && make install)"
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

install-bootstrap:
	@echo "***********************************************************"
	@echo "** Installing Twitter Bootstrap, please wait...          **"
	@echo "***********************************************************"
	rm -rf /tmp/invenio-bootstrap
	mkdir /tmp/invenio-bootstrap
	(cd /tmp/invenio-bootstrap && \
	wget -O bootstrap.zip 'https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAPV}/bootstrap-${BOOTSTRAPV}-dist.zip' && \
	unzip -u bootstrap.zip && \
	cp dist/css/bootstrap.css ${prefix}/var/www/css/bootstrap.css && \
	cp dist/css/bootstrap.min.css ${prefix}/var/www/css/bootstrap.min.css && \
	cp dist/css/bootstrap-theme.css ${prefix}/var/www/css/bootstrap-theme.css && \
	cp dist/css/bootstrap-theme.min.css ${prefix}/var/www/css/bootstrap-theme.min.css && \
	mkdir -p ${prefix}/var/www/fonts && \
	cp dist/fonts/glyphicons-halflings-regular.eot ${prefix}/var/www/fonts/glyphicons-halflings-regular.eot && \
	cp dist/fonts/glyphicons-halflings-regular.svg ${prefix}/var/www/fonts/glyphicons-halflings-regular.svg && \
	cp dist/fonts/glyphicons-halflings-regular.ttf ${prefix}/var/www/fonts/glyphicons-halflings-regular.ttf && \
	cp dist/fonts/glyphicons-halflings-regular.woff ${prefix}/var/www/fonts/glyphicons-halflings-regular.woff && \
	cp dist/js/bootstrap.js ${prefix}/var/www/js/bootstrap.js && \
	cp dist/js/bootstrap.min.js ${prefix}/var/www/js/bootstrap.min.js && \
	wget -O bootstrap-typeahead.zip 'http://twitter.github.com/typeahead.js/releases/latest/typeahead.js.zip' && \
	unzip -u bootstrap-typeahead.zip && \
	cp typeahead.js/typeahead.js ${prefix}/var/www/js/typeahead.js && \
	cp typeahead.js/typeahead.min.js ${prefix}/var/www/js/typeahead.min.js && \
	wget -O typeahead.js-bootstrap.css 'https://raw.github.com/jharding/typeahead.js-bootstrap.css/master/typeahead.js-bootstrap.css' && \
	mv typeahead.js-bootstrap.css ${prefix}/var/www/css/typeahead.js-bootstrap.css && \
	rm -fr /tmp/invenio-bootstrap )
	@echo "***********************************************************"
	@echo "** The Twitter Bootstrap was successfully installed.     **"
	@echo "***********************************************************"

uninstall-bootstrap:
	rm ${prefix}/var/www/css/bootstrap.css && \
	rm ${prefix}/var/www/css/bootstrap.min.css && \
	rm ${prefix}/var/www/css/bootstrap-theme.css && \
	rm ${prefix}/var/www/css/bootstrap-theme.min.css && \
	rm ${prefix}/var/www/css/typeahead.js-bootstrap.css && \
	rm ${prefix}/var/www/fonts/glyphicons-halflings-regular.eot && \
	rm ${prefix}/var/www/fonts/glyphicons-halflings-regular.svg && \
	rm ${prefix}/var/www/fonts/glyphicons-halflings-regular.ttf && \
	rm ${prefix}/var/www/fonts/glyphicons-halflings-regular.woff && \
	rm ${prefix}/var/www/js/bootstrap.js && \
	rm ${prefix}/var/www/js/bootstrap.min.js && \
	rm ${prefix}/var/www/js/typeahead.js && \
	rm ${prefix}/var/www/js/typeahead.min.js
	@echo "***********************************************************"
	@echo "** The Twitter Bootstrap was successfully uninstalled.   **"
	@echo "***********************************************************"

install-hogan-plugin:
	@echo "***********************************************************"
	@echo "** Installing Hogan.js, please wait...                   **"
	@echo "***********************************************************"
	rm -rf /tmp/hogan
	mkdir /tmp/hogan
	(cd /tmp/hogan && \
	wget -O hogan-${HOGANVER}.js 'http://twitter.github.com/hogan.js/builds/${HOGANVER}/hogan-${HOGANVER}.js' && \
	cp hogan-${HOGANVER}.js ${prefix}/var/www/js/hogan.js && \
	rm -fr /tmp/hogan )
	@echo "***********************************************************"
	@echo "** Hogan.js was successfully installed.                  **"
	@echo "***********************************************************"

uninstall-hogan-plugin:
	rm ${prefix}/var/www/js/hogan.js
	@echo "***********************************************************"
	@echo "** Hogan.js was successfully uninstalled.                **"
	@echo "***********************************************************"

install-typeahead-plugin:
	@echo "***********************************************************"
	@echo "** Installing typeahead.js, please wait...               **"
	@echo "***********************************************************"
	rm -rf /tmp/typeahead
	mkdir /tmp/typeahead
	(cd /tmp/typeahead && \
	wget -O typeahead.min.js 'http://twitter.github.com/typeahead.js/releases/latest/typeahead.min.js' && \
	cp typeahead.min.js ${prefix}/var/www/js/typeahead.min.js && \
	wget -O typeahead.js-bootstrap.css 'https://raw.github.com/jharding/typeahead.js-bootstrap.css/master/typeahead.js-bootstrap.css' && \
	cp typeahead.js-bootstrap.css ${prefix}/var/www/css/typeahead.js-bootstrap.css && \
	rm -fr /tmp/typeahead )
	@echo "***********************************************************"
	@echo "** typeahead.js was successfully installed.              **"
	@echo "***********************************************************"

uninstall-typeahead-plugin:
	rm ${prefix}/var/www/js/typeahead.min.js
	@echo "***********************************************************"
	@echo "** typeahead.js was successfully uninstalled.            **"

install-recline:
	@echo "***********************************************************"
	@echo "** Installing Recline JS, please wait...          **"
	@echo "***********************************************************"
	rm -rf /tmp/invenio-recline
	mkdir /tmp/invenio-recline
	(cd /tmp/invenio-recline && \
	wget -O recline.zip 'https://github.com/okfn/recline/archive/${RECLINEVER}.zip' && \
	unzip -u recline.zip && \
	rm recline.zip && \
	mv *recline* recline && \
	mkdir -p ${prefix}/var/www/js/recline/css && \
	mkdir -p ${prefix}/var/www/js/recline/dist && \
	mkdir -p ${prefix}/var/www/js/recline/src && \
	mkdir -p ${prefix}/var/www/js/recline/vendor && \
	cp -R recline/css ${prefix}/var/www/js/recline/ && \
	cp -R recline/src ${prefix}/var/www/js/recline/ && \
	cp -R recline/dist ${prefix}/var/www/js/recline/ && \
	cp -R recline/vendor ${prefix}/var/www/js/recline/ && \
	rm -rf /tmp/invenio-recline )
	@echo "***********************************************************"
	@echo "** The Recline JS was successfully installed.     **"
	@echo "***********************************************************"

uninstall-recline:
	rm -Rf ${prefix}/var/www/js/recline
	@echo "***********************************************************"
	@echo "** The Recline JS was successfully uninstalled.   **"
	@echo "***********************************************************"

install-jquery-tokeninput:
	@echo "***********************************************************"
	@echo "** Installing JQuery Tokeninput, please wait...          **"
	@echo "***********************************************************"
	rm -rf /tmp/jquery-tokeninput
	mkdir /tmp/jquery-tokeninput
	(cd /tmp/jquery-tokeninput && \
	wget -O jquery-tokeninput-master.zip 'https://github.com/loopj/jquery-tokeninput/archive/master.zip' --no-check-certificate && \
	unzip -u jquery-tokeninput-master.zip && \
	cp jquery-tokeninput-master/styles/token-input-facebook.css ${prefix}/var/www/css/token-input-facebook.css && \
	cp jquery-tokeninput-master/styles/token-input-mac.css ${prefix}/var/www/css/token-input-mac.css && \
	cp jquery-tokeninput-master/styles/token-input.css ${prefix}/var/www/css/token-input.css && \
	cp jquery-tokeninput-master/src/jquery.tokeninput.js ${prefix}/var/www/js/jquery.tokeninput.js && \
	rm -fr /tmp/jquery-tokeninput )
	@echo "***********************************************************"
	@echo "** The JQuery Tokeninput was successfully installed.     **"
	@echo "***********************************************************"

uninstall-jquery-tokeninput:
	rm ${prefix}/var/www/css/token-input-facebook.css && \
	rm ${prefix}/var/www/css/token-input-mac.css && \
	rm ${prefix}/var/www/css/token-input.css && \
	rm ${prefix}/var/www/js/jquery.tokeninput.js
	@echo "***********************************************************"
	@echo "** The JQuery Tokeninput was successfully uninstalled.   **"
	@echo "***********************************************************"

install-plupload-plugin:
	@echo "***********************************************************"
	@echo "** Installing Plupload plugin, please wait...            **"
	@echo "***********************************************************"
	rm -rf /tmp/plupload-plugin
	mkdir /tmp/plupload-plugin
	(cd /tmp/plupload-plugin && \
	wget -O plupload-plugin.zip 'http://invenio-software.org/download/jquery/plupload-1.5.5.zip' && \
	unzip -u plupload-plugin.zip && \
	mkdir -p ${prefix}/var/www/js/plupload/i18n/ && \
	cp -R plupload/js/jquery.plupload.queue ${prefix}/var/www/js/plupload/ && \
	cp -R plupload/js/jquery.ui.plupload ${prefix}/var/www/js/plupload/ && \
	cp plupload/js/plupload.browserplus.js ${prefix}/var/www/js/plupload/plupload.browserplus.js && \
	cp plupload/js/plupload.flash.js ${prefix}/var/www/js/plupload/plupload.flash.js && \
	cp plupload/js/plupload.flash.swf ${prefix}/var/www/js/plupload/plupload.flash.swf && \
	cp plupload/js/plupload.full.js ${prefix}/var/www/js/plupload/plupload.full.js && \
	cp plupload/js/plupload.gears.js ${prefix}/var/www/js/plupload/plupload.gears.js && \
	cp plupload/js/plupload.html4.js ${prefix}/var/www/js/plupload/plupload.html4.js && \
	cp plupload/js/plupload.html5.js ${prefix}/var/www/js/plupload/plupload.html5.js && \
	cp plupload/js/plupload.js ${prefix}/var/www/js/plupload/plupload.js && \
	cp plupload/js/plupload.silverlight.js ${prefix}/var/www/js/plupload/plupload.silverlight.js && \
	cp plupload/js/plupload.silverlight.xap ${prefix}/var/www/js/plupload/plupload.silverlight.xap && \
	cp plupload/js/i18n/*.js ${prefix}/var/www/js/plupload/i18n/ && \
	rm -fr /tmp/plupload-plugin )
	@echo "***********************************************************"
	@echo "** The Plupload plugin was successfully installed.       **"
	@echo "***********************************************************"

uninstall-plupload-plugin:
	rm -rf ${prefix}/var/www/js/plupload
	@echo "***********************************************************"
	@echo "** The Plupload was successfully uninstalled.            **"
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
	wget http://archive.apache.org/dist/lucene/solr/3.1.0/apache-solr-3.1.0.tgz && \
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

update-v0.99.0-tables:
	cat $(top_srcdir)/invenio/legacy/miscutil/sql/tabcreate.sql | grep -v 'INSERT INTO upgrade' | ${prefix}/bin/dbexec
	echo "DROP TABLE IF EXISTS oaiREPOSITORY;" | ${prefix}/bin/dbexec
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

update-v0.99.8-tables:
	@echo "Nothing to do; table structure did not change between v0.99.8 and v0.99.9."

update-v0.99.9-tables: # from v0.99.9 to v1.0.0-rc0
	echo "RENAME TABLE oaiARCHIVE TO oaiREPOSITORY;" | ${prefix}/bin/dbexec
	cat $(top_srcdir)/invenio/legacy/miscutil/sql/tabcreate.sql | grep -v 'INSERT INTO upgrade' | ${prefix}/bin/dbexec
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
	echo -e 'from invenio.legacy.webcomment.adminlib import migrate_comments_populate_threads_index;\
	migrate_comments_populate_threads_index()' | $(PYTHON)
	echo -e 'from invenio.modules.access.firerole import repair_role_definitions;\
	repair_role_definitions()' | $(PYTHON)

CLEANFILES = *~ *.pyc *.tmp
