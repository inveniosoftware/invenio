# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Perform uploader operations."""

import argparse

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)


@manager.option('-f', '-filename', dest='blobs', nargs='+',
                type=argparse.FileType('r'))
def insert(blobs):
    """Upload new records."""
    from .api import run
    for blob in blobs:
        filename = getattr(blob, 'name', None)
        run('insert', blob.read(), master_format='marc',
            reader_info=dict(schema='xml'), filename=filename)


def main():
    """Execute manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
