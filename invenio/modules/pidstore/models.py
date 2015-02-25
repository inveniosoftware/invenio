# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
invenio.modules.pid_store.models
--------------------------------

PersistentIdentifier store and registration.

Usage example for registering new identifiers::

    from flask import url_for
    from invenio.modules.pidstore.models import PersistentIdentifier

    # Reserve a new DOI internally first
    pid = PersistentIdentifier.create('doi','10.0572/1234')

    # Get an already reserved DOI
    pid = PersistentIdentifier.get('doi', '10.0572/1234')

    # Assign it to a record.
    pid.assign('rec', 1234)

    url = url_for("record.metadata", recid=1234, _external=True)
    doc = "<resource ...."

    # Pre-reserve the DOI in DataCite
    pid.reserve(doc=doc)

    # Register the DOI (note parameters depended on the provider and pid type)
    pid.register(url=url, doc=doc)

    # Reassign DOI to new record
    pid.assign('rec', 5678, overwrite=True),

    # Update provider with new information
    pid.update(url=url, doc=doc)

    # Delete the DOI (you shouldn't be doing this ;-)
    pid.delete()
"""

from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.utils.text import to_unicode

from .provider import PidProvider


class PersistentIdentifier(db.Model):
    """
    Store and register persistent identifiers

    Assumptions:
      * Persistent identifiers can be represented as a string of max 255 chars.
      * An object has many persistent identifiers.
      * A persistent identifier has one and only one object.
    """

    __tablename__ = 'pidSTORE'
    __table_args__ = (
        db.Index('uidx_type_pid', 'pid_type', 'pid_value', unique=True),
        db.Index('idx_status', 'status'),
        db.Index('idx_object', 'object_type', 'object_value'),
    )

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True)
    """ Id of persistent identifier entry """

    pid_type = db.Column(db.String(6), nullable=False)
    """ Persistent Identifier Schema """

    pid_value = db.Column(db.String(length=255), nullable=False)
    """ Persistent Identifier """

    pid_provider = db.Column(db.String(length=255), nullable=False)
    """ Persistent Identifier Provider"""

    status = db.Column(db.CHAR(length=1), nullable=False)
    """ Status of persistent identifier, e.g. registered, reserved, deleted """

    object_type = db.Column(db.String(3), nullable=True)
    """ Object Type - e.g. rec for record """

    object_value = db.Column(db.String(length=255), nullable=True)
    """ Object ID - e.g. a record id """

    created = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    """ Creation datetime of entry """

    last_modified = db.Column(
        db.DateTime(), nullable=False, default=datetime.now,
        onupdate=datetime.now
    )
    """ Last modification datetime of entry """

    #
    # Class methods
    #
    @classmethod
    def create(cls, pid_type, pid_value, pid_provider='', provider=None):
        """
        Internally reserve a new persistent identifier in Invenio.

        A provider for the given persistent identifier type must exists. By
        default the system will choose a provider according to the pid
        type. If desired, the default system provider can be overridden via
        the provider keyword argument.

        Returns PID object if successful otherwise None.
        """
        # Ensure provider exists
        if provider is None:
            provider = PidProvider.create(pid_type, pid_value, pid_provider)
            if not provider:
                raise Exception(
                    "No provider found for %s:%s (%s)" % (
                        pid_type, pid_value, pid_provider)
                )

        try:
            obj = cls(pid_type=provider.pid_type,
                      pid_value=provider.create_new_pid(pid_value),
                      pid_provider=pid_provider,
                      status=cfg['PIDSTORE_STATUS_NEW'])
            obj._provider = provider
            db.session.add(obj)
            db.session.commit()
            obj.log("CREATE", "Created")
            return obj
        except SQLAlchemyError:
            db.session.rollback()
            obj.log("CREATE", "Failed to created. Already exists.")
            return None

    @classmethod
    def get(cls, pid_type, pid_value, pid_provider='', provider=None):
        """
        Get persistent identifier.

        Returns None if not found.
        """
        pid_value = to_unicode(pid_value)
        obj = cls.query.filter_by(
            pid_type=pid_type, pid_value=pid_value, pid_provider=pid_provider
        ).first()
        if obj:
            obj._provider = provider
            return obj
        else:
            return None

    #
    # Instance methods
    #
    def has_object(self, object_type, object_value):
        """
        Determine if this persistent identifier is assigned to a specific
        object.
        """
        if object_type not in cfg['PIDSTORE_OBJECT_TYPES']:
            raise Exception("Invalid object type %s." % object_type)

        object_value = to_unicode(object_value)

        return self.object_type == object_type and \
            self.object_value == object_value

    def get_provider(self):
        """
        Get the provider for this type of persistent identifier
        """
        if self._provider is None:
            self._provider = PidProvider.create(
                self.pid_type, self.pid_value, self.pid_provider
            )
        return self._provider

    def assign(self, object_type, object_value, overwrite=False):
        """
        Assign this persistent identifier to a given object

        Note, the persistent identifier must first have been reserved. Also,
        if an exsiting object is already assigned to the pid, it will raise an
        exception unless overwrite=True.
        """
        if object_type not in cfg['PIDSTORE_OBJECT_TYPES']:
            raise Exception("Invalid object type %s." % object_type)
        object_value = to_unicode(object_value)

        if not self.id:
            raise Exception(
                "You must first create the persistent identifier before you "
                "can assign objects to it."
            )

        if self.is_deleted():
            raise Exception(
                "You cannot assign objects to a deleted persistent identifier."
            )

        # Check for an existing object assigned to this pid
        existing_obj_id = self.get_assigned_object(object_type)

        if existing_obj_id and existing_obj_id != object_value:
            if not overwrite:
                raise Exception(
                    "Persistent identifier is already assigned to another "
                    "object"
                )
            else:
                self.log(
                    "ASSIGN",
                    "Unassigned object %s:%s (overwrite requested)" % (
                        self.object_type, self.object_value)
                )
                self.object_type = None
                self.object_value = None
        elif existing_obj_id and existing_obj_id == object_value:
            # The object is already assigned to this pid.
            return True

        self.object_type = object_type
        self.object_value = object_value
        db.session.commit()
        self.log("ASSIGN", "Assigned object %s:%s" % (self.object_type,
                                                      self.object_value))
        return True

    def update(self, with_deleted=False, *args, **kwargs):
        """ Update the persistent identifier with the provider. """
        if self.is_new() or self.is_reserved():
            raise Exception(
                "Persistent identifier has not yet been registered."
            )

        if not with_deleted and self.is_deleted():
            raise Exception("Persistent identifier has been deleted.")

        provider = self.get_provider()
        if provider is None:
            self.log("UPDATE", "No provider found.")
            raise Exception("No provider found.")

        if provider.update(self, *args, **kwargs):
            if with_deleted and self.is_deleted():
                self.status = cfg['PIDSTORE_STATUS_REGISTERED']
                db.session.commit()
            return True
        return False

    def reserve(self, *args, **kwargs):
        """
        Reserve the persistent identifier with the provider

        Note, the reserve method may be called multiple times, even if it was
        already reserved.
        """
        if not (self.is_new() or self.is_reserved()):
            raise Exception(
                "Persistent identifier has already been registered."
            )

        provider = self.get_provider()
        if provider is None:
            self.log("RESERVE", "No provider found.")
            raise Exception("No provider found.")

        if provider.reserve(self, *args, **kwargs):
            self.status = cfg['PIDSTORE_STATUS_RESERVED']
            db.session.commit()
            return True
        return False

    def register(self, *args, **kwargs):
        """
        Register the persistent identifier with the provider
        """
        if self.is_registered() or self.is_deleted():
            raise Exception(
                "Persistent identifier has already been registered."
            )

        provider = self.get_provider()
        if provider is None:
            self.log("REGISTER", "No provider found.")
            raise Exception("No provider found.")

        if provider.register(self, *args, **kwargs):
            self.status = cfg['PIDSTORE_STATUS_REGISTERED']
            db.session.commit()
            return True
        return False

    def delete(self, *args, **kwargs):
        """
        Delete the persistent identifier
        """
        if self.is_new():
            # New persistent identifier which haven't been registered yet. Just
            #  delete it completely but keep log)
            # Remove links to log entries (but otherwise leave the log entries)
            PidLog.query.filter_by(id_pid=self.id).update({'id_pid': None})
            db.session.delete(self)
            self.log("DELETE", "Unregistered PID successfully deleted")
        else:
            provider = self.get_provider()
            if not provider.delete(self, *args, **kwargs):
                return False
            self.status = cfg['PIDSTORE_STATUS_DELETED']
            db.session.commit()
        return True

    def sync_status(self, *args, **kwargs):
        """
        Synchronize persistent identifier status. Used when the provider uses
        an external service, which might have been modified outside of our
        system.
        """
        provider = self.get_provider()
        result = provider.sync_status(self, *args, **kwargs)
        db.session.commit()
        return result

    def get_assigned_object(self, object_type=None):
        if object_type is not None and self.object_type == object_type:
            return self.object_value
        return None

    def is_registered(self):
        """ Returns true if the persistent identifier has been registered """
        return self.status == cfg['PIDSTORE_STATUS_REGISTERED']

    def is_deleted(self):
        """ Returns true if the persistent identifier has been deleted """
        return self.status == cfg['PIDSTORE_STATUS_DELETED']

    def is_new(self):
        """
        Returns true if the persistent identifier has not yet been
        registered or reserved
        """
        return self.status == cfg['PIDSTORE_STATUS_NEW']

    def is_reserved(self):
        """
        Returns true if the persistent identifier has not yet been
        reserved.
        """
        return self.status == cfg['PIDSTORE_STATUS_RESERVED']

    def log(self, action, message):
        if self.pid_type and self.pid_value:
            message = "[%s:%s] %s" % (self.pid_type, self.pid_value, message)
        p = PidLog(id_pid=self.id, action=action, message=message)
        db.session.add(p)
        db.session.commit()


class PidLog(db.Model):
    """
    Audit log of actions happening to persistent identifiers.

    This model is primarily used through PersistentIdentifier.log and rarely
    created manually.
    """
    __tablename__ = 'pidLOG'
    __table_args__ = (
        db.Index('idx_action', 'action'),
    )

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True)
    """ Id of persistent identifier entry """

    id_pid = db.Column(
        db.Integer(15, unsigned=True), db.ForeignKey(PersistentIdentifier.id),
        nullable=True,
    )
    """ PID """

    timestamp = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    """ Creation datetime of entry """

    action = db.Column(db.String(10), nullable=False)
    """ Action identifier """

    message = db.Column(db.Text(), nullable=False)
    """ Log message """

    # Relationship
    pid = db.relationship("PersistentIdentifier", backref="logs")


__all__ = ['PersistentIdentifier',
           'PidLog']
