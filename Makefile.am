SUBDIRS = config dbutil cgibin htdocs

EXTRA_DIST = UNINSTALL .wmlrc

uninstall-local:
	rm -rf @RTLOGSDIR@

load-sample-data: install ./dbutil/tabfill.sql
	./dbutil/dbexec < ./dbutil/samplecfgdata.sql
	(cd ./dbutil; ./bibformat < ./samplebibdata.xml > ./samplebibdatafmt.xml)
	(cd ./dbutil; ./bibupload ./samplebibdatafmt.xml)
	rm -f ./dbutil/samplebibdatafmt.xml
	./cgibin/create_collection_pages ""+
	./dbutil/bibwords add 1-70
	@echo "*******************************************************************************"
	@echo "** The sample data has been successfully loaded.                             **"
	@echo "** Please point your browser to @HTDOCSURL@ "
	@echo "** You should be able to see sample collections and to do some searches.     **"
	@echo "** Note that you can do 'gmake clean-sample-data' to remove the sample data. **"
	@echo "*******************************************************************************"

clean-sample-data: ./dbutil/tabfill.sql
	./dbutil/dbexec < ./dbutil/tabdrop.sql
	./dbutil/dbexec < ./dbutil/tabcreate.sql
	./dbutil/dbexec < ./dbutil/tabfill.sql
	./cgibin/create_collection_pages ""+
	@echo "****************************************************"
	@echo "** The sample data has been successfully cleaned. **"
	@echo "****************************************************"

create-tables: ./dbutil/tabfill.sql
	./dbutil/dbexec < ./dbutil/tabcreate.sql
	./dbutil/dbexec < ./dbutil/tabfill.sql

drop-tables:
	./dbutil/dbexec < ./dbutil/tabdrop.sql

CLEANFILES = *~ index.wml
