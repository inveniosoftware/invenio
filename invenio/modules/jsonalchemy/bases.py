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

r"""General extensions for JSON objects.

JSONAlchemy allows the developer to extend the behavior or capabilities of the
JSON objects using `extensions`. For more information about how extensions
works check :class:`invenio.modules.jsonalchemy.jsonext.parsers.\
extension_model_parser.ExtensionModelParser`.
"""


class Versionable(object):

    """Versionable behavior for JSONAlchemy models."""

    def update(self):
        """Create new revision of the object and saves link to the old one."""
        #  We need a copy not to modify references to the old object!
        cls = self.__class__
        data = self.dumps()
        self = cls(data)
        self['older_version'] = self['_id']
        self['_id'] = str(__import__('uuid').uuid4())
        # self.set_default_value('_id')  # pylint: disable=E1101
        return super(Versionable, self).update()
