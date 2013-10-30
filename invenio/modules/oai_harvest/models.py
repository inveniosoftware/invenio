# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""
Oai harvest database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

#from websearch_model import Collection
from invenio.modules.record_editor.models import Bibrec
from invenio.modules.scheduler.models import SchTASK


class OaiHARVEST(db.Model):
    """Represents a OaiHARVEST record."""

    __tablename__ = 'oaiHARVEST'

    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    baseurl = db.Column(db.String(255), nullable=False, server_default='')
    metadataprefix = db.Column(db.String(255), nullable=False,
                               server_default='oai_dc')
    arguments = db.Column(db.LargeBinary, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    lastrun = db.Column(db.DateTime, nullable=True)
    frequency = db.Column(db.MediumInteger(12), nullable=False,
                          server_default='0')
    postprocess = db.Column(db.String(20), nullable=False,
                            server_default='h')
    setspecs = db.Column(db.Text, nullable=False)

    @classmethod
    def get(cls, *criteria, **filters):
        """ A wrapper for the filter and filter_by functions of sqlalchemy.
        Define a dict with which columns should be filtered by which values.

        look up also sqalchemy BaseQuery's filter and filter_by documentation
        """
        return cls.query.filter(*criteria).filter_by(**filters)


class OaiREPOSITORY(db.Model):
    """Represents a OaiREPOSITORY record."""
    __tablename__ = 'oaiREPOSITORY'
    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    setName = db.Column(db.String(255), nullable=False,
                        server_default='')
    setSpec = db.Column(db.String(255), nullable=False,
                        server_default='')
    setCollection = db.Column(db.String(255), nullable=False,
                              server_default='')
    setDescription = db.Column(db.Text, nullable=False)
    setDefinition = db.Column(db.Text, nullable=False)
    setRecList = db.Column(db.iLargeBinary, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False,
                             server_default='1970-01-01 00:00:00')
    p1 = db.Column(db.Text, nullable=False)
    f1 = db.Column(db.Text, nullable=False)
    m1 = db.Column(db.Text, nullable=False)
    p2 = db.Column(db.Text, nullable=False)
    f2 = db.Column(db.Text, nullable=False)
    m2 = db.Column(db.Text, nullable=False)
    p3 = db.Column(db.Text, nullable=False)
    f3 = db.Column(db.Text, nullable=False)
    m3 = db.Column(db.Text, nullable=False)


class OaiHARVESTLOG(db.Model):
    """Represents a OaiHARVESTLOG record."""
    __tablename__ = 'oaiHARVESTLOG'
    id_oaiHARVEST = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(OaiHARVEST.id), nullable=False)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), nullable=False, server_default='0')
    bibupload_task_id = db.Column(db.Integer(11), db.ForeignKey(SchTASK.id),
                                  nullable=False, server_default='0',
                                  primary_key=True)
    oai_id = db.Column(db.String(40), nullable=False, server_default='',
                       primary_key=True)
    date_harvested = db.Column(db.DateTime, nullable=False,
                               server_default='1900-01-01 00:00:00',
                               primary_key=True)
    date_inserted = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00')
    inserted_to_db = db.Column(db.Char(1), nullable=False,
                               server_default='P')
    bibrec = db.relationship(Bibrec, backref='harvestlogs')
    schtask = db.relationship(SchTASK)


__all__ = ['OaiHARVEST',
           'OaiREPOSITORY',
           'OaiHARVESTLOG']
