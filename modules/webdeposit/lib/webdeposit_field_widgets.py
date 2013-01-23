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

from wtforms import Label
from wtforms.widgets import html_params, HTMLString

def date_widget(field, **kwargs):
    field_id = kwargs.pop('id', field.id)
    html = [u'<input class="datepicker" %s value="" type="text">' \
            % html_params(id=field_id, name=field_id)]
    field_class = kwargs.pop('class', '') or kwargs.pop('class_', '')
    kwargs['class'] = u'datepicker %s' % field_class
    kwargs['class'] = u'date %s' % field_class
    return HTMLString(u''.join(html))

def plupload_widget(field, **kwargs):
    field_id = kwargs.pop('id', field.id)
    html = [u'</td></tr><tr><td colspan="3"><div class="pluploader" %s>\
                <p>You browser doesn\'t have HTML5 support.</p>\
                </div></td></tr>' % html_params(id=field_id)]
    kwargs['class'] = u'plupload'
    return HTMLString(u''.join(html))


def bootstrap_submit(field, **kwargs):
    html = u'<input %s >' \
                % html_params(style="float:right;", \
                              id="submitButton", \
                              class_="btn btn-primary btn-large", \
                              name="submitButton",
                              type="submitButton", \
                              value=field.label.text,)
    html = [u'<div style="float:right;" ></br>' + html + u'</div>']
    return HTMLString(u''.join(html))
