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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import msgpack
import calendar

from invenio.ext.cache import cache
from .registry import workflows


def session_manager(orig_func):
    """Decorator to wrap function with the session."""
    from invenio.ext.sqlalchemy import db

    def new_func(self, *a, **k):
        """Wrappen function to manage DB session."""
        try:
            resp = orig_func(self, *a, **k)
            db.session.commit()
            return resp
        except:
            db.session.rollback()
            raise

    return new_func


def convert_marcxml_to_bibfield(marcxml):
    """Return a SmartJson representation of MARC XML string.

    This function converts a MARCXML string to a JSON-like
    dictionary using the the jsonalchemy (aka. BibField) config.

    :param marcxml: MARCXML string to parse
    :type marcxml: string

    :return: SmartJson object.
    """
    from invenio.modules.jsonalchemy.reader import Reader
    from invenio.modules.jsonalchemy.wrappers import SmartJson
    if isinstance(marcxml, unicode):
        marcxml = marcxml.encode(errors='ignore')
    return Reader.translate(marcxml,
                            SmartJson,
                            master_format='marc',
                            namespace='recordext')


def test_teardown(self):
    """Clean up created objects in tests."""
    from invenio.modules.workflows.models import (BibWorkflowObject,
                                                  Workflow,
                                                  BibWorkflowEngineLog,
                                                  BibWorkflowObjectLog)
    from invenio.ext.sqlalchemy import db

    workflows = Workflow.get(Workflow.module_name == "unit_tests").all()
    for workflow in workflows:
        BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).delete()

        objects = BibWorkflowObjectLog.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).all()
        for obj in objects:
            db.session.delete(obj)
        db.session.delete(workflow)

        objects = BibWorkflowObjectLog.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).all()
        for obj in objects:
            BibWorkflowObjectLog.delete(id=obj.id)
        BibWorkflowEngineLog.delete(uuid=workflow.uuid)

    # Deleting dummy object created in tests
    Workflow.query.filter(Workflow.module_name == "unit_tests").delete()
    db.session.commit()


class BibWorkflowObjectIdContainer(object):

    """Mapping from an ID to BibWorkflowObject.

    This class is only used to be able to store a workflow ID and
    to retrieve easily the workflow from this ID from another process,
    such as a Celery worker process.

    It is used mainly to avoid problems with SQLAlchemy sessions
    when we use different processes.
    """

    def __init__(self, bibworkflowobject=None):
        """Initialize the object, optionally passing a BibWorkflowObject."""
        if bibworkflowobject is not None:
            self.id = bibworkflowobject.id
        else:
            self.id = None

    def get_object(self):
        """Get the BibWorkflowObject from self.id."""
        from ..workflows.models import BibWorkflowObject as bwlObject

        if self.id is not None:
            return bwlObject.query.filter(bwlObject.id == self.id).one()
        else:
            return None

    def from_dict(self, dict_to_process):
        """Take a dict with special keys and set the current id.

        :param dict_to_process: dict created before with to_dict()
        :type dict_to_process: dict

        :return: self, BibWorkflowObjectIdContainer.
        """
        self.id = dict_to_process[str(self.__class__)]["id"]
        return self

    def to_dict(self):
        """Create a dict with special keys for later retrieval."""
        return {str(self.__class__): self.__dict__}


class WorkflowsTaskResult(object):

    """The class to contain the current task results."""

    def __init__(self, task_name, name, result):
        """Create a task result passing task_name, name and result."""
        self.task_name = task_name
        self.name = name
        self.result = result

    def to_dict(self):
        """Return a dictionary representing a full task result."""
        return {
            'name': self.name,
            'task_name': self.task_name,
            'result': self.result
        }


def get_workflow_definition(name):
    """Try to load the given workflow from the system."""
    from .registry import workflows

    if name in workflows:
        return getattr(workflows[name], "workflow", None)
    else:
        return WorkflowMissing.workflow


class dictproperty(object):

    """Use a dict attribute as a @property.

    This is a minimal descriptor class that creates a proxy object,
    which implements __getitem__, __setitem__ and __delitem__,
    passing requests through to the functions that the user
    provided to the dictproperty constructor.
    """

    class _proxy(object):

        """The proxy object."""

        def __init__(self, obj, fget, fset, fdel):
            """Init the proxy object."""
            self._obj = obj
            self._fget = fget
            self._fset = fset
            self._fdel = fdel

        def __getitem__(self, key):
            """Get value from key."""
            return self._fget(self._obj, key)

        def __setitem__(self, key, value):
            """Set value for key."""
            self._fset(self._obj, key, value)

        def __delitem__(self, key):
            """Delete value for key."""
            self._fdel(self._obj, key)

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        """Init descriptor class."""
        self._fget = fget
        self._fset = fset
        self._fdel = fdel
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        """Return proxy or self."""
        if obj is None:
            return self
        return self._proxy(obj, self._fget, self._fset, self._fdel)


def sort_bwolist(bwolist, iSortCol_0, sSortDir_0):
    """Sort a list of BibWorkflowObjects for DataTables."""
    should_we_reverse = False
    if sSortDir_0 == 'desc':
        should_we_reverse = True
    if iSortCol_0 == 0:
        bwolist.sort(key=lambda x: x.id, reverse=should_we_reverse)
    elif iSortCol_0 == 1:
        bwolist.sort(key=lambda x: x.id, reverse=should_we_reverse)
    elif iSortCol_0 == 2:
        bwolist.sort(key=lambda x: msgpack.loads(cache.get(x.id))["title"], reverse=should_we_reverse)
    elif iSortCol_0 == 3:
        bwolist.sort(key=lambda x: msgpack.loads(cache.get(x.id))["description"], reverse=should_we_reverse)
    elif iSortCol_0 == 4:
        bwolist.sort(key=lambda x: x.created, reverse=should_we_reverse)
    elif iSortCol_0 == 5:
        bwolist.sort(key=lambda x: x.version, reverse=should_we_reverse)
    elif iSortCol_0 == 6:
        bwolist.sort(key=lambda x: x.data_type, reverse=should_we_reverse)
    elif iSortCol_0 == 7:
        bwolist.sort(key=lambda x: x.version, reverse=should_we_reverse)
    elif iSortCol_0 == 8:
        bwolist.sort(key=lambda x: x.version, reverse=should_we_reverse)
    return bwolist


def parse_bwids(bwolist):
    """Use ast to eval a string representing a list."""
    import ast
    return list(ast.literal_eval(bwolist))


def dummy_function(obj, eng):
    """Workflow function not found for workflow."""
    pass


class WorkflowMissing(object):

    """Workflow is missing."""

    workflow = [dummy_function]


class WorkflowBase(object):

    """Base class for workflow.

    Interface to define which functions should be imperatively implemented.
    All workflows should inherit from this class.
    """

    @staticmethod
    def get_title(bwo, **kwargs):
        """Return the value to put in the title column of HoldingPen."""
        return "No title"

    @staticmethod
    def get_description(bwo, **kwargs):
        """Return the value to put in the title  column of HoldingPen."""
        return "No description"

    @staticmethod
    def formatter(obj, **kwargs):
        """Format the object. Not implemented."""
        raise NotImplementedError


def get_holdingpen_objects(ptags=[]):
    """Get BibWorkflowObject's for display in Holding Pen.

    Uses DataTable naming for filtering/sorting. Work in progress.
    """
    from .models import (BibWorkflowObject,
                         ObjectVersion)

    tags_copy = ptags[:]
    version_showing = []
    for i in range(len(tags_copy) - 1, -1, -1):
        if tags_copy[i] in ObjectVersion.MAPPING.values():
            version_showing.append(ObjectVersion.REVERSE_MAPPING[tags_copy[i]])
            del tags_copy[i]

    if version_showing is None:
        version_showing = ObjectVersion.MAPPING.keys()
    ssearch = tags_copy
    bwobject_list = BibWorkflowObject.query.filter(
        BibWorkflowObject.id_parent == None  # noqa E711
    ).filter(not version_showing or BibWorkflowObject.version.in_(
        version_showing)).all()

    if ssearch and ssearch[0]:
        if not isinstance(ssearch, list):
            if "," in ssearch:
                ssearch = ssearch.split(",")
            else:
                ssearch = [ssearch]

        bwobject_list_tmp = []
        for bwo in bwobject_list:
            results = {
                "created": get_pretty_date(bwo),
                "type": get_type(bwo),
                "title": None,
                "description": None
            }
            results.update(get_formatted_holdingpen_object(bwo))

            if check_ssearch_over_data(ssearch, results):
                bwobject_list_tmp.append(bwo)

        bwobject_list = bwobject_list_tmp
    return bwobject_list


def get_versions_from_tags(tags):
    """Return a tuple with versions from tags.

    :param tags: list of tags
    :return: tuple of (versions to show, cleaned tags list)
    """
    from .models import ObjectVersion

    tags_copy = tags[:]
    version_showing = []
    for i in range(len(tags_copy) - 1, -1, -1):
        if tags_copy[i] in ObjectVersion.MAPPING.values():
            version_showing.append(ObjectVersion.REVERSE_MAPPING[tags_copy[i]])
            del tags_copy[i]
    return version_showing, tags_copy


def get_formatted_holdingpen_object(bwo, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """Return the formatted output, from cache if available."""
    results = cache.get(str(bwo.id))
    if results:
        results = msgpack.loads(cache.get(str((bwo.id))))
        if results["date"] == bwo.modified.strftime(date_format):
            return results
    results = generate_formatted_holdingpen_object(bwo)
    cache.set(str(bwo.id), msgpack.dumps(results))
    return results


def generate_formatted_holdingpen_object(bwo, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """Generate a dict with formatted column data from Holding Pen object."""
    workflows_name = bwo.get_workflow_name()

    if workflows_name and hasattr(workflows[workflows_name], 'get_description'):
        workflow_definition = workflows[workflows_name]
    else:
        workflow_definition = WorkflowBase

    results = {
        "name": workflows_name,
        "description": workflow_definition.get_description(bwo),
        "title": workflow_definition.get_title(bwo),
        "date": bwo.modified.strftime(date_format)
    }
    return results


def check_ssearch_over_data(ssearch, data):
    """Check for DataTables search request.

    Checks if the data match with one of the search tags in data.

    :param ssearch: list of tags used for filtering.
    :param data: data to check.

    :return: True if present, False otherwise.
    """
    total = 0
    for terms in ssearch:
        for datum in data:
            if data[datum] and terms.lower() in data[datum].lower():
                total += 1
                break
    return total == len(ssearch)


def get_pretty_date(bwo):
    """Get the pretty date from bwo.created."""
    from invenio.utils.date import pretty_date
    return pretty_date(bwo.created)


def get_type(bwo):
    """Get the type of the Object."""
    return bwo.data_type


def get_info(bwobject):
    """Parse the hpobject and extracts its info to a dictionary."""
    info = {}
    if bwobject.get_extra_data()['owner'] != {}:
        info['owner'] = bwobject.get_extra_data()['owner']
    else:
        info['owner'] = 'None'
    info['parent id'] = bwobject.id_parent
    info['workflow id'] = bwobject.id_workflow
    info['object id'] = bwobject.id
    info['action'] = bwobject.get_action()
    return info


def extract_data(bwobject):
    """Extract needed metadata from BibWorkflowObject.

    Used for rendering the Record's holdingpen table row and
    details and action page.
    """
    from .models import (BibWorkflowObject,
                         Workflow)
    extracted_data = {}
    if bwobject.id_parent is not None:
        extracted_data['bwparent'] = \
            BibWorkflowObject.query.get(bwobject.id_parent)
    else:
        extracted_data['bwparent'] = None

    # TODO: read the logstuff from the db
    extracted_data['loginfo'] = ""
    extracted_data['logtext'] = {}

    for log in extracted_data['loginfo']:
        extracted_data['logtext'][log.get_extra_data()['_last_task_name']] = \
            log.message

    extracted_data['info'] = get_info(bwobject)
    try:
        extracted_data['info']['action'] = bwobject.get_action()
    except (KeyError, AttributeError):
        pass

    extracted_data['w_metadata'] = \
        Workflow.query.filter(Workflow.uuid == bwobject.id_workflow).first()
    if extracted_data['w_metadata']:
        workflow_def = get_workflow_definition(extracted_data['w_metadata'].name)
        extracted_data['workflow_func'] = workflow_def
    else:
        extracted_data['workflow_func'] = [None]
    return extracted_data


def get_action_list(object_list):
    """Return a dict of action names mapped to halted objects.

    Get a dictionary mapping from action name to number of Pending
    actions (i.e. halted objects). Used in the holdingpen.index page.
    """
    from .registry import actions

    action_dict = {}
    found_actions = []

    # First get a list of all to count up later
    for bwo in object_list:
        action_name = bwo.get_action()
        if action_name is not None:
            found_actions.append(action_name)

    # Get "real" action name only once per action
    for action_name in set(found_actions):
        if action_name not in actions:
            # Perhaps some old action? Use stored name.
            action_nicename = action_name
        else:
            action = actions[action_name]
            action_nicename = getattr(action, "name", action_name)
        action_dict[action_nicename] = found_actions.count(action_name)
    return action_dict
