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

"""ES function to submit Celery tasks."""

from invenio.celery import celery


@celery.task
def index_records(sender, recid):
    """Celery function to index records."""
    from flask import current_app
    current_app.extensions.get("elasticsearch").index_records([recid])
    #TODO: get_text seems async should be replaced by a signal?
    import time
    time.sleep(1)
    current_app.extensions.get("elasticsearch").index_documents([recid])


@celery.task
def index_collections(sender, collections):
    """Celery function to index collections."""
    from flask import current_app
    current_app.extensions.get("elasticsearch").index_collections()
