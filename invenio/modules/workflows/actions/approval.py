# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Generic Approval action."""

from invenio.base.i18n import _
from flask import render_template, url_for


class approval(object):
    """Class representing the approval action."""
    name = _("Approve")
    url = url_for("holdingpen.resolve_action")

    def render_mini(self, obj):
        """Method to render the minified action."""
        return render_template(
            'workflows/actions/approval_mini.html',
            message=obj.get_action_message(),
            object=obj,
            resolve_url=self.url,
        )

    def render(self, obj):
        """Method to render the action."""
        return {
            "side": render_template('workflows/actions/approval_side.html',
                                    message=obj.get_action_message(),
                                    object=obj,
                                    resolve_url=self.url,),
            "main": render_template('workflows/actions/approval_main.html',
                                    message=obj.get_action_message(),
                                    object=obj,
                                    resolve_url=self.url,)
        }

    def resolve(self, bwo):
        """Resolve the action taken in the approval action."""
        from flask import request
        value = request.form.get("value", None)

        bwo.remove_action()
        extra_data = bwo.get_extra_data()

        if value == 'accept':
            extra_data["approved"] = True
            bwo.set_extra_data(extra_data)
            bwo.save()
            bwo.continue_workflow(delayed=True)
            return {
                "message": "Record has been accepted!",
                "category": "success",
            }
        elif value == 'reject':
            extra_data["approved"] = False
            bwo.set_extra_data(extra_data)
            bwo.save()
            bwo.continue_workflow(delayed=True)
            return {
                "message": "Record has been rejected (deleted)",
                "category": "warning",
            }
