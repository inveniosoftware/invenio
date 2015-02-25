# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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


import six

from invenio.modules.records.api import Record
from .models import DepositionDraft


def record_to_draft(record, draft=None, form_class=None, pre_process=None,
                    post_process=None, producer='json_for_form'):
    """
    Load a record into a draft
    """
    if draft is None:
        draft = DepositionDraft(None, form_class=form_class)

    draft.values = record.produce('json_for_form')

    if pre_process:
        draft = pre_process(draft)

    if draft.has_form():
        form = draft.get_form()
        form.post_process()
        draft.update(form)

    # Custom post process function
    if post_process:
        draft = post_process(draft)

    return draft


def drafts_to_record(drafts, post_process=None):
    """
    Export recjson from drafts
    """
    values = DepositionDraft.merge_data(drafts)

    if post_process:
        values = post_process(values)

    return make_record(values)


def deposition_record(record, form_classes, pre_process_load=None,
                      post_process_load=None, process_export=None):
    """
    Generate recjson representation of a record for this given deposition.
    """
    return drafts_to_record(
        [
            record_to_draft(
                record,
                form_class=cls,
                pre_process=pre_process_load,
                post_process=post_process_load,
            )
            for cls in form_classes
        ],
        post_process=process_export
    )


def make_record(values, is_dump=True):
    """
    Export recjson from drafts
    """
    if is_dump:
        record = Record(json=values, master_format='marc')
    else:
        record = Record(master_format='marc')
        for k, v in six.iteritems(values):
            record[k] = v
    return record
