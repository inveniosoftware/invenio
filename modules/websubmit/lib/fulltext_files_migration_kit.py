## $Id$

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

__revision__ = "$Id$"

"""This script updates the filesystem structure of fulltext files in order
to make it coherent with bibdocfile implementation (bibdocfile.py structure is backward
compatible with file.py structure, but the viceversa is not true).
"""

import sys
from invenio.config import logdir, supportemail
from invenio.dbquery import run_sql, OperationalError
from invenio.bibdocfile import BibRecDocs, InvenioWebSubmitFileError
from datetime import datetime

def retrieve_fulltext_recids():
    """Returns the list of all the recid number linked with at least a fulltext
    file."""
    res = run_sql('SELECT DISTINCT id_bibrec FROM bibrec_bibdoc')
    return [recid[0] for recid in res]

def fix_recid(recid, logfile):
    """Fix a given recid."""
    print "Fixing record %s ->" % recid,
    print >> logfile, "Fixing record %s:" % recid

    bibrec = BibRecDocs(recid)
    print >> logfile, bibrec
    docnames = bibrec.get_bibdoc_names()
    try:
        for docname in docnames:
            print docname,
            new_bibdocs = bibrec.fix(docname)
            new_bibdocnames = [bibdoc.get_docname() for bibdoc in new_bibdocs]
            if new_bibdocnames:
                print "(created bibdocs: '%s')" % "', '".join(new_bibdocnames),
                print >> logfile, "(created bibdocs: '%s')" % "', '".join(new_bibdocnames)
    except InvenioWebSubmitFileError, e:
        print >> logfile, BibRecDocs(recid)
        print "%s -> ERROR", e
        return False
    else:
        print >> logfile, BibRecDocs(recid)
        print "-> OK"
        return True

def backup_tables(drop=False):
    """This function create a backup of bibrec_bibdoc, bibdoc and bibdoc_bibdoc tables. Returns False in case dropping of previous table is needed."""
    if drop:
        run_sql('DROP TABLE bibrec_bibdoc_backup')
        run_sql('DROP TABLE bibdoc_backup')
        run_sql('DROP TABLE bibdoc_bibdoc_backup')
    try:
        run_sql("""CREATE TABLE bibrec_bibdoc_backup (KEY id_bibrec(id_bibrec),
                KEY id_bibdoc(id_bibdoc)) SELECT * FROM bibrec_bibdoc""")
        run_sql("""CREATE TABLE bibdoc_backup (PRIMARY KEY id(id))
                SELECT * FROM bibdoc""")
        run_sql("""CREATE TABLE bibdoc_bibdoc_backup (KEY id_bibdoc1(id_bibdoc1),
                KEY id_bibdoc2(id_bibdoc2)) SELECT * FROM bibdoc_bibdoc""")
    except OperationalError, e:
        if not drop:
            return False
        raise e
    return True

def check_yes():
    """Return True if the user types 'yes'."""
    return raw_input().strip() == 'yes'

def main():
    """Core loop."""
    recids = retrieve_fulltext_recids()
    print "*******************************************************************"
    print "* This script migrate the filesystem structure used to store      *"
    print "* fulltext files to the new stricter structure.                   *"
    print "* This script must not be run during normal Invenio operations.   *"
    print "* It is safe to run this script. No file will be deleted.         *"
    print "* Anyway it is recommended to run a backup of the filesystem      *"
    print "* structure just in case.                                         *"
    print "* A backup of the database tables involved will be automatically  *"
    print "* performed.                                                      *"
    print "*******************************************************************"
    print
    print "%s records will be migrated/fixed." % len(recids)
    print "Please type yes if you want to go further:",

    if not check_yes():
        print "INTERRUPTED"
        sys.exit(1)
    print "-" * 40
    print "Backing up database tables",
    try:
        if not backup_tables():
            print
            print "*******************************************************************"
            print "* It appears that is not the first time that you run this script. *"
            print "* Backup tables have been already created by a previous run.      *"
            print "* In order for the script to go further they need to be removed.  *"
            print "*******************************************************************"
            print
            print "Please, type yes if you agree to remove them and go further:",

            if not check_yes():
                print "INTERRUPTED"
                sys.exit(1)
            print "-" * 40
            print "Backing up database tables (after dropping previous backup)",
            backup_tables()
            print "-> OK"
        else:
            print "-> OK"
    except Exception, e:
        print
        print "Unexpected error while backing up tables. Please, do your checks."
        print e
        sys.exit(1)

    logfilename = '%s/fulltext_files_migration_kit-%s.log' % (logdir, datetime.today().strftime('%Y%m%d%H%M%S'))
    logfile = open(logfilename, 'w')
    print "Created a complete log file into %s" % logfilename
    for recid in recids:
        if not fix_recid(recid, logfile):
            print "-" * 40
            print "INTERRUPTED BECAUSE OF ERROR!"
            print "Please see the log file %s for what was the status of " % logfilename
            print "record %s prior to the error." % recid
            print "Contact %s in case of problems, attaching the log." % supportemail
            logfile.close()
            sys.exit(1)
    print "-" * 40
    print "DONE"

if __name__ == '__main__':
    main()
