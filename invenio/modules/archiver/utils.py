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

"""Archiver utility functions."""

from __future__ import absolute_import

import os
import six

from datetime import datetime
from werkzeug.utils import cached_property, import_string

from invenio.base.globals import cfg


def default_name_generator(document):
    """Return default name of archive with storage path."""
    return os.path.join(
        cfg["CFG_TMPSHAREDDIR"],
        "bagits",
        "{0}_{1}.zip".format(
            document['recid'],
            datetime.now().strftime("%Y-%m-%d_%H:%M:%S:%f")
        )
    )


class NameGenerator(object):

    """Archive name generator."""

    @cached_property
    def generator(self):
        """Load function from configuration ``ARCHIVER_NAME_GENERATOR``."""
        func = cfg.get('ARCHIVER_NAME_GENERATOR', default_name_generator)
        if isinstance(func, six.string_types):
            func = import_string(func)
        return func

    def __call__(self, *args, **kwargs):
        """Execute name generator function."""
        return self.generator(*args, **kwargs)

name_generator = NameGenerator()

__all__ = ('default_name_generator', 'name_generator')
