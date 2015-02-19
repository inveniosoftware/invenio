# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""PersistentIdentifier store and registration.

Usage example for registering new identifiers::

    from flask import url_for
    from invenio.pid_store import PersistentIdentifier

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

import os
from datetime import datetime

from invenio.config import CFG_PYLIBDIR
from invenio.dbquery import run_sql
from invenio.pluginutils import PluginContainer

from invenio.pid_provider import PidProvider

PIDSTORE_OBJECT_TYPES = ['rec', ]
"""
Definition of supported object types
"""

#
# Internal configuration values. Normally you will not need to edit
# any of the configuration values below.
#
PIDSTORE_STATUS_NEW = 'N'
"""
The pid has *not* yet been registered with the service provider.
"""

PIDSTORE_STATUS_REGISTERED = 'R'
"""
The pid has been registered with the service provider.
"""

PIDSTORE_STATUS_DELETED = 'D'
"""
The pid has been deleted/inactivated with the service proivider. This should
very rarely happen, and must be kept track of, as the PID should not be
reused for something else.
"""

PIDSTORE_STATUS_RESERVED = 'K'
"""
The pid has been reserved in the service provider but not yet fully
registered.
"""


def plugin_builder(plugin_name, plugin_code):
    if 'provider' in dir(plugin_code):
        candidate = getattr(plugin_code, 'provider')
        try:
            if issubclass(candidate, PidProvider):
                return candidate
        except:
            pass
    raise ValueError('%s is not a valid PID provider' % plugin_name)

_PID_PROVIDERS = PluginContainer(
    os.path.join(CFG_PYLIBDIR, 'invenio', 'pid_providers', '*.py'),
    plugin_builder=plugin_builder)


class PersistentIdentifier(object):
    """
    Store and register persistent identifiers

    Assumptions:
      * Persistent identifiers can be represented as a string of max 255 chars.
      * An object has many persistent identifiers.
      * A persistent identifier has one and only one object.
    """

    def __init__(self, id=None, pid_type=None, pid_value=None,
                 pid_provider=None, status=None, object_type=None,
                 object_value=None, created=None, last_modified=None):
        """
        :param id: Id of persistent identifier entry
        :param pid_type: Persistent Identifier Schema
        :param pid_str: Persistent Identifier
        :param pid_provider: Persistent Identifier Provider
        :param status: Status of persistent identifier, e.g. registered,
            reserved, deleted
        :param object_type: Object Type - e.g. rec for record
        :param object_value: Object ID - e.g. a record id
        :param created: Creation datetime of entry
        :param last_modified: Last modification datetime of entry
        """
        self.id = id
        self.pid_type = pid_type
        self.pid_value = pid_value
        self.pid_provider = pid_provider
        self.status = status
        self.object_type = object_type
        self.object_value = object_value
        self.created = created or datetime.now()
        self.last_modified = last_modified or datetime.now()

    def __repr__(self):
        return self.__dict__.__repr__()

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
                      status=PIDSTORE_STATUS_NEW)
            obj._provider = provider
            run_sql(
                'INSERT INTO pidSTORE '
                '(pid_type, pid_value, pid_provider, status,'
                ' created, last_modified) '
                'VALUES (%s, %s, %s, %s, NOW(), NOW())',
                (obj.pid_type, obj.pid_value, obj.pid_provider, obj.status)
            )
            obj.log("CREATE", "Created")
            return obj
        except Exception, e:
            obj.log("CREATE", e.message)
            raise e

    @classmethod
    def get(cls, pid_type, pid_value, pid_provider='', provider=None):
        """
        Get persistent identifier.

        Returns None if not found.
        """
        res = run_sql(
            'SELECT id, pid_type, pid_value, pid_provider, status, '
            'object_type, object_value, created, last_modified '
            'FROM pidSTORE '
            'WHERE pid_type=%s and pid_value=%s and pid_provider=%s',
            (pid_type, pid_value, pid_provider)
        )
        try:
            obj = cls(*res[0])
            obj._provider = provider
            return obj
        except IndexError:
            return None

    @classmethod
    def exists(cls, pid_type, pid_value):
        """Check existence of a PID."""
        res = run_sql(
            'SELECT id from pidSTORE where pid_type=%s and pid_value=%s',
            (pid_type, pid_value))
        return True if res else False

    #
    # Instance methods
    #
    def has_object(self, object_type, object_value):
        """
        Determine if this persistent identifier is assigned to a specific
        object.
        """
        if object_type not in PIDSTORE_OBJECT_TYPES:
            raise Exception("Invalid object type %s." % object_type)

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
        if object_type not in PIDSTORE_OBJECT_TYPES:
            raise Exception("Invalid object type %s." % object_type)

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
        self._update()
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
                self.status = PIDSTORE_STATUS_REGISTERED
                self._update()
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
            self.status = PIDSTORE_STATUS_RESERVED
            self._update()
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
            self.status = PIDSTORE_STATUS_REGISTERED
            self._update()
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
            run_sql('UPDATE pidLOG '
                    'SET id_pid=NULL WHERE id_pid=%s', (self.id, ))
            run_sql("DELETE FROM pidSTORE WHERE id=%s", (self.id, ))
            self.log("DELETE", "Unregistered PID successfully deleted")
        else:
            provider = self.get_provider()
            if not provider.delete(self, *args, **kwargs):
                return False
            self.status = PIDSTORE_STATUS_DELETED
            self._update()
        return True

    def sync_status(self, *args, **kwargs):
        """Synchronize persistent identifier status.
        Used when the provider uses an external service, which might have been
        modified outside of our system.
        """
        provider = self.get_provider()
        result = provider.sync_status(self, *args, **kwargs)
        self._update()
        return result

    def get_assigned_object(self, object_type=None):
        if object_type is not None and self.object_type == object_type:
            return self.object_value
        return None

    def is_registered(self):
        """Returns true if the persistent identifier has been registered """
        return self.status == PIDSTORE_STATUS_REGISTERED

    def is_deleted(self):
        """Returns true if the persistent identifier has been deleted """
        return self.status == PIDSTORE_STATUS_DELETED

    def is_new(self):
        """
        Returns true if the persistent identifier has not yet been
        registered or reserved
        """
        return self.status == PIDSTORE_STATUS_NEW

    def is_reserved(self):
        """
        Returns true if the persistent identifier has not yet been
        reserved.
        """
        return self.status == PIDSTORE_STATUS_RESERVED

    def log(self, action, message):
        if self.pid_type and self.pid_value:
            message = "[%s:%s] %s" % (self.pid_type, self.pid_value, message)
        run_sql('INSERT INTO pidLOG (id_pid, timestamp, action, message)'
                'VALUES(%s, NOW(), %s, %s)', (self.id, action, message))

    def _update(self):
        """Update the pidSTORE (self) object status on the DB."""
        run_sql(
            'UPDATE pidSTORE '
            'SET status=%s, object_type=%s, object_value=%s, '
            'last_modified=NOW() WHERE pid_type=%s and pid_value=%s',
            (self.status, self.object_type, self.object_value,
             self.pid_type, self.pid_value)
        )
