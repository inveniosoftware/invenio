SUBDIRS = config dbutil cgibin htdocs

EXTRA_DIST = UNINSTALL .wmlrc

uninstall-local:
	rm -rf @RTLOGSDIR@

load-sample-data: install
	./dbutil/dbexec < ./dbutil/samplecfgdata.sql
	./cgibin/create_collection_pages ""+
	(cd ./dbutil; ./cvxtm ./samplebibdata.xml)
	./dbutil/bibwords add 1-37
	@echo "*******************************************************************************"
	@echo "** The sample data has been successfully loaded.                             **"
	@echo "** Please point your browser to @HTDOCSURL@ "
	@echo "** You should be able to see sample collections and to do some searches.     **"
	@echo "** Note that you can do 'gmake clean-sample-data' to remove the sample data. **"
	@echo "*******************************************************************************"

clean-sample-data:
	./dbutil/dbexec < ./dbutil/drop_tables.sql
	./dbutil/dbexec < ./dbutil/create_tables.sql
	./cgibin/create_collection_pages ""+
	@echo "****************************************************"
	@echo "** The sample data has been successfully cleaned. **"
	@echo "****************************************************"

create-tables:
	./dbutil/dbexec < ./dbutil/create_tables.sql

drop-tables:
	./dbutil/dbexec < ./dbutil/drop_tables.sql

CLEANFILES = *~
