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

from flask.ext.login import current_user
from flask import render_template

from invenio.modules.deposit.models import DepositionType, Deposition
from invenio.modules.formatter import format_record
from invenio.modules.deposit.tasks import render_form, \
    create_recid, \
    prepare_sip, \
    finalize_record_sip, \
    upload_record_sip, \
    prefill_draft,\
    process_sip_metadata


class SimpleRecordDeposition(DepositionType):
    """
    Simple record submission with main workflow
    """
    workflow = [
        # Pre-fill draft with values passed in from request
        prefill_draft(draft_id='default'),
        # Render form and wait for user to submit
        render_form(draft_id='default'),
        # Create the submission information package by merging data
        # from all drafts.
        prepare_sip(),
        # Process SIP
        process_sip_metadata(),
        # Reserve a new record id
        create_recid(),
        # Generate MARC based on metadata dictionary
        finalize_record_sip(is_dump=False),
        # Seal the SIP and write MARCXML file and call bibupload on it
        # Note: after upload_record_sip()
        upload_record_sip(),
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

    @classmethod
    def process_sip_metadata(cls, deposition, metadata):
        """
        Implement this method in your subclass to process metadata prior to
        MARC generation.
        """
        pass
