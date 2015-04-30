# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Various utility functions for use across the workflows module."""

import msgpack

from flask import current_app, jsonify
from functools import wraps
from six import text_type

from invenio.base.helpers import unicodifier
from invenio.ext.cache import cache

from .registry import workflows


def convert_marcxml_to_bibfield(marcxml, model=None):
    """Return a SmartJson representation of MARC XML string.

    This function converts a MARCXML string to a JSON-like
    dictionary using the the jsonalchemy (aka. BibField) config.

    :param marcxml: MARCXML string to parse
    :type marcxml: string

    :return: SmartJson object.
    """
    from invenio.modules.jsonalchemy.reader import Reader
    from invenio.modules.jsonalchemy.wrappers import SmartJson

    if not model:
        model = ["__default__"]

    if isinstance(marcxml, text_type):
        marcxml = marcxml.encode(errors='ignore')
    return Reader.translate(marcxml,
                            SmartJson,
                            master_format='marc',
                            namespace='recordext',
                            model=model)


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
        from .models import BibWorkflowObject

        if self.id is not None:
            return BibWorkflowObject.query.filter(
                BibWorkflowObject.id == self.id
            ).one()
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


def get_workflow_definition(name):
    """Try to load the given workflow from the system."""
    if name in workflows:
        return getattr(workflows[name], "workflow", None)
    else:
        from .definitions import WorkflowMissing
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


def _sort_from_cache(name):
    def _sorter(item):
        try:
            results = cache.get("workflows_holdingpen_{0}".format(item.id))
            if results:
                return msgpack.loads(results)[name]
        except Exception:
            current_app.logger.exception(
                "Invalid format for object {0}: {1}".format(
                    item.id,
                    cache.get("workflows_holdingpen_{0}".format(item.id))
                )
            )
    return _sorter


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
        bwolist.sort(key=_sort_from_cache("title"), reverse=should_we_reverse)
    elif iSortCol_0 == 3:
        bwolist.sort(key=_sort_from_cache("description"), reverse=should_we_reverse)
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


def get_holdingpen_objects(ptags=None):
    """Get BibWorkflowObject's for display in Holding Pen.

    Uses DataTable naming for filtering/sorting. Work in progress.
    """
    from .models import (BibWorkflowObject,
                         ObjectVersion)

    if ptags is None:
        ptags = ObjectVersion.name_from_version(ObjectVersion.HALTED)

    tags_copy = ptags[:]
    version_showing = []
    for tag in ptags:
        if tag in ObjectVersion.MAPPING:
            version_showing.append(ObjectVersion.MAPPING[tag])
            tags_copy.remove(tag)

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

            if check_term_in_data(ssearch, results):
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
        if tags_copy[i] in ObjectVersion.MAPPING:
            version_showing.append(ObjectVersion.MAPPING[tags_copy[i]])
            del tags_copy[i]
    return version_showing, tags_copy


def get_formatted_holdingpen_object(bwo, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """Return the formatted output, from cache if available."""
    results = cache.get("workflows_holdingpen_{0}".format(bwo.id))
    if results:
        results = msgpack.loads(cache.get("workflows_holdingpen_{0}".format(bwo.id)))
        if results["date"] == bwo.modified.strftime(date_format):
            return results
    results = generate_formatted_holdingpen_object(bwo)
    if results:
        cache.set("workflows_holdingpen_{0}".format(bwo.id), msgpack.dumps(results))
    return results


def generate_formatted_holdingpen_object(bwo, date_format='%Y-%m-%d %H:%M:%S.%f'):
    """Generate a dict with formatted column data from Holding Pen object."""
    from .definitions import WorkflowBase

    workflows_name = bwo.get_workflow_name()

    if workflows_name and workflows_name in workflows and \
       hasattr(workflows[workflows_name], 'get_description'):
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


def check_term_in_data(term_list, data):
    """Check each term if present in data dictionary values.

    :param term_list: list of tags used for filtering.
    :type term_list: list

    :param data: data to check.
    :type data: dict

    :return: True if all terms present, False otherwise.
    """
    total = 0
    for term in term_list:
        term = term.encode("utf-8")
        for datum in data.values():
            if datum and term.lower() in datum.lower():
                total += 1
                break
    return total == len(term_list)


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
        extracted_data['workflow_func'] = []
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


def get_rendered_task_results(obj):
    """Return a list of rendered results from BibWorkflowObject task results."""
    from flask import render_template

    results = {}
    for name, res in obj.get_tasks_results().items():
        for result in res:
            results[name] = render_template(
                result.get("template", "workflows/results/default.html"),
                results=result,
                obj=obj
            )
    return results


def get_previous_next_objects(object_list, current_object_id):
    """Return tuple of (previous, next) object for given Holding Pen object."""
    if not object_list:
        return None, None
    try:
        current_index = object_list.index(current_object_id)
    except ValueError:
        # current_object_id not in object_list:
        return None, None
    try:
        next_object_id = object_list[current_index + 1]
    except IndexError:
        next_object_id = None
    try:
        if current_index == 0:
            previous_object_id = None
        else:
            previous_object_id = object_list[current_index - 1]
    except IndexError:
        previous_object_id = None
    return previous_object_id, next_object_id


def get_task_history(last_task):
    """Append last task to task history."""
    if hasattr(last_task, 'branch') and last_task.branch:
        return
    elif hasattr(last_task, 'hide') and last_task.hide:
        return
    else:
        return get_func_info(last_task)


def get_func_info(func):
    """Retrieve a function's information."""
    name = func.func_name
    doc = func.func_doc or ""
    try:
        nicename = func.description
    except AttributeError:
        if doc:
            nicename = doc.split('\n')[0]
            if len(nicename) > 80:
                nicename = name
        else:
            nicename = name
    parameters = []
    closure = func.func_closure
    varnames = func.func_code.co_freevars
    if closure:
        for index, arg in enumerate(closure):
            if not callable(arg.cell_contents):
                parameters.append((varnames[index], arg.cell_contents))
    return unicodifier({
        "nicename": nicename,
        "doc": doc,
        "parameters": parameters,
        "name": name
    })


def get_workflow_info(func_list):
    """Return function info, go through lists recursively."""
    funcs = []
    for item in func_list:
        if isinstance(item, list):
            funcs.append(get_workflow_info(item))
        else:
            funcs.append(get_func_info(item))
    return funcs


def alert_response_wrapper(func):
    """Wrap given function with wrapper to return JSON for alerts."""
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            current_app.logger.exception(error)
            return jsonify({
                "category": "danger",
                "message": "Error: {0}".format(error)
            })
    return inner
