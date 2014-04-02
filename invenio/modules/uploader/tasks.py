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
Core Uploader tasks
===================

Those are the main/common tasks that the uploader will use, they are used inside
the workflows defined in the ``worflows`` folder.
"""

from invenio.base.globals import cfg
from invenio.modules.pidstore.models import PersistentIdentifier

# Allow celery to collect uploader tasks
from .api import _translate, _run_workflow, _error_handler  # pylint: disable=W0611
from .errors import UploaderWorkflowException


def raise_(ex):
    """
    Helper task to raise an exception.
    """
    def _raise_(obj, eng):
        raise ex
    return _raise_


def validate(step):
    """
    Validate the record using the `validate` method present in each record and
    the validation mode, either from the command line `options` or from
    `UPLOADER_VALIDATION_MODE`.

    The for the validation the `schema` information from the field definition
    is used, see `invenio.modules.jsonalchemy.jsonext.parsers.schema_parser`
    """
    def _validate(obj, eng):
        record = obj[1]
        mode = eng.getVar('options', {}).get('validation_mode',
                                             cfg['UPLOADER_VALIDATION_MODE'])
        eng.log.info("Validating record using mode: '%s'", (mode, ))
        if not hasattr(record, 'validate'):
            raise UploaderWorkflowException(
                step, msg="An 'validate' method is needed")

        validator_errors = record.validate()
        eng.log.info('Validation errors: %s' % (str(validator_errors), ))
        if mode.lower() == 'strict' and validator_errors:
            raise UploaderWorkflowException(
                step, msg="One or more validation errors have occurred, please "
                          " check them or change the 'validation_mode' to "
                          "'permissive'.\n%s" % (str(validator_errors), ))
        eng.log.info('Finish validating the current record')
    return _validate


def retrieve_record_id_from_pids(step):
    """
    Retrieve the record identifier from a record by using all the persistent
    identifiers present in the record.

    If any PID matches with the any in DB then, the record id found is set to
    the current `record`
    """
    def _retrieve_record_id_from_pids(obj, eng):
        record = obj[1]
        eng.log.info('Look for PIDs inside the current record')
        if not hasattr(record, 'persistent_identifiers'):
            raise UploaderWorkflowException(
                step, msg="An 'persistent_identifiers' method is needed")

        for pid_name, pid_values in record.persistent_identifiers:
            eng.log.info("Found PID '%s' with value '%s', trying to match it",
                         (pid_name, pid_values))
            matching_recids = set()
            for possible_pid in pid_values:
                eng.log.info("Looking for PID %s", (possible_pid, ))
                pid = PersistentIdentifier.get(
                    possible_pid.get('type'), possible_pid.get('value'),
                    possible_pid.get('provider'))
                if pid:
                    eng.log.inf("PID found in the data base %s",
                                (pid.object_value, ))
                    matching_recids.add(pid.object_value)
            if len(matching_recids) > 1:
                raise UploaderWorkflowException(
                    step, msg="Multiple records found in the database, %s that "
                              "match '%s'" % (repr(matching_recids), pid_name))
            elif matching_recids:
                record['recid'] = matching_recids.pop()
                eng.log.info(
                    'Finish looking for PIDs inside the current record')
                break
        eng.log.info('Finish looking for PIDs inside the current record')
    return _retrieve_record_id_from_pids


def reserve_record_id(step):
    """
    Reserve a new record id for the current object and add it to
    `record['recid']`.
    """
    # TODO: manage exceptions in a better way
    def _reserve_record_id(obj, eng):
        record = obj[1]
        eng.log.info('Reserve a recid for the new record')
        try:
            pid = PersistentIdentifier.create('recid', pid_value=None,
                                              pid_provider='invenio')
            record['recid'] = int(pid.pid_value)
            pid.reserve()
            eng.log.info("Finish reserving a recid '%s' for the new record",
                         (pid.pid_value, ))
        except Exception as e:
            raise UploaderWorkflowException(step, e.message)
    return _reserve_record_id


def save_record(step):
    """
    Save the record to the DB using the `_save` method from it.
    """
    def _save(obj, eng):
        record = obj[1]
        eng.log.info('Saving record to DB')
        if not hasattr(record, '_save'):
            raise UploaderWorkflowException(
                step, msg="An '_save' method is needed")
        try:

            record._save()
            eng.log.info('Record saved to DB')
        except Exception as e:
            raise UploaderWorkflowException(step, e.message)
    return _save


def save_master_format(step):
    """@todo: Docstring for save_master_format.

    :step: @todo
    :returns: @todo

    """
    def _save_master_format(obj, eng):
        from invenio.base.helpers import utf8ifier
        from invenio.modules.formatter.models import Bibfmt
        from invenio.ext.sqlalchemy import db
        from zlib import compress
        eng.log.info('Saving master record to DB')
        bibfmt = Bibfmt(id_bibrec=obj[1]['recid'],
                        format=obj[1].additional_info.master_format,
                        kind='master',
                        last_updated=obj[1]['modification_date'],
                        value=compress(utf8ifier(obj[0])))
        db.session.add(bibfmt)
        db.session.commit()
        eng.log.info('Master record saved to DB')
    return _save_master_format


def update_pidstore(step):
    """
    Save each PID present in the record to the `PersistentIdentifier` data
    storage.
    """
    # TODO: manage exceptions
    def _update_pidstore(obj, eng):
        record = obj[1]
        eng.log.info('Look for PIDs inside the current record and register '
                     'them in the DB')
        if not hasattr(record, 'persistent_identifiers'):
            raise UploaderWorkflowException(
                step, msg="An 'persistent_identifiers' method is needed")

        for pid_name, pid_values in record.persistent_identifiers:
            eng.log.info("Found PID '%s'", (pid_name, ))
            for pid_value in pid_values:
                pid = PersistentIdentifier.get(
                    pid_value.get('type'), pid_value.get('value'),
                    pid_value.get('provider'))
                if pid is None:
                    pid = PersistentIdentifier.create(
                        pid_value.get('type'), pid_value.get('value'),
                        pid_value.get('provider'))
                if not pid.has_object('rec', record['recid']):
                    pid.assign('rec', record['recid'])
        eng.log.info('Finish looking for PIDs inside the current record and '
                     'register them in the DB')

    return _update_pidstore
