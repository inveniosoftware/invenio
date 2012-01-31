# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
from invenio.sqlalchemyutils import db

# Create your models here.

#from websearch_model import Collection
from bibedit_model import Bibrec
from bibsched_model import SchTASK

class OaiHARVEST(db.Model):
    """Represents a OaiHARVEST record."""
    def __init__(self):
        pass
    __tablename__ = 'oaiHARVEST'
    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    baseurl = db.Column(db.String(255), nullable=False,
                server_default='')
    metadataprefix = db.Column(db.String(255), nullable=False,
                server_default='oai_dc')
    arguments = db.Column(db.Text, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    bibconvertcfgfile = db.Column(db.String(255),
                nullable=True)
    name = db.Column(db.String(255), nullable=False)
    lastrun = db.Column(db.DateTime, nullable=True)
    frequency = db.Column(db.MediumInteger(12), nullable=False,
                server_default='0')
    postprocess = db.Column(db.String(20), nullable=False,
                server_default='h')
    bibfilterprogram = db.Column(db.String(255), nullable=False,
                server_default='')
    setspecs = db.Column(db.Text, nullable=False)


class OaiREPOSITORY(db.Model):
    """Represents a OaiREPOSITORY record."""
    def __init__(self):
        pass
    __tablename__ = 'oaiREPOSITORY'
    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                primary_key=True,
                autoincrement=True)
    setName = db.Column(db.String(255), nullable=False,
                server_default='')
    setSpec = db.Column(db.String(255), nullable=False,
                server_default='')
    setCollection = db.Column(db.String(255), nullable=False,
                server_default='')
    setDescription = db.Column(db.Text, nullable=False)
    setDefinition = db.Column(db.Text, nullable=False)
    setRecList = db.Column(db.iLargeBinary, nullable=True)
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
    def __init__(self):
        pass
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
                server_default='0001-01-01 00:00:00',
                primary_key=True)
    date_inserted = db.Column(db.DateTime, nullable=False,
        server_default='0001-01-01 00:00:00')
    inserted_to_db = db.Column(db.Char(1), nullable=False,
                server_default='P')
    bibrec = db.relationship(Bibrec, backref='harvestlogs')
    schtask = db.relationship(SchTASK)



__all__ = ['OaiHARVEST',
           'OaiREPOSITORY',
           'OaiHARVESTLOG']
