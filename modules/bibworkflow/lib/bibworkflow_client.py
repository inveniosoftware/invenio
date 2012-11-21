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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import traceback
from workflow.engine import HaltProcessing


def run_workflow(wfe, data):
    """
    Main function running the workflow.
    """
    initial_run = True

    while True:
        try:
            if initial_run:
                initial_run = False
                wfe.process(data)
                # We processed the workflow. We're done.
                break
            else:
                wfe._unpickled = True
                wfe.restart('current', 'current')
                # We processed the restarted workflow. We're done.
                break
        except HaltProcessing as e:
            # Processing was halted. Lets save current object and continue.
            wfe.log.info("Processing halted!")
            wfe._objects[wfe.getCurrObjId()].save(2, wfe.getCurrTaskId())
            wfe.save(0)
            wfe.setPosition(wfe.getCurrObjId() + 1, [0, 0])
        except Exception as e:
            # Processing generated an exception. We print the stacktrace, save the object and continue
            wfe.log.info("Processing error!")
            wfe.log.info(str(e))
            wfe.log.info(traceback.format_exc())
            # Changing counter should be moved to wfe object together with default exception handling
            wfe.increaseCounterError()
            wfe._objects[wfe.getCurrObjId()].save(2, wfe.getCurrTaskId())
            wfe.save(0)
            wfe.setPosition(wfe.getCurrObjId() + 1, [0, 0])


def restart_workflow(wfe, data, restart_point):
    wfe.log.info("bibw_client.restart_workflow::restart_point: " + str(restart_point))
    objects = []
    for o in data:
        objects.append(o)

    if restart_point == "beginning":
        wfe.setPosition(wfe.db_obj.current_object, [0])
    else:
        wfe.setPosition(wfe.db_obj.current_object, restart_point)
    wfe._unpickled = True

    initial_run = True

    wfe._objects = objects
    while True:
        try:
            if initial_run:
                initial_run = False
                wfe.restart('current', 'current')
                # We processed the workflow. We're done.
                break
            else:
                wfe._unpickled = True
                wfe.restart('current', 'current')
                # We processed the restarted workflow. We're done.
                break
        except HaltProcessing as e:
            # Processing was halted. Lets save current object and continue.
            wfe.log.info("Processing halted!")
            wfe._objects[wfe.getCurrObjId()].save(2, wfe.getCurrTaskId())
            wfe.save(0)
            wfe.setPosition(wfe.getCurrObjId() + 1, [0, 0])
        except Exception as e:
            # Processing generated an exception. We print the stacktrace, save the object and continue
            wfe.log.info("Processing error!")
            wfe.log.info(str(e))
            wfe.log.info(traceback.format_exc())
            # Changing counter should be moved to wfe object together with default exception handling
            wfe.increaseCounterError()
            wfe._objects[wfe.getCurrObjId()].save(2, wfe.getCurrTaskId())
            wfe.save(0)
            wfe.setPosition(wfe.getCurrObjId() + 1, [0, 0])
