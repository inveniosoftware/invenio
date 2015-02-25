# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

import os
from invenio.testsuite import InvenioTestCase
from flask import url_for


class DepositionTestCase(InvenioTestCase):
    """
    Helper class for easier testing of deposition types.
    """
    def register(self, deposition_type):
        """ Register the deposition type """
        from invenio.modules.deposit.registry import deposit_types
        from invenio.modules.deposit.url_converters import refresh_url_map
        deposit_types.register(deposition_type)
        assert deposition_type in deposit_types
        self.deposition_type = deposition_type
        refresh_url_map(self.app)

    def unregister(self):
        """ Unregister an already registered deposition type """
        from invenio.modules.deposit.registry import deposit_types
        from invenio.modules.deposit.url_converters import refresh_url_map
        deposit_types.unregister(self.deposition_type)
        assert self.deposition_type not in deposit_types
        self.deposition_type = None
        refresh_url_map(self.app)

    def clear(self, deposition_type):
        """
        Remove all traces of the specified deposition type
        """
        from invenio.modules.workflows.models import Workflow, \
            BibWorkflowObject, BibWorkflowObjectLog, BibWorkflowEngineLog
        from invenio.ext.sqlalchemy import db

        workflow_ids = map(
            lambda x: x.uuid,
            Workflow.query.filter_by(
                module_name='webdeposit', name=deposition_type
            ).all()
        )

        if workflow_ids:
            obj_ids = map(
                lambda x: x.id,
                BibWorkflowObject.query.filter(
                    BibWorkflowObject.id_workflow.in_(workflow_ids)
                ).all()
            )

            db.session.commit()

            if obj_ids:
                BibWorkflowObjectLog.query.filter(
                    BibWorkflowObjectLog.id_object.in_(obj_ids)
                ).delete(synchronize_session=False)

            BibWorkflowEngineLog.query.filter(
                BibWorkflowEngineLog.id_object.in_(workflow_ids)
            ).delete(synchronize_session=False)

            BibWorkflowObject.query.filter(
                BibWorkflowObject.id.in_(obj_ids)
            ).delete(synchronize_session=False)

            Workflow.query.filter(
                Workflow.uuid.in_(workflow_ids)
            ).delete(synchronize_session=False)

            db.session.commit()

    def run_task_id(self, task_id):
        """ Run a bibsched task """

        from invenio.modules.scheduler.models import SchTASK

        CFG_BINDIR = self.app.config['CFG_BINDIR']

        bibtask = SchTASK.query.filter(SchTASK.id == task_id).first()
        assert bibtask is not None
        assert bibtask.status == 'WAITING'

        cmd = "%s/%s %s" % (CFG_BINDIR, bibtask.proc, task_id)
        assert not os.system(cmd)

    def run_tasks(self, alias=None):
        """
        Run all background tasks matching parameters
        """
        from invenio.modules.scheduler.models import SchTASK

        q = SchTASK.query
        if alias:
            q = q.filter(SchTASK.user == alias, SchTASK.status == 'WAITING')

        for r in q.all():
            self.run_task_id(r.id)

    def run_deposition_tasks(self, deposition_id, with_webcoll=True):
        """
        Run all task ids specified in the latest SIP and optionally run
        webcoll.
        """
        # Run submitted tasks
        from invenio.modules.deposit.models import Deposition
        dep = Deposition.get(deposition_id)
        sip = dep.get_latest_sip(sealed=True)

        for task_id in sip.task_ids:
            self.run_task_id(task_id)

        if with_webcoll:
            # Run webcoll (to ensure record is assigned permissions)
            from invenio.legacy.bibsched.bibtask import \
                task_low_level_submission
            task_id = task_low_level_submission('webcoll', 'webdeposit', '-q')
            self.run_task_id(task_id)

            # Check if record is accessible
            response = self.client.get(
                url_for('record.metadata', recid=sip.metadata['recid']),
                base_url=self.app.config['CFG_SITE_SECURE_URL'],
            )
            self.assertStatus(response, 200)

    def create(self, deposition_type):
        """ Create a deposition and return is deposition id """
        res = self.client.get(url_for(
            'webdeposit.create', deposition_type=deposition_type,
        ))
        assert res.status_code == 302
        return res.location.split("/")[-1]
