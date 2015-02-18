# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011, 2105 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from __future__ import print_function

__revision__ = "$Id$"

"""This script updates the filesystem structure of fulltext files in order
to make it coherent with bibdocfile implementation (bibdocfile.py structure is backward
compatible with file.py structure, but the viceversa is not true).
"""

import sys
from intbitset import intbitset
from invenio.utils.text import wrap_text_in_a_box
from invenio.config import CFG_LOGDIR, CFG_SITE_SUPPORT_EMAIL
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibdocfile.api import BibRecDocs, InvenioBibDocFileError

from datetime import datetime

from sqlalchemy.exc import OperationalError


def retrieve_fulltext_recids():
    """Returns the list of all the recid number linked with at least a fulltext
    file."""
    res = run_sql('SELECT DISTINCT id_bibrec FROM bibrec_bibdoc')
    return intbitset(res)

def fix_recid(recid, logfile):
    """Fix a given recid."""
    print("Upgrading record %s ->" % recid, end=' ')
    print("Upgrading record %s:" % recid, file=logfile)

    bibrec = BibRecDocs(recid)
    print(bibrec, file=logfile)
    docnames = bibrec.get_bibdoc_names()
    try:
        for docname in docnames:
            print(docname, end=' ')
            new_bibdocs = bibrec.fix(docname)
            new_bibdocnames = [bibrec.get_docname(bibdoc.id) for bibdoc in new_bibdocs]
            if new_bibdocnames:
                print("(created bibdocs: '%s')" % "', '".join(new_bibdocnames), end=' ')
                print("(created bibdocs: '%s')" % "', '".join(new_bibdocnames), file=logfile)
    except InvenioBibDocFileError as e:
        print(BibRecDocs(recid), file=logfile)
        print("%s -> ERROR", e)
        return False
    else:
        print(BibRecDocs(recid), file=logfile)
        print("-> OK")
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
    except OperationalError as e:
        if not drop:
            return False
        raise
    return True

def check_yes():
    """Return True if the user types 'yes'."""
    try:
        return raw_input().strip() == 'yes'
    except KeyboardInterrupt:
        return False

def main():
    """Core loop."""
    logfilename = '%s/fulltext_files_migration_kit-%s.log' % (CFG_LOGDIR, datetime.today().strftime('%Y%m%d%H%M%S'))
    try:
        logfile = open(logfilename, 'w')
    except IOError as e:
        print(wrap_text_in_a_box('NOTE: it\'s impossible to create the log:\n\n  %s\n\nbecause of:\n\n  %s\n\nPlease run this migration kit as the same user who runs Invenio (e.g. Apache)' % (logfilename, e), style='conclusion', break_long=False))
        sys.exit(1)

    recids = retrieve_fulltext_recids()
    print(wrap_text_in_a_box ("""This script migrate the filesystem structure used to store fulltext files to the new stricter structure.
This script must not be run during normal Invenio operations.
It is safe to run this script. No file will be deleted.
Anyway it is recommended to run a backup of the filesystem structure just in case.
A backup of the database tables involved will be automatically performed.""", style='important'))
    print("%s records will be migrated/fixed." % len(recids))
    print("Please type yes if you want to go further:", end=' ')

    if not check_yes():
        print("INTERRUPTED")
        sys.exit(1)
    print("Backing up database tables")
    try:
        if not backup_tables():
            print(wrap_text_in_a_box("""It appears that is not the first time that you run this script.
Backup tables have been already created by a previous run.
In order for the script to go further they need to be removed.""", style='important'))

            print("Please, type yes if you agree to remove them and go further:", end=' ')

            if not check_yes():
                print(wrap_text_in_a_box("INTERRUPTED", style='conclusion'))
                sys.exit(1)
            print("Backing up database tables (after dropping previous backup)", end=' ')
            backup_tables(drop=True)
            print("-> OK")
        else:
            print("-> OK")
    except Exception as e:
        print(wrap_text_in_a_box("Unexpected error while backing up tables. Please, do your checks: %s" % e, style='conclusion'))
        sys.exit(1)

    print("Created a complete log file into %s" % logfilename)
    for recid in recids:
        if not fix_recid(recid, logfile):
            logfile.close()
            print(wrap_text_in_a_box(title="INTERRUPTED BECAUSE OF ERROR!", body="""Please see the log file %s for what was the status of record %s prior to the error. Contact %s in case of problems, attaching the log.""" % (logfilename, recid, CFG_SITE_SUPPORT_EMAIL),
            style='conclusion'))
            sys.exit(1)
    print(wrap_text_in_a_box("DONE", style='conclusion'))

if __name__ == '__main__':
    main()
