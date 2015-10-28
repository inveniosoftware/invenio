# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2015 CERN.
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

""" Bibcheck plugin to add texkeys """

from invenio.bibrecord import record_add_field
from invenio.sequtils_texkey import (TexkeyNoAuthorError, TexkeyNoYearError,
                                     TexkeySeq)


def check_record(record, texkey_field="035__a",
                 provenances=None, extra_subfields=None):
    """
    Add a texkey to a record, checking that it doesn't have one already.
    """

    if provenances is None:
        provenances = ["SPIRESTeX", "INSPIRETeX"]

    for provenance in provenances:
        for _, val in record.iterfield(texkey_field,
                                       subfield_filter=('9', provenance)):
            if len(val) > 6:  # texkey composition <name>:\d{4}<randchars>
                return

    try:
        texkey = TexkeySeq().next_value(bibrecord=record)
    except TexkeyNoAuthorError:
        record.warn("No first author or collaboration")
        return
    except TexkeyNoYearError:
        record.warn("No suitable year/date info")
        return

    if extra_subfields is None:
        extra_subfields = [('9', 'INSPIRETeX')]

    tag = texkey_field[:3]
    ind1, ind2, subfield = texkey_field[3:]
    subfields_to_add = [(subfield, texkey)] + map(tuple, extra_subfields)
    record_add_field(record, tag=tag, ind1=ind1, ind2=ind2,
                     subfields=subfields_to_add)
    record.set_amended("Added Tex key '%s' to field %s"
                       % (texkey, texkey_field))
