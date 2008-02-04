# -*- coding: utf-8 -*-
##
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

"""
BibClassify daemon.
"""

__revision__ = "$Id$"

import sys

from invenio.dbquery import run_sql
from invenio.config import tmpdir
from invenio.bibtask import task_init, write_message, get_datetime, \
    task_set_option, task_get_option, task_get_task_param, task_update_status, \
    task_update_progress

def get_recIDs_of_modified_records_since_last_run():
    """
    Return list of record IDs of records modified since last bibclassify daemon run.
    """
    # first, detect last run of the daemon:
    res = run_sql("""SELECT DATE_FORMAT(last_updated, '%Y-%m-%d %H:%i:%s') FROM clsMETHOD""")
    if res:
        try:
            date_last_run = res[0][0]
        except IndexError:
            date_last_run = '0000-00-00 00:00:00'
    else:
        return []
    # now, select records modified since that time:
    res = run_sql("SELECT id FROM bibrec WHERE modification_date >= %s", (date_last_run,))
    # return list of recIDs:
    recIDs = [x[0] for x in res]
    return recIDs

def update_date_of_last_run(time_to_store):
    """
    Update bibclassify daemon table information about last run time.
    """
    run_sql("UPDATE clsMETHOD SET last_updated=%s", (time_to_store,))

def task_run_core():
    """BibClassify daemon task core."""

    import time

    # store running time:
    time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # see which records we'll have to process:
    recIDs = get_recIDs_of_modified_records_since_last_run()

    if recIDs:
        # process records:
        outfilename = tmpdir + "/bibclassifyd_%s.xml" % time.strftime("%Y%m%dH%M%S", time.localtime())
        outfiledesc = open(outfilename, "w")
        for idx in range(0, len(recIDs)):
            # FIXME: 1. launch bibclassify on recIDs
            # FIXME: 2. (a) bibclassify -> text -> MARCXML; (b) modify bibclassify to spit out XML
            # FIXME: 3. collect MARCXML output into outfile
            outfiledesc.write("""
            <record>
               <controlfield tag="001">%(recID)s</controlfield>
               <datafield tag="653" ind1="1" ind2="">
                 <subfield code="a">muon</subfield>
                 <subfield code="9">BibClassify</subfield>
               </datafield>
               <datafield tag="653" ind1="1" ind2="">
                 <subfield code="a">kaon</subfield>
                 <subfield code="9">BibClassify</subfield>
               </datafield>
               <datafield tag="653" ind1="1" ind2="">
                 <subfield code="a">mass</subfield>
                 <subfield code="9">BibClassify</subfield>
               </datafield>
            </record>
            """ % { 'recID': recIDs[idx]} )
            # update the task progress bar:
            task_update_progress("Done %s of %s." % (idx, len(recIDs)))
            print "processing record ID %s..." % recIDs[idx]
        # FIXME: 4. submit collected MARCXML output:
        #    os.system("bibupload -c foo.xml")

    else:
        write_message("Nothing to be done.")

    # finally, update last run:
    update_date_of_last_run(time_now)
    return

def main():
    """Constructs the bibclassifyd bibtask."""
    task_init(authorization_action='runbibindex',
              authorization_msg="BibIndex Task Submission",
              description="""Examples:
\t%s -u admin
""" % (sys.argv[0],),
              version=__revision__,
              task_run_fnc = task_run_core)

if __name__ == '__main__':
    main()


# FIXME: one can have more than one ontologies in clsMETHOD.
#    bibclassifyd -w HEP,Pizza

# FIXME: add more CLI options like bibindex ones, e.g.
#    bibclassifyd -a -i 10-20

# FIXME: outfiledesc can be multiple files, e.g. when processing
#    100000 records it is good to store results by 1000 records
#    (see oaiharvest)
