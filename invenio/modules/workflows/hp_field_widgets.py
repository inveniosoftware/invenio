# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2013, 2014 CERN.
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


def bootstrap_accept(field):
    """
    Accept button for hp
    """
    html = u'<input %s >' \
           % html_params(id="submitButton",
                         class_="btn btn-success",
                         name="submitButton",
                         type="submit",
                         value=field.label.text,)
    return HTMLString(u''.join(html))


def bootstrap_submit(field):
    """
    Submit button for edit record action
    """
    html = u'<input %s >' \
           % html_params(id="submitButton",
                         class_="btn btn-sm btn-primary",
                         name="submitButton",
                         type="submit",)
    return HTMLString(u''.join(html))


def bootstrap_accept_mini(field, **kwargs):
    """
    Mini Accept button for hp
    """
    objectid = kwargs.pop('objectid', '')
    html = u'<input %s >' \
           % html_params(id="submitButtonMini",
                         class_="btn btn-success btn-xs",
                         name="submitButton",
                         type="submit",
                         value=field.label.text,
                         onclick="approval.mini_approval('Accept', event, %s);" % (objectid,),)
    return HTMLString(u''.join(html))


def bootstrap_reject(field):
    """
    Reject button for hp
    """
    html = u'<input %s >' \
           % html_params(id="submitButton",
                         class_="btn btn-danger",
                         name="submitButton",
                         type="submit",
                         value=field.label.text,)
    return HTMLString(u''.join(html))


def bootstrap_reject_mini(field, **kwargs):
    """
    Mini Reject button for hp
    """
    objectid = kwargs.pop('objectid', '')
    html = u'<input %s >' \
           % html_params(id="submitButtonMini",
                         class_="btn btn-danger btn-xs",
                         name="submitButton",
                         type="submit",
                         value=field.label.text,
                         onclick="approval.mini_approval('Reject', event, %s);" % (objectid,),)
    return HTMLString(u''.join(html))
