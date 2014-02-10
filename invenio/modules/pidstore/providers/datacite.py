# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""
    invenio.modules.pid_store.providers.data_cite_pid_provider
    ----------------------------------------------------------

    DataCite PID provider
"""

from invenio.base.globals import cfg
from invenio.utils.datacite import DataCite, HttpError, DataCiteError

from invenio.modules.pidstore.provider import PidProvider

class DataCite(PidProvider):
    """
    DOI provider using DataCite API.
    """
    pid_type = 'doi'

    def __init__(self):
        self.api = DataCite()

    def _get_url(self, kwargs):
        try:
            return kwargs['url']
        except KeyError:
            raise Exception("url keyword argument must be specified.")

    def _get_doc(self, kwargs):
        try:
            return kwargs['doc']
        except KeyError:
            raise Exception("doc keyword argument must be specified.")

    def reserve(self, pid, *args, **kwargs):
        """ Reserve a DOI (amounts to upload metadata, but not to mint) """
        # Only registered PIDs can be updated.
        doc = self._get_doc(kwargs)

        try:
            self.api.metadata_post(doc)
        except DataCiteError, e:
            pid.log("RESERVE", "Failed with %s" % e.__class__.__name__)
            return False
        except HttpError, e:
            pid.log("RESERVE", "Failed with HttpError - %s" % unicode(e))
            return False
        else:
            pid.log("RESERVE", "Successfully reserved in DataCite")
        return True

    def register(self, pid, *args, **kwargs):
        """ Register a DOI via the DataCite API """
        url = self._get_url(kwargs)
        doc = self._get_doc(kwargs)

        try:
            # Set metadata for DOI
            self.api.metadata_post(doc)
            # Mint DOI
            self.api.doi_post(pid.pid_value, url)
        except DataCiteError, e:
            pid.log("REGISTER", "Failed with %s" % e.__class__.__name__)
            return False
        except HttpError, e:
            pid.log("REGISTER", "Failed with HttpError - %s" % unicode(e))
            return False
        else:
            pid.log("REGISTER", "Successfully registered in DataCite")
        return True

    def update(self, pid, *args, **kwargs):
        """
        Update metadata associated with a DOI.

        This can be called before/after a DOI is registered

        """
        url = self._get_url(kwargs)
        doc = self._get_doc(kwargs)

        if pid.is_deleted():
            pid.log("UPDATE", "Reactivate in DataCite")

        try:
            # Set metadata
            self.api.metadata_post(doc)
            self.api.doi_post(pid.pid_value, url)
        except DataCiteError, e:
            pid.log("UPDATE", "Failed with %s" % e.__class__.__name__)
            return False
        except HttpError, e:
            pid.log("UPDATE", "Failed with HttpError - %s" % unicode(e))
            return False
        else:
            if pid.is_deleted():
                pid.log("UPDATE", "Successfully updated and possibly registered in DataCite")
            else:
                pid.log("UPDATE", "Successfully updated in DataCite")
        return True

    def delete(self, pid, *args, **kwargs):
        """ Delete a registered DOI """
        try:
            self.api.metadata_delete(pid.pid_value)
        except DataCiteError, e:
            pid.log("DELETE", "Failed with %s" % e.__class__.__name__)
            return False
        except HttpError, e:
            pid.log("DELETE", "Failed with HttpError - %s" % unicode(e))
            return False
        else:
            pid.log("DELETE", "Successfully deleted in DataCite")
        return True

    @classmethod
    def is_provider_for_pid(cls, pid_str):
        """
        Check if DataCite is the provider for this DOI

        Note: If you e.g. changed DataCite account and received a new prefix,
        then this provider can only update and register DOIs for the new
        prefix.
        """
        return pid_str.startswith("%s/" % cfg['CFG_DATACITE_DOI_PREFIX'])
