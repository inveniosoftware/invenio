SUBDIRS = config dbutil cgibin htdocs

EXTRA_DIST = UNINSTALL .wmlrc

uninstall-local:
	rm -rf @RTLOGSDIR@

load-sample-data:
	## This functionality is not available yet.

clean-sample-data:
	## This functionality is not available yet.

create-tables:
	./dbutil/dbexec < ./dbutil/create_tables.sql

drop-tables:
	./dbutil/dbexec < ./dbutil/drop_tables.sql

CLEANFILES = *~
