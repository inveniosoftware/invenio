# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Collection of fields that can be used to render Jinja templates."""

from invenio.modules.deposit.field_base import WebDepositField

from .. import field_widgets

__all__ = ['JinjaField']


class JinjaField(WebDepositField):

    """Generic field that renders a given template."""

    def __init__(self, **kwargs):
        """Create field that displays a given template.

        :param template: path to template that should be used for rendering.
        :type template: str
        """
        defaults = dict(
            widget_classes='form-control',
            widget=field_widgets.JinjaWidget()
        )
        defaults.update(kwargs)
        self.template = defaults.pop('template')
        super(JinjaField, self).__init__(**defaults)
