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

SUBDIRS = modules

EXTRA_DIST = UNINSTALL .wmlrc

## submit stuff for sample data link creation
sbmdir = $(HTDOCSDIR)submit/access/protected
sbmdat = SBITEXT MBITEXT FTTTEXT SRVTEXT TFUTEXT \
	 SBIRTEXT MBIRTEXT FTTRTEXT SRVRTEXT TFURTEXT APPRTEXT \
	 SBIPICT MBIPICT FTTPICT \
         SBIRPICT MBIRPICT FTTRPICT APPRPICT

uninstall-local:
	rm -rf @RTLOGSDIR@

load-sample-data: install ./dbutil/tabfill.sql
	for f in $(sbmdat); do \
	    if [ ! -e $(sbmdir)/$$f.shtml ]; then \
		ln -s $(sbmdir)/go.shtml $(sbmdir)/$$f.shtml ; \
	    else \
		echo "link $(sbmdir)/$$f.shtml already exists"; \
	    fi \
	done
	exit 0
	./dbutil/dbexec < ./dbutil/samplecfgdata.sql
	(cd ./dbutil; ./bibupload ./samplebibdata.xml)
	(cd ./dbutil; ./bibformat otype=HB,HD,HP,HC < ./samplebibdata.xml > ./samplebibdatafmt.xml)
	(cd ./dbutil; ./bibupload ./samplebibdatafmt.xml)
	rm -f ./dbutil/samplebibdatafmt.xml
	./cgibin/create_collection_pages ""+
	./dbutil/bibwords -ucds.support@cern.ch
	./dbutil/bibwords 1
	./cgibin/create_collection_pages ""+
	@echo "*******************************************************************************"
	@echo "** The sample data has been successfully loaded.                             **"
	@echo "** Please point your browser to @HTDOCSURL@ "
	@echo "** You should be able to see sample collections and to do some searches.     **"
	@echo "** Note that you can do 'gmake clean-sample-data' to remove the sample data. **"
	@echo "*******************************************************************************"

clean-sample-data: install ./dbutil/tabfill.sql
	./dbutil/dbexec < ./dbutil/tabdrop.sql
	./dbutil/dbexec < ./dbutil/tabcreate.sql
	./dbutil/dbexec < ./dbutil/tabfill.sql
	for f in $(sbmdat); do rm -f $(sbmdir)/$$f.shtml ; done
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
