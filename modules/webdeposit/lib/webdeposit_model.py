# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
WebDeposit database models.
"""

# General imports.
from invenio.sqlalchemyutils import db
from invenio.bibworkflow_model import Workflow

# Create your models here.


class WebDepositDraft(db.Model):
    """Represents a deposition draft."""
    __tablename__ = 'depDRAFT'
    uuid = db.Column(db.String(36), db.ForeignKey(Workflow.uuid),
                     primary_key=True)
    step = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                     autoincrement=False)
    form_type = db.Column(db.String(45), nullable=False)
    form_values = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Integer(15, unsigned=True), autoincrement=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    workflow = db.relationship(Workflow, backref='drafts')


__all__ = ['WebDepositDraft']
