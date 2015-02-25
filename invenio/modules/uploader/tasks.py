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

"""Uploader celery tasks."""

from workflow.engine import GenericWorkflowEngine as WorkflowEngine

from invenio.base.globals import cfg
from invenio.celery import celery
from invenio.modules.jsonalchemy.reader import Reader
from invenio.modules.records.api import Record
from invenio.modules.workflows.registry import workflows

from . import signals
from .errors import UploaderException


@celery.task
def translate(blob, master_format, kwargs=None):
    """Translate from the `master_format` to `JSON`.

    :param blob: String contain the input file.
    :param master_format: Format of the blob, it will used to decide which
        reader to use.
    :param kwargs: Arguments to be used by the reader.
        See :class:`invenio.modules.jsonalchemy.reader.Reader`

    :returns: The blob and the `JSON` representation of the input file created
        by the reader.

    """
    return (blob,
            Reader.translate(blob, Record, master_format,
                             **(kwargs or dict())).dumps())


@celery.task
def run_workflow(records, name, **kwargs):
    """Run the uploader workflow itself.

    :param records: List of tuples `(blob, json_record)` from :func:`translate`
    :param name: Name of the workflow to be run.
    :parma kwargs: Additional arguments to be used by the tasks of the workflow

    :returns: Typically the list of record Ids that has been process, although
        this value could be modify by the `post_tasks`.

    """
    def _run_pre_post_tasks(tasks):
        """Helper function to run list of functions."""
        for task in tasks:
            task(records, **kwargs)

    #FIXME: don't know why this is needed but IT IS!
    records = records[0]

    if name in cfg['UPLOADER_WORKFLOWS']:
        workflow = workflows.get(name)
    else:
        raise UploaderException("Workflow {0} not in UPLOADER_WORKFLOWS".format(name))
    _run_pre_post_tasks(workflow.pre_tasks)
    wfe = WorkflowEngine()
    wfe.setWorkflow(workflow.tasks)
    wfe.setVar('options', kwargs)
    wfe.process(records)
    _run_pre_post_tasks(workflow.post_tasks)
    signals.uploader_finished.send(uploader_workflow=name,
                                   result=records, **kwargs)
    return records


# @celery.task
# def error_handler(uuid):
#     """@todo: Docstring for _error_handler.
#
#     :uuid: @todo
#     :returns: @todo
#
#     """
#     result = celery.AsyncResult(uuid)
#     exc = result.get(propagate=False)
#     print('Task %r raised exception: %r\n%r'
#           % (uuid, exc, result.traceback))
#     return None

__all__ = ('translate', 'run_workflow')
