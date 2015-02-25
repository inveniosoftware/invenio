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


def get_modification_date(recid):
    """
    Returns creation date for given record.

    @param recid:

    @return: Creation date
    """
    # WARNING: HACK/FIXME
    #
    # When bibupload inserts/updates records it sets hstRECORD.job_date=t1 and
    # bibfmt.last_updated=t1 and bibrec.modification_date=t2 (with t2 > t1).
    # This is intended behaviour in master (see ticket #1431).
    #
    # Revision verifier checks 005 on upload against hstRECORD.job_date
    # (i.e. t1).
    #
    # JSONAlchemy was getting modification_date/005 from
    # bibrec.modification_date (i.e. t2).
    #
    # Thus if you did a get_record, and tried to reupload the file, the XML
    # woudl have t2 in 005, which revision verifier would reject since it
    # compares against t1.
    #
    # Modification date ought to be taken from bibrec.modification_date and all
    # three timestamps ought to be the same. Thus below is a hack, that ought
    # to be fixed in bibupload instead. Unfortunately so much other code is
    # might rely on the current behaviour that it's hard to change.
    from invenio.modules.formatter.models import Bibfmt
    from invenio.modules.records.models import Record as Bibrec

    try:
        return Bibfmt.query.filter_by(
            id_bibrec=recid, format='xm'
        ).first().last_updated
    except AttributeError:
        try:
            return Bibrec.query.get(recid).modification_date
        except AttributeError:
            return None
