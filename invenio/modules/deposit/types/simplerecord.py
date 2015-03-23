# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

from flask_login import current_user
from flask import render_template

from invenio.modules.deposit.models import DepositionType, Deposition
from invenio.modules.formatter import format_record
from invenio.modules.deposit.tasks import render_form, \
    create_recid, \
    prepare_sip, \
    finalize_record_sip, \
    upload_record_sip, \
    prefill_draft, \
    process_sip_metadata, \
    hold_for_approval


class SimpleRecordDeposition(DepositionType):

    """Simple record submission - no support for editing nor REST API."""

    workflow = [
        # Pre-fill draft with values passed in from request
        prefill_draft(draft_id='default'),
        # Render form and wait for user to submit
        render_form(draft_id='default'),
        # Create the submission information package by merging form data
        # from all drafts (in this case only one draft exists).
        prepare_sip(),
        # Process metadata to match your JSONAlchemy record model. This will
        # call process_sip_metadata() on your subclass.
        process_sip_metadata(),
        # Reserve a new record id, so that we can provide proper feedback to
        # user before the record has been uploaded.
        create_recid(),
        # Generate MARC based on metadata dictionary.
        finalize_record_sip(is_dump=False),
        # Hold the deposition for admin approval
        hold_for_approval(),
        # Seal the SIP and write MARCXML file and call bibupload on it
        upload_record_sip(),
    ]

    hold_for_upload = False

    @classmethod
    def render_completed(cls, d):
        """Page to render when deposition was successfully completed."""
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
        """Implement this method in your subclass to process metadata prior to MARC generation."""
        pass
