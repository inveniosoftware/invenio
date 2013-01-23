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

from invenio.sqlalchemyutils import db


class WebDepositDraft(db.Model):
    """Represents a deposition draft."""
    __tablename__ = 'deposition_drafts'
    uuid = db.Column(db.String(36),
                     nullable=False,
                     primary_key=True)
    ## FIXME change database column name
    dep_type = db.Column(db.String(45),
                     nullable=False)
    step = db.Column(db.Integer(15,
                     unsigned=True),
                     nullable=False,
                     primary_key=True)
    user_id = db.Column(db.Integer(15,
                        unsigned=True),
                        nullable=False)
    form_type = db.Column(db.String(45),
                          nullable=False)
    form_values = db.Column(db.String(2048),
                            nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class WebDepositWorkflow(db.Model):
    """Represents a deposition workflow."""
    __tablename__ = 'deposition_workflows'
    uuid = db.Column(db.String(36),
                     primary_key=True,
                     unique=True,
                     nullable=False)
    dep_type = db.Column(db.String(45),
                         nullable=False)
    obj_json = db.Column(db.String(2048),
                         nullable=False)
    current_step = db.Column(db.Integer(15,
                             unsigned=True),
                             nullable=False)
    status = db.Column(db.Integer(10, unsigned=True),
                       nullable=False)

__all__ = ['WebDepositDraft', 'WebDepositWorkflow']
