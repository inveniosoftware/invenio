## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""
This script updates the filesystem and database structure WRT icons.

In particular it will move all the icons information out of bibdoc_bibdoc
tables and into the normal bibdoc + subformat infrastructure.
"""

import sys
from datetime import datetime

from invenio.textutils import wrap_text_in_a_box, wait_for_user
from invenio.bibtask import check_running_process_user
from invenio.dbquery import run_sql, OperationalError
from invenio.bibdocfile import BibDoc
from invenio.config import CFG_LOGDIR, CFG_SITE_SUPPORT_EMAIL
from invenio.bibdocfilecli import cli_fix_marc
from invenio.errorlib import register_exception
from invenio.intbitset import intbitset
from invenio.search_engine import record_exists


def retrieve_bibdoc_bibdoc():
    return run_sql('SELECT id_bibdoc1, id_bibdoc2 from bibdoc_bibdoc')

def get_recid_from_docid(docid):
    return run_sql('SELECT id_bibrec FROM bibrec_bibdoc WHERE id_bibdoc=%s', (docid, ))

def backup_tables(drop=False):
    """This function create a backup of bibrec_bibdoc, bibdoc and bibdoc_bibdoc tables. Returns False in case dropping of previous table is needed."""
    if drop:
        run_sql('DROP TABLE bibdoc_bibdoc_backup_for_icon')
    try:
        run_sql("""CREATE TABLE bibdoc_bibdoc_backup_for_icon (KEY id_bibdoc1(id_bibdoc1),
                KEY id_bibdoc2(id_bibdoc2)) SELECT * FROM bibdoc_bibdoc""")
    except OperationalError, e:
        if not drop:
            return False
        raise e
    return True

def fix_bibdoc_bibdoc(id_bibdoc1, id_bibdoc2, logfile):
    """
    Migrate an icon.
    """

    try:
        the_bibdoc = BibDoc.create_instance(id_bibdoc1)
    except Exception, err:
        msg = "WARNING: when opening docid %s: %s" % (id_bibdoc1, err)
        print >> logfile, msg
        print msg
        return True
    try:
        msg = "Fixing icon for the document %s" % (id_bibdoc1, )
        print msg,
        print >> logfile, msg,
        the_icon = BibDoc.create_instance(id_bibdoc2)
        for a_file in the_icon.list_latest_files():
            the_bibdoc.add_icon(a_file.get_full_path(), format=a_file.get_format())
        the_icon.delete()
        run_sql("DELETE FROM bibdoc_bibdoc WHERE id_bibdoc1=%s AND id_bibdoc2=%s", (id_bibdoc1, id_bibdoc2))
        print "OK"
        print >> logfile, "OK"
        return True
    except Exception, err:
        print "ERROR: %s" % err
        print >> logfile, "ERROR: %s" % err
        register_exception()
        return False

def main():
    """Core loop."""
    check_running_process_user()
    logfilename = '%s/fulltext_files_migration_kit-%s.log' % (CFG_LOGDIR, datetime.today().strftime('%Y%m%d%H%M%S'))
    try:
        logfile = open(logfilename, 'w')
    except IOError, e:
        print wrap_text_in_a_box('NOTE: it\'s impossible to create the log:\n\n  %s\n\nbecause of:\n\n  %s\n\nPlease run this migration kit as the same user who runs Invenio (e.g. Apache)' % (logfilename, e), style='conclusion', break_long=False)
        sys.exit(1)

    bibdoc_bibdoc = retrieve_bibdoc_bibdoc()

    print wrap_text_in_a_box ("""This script migrate the filesystem structure used to store icons files to the new stricter structure.
This script must not be run during normal Invenio operations.
It is safe to run this script. No file will be deleted.
Anyway it is recommended to run a backup of the filesystem structure just in case.
A backup of the database tables involved will be automatically performed.""", style='important')
    if not bibdoc_bibdoc:
        print wrap_text_in_a_box("No need for migration", style='conclusion')
        return
    print "%s icons will be migrated/fixed." % len(bibdoc_bibdoc)
    wait_for_user()
    print "Backing up database tables"
    try:
        if not backup_tables():
            print wrap_text_in_a_box("""It appears that is not the first time that you run this script.
Backup tables have been already created by a previous run.
In order for the script to go further they need to be removed.""", style='important')

            wait_for_user()
            print "Backing up database tables (after dropping previous backup)",
            backup_tables(drop=True)
            print "-> OK"
        else:
            print "-> OK"
    except Exception, e:
        print wrap_text_in_a_box("Unexpected error while backing up tables. Please, do your checks: %s" % e, style='conclusion')
        sys.exit(1)

    to_fix_marc = intbitset()
    print "Created a complete log file into %s" % logfilename
    try:
        try:
            for id_bibdoc1, id_bibdoc2 in bibdoc_bibdoc:
                try:
                    record_does_exist = True
                    recids = get_recid_from_docid(id_bibdoc1)
                    if not recids:
                        print "Skipping %s" % id_bibdoc1
                        continue
                    for recid in recids:
                        if record_exists(recid[0]) > 0:
                            to_fix_marc.add(recid[0])
                        else:
                            record_does_exist = False
                    if not fix_bibdoc_bibdoc(id_bibdoc1, id_bibdoc2, logfile):
                        if record_does_exist:
                            raise StandardError("Error when correcting document ID %s" % id_bibdoc1)
                except Exception, err:
                    print >> logfile, "ERROR: %s" % err
            print wrap_text_in_a_box("DONE", style='conclusion')
        except:
            logfile.close()
            register_exception()
            print wrap_text_in_a_box(
                title = "INTERRUPTED BECAUSE OF ERROR!",
                body = """Please see the log file %s for what was the status prior to the error. Contact %s in case of problems, attaching the log.""" % (logfilename, CFG_SITE_SUPPORT_EMAIL),
            style = 'conclusion')
            sys.exit(1)
    finally:
        print "Scheduling FIX-MARC to synchronize MARCXML for updated records."
        cli_fix_marc(options={}, explicit_recid_set=to_fix_marc)


if __name__ == '__main__':
    main()
