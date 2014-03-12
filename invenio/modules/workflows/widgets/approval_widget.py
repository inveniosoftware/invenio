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

from ..hp_field_widgets import (bootstrap_accept, bootstrap_accept_mini,
                                bootstrap_reject, bootstrap_reject_mini)

from wtforms import SubmitField, Form
from invenio.base.i18n import _


__all__ = ['approval_widget']


class approval_widget(Form):
    reject = SubmitField(label=_('Reject'), widget=bootstrap_reject)
    accept = SubmitField(label=_('Accept'), widget=bootstrap_accept)

    class mini_widget(Form):
        reject = SubmitField(label=_('Reject'), widget=bootstrap_reject_mini)
        accept = SubmitField(label=_('Accept'), widget=bootstrap_accept_mini)

    def render(self, bwobject_list, bwparent_list, info_list,
               logtext_list, w_metadata_list,
               workflow_func_list, *args, **kwargs):
        data_preview_list = []
        # setting up approval widget
        for bwo in bwobject_list:
            data_preview_list.append(bwo.get_formatted_data())

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

    def run_widget(self, objectid):
        """
        Resolves the action taken in the approval widget
        """
        from flask import request, flash
        from ..api import continue_oid
        from ..models import BibWorkflowObject

        bwobject = BibWorkflowObject.query.get(objectid)

        if request.form['decision'] == 'Accept':
            bwobject.remove_widget()
            continue_oid(objectid)
            flash('Record Accepted')

        elif request.form['decision'] == 'Reject':
            BibWorkflowObject.delete(objectid)
            flash('Record Rejected')

approval_widget.__title__ = 'Approve Record'
approval_widget.static = ["js/workflows/widgets/approval.js"]

widget = approval_widget()
