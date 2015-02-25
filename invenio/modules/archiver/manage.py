# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Perform record archiving operations."""

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)

option_recid = manager.option("recid", metavar='RECID', type=int,
                              help="Record identifier")
option_version = manager.option("--version", dest="version", type=int,
                                default=-1, help="Version or archived record.")


@option_recid
def create(recid):
    """Create an archive of record."""
    from .api import create_archive_package
    create_archive_package(recid)


@option_recid
@option_version
def mount(recid, version=-1):
    """Discover content of the record archive."""
    from .api import mount_archive_package
    return mount_archive_package(recid, version=version).tree()


@option_recid
@option_version
def delete(recid, version=-1, delete_all=False):
    """Delete archive(s) of the record(s)."""
    from .api import delete_archive_package
    if delete_all and version != -1:
        raise Exception("Invalid arguments combination --all and --version.")
    elif delete_all:
        # Delete *ALL* versions.
        version = None
    return delete_archive_package(recid, version=version).tree()


@manager.option("--dry-run", dest="dry_run", action="store_true",
                default=False)
def update(dry_run=False):
    """Check if all records have an archive from their latest version."""
    from invenio.ext.sqlalchemy import db
    from invenio.modules.records.models import Record
    from .api import get_archive_package, create_archive_package
    from .errors import ArchiverError
    records = db.select([Record.id, Record.modification_date])

    for (recid, modification_date) in db.session.execute(records):
        try:
            archive = get_archive_package(recid, version=-1)
        except ArchiverError:
            archive = None
        if archive is None or archive['creation_date'] < modification_date:
            if dry_run:
                print("Record {0} needs to be archived.".format(recid))
            else:
                create_archive_package(recid)

# FIXME implement purge command


def main():
    """Execute manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
