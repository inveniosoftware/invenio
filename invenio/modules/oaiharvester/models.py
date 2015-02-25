# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

"""OAI harvest database models."""

from sqlalchemy import event

from invenio.ext.sqlalchemy import db
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.modules.records.models import Record as Bibrec
from invenio.modules.scheduler.models import SchTASK


def get_default_arguments():
    """Return default values for arguments."""
    arguments_default = {'c_stylesheet': '',
                         'r_kb-rep-no-file': '',
                         'r_format': '',
                         'u_name': '',
                         'a_rt-queue': '',
                         'r_kb-journal-file': '',
                         'u_priority': '',
                         'a_stylesheet': '',
                         't_doctype': '',
                         'f_filter-file': '',
                         'p_extraction-source': []}
    return arguments_default


class OaiHARVEST(db.Model):

    """Represents a OaiHARVEST record."""

    __tablename__ = 'oaiHARVEST'

    id = db.Column(db.MediumInteger(9, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    baseurl = db.Column(db.String(255), nullable=False, server_default='')
    metadataprefix = db.Column(db.String(255), nullable=False,
                               server_default='oai_dc')
    arguments = db.Column(db.MarshalBinary(default_value=get_default_arguments(),
                                           force_type=dict), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    lastrun = db.Column(db.DateTime, nullable=True)
    postprocess = db.Column(db.String(20), nullable=False,
                            server_default='h')
    workflows = db.Column(db.String(255),
                          nullable=False,
                          server_default='')
    setspecs = db.Column(db.Text, nullable=False)

    def to_dict(self):
        """Get model as dict."""
        dict_representation = self.__dict__
        del dict_representation["_sa_instance_state"]
        return dict_representation

    @classmethod
    def get(cls, *criteria, **filters):
        """Wrapper for filter and filter_by functions of SQLAlchemy.

        .. code-block:: python

            OaiHARVEST.get(OaiHARVEST.id == 1)
            OaiHARVEST.get(id=1)
        """
        return cls.query.filter(*criteria).filter_by(**filters)

    @session_manager
    def save(self):
        """Save object to persistent storage."""
        db.session.add(self)


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
    p1 = db.Column(db.Text, nullable=False, default='')
    f1 = db.Column(db.Text, nullable=False, default='')
    m1 = db.Column(db.Text, nullable=False, default='')
    p2 = db.Column(db.Text, nullable=False, default='')
    f2 = db.Column(db.Text, nullable=False, default='')
    m2 = db.Column(db.Text, nullable=False, default='')
    p3 = db.Column(db.Text, nullable=False, default='')
    f3 = db.Column(db.Text, nullable=False, default='')
    m3 = db.Column(db.Text, nullable=False, default='')

    @classmethod
    def update_setdefinition_listener(cls, mapper, connection, target):
        """Update setDefinition attribute on before_insert/before_update events."""
        # FIXME: Next two lines
        op1 = ''
        op2 = ''

        # Set fields to empty string if none.
        for attr in ['p1', 'f1', 'm1', 'p2', 'f2', 'm2', 'p3', 'f3', 'm3',
                     'setCollection', 'setName', 'setSpec', 'setDescription']:
            if getattr(target, attr) is None:
                setattr(target, attr, '')

        target.setDefinition = \
            'c=' + target.setCollection + ';' + \
            'p1=' + target.p1 + ';' + \
            'f1=' + target.f1 + ';' + \
            'm1=' + target.m1 + ';' + \
            'op1=' + op1 + ';' + \
            'p2=' + target.p2 + ';' + \
            'f2=' + target.f2 + ';' + \
            'm2=' + target.m2 + ';' + \
            'op2=' + op2 + ';' + \
            'p3=' + target.p3 + ';' + \
            'f3=' + target.f3 + ';' + \
            'm3=' + target.m3 + ';'

# Connect Alchemy event listeners to update setDefinition on INSERT and UPDATE
event.listen(
    OaiREPOSITORY, 'before_insert', OaiREPOSITORY.update_setdefinition_listener
)
event.listen(
    OaiREPOSITORY, 'before_update', OaiREPOSITORY.update_setdefinition_listener
)


class OaiHARVESTLOG(db.Model):

    """Represents a OaiHARVESTLOG record."""

    __tablename__ = 'oaiHARVESTLOG'
    id_oaiHARVEST = db.Column(
        db.MediumInteger(9, unsigned=True),
        db.ForeignKey(OaiHARVEST.id), nullable=False
    )
    id_bibrec = db.Column(
        db.MediumInteger(8, unsigned=True),
        db.ForeignKey(Bibrec.id), nullable=False, server_default='0'
    )
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


__all__ = ('OaiHARVEST',
           'OaiREPOSITORY',
           'OaiHARVESTLOG')
