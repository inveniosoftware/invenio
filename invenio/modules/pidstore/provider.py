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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
from werkzeug.utils import import_string

from invenio.base.globals import cfg
from invenio.utils.datastructures import LazyDict


class PidProvider(object):
    """
    Abstract class for persistent identifier provider classes.

    Subclasses must implement register, update, delete and is_provider_for_pid
    methods and register itself:

        class MyProvider(PidProvider):
            pid_type = "mypid"

            def reserve(self, pid, *args, **kwargs):
                return True

            def register(self, pid, *args, **kwargs):
                return True

            def update(self, pid, *args, **kwargs):
                return True

            def delete(self, pid, *args, **kwargs):
                try:
                    ...
                except Exception as e:
                    pid.log("DELETE","Deletion failed")
                    return False
                else:
                    pid.log("DELETE","Successfully deleted")
                    return True

            def is_provider_for_pid(self, pid_str):
                pass

        PidProvider.register_provider(MyProvider)


    The provider is responsible for handling of errors, as well as logging of
    actions happening to the pid. See example above as well as the
    DataCitePidProvider.

    Each method takes variable number of argument and keywords arguments. This
   can be used to pass additional information to the provider when registering
    a persistent identifier. E.g. a DOI requires URL and metadata to be able
    to register the DOI.
    """

    def __load_providers():
        registry = dict()
        for provider_str in cfg['PIDSTORE_PROVIDERS']:
            provider = import_string(provider_str)
            if not issubclass(provider, PidProvider):
                raise TypeError("Argument not an instance of PidProvider.")
            pid_type = getattr(provider, 'pid_type', None)
            if pid_type is None:
                raise AttributeError(
                    "Provider must specify class variable pid_type."
                )
            pid_type = pid_type.lower()
            if pid_type not in registry:
                registry[pid_type] = []

            # Prevent double registration
            if provider not in registry[pid_type]:
                registry[pid_type].append(provider)
        return registry
    registry = LazyDict(__load_providers)
    """ Registry of possible providers """

    pid_type = None
    """
    Must be overwritten in subcleass and specified as a string (max len 6)
    """

    @staticmethod
    def create(pid_type, pid_str, pid_provider, *args, **kwargs):
        """
        Create a new instance of a PidProvider for the
        given type and pid.
        """
        providers = PidProvider.registry.get(pid_type.lower(), None)
        for p in providers:
            if p.is_provider_for_pid(pid_str):
                return p(*args, **kwargs)
        return None

    #
    # API methods which must be implemented by each provider.
    #
    def reserve(self, pid, *args, **kwargs):
        """
        Reserve a new persistent identifier

        This might or might not be useful depending on the service of the
        provider.
        """
        raise NotImplementedError

    def register(self, pid, *args, **kwargs):
        """ Register a new persistent identifier """
        raise NotImplementedError

    def update(self, pid, *args, **kwargs):
        """ Update information about a persistent identifier """
        raise NotImplementedError

    def delete(self, pid, *args, **kwargs):
        """ Delete a persistent identifier """
        raise NotImplementedError

    def sync_status(self, pid, *args, **kwargs):
        """
        Synchronize persistent identifier status with remote service provider.
        """
        return True

    @classmethod
    def is_provider_for_pid(cls, pid_str):
        raise NotImplementedError

    #
    # API methods which might need to be implemented depending on each provider.
    #
    def create_new_pid(self, pid_value):
        """ Some PidProvider might have the ability to create new values """
        return pid_value

class LocalPidProvider(PidProvider):
    """
    Abstract class for local persistent identifier provides (i.e locally
    unmanaged DOIs).
    """
    def reserve(self, pid, *args, **kwargs):
        pid.log("RESERVE", "Successfully reserved locally")
        return True

    def register(self, pid, *args, **kwargs):
        pid.log("REGISTER", "Successfully registered in locally")
        return True

    def update(self, pid, *args, **kwargs):
        # No logging necessary as status of PID is not changing
        return True

    def delete(self, pid, *args, **kwargs):
        """ Delete a registered DOI """
        pid.log("DELETE", "Successfully deleted locally")
        return True
