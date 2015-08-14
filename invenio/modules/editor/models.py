# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Editor database models."""

from invenio.ext.sqlalchemy import db

from invenio_records.models import Record as Bibrec


class HstRECORD(db.Model):

    """Represent a HstRECORD record."""

    __tablename__ = 'hstRECORD'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   nullable=False, autoincrement=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), autoincrement=False,
                          nullable=False, primary_key=True)
    marcxml = db.Column(db.iBinary, nullable=False)
    job_id = db.Column(db.MediumInteger(15, unsigned=True),
                       nullable=False, index=True)
    job_name = db.Column(db.String(255), nullable=False, index=True)
    job_person = db.Column(db.String(255), nullable=False, index=True)
    job_date = db.Column(db.DateTime, nullable=False, index=True)
    job_details = db.Column(db.iBinary, nullable=False)
    affected_fields = db.Column(db.Text, nullable=True)


__all__ = ('HstRECORD',)
