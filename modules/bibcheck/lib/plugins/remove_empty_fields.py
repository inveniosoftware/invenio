#!/usr/bin/env python

##
## This file is part of Invenio.
## Copyright (C) 2014, 2016 CERN.
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

from invenio.bibcheck_task import AmendableRecord

def check_record(record):
    """ Bibcheck plugin to remove empty fields from records """
    remove_empty_subfields(record)
    remove_empty_tags(record)


def remove_empty_subfields(record):
    """ removes subfields with no value """
    for position, value in record.iterfield('%%%%%%'):
        if not value:
            message = 'remove empty subfield: ' + position[0]
            record.delete_field(position, message)
            remove_empty_subfields(record)
            break


def remove_empty_tags(record):
    """ removes tags with no subfields and no value """
    for tag in record.keys():
        for (local_position, field_obj) in enumerate(record[tag]):
            if not field_obj[0] and not field_obj[3]:
                record[tag].pop(local_position)
                record.set_amended('removed empty tag: ' + tag)
