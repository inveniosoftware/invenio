## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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


class HoldingPenContainer():
    """
    Class containing three HPItems of a single record plus metadata for
    the record
    """
    def __init__(self, initial, error=None, final=None, owner="",
                 description="", ISBN=0, invenio_id=0,
                 publisher="", category="", version=0):
        self.id = initial.id
        self.initial = initial
        self.error = error
        self.final = final
        if self.final:
            self.current = self.final
        elif self.error:
            self.current = self.error
        self.owner = owner
        self.description = description
        self.ISBN = ISBN
        self.invenio_id = invenio_id
        self.publisher = publisher
        self.category = category
        self.version = version
        try:
            self.widget = self.current.extra_data['widget']
        except:
            self.widget = None
