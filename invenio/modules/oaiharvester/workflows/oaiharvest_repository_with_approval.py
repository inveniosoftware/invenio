# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111 1307, USA.

"""Main workflow iterating over selected repositories and downloaded files."""

from .oaiharvest_harvest_repositories import oaiharvest_harvest_repositories


class oaiharvest_repository_with_approval(oaiharvest_harvest_repositories):

    """A workflow for use with OAI harvesting in BibSched with approval."""

    record_workflow = "oaiharvest_record_approval"

    @staticmethod
    def get_description(bwo):
        """Return description of object."""
        from flask import render_template

        identifiers = None

        extra_data = bwo.get_extra_data()
        if 'options' in extra_data and 'identifiers' in extra_data["options"]:
            identifiers = extra_data["options"]["identifiers"]

        results = bwo.get_tasks_results()

        if 'review_workflow' in results:
            result_progress = results['review_workflow'][0]['result']
        else:
            result_progress = {}

        current_task = extra_data['_last_task_name']

        return render_template("workflows/styles/harvesting_description.html",
                               identifiers=identifiers,
                               result_progress=result_progress,
                               current_task=current_task)

    @staticmethod
    def get_title(bwo):
        """Return title of object."""
        return "Summary of OAI harvesting from: {0}".format(
            bwo.get_extra_data()["repository"]["name"])
