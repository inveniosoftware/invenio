# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from ..hp_field_widgets import (bootstrap_accept,
                                bootstrap_reject)

from wtforms import SubmitField, Form

__all__ = ['approval_widget']


class approval_widget(Form):
    reject = SubmitField(label='Reject', widget=bootstrap_reject)
    accept = SubmitField(label='Accept', widget=bootstrap_accept)
    widget_title = "Approve Record"

    def render(self, bwobject_list, bwparent_list, info_list,
               logtext_list, w_metadata_list,
               workflow_func_list, *args, **kwargs):
        from ..views.holdingpen import _entry_data_preview

        data_preview_list = []
        # setting up approval widget
        for bwo in bwobject_list:
            data_preview_list.append(_entry_data_preview(bwo.get_data()))

        return ('workflows/hp_approval_widget.html',
                {'bwobject_list': bwobject_list,
                 'bwparent_list': bwparent_list,
                 'widget': approval_widget(),
                 'data_preview_list': data_preview_list,
                 'obj_number': len(bwobject_list),
                 'info_list': info_list,
                 'logtext_list': logtext_list,
                 'w_metadata_list': w_metadata_list,
                 'workflow_func_list': workflow_func_list})

    def run_widget(self, bwobject_id, request):
        """
        Resolves the action taken in the approval widget
        """
        from flask import request, flash, redirect, url_for
        from ..api import continue_oid_delayed
        from ..views.holdingpen import _delete_from_db
        from ..models import BibWorkflowObject
        from invenio.sqlalchemyutils import db

        bwobject = BibWorkflowObject.query.filter(
            BibWorkflowObject.id == bwobject_id).first()

        if 'Accept' in request.form:
            extra_data_dict = bwobject.get_extra_data()
            extra_data_dict['widget'] = None
            bwobject.set_extra_data(extra_data_dict)
            db.session.commit()
            continue_oid_delayed(bwobject_id)

            flash('Record Accepted')
        elif 'Reject' in request.form:
            _delete_from_db(bwobject_id)
            flash('Record Rejected')

approval_widget.__title__ = 'Approve Record'

widget = approval_widget()
