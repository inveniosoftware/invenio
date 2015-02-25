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
Uploader workflow tasks.

Those are the main/common tasks that the uploader will use, they are used
inside the workflows defined in :py:mod:`~invenio.modules.uploader.workflows`.

See: `Simple workflows for Python <https://pypi.python.org/pypi/workflow/1.0>`_
"""

import os

from invenio.base.globals import cfg
from invenio.modules.pidstore.models import PersistentIdentifier

from .errors import UploaderWorkflowException

###########################################################
##############          Pre tasks         #################
###########################################################


def create_records_for_workflow(records, **kwargs):
    """Create the record object from the json.

    :param records: List of records to be process.
    :kwargs:
    """
    from invenio.modules.records.api import Record
    for i, obj in enumerate(records):
        records[i] = (obj[0], Record(json=obj[1]))

###########################################################
##############          Post tasks        #################
###########################################################


def return_recordids_only(records, **kwargs):
    """Retrieve from the records only the record ID to return them.

    :param records: Processed list of records
    :parma kwargs:
    """
    for i, obj in enumerate(records):
        records[i] = obj[1].get('recid')


###########################################################
##############        Workflow tasks      #################
###########################################################


def raise_(ex):
    """Helper task to raise an exception."""
    def _raise_(obj, eng):
        raise ex
    return _raise_


def validate(step):
    """Validate the record.

    Validate the record using the `validate` method present in each record and
    the validation mode, either from the command line options or from
    `UPLOADER_VALIDATION_MODE`.

    For the validation the `schema` information from the field definition
    is used, see `invenio.modules.jsonalchemy.jsonext.parsers.schema_parser`.
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
                step, msg="One or more validation errors have occurred, please"
                          " check them or change the 'validation_mode' to "
                          "'permissive'.\n%s" % (str(validator_errors), ))
        eng.log.info('Finish validating the current record')
    return _validate


def retrieve_record_id_from_pids(step):
    """Retrieve the record identifier from a record using its PIDS.

    If any PID matches with any in the DB then the record id found is set to
    the current `record`
    """
    def _retrieve_record_id_from_pids(obj, eng):
        record = obj[1]
        eng.log.info('Look for PIDs inside the current record')
        if not hasattr(record, 'persistent_identifiers'):
            raise UploaderWorkflowException(
                step, msg="An 'persistent_identifiers' method is needed")

        for pid_name, pid_values in record.persistent_identifiers:
            eng.log.info("Found PID '%s' trying to match it", (pid_name, ))
            matching_recids = set()
            for possible_pid in pid_values:
                eng.log.info("Looking for PID %s", (possible_pid, ))
                pid = PersistentIdentifier.get(
                    possible_pid.get('type'), possible_pid.get('value'),
                    possible_pid.get('provider'))
                if pid:
                    eng.log.info("PID found in the data base %s",
                                 (pid.object_value, ))
                    matching_recids.add(pid.object_value)
            if len(matching_recids) > 1:
                raise UploaderWorkflowException(
                    step, msg="Found multiple match in the database, %s "
                              "for '%s'" % (repr(matching_recids), pid_name))
            elif matching_recids:
                record['recid'] = matching_recids.pop()
                eng.log.info(
                    'Finish looking for PIDs inside the current record')
                break
        eng.log.info('Finish looking for PIDs inside the current record')
    return _retrieve_record_id_from_pids


def reserve_record_id(step):
    """Reserve a new record id for the current object and set it inside."""
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
    """Save the record to the DB using the `_save` method from it."""
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
    """Put the master format info the `bfmt` DB table."""
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
                        value=compress(utf8ifier(
                            obj[0]
                            if obj[1].additional_info.master_format == 'marc'
                            else obj[1].legacy_export_as_marc()
                        )))
        db.session.add(bibfmt)
        db.session.commit()
        eng.log.info('Master record saved to DB')
    return _save_master_format


def update_pidstore(step):
    """Save each PID present in the record to the PID storage."""
    # TODO: manage exceptions
    def _update_pidstore(obj, eng):
        record = obj[1]
        eng.log.info('Look for PIDs inside the current record and register '
                     'them in the DB')
        if not hasattr(record, 'persistent_identifiers'):
            raise UploaderWorkflowException(
                step, msg="An 'persistent_identifiers' method is needed")

        eng.log.info("Found PIDs '%s'", (record.persistent_identifiers, ))

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


def manage_attached_documents(step):
    """Attach and treat all the documents embeded in the input filex."""
    from invenio.modules.documents import api
    from invenio.modules.documents.tasks import set_document_contents
    from invenio.modules.records.utils import name_generator

    def _manage_attached_documents(obj, eng):
        record = obj[1]
        filename = eng.getVar('options').get('filename')
        dirname = os.path.abspath(os.path.dirname(filename)) \
            if filename is not None else os.curdir

        def _check_path(source):
            """Check if the ``source`` path.

            If it is relative path than the directory path of original blob
            filename, if defined, or the current directory will be prepended.
            """
            if not os.path.isabs(source):
                new_source = os.path.join(dirname, source)
                if os.path.exists(new_source):
                    return new_source
                eng.log.error('File %s does not exist.', (new_source,))
            return source

        eng.log.info('Look documents to manage')

        def _create_document(metadata, record):
            metadata['source'] = _check_path(metadata['source'])

            if '_documents' not in record:
                record['_documents'] = []

            model = metadata.pop('model', 'record_document_base')

            if 'recids' not in metadata:
                metadata['recids'] = list()
            if record.get('recid', -1) not in metadata['recids']:
                metadata['recids'].append(record.get('recid', -1), )

            document = api.Document.create(metadata, model=model)
            eng.log.info('Document %s created', (document['_id'],))

            record['_documents'].append((document['title'], document['_id']))
            return document

        if 'files_to_upload' in record:
            eng.log.info('Documents to upload found')
            files_to_upload = record.get('files_to_upload', [])

            for file_to_upload in files_to_upload:
                document = _create_document(file_to_upload, record)

                set_document_contents.delay(
                    document['_id'],
                    document['source'],
                    name_generator(document)
                )

            eng.log.info('Finish creating documents, delete temporary key')
            del record['files_to_upload']

        if 'files_to_link' in record:
            eng.log.info('Documents to link found')
            files_to_link = record.get('files_to_link', [])

            for file_to_link in files_to_link:
                _create_document(file_to_link, record)

            eng.log.info('Finish linking documents, delete temporary key')
            del record['files_to_link']

    return _manage_attached_documents


def legacy(step):
    """Update legacy bibxxx tables."""
    def _legacy(obj, eng):
        record = obj[1]
        if record.additional_info.master_format != 'marc':
            return
        import marshal
        from invenio.legacy.bibupload.engine import (
            CFG_BIBUPLOAD_DISABLE_RECORD_REVISIONS,
            CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE,
            archive_marcxml_for_history,
            update_bibfmt_format,
            update_database_with_metadata,
        )

        modification_date = record['modification_date'].strftime(
            '%Y-%m-%d %H:%M:%S')

        update_bibfmt_format(
            record['recid'],
            record.legacy_export_as_marc(),
            'xm',
            modification_date
        )
        if CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE:
            update_bibfmt_format(
                record['recid'],
                marshal.dumps(record.legacy_create_recstruct()),
                'recstruct',
                modification_date
            )
        if not CFG_BIBUPLOAD_DISABLE_RECORD_REVISIONS:
            archive_marcxml_for_history(
                record['recid'], affected_fields={}
            )

        update_database_with_metadata(
            record.legacy_create_recstruct(),
            record['recid']
        )
        eng.log.info(
            'Finishing legacy task for record {0}'.format(record['recid'])
        )

    return _legacy
