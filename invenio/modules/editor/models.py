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

from __future__ import print_function

import os
import shutil

from invenio.ext.sqlalchemy import db
from invenio.modules.records.models import Record as Bibrec

from sqlalchemy import event


class BibHOLDINGPEN(db.Model):

    """Represent a BibHOLDINGPEN record."""

    __tablename__ = 'bibHOLDINGPEN'
    changeset_id = db.Column(db.Integer(11), primary_key=True,
                             autoincrement=True)
    changeset_date = db.Column(db.DateTime, nullable=False,
                               server_default='1900-01-01 00:00:00',
                               index=True)
    changeset_xml = db.Column(db.Text, nullable=False)
    oai_id = db.Column(db.String(40), nullable=False,
                       server_default='')
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=False,
                          server_default='0')
    bibrec = db.relationship(Bibrec, backref='holdingpen')


class Bibdoc(db.Model):

    """Represent a Bibdoc record."""

    __tablename__ = 'bibdoc'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                   nullable=False, autoincrement=True)
    status = db.Column(db.Text, nullable=False)
    docname = db.Column(db.String(250), nullable=True,  # collation='utf8_bin'
                        index=True)
    creation_date = db.Column(db.DateTime, nullable=False,
                              server_default='1900-01-01 00:00:00', index=True)
    modification_date = db.Column(db.DateTime, nullable=False,
                                  server_default='1900-01-01 00:00:00',
                                  index=True)
    text_extraction_date = db.Column(db.DateTime, nullable=False,
                                     server_default='1900-01-01 00:00:00')
    doctype = db.Column(db.String(255))


class BibdocBibdoc(db.Model):

    """Represent a BibdocBibdoc record."""

    __tablename__ = 'bibdoc_bibdoc'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                   nullable=False, autoincrement=True)
    id_bibdoc1 = db.Column(db.MediumInteger(9, unsigned=True),
                           db.ForeignKey(Bibdoc.id), nullable=True)
    version1 = db.Column(db.TinyInteger(4, unsigned=True))
    format1 = db.Column(db.String(50))
    id_bibdoc2 = db.Column(db.MediumInteger(9, unsigned=True),
                           db.ForeignKey(Bibdoc.id), nullable=True)
    version2 = db.Column(db.TinyInteger(4, unsigned=True))
    format2 = db.Column(db.String(50))
    rel_type = db.Column(db.String(255), nullable=True)
    bibdoc1 = db.relationship(Bibdoc, backref='bibdoc2s',
                              primaryjoin=Bibdoc.id == id_bibdoc1)
    bibdoc2 = db.relationship(Bibdoc, backref='bibdoc1s',
                              primaryjoin=Bibdoc.id == id_bibdoc2)


class BibrecBibdoc(db.Model):

    """Represent a BibrecBibdoc record."""

    __tablename__ = 'bibrec_bibdoc'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), nullable=False,
                          server_default='0', primary_key=True)
    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                          db.ForeignKey(Bibdoc.id), nullable=False,
                          server_default='0', primary_key=True)
    docname = db.Column(db.String(250), nullable=False,  # collation='utf8_bin'
                        server_default='file', index=True)
    type = db.Column(db.String(255), nullable=True)
    bibrec = db.relationship(Bibrec, backref='bibdocs')
    bibdoc = db.relationship(Bibdoc, backref='bibrecs')


class HstDOCUMENT(db.Model):

    """Represent a HstDOCUMENT record."""

    __tablename__ = 'hstDOCUMENT'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   nullable=False, autoincrement=True)
    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                          db.ForeignKey(Bibdoc.id), primary_key=True,
                          nullable=False, autoincrement=False)
    docname = db.Column(db.String(250), nullable=False, index=True)
    docformat = db.Column(db.String(50), nullable=False, index=True)
    docversion = db.Column(db.TinyInteger(4, unsigned=True),
                           nullable=False)
    docsize = db.Column(db.BigInteger(15, unsigned=True),
                        nullable=False)
    docchecksum = db.Column(db.Char(32), nullable=False)
    doctimestamp = db.Column(db.DateTime, nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    job_id = db.Column(db.MediumInteger(15, unsigned=True),
                       nullable=True, index=True)
    job_name = db.Column(db.String(255), nullable=True, index=True)
    job_person = db.Column(db.String(255), nullable=True, index=True)
    job_date = db.Column(db.DateTime, nullable=True, index=True)
    job_details = db.Column(db.iBinary, nullable=True)


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


class BibEDITCACHE(db.Model):

    """Represent a BibEDITCACHE record."""

    __tablename__ = 'bibEDITCACHE'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Bibrec.id), autoincrement=False,
                          nullable=False, primary_key=True)
    uid = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                    nullable=False, autoincrement=False)
    data = db.Column(db.iBinary, nullable=False)
    post_date = db.Column(db.DateTime, nullable=False, index=True)
    is_active = db.Column(db.TinyInteger(1, unsigned=True),
                          server_default='1', nullable=False)


def bibdoc_before_drop(target, connection_dummy, **kw_dummy):
    from invenio.legacy.bibdocfile.api import _make_base_dir

    print(">>> Going to remove records data...")
    for (docid,) in db.session.query(target.c.id).all():
        directory = _make_base_dir(docid)
        if os.path.isdir(directory):
            print('    >>> Removing files for docid = {0}'.format(docid))
            shutil.rmtree(directory)
    db.session.commit()
    print(">>> Data has been removed.")

event.listen(Bibdoc.__table__, "before_drop", bibdoc_before_drop)

__all__ = ('Bibrec',
           'BibEDITCACHE',
           'BibHOLDINGPEN',
           'Bibdoc',
           'BibdocBibdoc',
           'BibrecBibdoc',
           'HstDOCUMENT',
           'HstRECORD',
           )
