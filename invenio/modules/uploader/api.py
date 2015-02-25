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
Uploader API.

Following example shows how to use this API for an easy use case::

    >>> from invenio.modules.uploader.api import run
    >>> blob = open('./testsuite/data/demo_record_marc_data.xml').read()
    >>> reader_info = dict(schema='xml')
    >>> run('insert', blob, master_format='marc', reader_info=reader_info)

"""

from __future__ import print_function

from celery import chord

from invenio.base.globals import cfg
from invenio.modules.jsonalchemy.reader import split_blob

from . import signals
from .tasks import translate, run_workflow


def run(name, input_file, master_format='marc', reader_info={}, **kwargs):
    """Entry point to run any of the modes of the uploader.

    :param name: Upload mode, see `~.config.UPLOADER_WORKFLOWS` for more info.
    :type name: str
    :input_file: Input master format, typically the content of an XML file.
    :type input_file: str
    :param master_format: Input file format, for example `marc`
    :type master_format: str
    :param reader_info: Any kind of information relevan to the reader, like for
        example char encoding or special characters.
    :type reader_info: dict
    :param kwargs:
        * force:
        * pretend:
        * sync: False by default, if set to True the hole process will be
          teated synchronously
        * filename: original blob filename if it contains relative paths
    """
    signals.uploader_started.send(mode=name,
                                  blob=input_file,
                                  master_format=master_format,
                                  **kwargs)
    for chunk in split_blob(input_file, master_format,
                            cfg['UPLOADER_NUMBER_RECORD_PER_WORKER'],
                            **reader_info):
        chord(translate.starmap(
            [(blob, master_format, reader_info) for blob in chunk])
        )(run_workflow.s(name=name, **kwargs))
