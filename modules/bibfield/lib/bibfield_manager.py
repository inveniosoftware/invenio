# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from flask.ext.script import Manager

manager = Manager(usage="Perform BibField operations")

bibfield_config = Manager(usage="Manipulates BibField config.")
manager.add_command("config", bibfield_config)


@bibfield_config.command
def load():
    """Loads BibField config."""

    print ">>> Going to load BibField config..."
    from invenio.bibfield_config_engine import BibFieldParser
    BibFieldParser().write_to_file()
    print ">>> BibField config load successfully."


@manager.command
def reset(split_by=1000):
    """It either stores or does not store the recjson format.

    If CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE is changed, this function
    will adapt the database to either store or not store the recjson
    format."""
    split_by = int(split_by)
    import sys
    try:
        import cPickle as pickle
    except:
        import pickle
    from itertools import islice
    from invenio.config import CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE
    from invenio.intbitset import intbitset
    from invenio.bibfield import get_record
    from invenio.bibsched import server_pid, pidfile
    from invenio.sqlalchemyutils import db
    from invenio.bibedit_model import Bibrec, Bibfmt
    pid = server_pid(ping_the_process=False)
    if pid:
        print >> sys.stderr, "ERROR: bibsched seems to run with pid %d, according to %s." % (pid, pidfile)
        print >> sys.stderr, "       Please stop bibsched before running this procedure."
        sys.exit(1)
    if CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE:
        print ">>> Searching records which need recjson cache resetting; this may take a while..."
        all_recids = intbitset(db.session.query(Bibrec.id).all())
        #TODO: prevent doing all records?
        recids = all_recids
        print ">>> Generating recjson cache..."
        tot = len(recids)
        count = 0
        it = iter(recids)
        while True:
            rec_group = tuple(islice(it, split_by))
            Bibfmt.query.filter(db.and_(
                Bibfmt.id_bibrec.in_(rec_group),
                Bibfmt.format == 'recjson')).delete(synchronize_session=False)
            db.session.commit()
            #TODO: Update the cache or wait for the first access
            map(get_record, rec_group)
            count += len(rec_group)
            print "    ... done records %s/%s" % (count, tot)
            if len(rec_group) < split_by or count >= tot:
                break

        print ">>> recjson cache generated successfully."


def main():
    from invenio.webinterface_handler_flask import create_invenio_flask_app
    app = create_invenio_flask_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
