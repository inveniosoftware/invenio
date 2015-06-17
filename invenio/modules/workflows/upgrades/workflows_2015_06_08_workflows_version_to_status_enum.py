# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

import warnings

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op
from invenio.utils.text import wait_for_user

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as BaseSession, relationship

from invenio.modules.workflows.models import (
    CallbackPosType,
    ChoiceType,
    ObjectStatus,
    WorkflowStatus,
    _encoded_default_extra_data,
    _encoded_default_data,
    _decode,
)

Session = sessionmaker()
Base = declarative_base()


# Important: Below is only a best guess. You MUST validate which previous
# upgrade you depend on.
depends_on = [u'workflows_2014_08_12_initial']


class Workflow(Base):

    """Handle for the actual Workflow model."""

    __tablename__ = "bwlWORKFLOW"

    uuid = db.Column(db.String(36), primary_key=True, nullable=False)

    status = db.Column(db.Integer, default=0, nullable=False)
    status_old = db.Column(db.Integer, default=0, nullable=False)

from collections import namedtuple
Mapping = namedtuple('Mapping', ['db_name', 'default_x_data'])

class DbWorkflowObject(Base):

    """Handle for the actual WorkflowObject model."""

    __tablename__ = "bwlOBJECT"

    id = db.Column(db.Integer, primary_key=True)

    version = db.Column(db.Integer,
                        default=0, nullable=False)  # Hardcoded default because
                                                    # Objectversion is dead

    status = db.Column(ChoiceType(ObjectStatus, impl=db.Integer),
                       default=ObjectStatus.INITIAL, nullable=False,
                       index=True)

    callback_pos = db.Column(CallbackPosType())  # ex-task_counter

    _extra_data = db.Column(db.LargeBinary, nullable=False,
                            default=_encoded_default_extra_data)

    def __getattribute__(self, name):
        """Return `data` and `extra_data` user-facing storage representations.

        Initialize the one requested with default content if it is not yet
        loaded.

        Calling :py:func:`.save` is neccessary to reflect any changes made to
        these objects in the model.
        """
        data_getter = {
            # 'data': Mapping('_data', _encoded_default_data),
            'extra_data': Mapping('_extra_data', _encoded_default_extra_data),
        }
        if name in data_getter and name not in self.__dict__:
            mapping = data_getter[name]
            if getattr(self, mapping.db_name) is None:
                # Object has not yet been intialized
                stored_data = mapping.default_x_data
            else:
                stored_data = getattr(self, mapping.db_name)
            setattr(self, name, _decode(stored_data))
        return object.__getattribute__(self, name)


def info():
    """Info message."""
    return ""


def do_upgrade():
    """Implement your upgrades here."""

    # Bind and session
    bind = op.get_bind()
    session = Session(bind=bind)

    # 1. <<< bwlWORKFLOW >>>

    # 1.1 KILL: counter_{initial,halted,error,finished}

    for column_name in ('counter_initial', 'counter_halted', 'counter_error',
                        'counter_finished'):
        op.drop_column('bwlWORKFLOW', column_name)

    # 2. <<< bwlOBJECT >>>

    # 2.1 version -> status (ChoiceType(ObjectStatus))
    op.alter_column('blwOBJECT',
                    'version',
                    new_column_name='status',
                    existing_type=db.Integer,
                    existing_server_default='0',
                    existing_nullable=False)

    # 2.2 NEW: callback_pos (CallbackPosType)
    op.add_column('bwlOBJECT',
                  db.Column('callback_pos', CallbackPosType()))

    # 2.2 Data migration
    for object_ in session.query(DbWorkflowObject):
        try:
            object_.callback_pos = object_.extra_data["_task_counter"]
            del object_.extra_data["_task_counter"]
        except KeyError:
            # Assume old version "task_counter"
            object_.callback_pos = object_.extra_data["task_counter"]
            del object_.extra_data["task_counter"]

    session.commit()


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
