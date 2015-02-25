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

"""
Returns template subject and content for:
a sample ticket
"""

from invenio.bibrecord import record_get_field_value


def get_template_data(record):
    """
    Returns template subject and content for:
    a sample ticket

    record is a recstruct
    """

    recid = record_get_field_value(record, tag="001")
    queue = "Test"
    subject = "Test ticket"
    content = "This is a test ticket for record %s." % recid

    return (queue, subject, content)
