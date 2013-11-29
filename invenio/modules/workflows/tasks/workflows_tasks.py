
from invenio.modules.workflows.models import (BibWorkflowObject,
                                              BibWorkflowEngineLog)
from invenio.modules.workflows.api import (start_delayed)

from invenio.modules.workflows.utils import InvenioWorkflowError


def get_nb_workflow_created(obj, eng):
    eng.log.info("last task name: get_nb_workflow_created")
    return eng.extra_data["nb_workflow"]


def start_workflow(workflow_to_run="default", data=None, copy=True, **kwargs):
    """
     This function allow you to run a new asynchronous workflow, this
     will be run on the celery node configurer into invenio
     configuration.

     The first argument is the name of the workflow.

     The second one is the data to use for this workflow

     The copy parameter allow you to pass to the workflow  a copy
     of the obj at the moment of the call .

     **kargs allow you to add some key:value into the extra data of
     the object.
     """

    def _start_workflow(obj, eng):

        eng.log.info("last task name: start_workflow")

        eng.log.info("Workflow object in creation")
        myobject = BibWorkflowObject()

        if copy is True:
            myobject.copy(obj)
        if data is not None:
            myobject.data = data
        eng.log.info("Workflow object ready")

        myobject.save()
        workflow_id = start_delayed(workflow_to_run, data=[myobject], **kwargs)

        eng.log.info("Workflow launched")
        try:
            eng.extra_data["workflow_ids"].append(workflow_id)
        except KeyError:
            eng.extra_data["workflow_ids"] = [workflow_id]

        try:
            eng.extra_data["nb_workflow"] += 1
        except KeyError:
            eng.extra_data["nb_workflow"] = 1

        if "nb_workflow_failed" not in eng.extra_data:
            eng.extra_data["nb_workflow_failed"] = 0

    return _start_workflow


def wait_for_workflows_to_complete(obj, eng):
    """
     This function wait all the asynchronous workflow launched.
     It acts like a barrier
     """
    eng.log.info("last task name: wait_for_workflows_to_complete")

    if 'workflow_ids' in eng.extra_data:
        for workflow_id in eng.extra_data['workflow_ids']:
            try:
                workflow_id.get()

            except InvenioWorkflowError as e:

                eng.log.error("___________________\n_______ALERT_______\n___________________\n_______WORKFLOW " +
                              e.id_workflow + " FAILED_______\n_______ERROR MESSAGE IS :_______\n" + repr(e))

                workflowlog = BibWorkflowEngineLog.query.filter(BibWorkflowEngineLog.id_object == e.id_workflow).all()

                for log in workflowlog:
                    eng.log.error(log.message)

                eng.extra_data["nb_workflow_failed"] += 1
            except Exception as e:
                eng.log.error("_______ALERT_______")
                eng.log.error(str(e))
                eng.extra_data["nb_workflow_failed"] += 1
    else:
        eng.extra_data["nb_workflow"] = 0
        eng.extra_data["nb_workflow_failed"] = 0


def wait_for_workflow_to_complete(obj, eng):
    """
     This function wait for the asynchronous workflow specified
     in obj.data ( asyncresult )
     It acts like a barrier
     """
    eng.log.info("last task name: wait_for_workflow_to_complete")
    for workflow_id in eng.extra_data['workflow_ids']:
        try:
            obj.data.get()
        except Exception as e:
            eng.log.error(str(e))
            eng.extra_data["nb_workflow_failed"] += 1


def get_list_of_workflows_to_wait(obj, eng):
    """
     Return a list of asyncresult corresponding to running
     asynchrnous workflow
     """
    eng.log.info("last task name: get_list_of_workflows_to_wait")
    return eng.extra_data["workflow_ids"]


def get_status_async_result_obj_data(obj, eng):
    eng.log.info("last task name: get_status_async_result_obj_data")
    return obj.data.state


def workflows_reviews(obj, eng):
    """
     This function write a  little report about
     asynchronous workflows in this main workflow
     Raise an exception if a workflow is gone rogue
     """
    eng.log.info("last task name: workflows_reviews")
    eng.log.info("%s / %s failed" % (eng.extra_data["nb_workflow_failed"], eng.extra_data["nb_workflow"]))

    if eng.extra_data["nb_workflow_failed"]:
        raise Exception("%s / %s failed" % (eng.extra_data["nb_workflow_failed"], eng.extra_data["nb_workflow"]))


def log_info(message):
    def _log_info(obj, eng):
        eng.log.info(message)

    return _log_info
