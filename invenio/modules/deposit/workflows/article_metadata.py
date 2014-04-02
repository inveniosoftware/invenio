# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from datetime import date
from flask.ext.login import current_user
from flask import render_template
from lxml.html import fromstring

from invenio.modules.deposit.models import DepositionType, Deposition
from invenio.modules.formatter import format_record
from invenio.modules.deposit.tasks import render_form, \
    create_recid, \
    prepare_sip, \
    finalize_record_sip, \
    upload_record_sip, \
    prefill_draft, \
    process_sip_metadata
from invenio.modules.deposit import forms
from invenio.legacy.bibsched.bibtask import task_low_level_submission
from invenio.modules.deposit.tasks import filter_empty_helper


__all__ = ['Article']


def filter_empty_elements(recjson):
    recjson['keywords'] = filter(filter_empty_helper(),
                                 recjson.get('keywords', []))

    return recjson


def process_recjson(deposition, recjson):
    """
    Process exported recjson (common for both new and edited records)
    """
    # ================
    # ISO format dates
    # ================
    for k in recjson.keys():
        if isinstance(recjson[k], date):
            recjson[k] = recjson[k].isoformat()

    # ==================================
    # Map dot-keys to their dictionaries
    # ==================================
    for k in recjson.keys():
        if '.' in k:
            mainkey, subkey = k.split('.')
            if mainkey not in recjson:
                recjson[mainkey] = {}
            recjson[mainkey][subkey] = recjson.pop(k)

    return recjson


def strip_abstract_html_tags(deposition, recjson):
    """
    Strips off html tags from abstract field
    """
    recjson['abstract']['summary'] = fromstring(
                                                recjson['abstract']['summary']
                                                ).text_content()

    return deposition


def fix_recid(deposition, recjson):
    """
    Adds _id field to sip.metadata
    """
    recjson['_id'] = recjson['recid']

    return deposition


def process_recjson_new(deposition, recjson):
    """
    Process exported recjson for a new record
    """
    process_recjson(deposition, recjson)
    return recjson


def process_recjson_edit(deposition, recjson):
    """
    Process recjson for an edited record
    """
    process_recjson(deposition, recjson)
    return recjson


# ==============
# Workflow tasks
# ==============
def run_tasks():
    """
    Run bibtasklet and webcoll after upload.
    """
    def _run_tasks(obj, dummy_eng):
        d = Deposition(obj)
        sip = d.get_latest_sip(sealed=True)

        communities = sip.metadata.get('provisional_communities', [])

        common_args = ['-P5', ]
        sequenceid = getattr(d.workflow_object, 'task_sequence_id', None)
        if sequenceid:
            common_args += ['-I', str(sequenceid)]

        for c in communities:
            task_id = task_low_level_submission(
                'webcoll', 'webdeposit', '-c', 'provisional-user-%s' % c,
                *common_args
            )
            sip.task_ids.append(task_id)
        d.update()
    return _run_tasks


class SimpleRecordSubmission(DepositionType):
    """
    Simple record submission with main workflow
    """
    #from invenio.modules.workflows.tasks.marcxml_tasks import approve_record
    workflow = [
        # New deposition
        prefill_draft(draft_id='default'),
        render_form(draft_id='default'),
        # Create the submission information package by merging data
        # from all drafts - i.e. generate the recjson.
        prepare_sip(),
        process_sip_metadata(process_recjson_new),
        # Reserve a new record id
        create_recid(),
        process_sip_metadata(fix_recid),
        # Generate MARC based on recjson structure
        finalize_record_sip(),
        # Collaborator approves/rejects the deposition
        #FIXME add approval task
        # Seal the SIP and write MARCXML file and call bibupload on it
        # Note: after upload_record_sip(), has_submission will return
        # True no matter if it's a new or editing of a deposition.
        upload_record_sip(),
        # Schedule background tasks.
        run_tasks(),
    ]

    @classmethod
    def render_completed(cls, d):
        """
        Render page when deposition was successfully completed
        """
        ctx = dict(
            deposition=d,
            deposition_type=(
                None if d.type.is_default() else d.type.get_identifier()
            ),
            uuid=d.id,
            my_depositions=Deposition.get_depositions(
                current_user, type=d.type
            ),
            sip=d.get_latest_sip(),
            format_record=format_record,
        )

        return render_template('deposit/completed.html', **ctx)


class Article(SimpleRecordSubmission):
    name = "Article"
    name_plural = "Articles"
    group = "Articles & Preprints"
    enabled = True
    draft_definitions = {
        'default': forms.ArticleForm,
    }
