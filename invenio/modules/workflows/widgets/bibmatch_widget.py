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

from invenio.bibworkflow_hp_field_widgets import bootstrap_accept
from wtforms import SubmitField, Form
__all__ = ['bibmatch_widget']


class bibmatch_widget(Form):
    accept = SubmitField(label='Accept', widget=bootstrap_accept)
    widget_title = "Bibmatch Widget"

    def render(self, bwobject, *args, **kwargs):
        from ..models import BibWorkflowObject
        from ..views.holdingpen import _entry_data_preview

        # setting up bibmatch widget
        try:
            matches = bwobject.extra_data['tasks_results']['match_record']
        except:
            pass

        match_preview = []
        # adding dummy matches
        match_preview.append(BibWorkflowObject.query.filter(
            BibWorkflowObject.id == bwobject.id).first())
        match_preview.append(BibWorkflowObject.query.filter(
            BibWorkflowObject.id == bwobject.id).first())

        data_preview = _entry_data_preview(bwobject.get_data())

        return ('workflows/hp_bibmatch_widget.html',
                {'bwobject': bwobject,
                 'widget': bibmatch_widget(),
                 'match_preview': match_preview,
                 'matches': matches,
                 'data_preview': data_preview})


bibmatch_widget.__title__ = 'Bibmatch Widget'

widget = bibmatch_widget()
