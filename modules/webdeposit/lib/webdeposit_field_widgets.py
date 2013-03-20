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

from wtforms.widgets import html_params, HTMLString


def date_widget(field, **kwargs):
    field_id = kwargs.pop('id', field.id)
    html = [u'<input class="datepicker" %s value="" type="text">'
            % html_params(id=field_id, name=field_id)]
    field_class = kwargs.pop('class', '') or kwargs.pop('class_', '')
    kwargs['class'] = u'datepicker %s' % field_class
    kwargs['class'] = u'date %s' % field_class
    return HTMLString(u''.join(html))


def plupload_widget(field, **kwargs):
    field_id = kwargs.pop('id', field.id)
    # FIXME: Move html code in a template and initialize html variable
    #        with the render_template_to_string function
    html = [u' \
            <div class="pluploader" %s > \
                <div class="well" id="filebox">\
                    <div id="drag_and_drop_text" style="text-align:center;z-index:-100;">\
                        <h1><small>Drag and Drop files here</small></h1>\
                    </div>\
                </div> \
                <table id="file-table" class="table table-striped table-bordered" style="display:none;">\
                    <thead>\
                        <tr>\
                        <th>Filename</th>\
                        <th>Size</th>\
                        <th>Status</th>\
                        <td></td>\
                        </tr>\
                    </thead>\
                    <tbody id="filelist">\
                    </tbody>\
                </table>\
                <a class="btn btn-primary" id="pickfiles" >Select files</a> \
                <a class="btn btn-success disabled" id="uploadfiles"><i class="icon-upload icon-white"></i> Start upload</a>\
                <a class="btn btn-danger" id="stopupload" style="display:none;"><i class="icon-stop icon-white"></i> Stop upload</a>\
                <div id="upload-errors"></div>\
            </div>' % html_params(id=field_id)]
    kwargs['class'] = u'plupload'
    return HTMLString(u''.join(html))


def bootstrap_submit(field, **kwargs):
    html = u'<input %s >' % html_params(style="float:right;",
                                        id="submitButton",
                                        class_="btn btn-primary btn-large",
                                        name="submitButton",
                                        type="submitButton",
                                        value=field.label.text,)
    html = [u'<div style="float:right;" >' + html + u'</div>']
    return HTMLString(u''.join(html))


def ckeditor_widget(field, **kwargs):
    field.ckeditor = True
    field_id = kwargs.pop('id', field.id)
    html = [u'<textarea %s >'
            % html_params(id=field_id, name=field_id)]
    if field.data is not None:
        html.append('%s</textarea>' % field.data)
    else:
        html.append('</textarea>')
    return HTMLString(u''.join(html))

    field_id = "ckeditor_" + field_id
    html = [u'<textarea %s ></textarea>'
            % html_params(id=field_id, name=field_id)]
    return HTMLString(u''.join(html))
