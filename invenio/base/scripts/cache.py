# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

from flask import current_app
from invenio.ext.script import Manager, change_command_name

manager = Manager(usage="Perform cache operations")


def reset_rec_cache(output_format, get_record, split_by=1000):
    """It either stores or does not store the output_format.

    If CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE is changed, this function
    will adapt the database to either store or not store the output_format."""

    import sys
    try:
        from six.moves import cPickle as pickle
    except:
        import pickle
    from itertools import islice
    from intbitset import intbitset
    from invenio.legacy.bibsched.cli import server_pid, pidfile
    from invenio.ext.sqlalchemy import db
    from invenio.modules.records.models import Record as Bibrec
    from invenio.modules.formatter.models import Bibfmt
    pid = server_pid(ping_the_process=False)
    if pid:
        print("ERROR: bibsched seems to run with pid {0}, according to {1}.".format(pid, pidfile), file=sys.stderr)
        print("       Please stop bibsched before running this procedure.", file=sys.stderr)
        sys.exit(1)
    if current_app.config.get('CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE'):
        print(">>> Searching records which need %s cache resetting; this may take a while..." % (output_format, ))
        all_recids = intbitset(db.session.query(Bibrec.id).all())
        #TODO: prevent doing all records?
        recids = all_recids
        print(">>> Generating %s cache..." % (output_format, ))
        tot = len(recids)
        count = 0
        it = iter(recids)
        while True:
            rec_group = tuple(islice(it, split_by))
            if not len(rec_group):
                break
            Bibfmt.query.filter(db.and_(
                Bibfmt.id_bibrec.in_(rec_group),
                Bibfmt.format == output_format)).delete(synchronize_session=False)
            db.session.commit()
            #TODO: Update the cache or wait for the first access
            map(get_record, rec_group)
            count += len(rec_group)
            print("    ... done records %s/%s" % (count, tot))
            if len(rec_group) < split_by or count >= tot:
                break

        print(">>> %s cache generated successfully." % (output_format, ))
    else:
        print(">>> Cleaning %s cache..." % (output_format, ))
        Bibfmt.query.filter(Bibfmt.format == output_format).delete(synchronize_session=False)
        db.session.commit()


@manager.command
@change_command_name
def reset_recjson(split_by=1000):
    """Reset record json structure cache lazily"""
    from invenio.modules.records.models import RecordMetadata
    RecordMetadata.query.delete()


@manager.command
@change_command_name
def reset_recstruct(split_by=1000):
    """Reset record structure cache."""
    from invenio.legacy.bibrecord.bibrecord_manager import reset
    reset(split_by)


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
