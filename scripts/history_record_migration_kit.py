# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Populate new history record table from `hstRECORD`."""

from __future__ import print_function

from invenio.ext.script import Manager

manager = Manager(usage="Populate new history record table from `hstRECORD`")


@manager.option('-f', '--flush', dest='flush', default=1000)
def run(flush):
    """Create json representation for old records and store it."""
    from invenio.ext.sqlalchemy import db
    from invenio.modules.records.api import create_record
    from invenio.modules.records.models import Record, RecordHistory
    from invenio.legacy.bibedit.utils import \
        get_marcxml_of_revision, get_record_revisions

    for recid in db.session.query(Record.id).yield_per(flush):
        recid = recid[0]
        for dummy, revision in get_record_revisions(recid):
            marc_xml = get_marcxml_of_revision(recid, revision)
            record = create_record(marc_xml, 'marc', schema='xml')
            hst_record = RecordHistory(
                id=recid,
                revision=record['modification_date'],
                json=record.dumps(clean=True))
            try:
                db.session.add(hst_record)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(
                    'An error occurred while processing {0}:{1}, {2}'.format(
                        recid, revision, e))


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
