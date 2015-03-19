# -*- coding: utf8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""
Flask-Collect custom storage for development mode.

It creates symbolic links to the real files so any changes to them will be
reflected.
"""

import os
from flask_collect.storage.base import BaseStorage


class Storage(BaseStorage):

    """Storage that creates symlinks to the resources."""

    def run(self):
        """Collect static from blueprints.

        Create the directory tree but will symlink all the files.
        """
        self.log("Collect static from blueprints")
        skipped, total = 0, 0
        for bp, f, o in self:
            destination = os.path.join(self.collect.static_root, o)
            destination_dir = os.path.dirname(destination)
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)

            if not os.path.exists(destination):
                # the path is a link, but points to invalid location
                if os.path.islink(destination):
                    os.remove(destination)
                os.symlink(f, destination)
                self.log("{0}:{1} symbolink link created".format(bp.name, o))
            else:
                skipped += 1
            total += 1
        self.log("{0} of {1} files already present".format(skipped, total))
        self.log("Done collecting.")
