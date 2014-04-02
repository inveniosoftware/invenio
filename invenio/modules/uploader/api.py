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

from __future__ import print_function

from celery import chord
from werkzeug.utils import import_string
from workflow.engine import GenericWorkflowEngine as WorkflowEngine

from invenio.base.globals import cfg
from invenio.celery import celery
from invenio.modules.jsonalchemy.reader import Reader, split_blob
from invenio.modules.records.api import Record

from . import signals


def run(name, input_file, master_format='marc', force=False, pretend=False,
        sync=False, reader_info={}, **kwargs):
    """@todo: Docstring for run.

    :name: @todo
    :input_file: @todo
    :master_format: @todo
    :force: @todo
    :pretend: @todo
    :sync: @todo
    :reader_info: @todo
    :**kwargs: @todo

    :returns: @todo
    """
    signals.uploader_started.send(mode=name, blob=input_file,
                                  master_format=master_format, force=force,
                                  pretend=pretend, **kwargs)
    for chunk in split_blob(input_file, master_format,
                            cfg['UPLOADER_NUMBER_RECORD_PER_WORKER'],
                            **reader_info):
        chord(_translate.starmap(
            [(blob, master_format, reader_info) for blob in chunk])
        )(_run_workflow.s(name=name, force=force, pretend=pretend, **kwargs))


@celery.task
def _translate(blob, master_format, kwargs={}):
    """@todo: Docstring for _translate.

    :blob: @todo
    :master_format: @todo
    :kwargs: @todo
    :returns: @todo

    """
    return (blob,
            Reader.translate(blob, Record, master_format, **kwargs).dumps())


@celery.task
def _run_workflow(records, name, **kwargs):
    """@todo: Docstring for _run_workflow.

    :records: @todo
    :name: @todo
    :**kwargs: @todo
    :returns: @todo

    """
    workflow = import_string(cfg['UPLOADER_WORKFLOWS'][name])
    wfe = WorkflowEngine()
    wfe.setWorkflow(workflow)
    wfe.setVar('options', kwargs)
    records = [(obj[0], Record(json=obj[1])) for obj in records[0]]
    wfe.process(records)
    records = [obj[1].get('recid') for obj in records]
    signals.uploader_finished.send(name=name, result=records, **kwargs)
    return records


@celery.task
def _error_handler(uuid):
    """@todo: Docstring for _error_handler.

    :uuid: @todo
    :returns: @todo

    """
    result = celery.AsyncResult(uuid)
    exc = result.get(propagate=False)
    print('Task %r raised exception: %r\n%r'
          % (uuid, exc, result.traceback))
    return None
