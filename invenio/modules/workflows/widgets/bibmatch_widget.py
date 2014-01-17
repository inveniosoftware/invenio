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

from invenio.base.i18n import _
from ..hp_field_widgets import bootstrap_accept
from wtforms import SubmitField, Form
__all__ = ['bibmatch_widget']


class bibmatch_widget(Form):
    accept = SubmitField(label=_('Accept'), widget=bootstrap_accept)

    def render(self, bwobject_list, *args, **kwargs):
        # FIXME: Currently not working

        # setting up bibmatch widget
        bwobject = bwobject_list[0]
        results = bwobject.get_extra_data()['_tasks_results']

        matches = []
        match_preview = []
        for res in results:
            if res.name == "matcher":
                matches.append(res.result)

        data_preview = None

        return ('workflows/hp_bibmatch_widget.html',
                {'bwobject': bwobject,
                 'widget': bibmatch_widget(),
                 'match_preview': match_preview,
                 'matches': matches,
                 'data_preview': data_preview})


bibmatch_widget.__title__ = 'Bibmatch Widget'

widget = bibmatch_widget()
