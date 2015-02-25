# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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
websubmit database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db

# Create your models here.

class SbmACTION(db.Model):
    """Represents a SbmACTION record."""
    __tablename__ = 'sbmACTION'
    lactname = db.Column(db.Text, nullable=True)
    sactname = db.Column(db.Char(3), nullable=False, server_default='',
                primary_key=True)
    dir = db.Column(db.Text, nullable=True)
    cd = db.Column(db.Date, nullable=True)
    md = db.Column(db.Date, nullable=True)
    actionbutton = db.Column(db.Text, nullable=True)
    statustext = db.Column(db.Text, nullable=True)

class SbmALLFUNCDESCR(db.Model):
    """Represents a SbmALLFUNCDESCR record."""
    __tablename__ = 'sbmALLFUNCDESCR'
    #FIX ME pk
    function = db.Column(db.String(40), nullable=False, server_default='',
                primary_key=True)
    description	= db.Column(db.TinyText, nullable=True)

class SbmAPPROVAL(db.Model):
    """Represents a SbmAPPROVAL record."""
    __tablename__ = 'sbmAPPROVAL'
    doctype = db.Column(db.String(10), nullable=False,
                server_default='')
    categ = db.Column(db.String(50), nullable=False,
                server_default='')
    rn = db.Column(db.String(50), nullable=False, server_default='',
                primary_key=True)
    status = db.Column(db.String(10), nullable=False,
                server_default='')
    dFirstReq = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    dLastReq = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    dAction = db.Column(db.DateTime, nullable=False,
        server_default='1900-01-01 00:00:00')
    access = db.Column(db.String(20), nullable=False,
                server_default='0')
    note = db.Column(db.Text, nullable=False)

class SbmCATEGORIES(db.Model):
    """Represents a SbmCATEGORIES record."""
    __tablename__ = 'sbmCATEGORIES'
    doctype = db.Column(db.String(10), nullable=False, server_default='',
                primary_key=True, index=True)
    sname = db.Column(db.String(75), nullable=False, server_default='',
                primary_key=True, index=True)
    lname = db.Column(db.String(75), nullable=False,
                server_default='')
    score = db.Column(db.TinyInteger(3, unsigned=True), nullable=False,
                server_default='0')

class SbmCHECKS(db.Model):
    """Represents a SbmCHECKS record."""
    __tablename__ = 'sbmCHECKS'
    chname = db.Column(db.String(15), nullable=False, server_default='',
                primary_key=True)
    chdesc = db.Column(db.Text, nullable=True)
    cd = db.Column(db.Date, nullable=True)
    md = db.Column(db.Date, nullable=True)
    chefi1 = db.Column(db.Text, nullable=True)
    chefi2 = db.Column(db.Text, nullable=True)

class SbmCOLLECTION(db.Model):
    """Represents a SbmCOLLECTION record."""
    __tablename__ = 'sbmCOLLECTION'
    id = db.Column(db.Integer(11), nullable=False,
                primary_key=True,
                autoincrement=True)
    name = db.Column(db.String(100), nullable=False,
                server_default='')

class SbmCOLLECTIONSbmCOLLECTION(db.Model):
    """Represents a SbmCOLLECTIONSbmCOLLECTION record."""
    __tablename__ = 'sbmCOLLECTION_sbmCOLLECTION'
    id_father = db.Column(db.Integer(11), db.ForeignKey(SbmCOLLECTION.id),
                nullable=False, server_default='0', primary_key=True)
    id_son = db.Column(db.Integer(11), db.ForeignKey(SbmCOLLECTION.id),
                nullable=False, server_default='0', primary_key=True)
    catalogue_order = db.Column(db.Integer(11), nullable=False,
                server_default='0')

class SbmDOCTYPE(db.Model):
    """Represents a SbmDOCTYPE record."""
    __tablename__ = 'sbmDOCTYPE'
    ldocname = db.Column(db.Text, nullable=True)
    sdocname = db.Column(db.String(10), nullable=True,
                primary_key=True)
    cd = db.Column(db.Date, nullable=True)
    md = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)


class SbmCOLLECTIONSbmDOCTYPE(db.Model):
    """Represents a SbmCOLLECTIONSbmDOCTYPE record."""
    __tablename__ = 'sbmCOLLECTION_sbmDOCTYPE'
    id_father = db.Column(db.Integer(11), db.ForeignKey(SbmCOLLECTION.id),
                nullable=False, server_default='0', primary_key=True)
    id_son = db.Column(db.Char(10), db.ForeignKey(SbmDOCTYPE.sdocname),
                nullable=False, server_default='0', primary_key=True)
    catalogue_order = db.Column(db.Integer(11), nullable=False,
                server_default='0')

class SbmCOOKIES(db.Model):
    """Represents a SbmCOOKIES record."""
    __tablename__ = 'sbmCOOKIES'
    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)
    uid = db.Column(db.Integer(15), nullable=False)

class SbmCPLXAPPROVAL(db.Model):
    """Represents a SbmCPLXAPPROVAL record."""
    __tablename__ = 'sbmCPLXAPPROVAL'
    doctype = db.Column(db.String(10), nullable=False,
                server_default='')
    categ = db.Column(db.String(50), nullable=False,
                server_default='')
    rn = db.Column(db.String(50), nullable=False, server_default='',
                primary_key=True)
    type = db.Column(db.String(10), nullable=False,
                primary_key=True)
    status = db.Column(db.String(10), nullable=False)
    id_group = db.Column(db.Integer(15, unsigned=True), nullable=False,
                server_default='0')
    id_bskBASKET = db.Column(db.Integer(15, unsigned=True), nullable=False,
                server_default='0')
    id_EdBoardGroup = db.Column(db.Integer(15, unsigned=True), nullable=False,
                server_default='0')
    dFirstReq = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dLastReq = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dEdBoardSel = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dRefereeSel = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dRefereeRecom = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dEdBoardRecom = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dPubComRecom = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dProjectLeaderAction = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')


class SbmFIELD(db.Model):
    """Represents a SbmFIELD record."""
    __tablename__ = 'sbmFIELD'
    subname = db.Column(db.String(13), nullable=True,
                primary_key=True)
    pagenb = db.Column(db.Integer(11), nullable=True,
                primary_key=True, autoincrement=False)
    fieldnb = db.Column(db.Integer(11), nullable=True)
    fidesc = db.Column(db.String(15), nullable=True,
                primary_key=True)
    fitext = db.Column(db.Text, nullable=True)
    level = db.Column(db.Char(1), nullable=True)
    sdesc = db.Column(db.Text, nullable=True)
    checkn = db.Column(db.Text, nullable=True)
    cd = db.Column(db.Date, nullable=True)
    md = db.Column(db.Date, nullable=True)
    fiefi1 = db.Column(db.Text, nullable=True)
    fiefi2 = db.Column(db.Text, nullable=True)


class SbmFIELDDESC(db.Model):
    """Represents a SbmFIELDDESC record."""
    __tablename__ = 'sbmFIELDDESC'
    name = db.Column(db.String(15), #db.ForeignKey(SbmFIELD.fidesc),
                nullable=False, server_default='', primary_key=True)
    alephcode = db.Column(db.String(50), nullable=True)
    marccode = db.Column(db.String(50), nullable=False, server_default='')
    type = db.Column(db.Char(1), nullable=True)
    size = db.Column(db.Integer(11), nullable=True)
    rows = db.Column(db.Integer(11), nullable=True)
    cols = db.Column(db.Integer(11), nullable=True)
    maxlength = db.Column(db.Integer(11), nullable=True)
    val = db.Column(db.Text, nullable=True)
    fidesc = db.Column(db.Text, nullable=True)
    cd = db.Column(db.Date, nullable=True)
    md = db.Column(db.Date, nullable=True)
    modifytext = db.Column(db.Text, nullable=True)
    fddfi2 = db.Column(db.Text, nullable=True)
    cookie = db.Column(db.Integer(11), nullable=True,
                server_default='0')
    #field = db.relationship(SbmFIELD, backref='fielddescs')


class SbmFORMATEXTENSION(db.Model):
    """Represents a SbmFORMATEXTENSION record."""
    __tablename__ = 'sbmFORMATEXTENSION'
    FILE_FORMAT = db.Column(db.Text(50), nullable=False,
                primary_key=True)
    FILE_EXTENSION = db.Column(db.Text(10), nullable=False,
                primary_key=True)


class SbmFUNCTIONS(db.Model):
    """Represents a SbmFUNCTIONS record."""
    __tablename__ = 'sbmFUNCTIONS'
    action = db.Column(db.String(10), nullable=False,
                server_default='', primary_key=True)
    doctype = db.Column(db.String(10), nullable=False,
                server_default='', primary_key=True)
    function = db.Column(db.String(40), nullable=False,
                server_default='', primary_key=True)
    score = db.Column(db.Integer(11), nullable=False,
                server_default='0', primary_key=True)
    step = db.Column(db.TinyInteger(4), nullable=False,
                server_default='1', primary_key=True)

class SbmFUNDESC(db.Model):
    """Represents a SbmFUNDESC record."""
    __tablename__ = 'sbmFUNDESC'
    function = db.Column(db.String(40), nullable=False,
                server_default='', primary_key=True)
    param = db.Column(db.String(40), primary_key=True)

class SbmGFILERESULT(db.Model):
    """Represents a SbmGFILERESULT record."""
    __tablename__ = 'sbmGFILERESULT'
    FORMAT = db.Column(db.Text(50), nullable=False,
                primary_key=True)
    RESULT = db.Column(db.Text(50), nullable=False,
                primary_key=True)

class SbmIMPLEMENT(db.Model):
    """Represents a SbmIMPLEMENT record."""
    __tablename__ = 'sbmIMPLEMENT'
    docname = db.Column(db.String(10), nullable=True)
    actname = db.Column(db.Char(3), nullable=True)
    displayed = db.Column(db.Char(1), nullable=True)
    subname = db.Column(db.String(13), nullable=True, primary_key=True)
    nbpg = db.Column(db.Integer(11), nullable=True, primary_key=True,
                autoincrement=False)
    cd = db.Column(db.Date, nullable=True)
    md = db.Column(db.Date, nullable=True)
    buttonorder = db.Column(db.Integer(11), nullable=True)
    statustext = db.Column(db.Text, nullable=True)
    level = db.Column(db.Char(1), nullable=False, server_default='')
    score = db.Column(db.Integer(11), nullable=False, server_default='0')
    stpage = db.Column(db.Integer(11), nullable=False, server_default='0')
    endtxt = db.Column(db.String(100), nullable=False, server_default='')

class SbmPARAMETERS(db.Model):
    """Represents a SbmPARAMETERS record."""
    __tablename__ = 'sbmPARAMETERS'
    doctype = db.Column(db.String(10), nullable=False,
                server_default='', primary_key=True)
    name = db.Column(db.String(40), nullable=False,
                server_default='', primary_key=True)
    value = db.Column(db.Text, nullable=False)

class SbmPUBLICATION(db.Model):
    """Represents a SbmPUBLICATION record."""
    __tablename__ = 'sbmPUBLICATION'
    doctype = db.Column(db.String(10), nullable=False,
                server_default='', primary_key=True)
    categ = db.Column(db.String(50), nullable=False,
                server_default='', primary_key=True)
    rn = db.Column(db.String(50), nullable=False, server_default='',
                primary_key=True)
    status = db.Column(db.String(10), nullable=False, server_default='')
    dFirstReq = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dLastReq = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dAction = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    accessref = db.Column(db.String(20), nullable=False, server_default='')
    accessedi = db.Column(db.String(20), nullable=False, server_default='')
    access = db.Column(db.String(20), nullable=False, server_default='')
    referees = db.Column(db.String(50), nullable=False, server_default='')
    authoremail = db.Column(db.String(50), nullable=False,
                server_default='')
    dRefSelection = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dRefRec = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    dEdiRec = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    accessspo = db.Column(db.String(20), nullable=False, server_default='')
    journal = db.Column(db.String(100), nullable=True)


class SbmPUBLICATIONCOMM(db.Model):
    """Represents a SbmPUBLICATIONCOMM record."""
    __tablename__ = 'sbmPUBLICATIONCOMM'
    id = db.Column(db.Integer(11), nullable=False,
                primary_key=True, autoincrement=True)
    id_parent = db.Column(db.Integer(11), server_default='0', nullable=True)
    rn = db.Column(db.String(100), nullable=False, server_default='')
    firstname = db.Column(db.String(100), nullable=True)
    secondname = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String(40), nullable=False, server_default='')
    synopsis = db.Column(db.String(255), nullable=False, server_default='')
    commentfulltext = db.Column(db.Text, nullable=True)


class SbmPUBLICATIONDATA(db.Model):
    """Represents a SbmPUBLICATIONDATA record."""
    __tablename__ = 'sbmPUBLICATIONDATA'
    doctype = db.Column(db.String(10), nullable=False,
                server_default='', primary_key=True)
    editoboard = db.Column(db.String(250), nullable=False, server_default='')
    base = db.Column(db.String(10), nullable=False, server_default='')
    logicalbase = db.Column(db.String(10), nullable=False, server_default='')
    spokesperson = db.Column(db.String(50), nullable=False, server_default='')

class SbmREFEREES(db.Model):
    """Represents a SbmREFEREES record."""
    __tablename__ = 'sbmREFEREES'
    doctype = db.Column(db.String(10), nullable=False, server_default='')
    categ = db.Column(db.String(10), nullable=False, server_default='')
    name = db.Column(db.String(50), nullable=False, server_default='')
    address = db.Column(db.String(50), nullable=False, server_default='')
    rid = db.Column(db.Integer(11), nullable=False, primary_key=True,
                autoincrement=True)

class SbmSUBMISSIONS(db.Model):
    """Represents a SbmSUBMISSIONS record."""
    __tablename__ = 'sbmSUBMISSIONS'
    email = db.Column(db.String(50), nullable=False,
                server_default='')
    doctype = db.Column(db.String(10), nullable=False,
                server_default='')
    action = db.Column(db.String(10), nullable=False,
                server_default='')
    status = db.Column(db.String(10), nullable=False,
                server_default='')
    id = db.Column(db.String(30), nullable=False,
                server_default='')
    reference = db.Column(db.String(40), nullable=False,
                server_default='')
    cd = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    md = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    log_id = db.Column(db.Integer(11), nullable=False,
                primary_key=True,
                autoincrement=True)


__all__ = ['SbmACTION',
           'SbmALLFUNCDESCR',
           'SbmAPPROVAL',
           'SbmCATEGORIES',
           'SbmCHECKS',
           'SbmCOLLECTION',
           'SbmCOLLECTIONSbmCOLLECTION',
           'SbmDOCTYPE',
           'SbmCOLLECTIONSbmDOCTYPE',
           'SbmCOOKIES',
           'SbmCPLXAPPROVAL',
           'SbmFIELD',
           'SbmFIELDDESC',
           'SbmFORMATEXTENSION',
           'SbmFUNCTIONS',
           'SbmFUNDESC',
           'SbmGFILERESULT',
           'SbmIMPLEMENT',
           'SbmPARAMETERS',
           'SbmPUBLICATION',
           'SbmPUBLICATIONCOMM',
           'SbmPUBLICATIONDATA',
           'SbmREFEREES',
           'SbmSUBMISSIONS']
