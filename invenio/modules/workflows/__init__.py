# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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
r"""
This module allows you to easily push your data through a determined set of tasks
and stop/continue execution if necessary.

.. sidebar:: Holding Pen

    Holding Pen (:py:mod:`.views.holdingpen`) is a web interface displaying
    all the data objects that ran through a workflow.

    Here you can interact with the workflows and data directly via a GUI.


=================
Create a workflow
=================

Create a workflow for your data using functions as individual tasks.

.. code-block:: python

    from invenio.modules.workflows.tasks.sample_tasks import (
        add_data,
        halt_if_higher_than_20,
    )

    class myworkflow(object):
        \"\"\"Add 20 to integer and halt if higher.\"\"\"
        workflow = [add_data(20),
                    halt_if_higher_than_20]


Save it as a new file in your module located under `workflows/` with the same
name as the class. For example at `yourmodule/workflows/myworkflow.py`.

The `workflow` attribute should be a list of functions
(or list of lists of tasks) as per the conditions of the
underlying `workflows-module`_.

.. sidebar:: Naming things
    :subtitle: A valid workflow must:

    (a) Have matching class name and file-name or (b) map the class
    name using ``__all__ = ["myname"]`` notation.

    The workflows registry will make sure pick up any files under `workflows/`.


=============
Create a task
=============


The functions in the workflow are called tasks. Each task must *at least*
take two arguments:

.. code-block:: python

    def halt_if_higher_than_20(obj, eng):
        \"\"\"Check if current data is more than than 20.\"\"\"
        if obj.data > 20:
            eng.halt("Data higher than 20.")


`obj` (:py:class:`.models.BibWorkflowObject`)
    *is the current object being worked on*

    `obj` adds extra functionality by wrapping around your data and
    provide utilities to interface with the Holding Pen interface.

`eng` (:py:class:`.engine.BibWorkflowEngine`)
    *is the current instance of the workflow engine*

    `eng` give you access to manipulating the workflow execution itself and
    to retrieve all the objects being processed.

Other parameters may be passed as `*args` or `**kwargs`.

Pass additional arguments
=========================

To allow arguments being passed to the task from the workflow definition,
simply wrap your task in a closure:

.. code-block:: python

    def add_data(data_param):
        \"\"\"Add data_param to the obj.data.\"\"\"
        def _add_data(obj, eng):
            data = data_param
            obj.data += data

        return _add_data

It can then be called from the workflow definition as `add_data(20)`,
returning the inner function.


==============
Run a workflow
==============

Finally, to run your workflow you there are mainly two use-cases:

    * run only a **single data object**, or
    * run **multiple data objects** through a workflow.

The former use the :py:class:`.models.BibWorkflowObject` model API, and
the latter use the :py:mod:`.api`.

Run a single data object
========================

.. note:: This method is recommended if you only have one data
    item you want to run through the workflow.

.. code-block:: python

    from invenio.modules.workflows.models import BibWorkflowObject
    myobj = BibWorkflowObject.create_object()
    myobj.set_data(10)
    eng = myobj.start_workflow("myworkflow")


Once the workflow completes it will return the engine instance that ran it.

To get the data, simply call the `get_data()` function of
:py:class:`.models.BibWorkflowObject`

.. code-block:: python

    myobj.get_data()  # outputs: 30


Run multiple data objects
=========================

.. note:: This method is recommended if you need to run several objects through a workflow.

To do this simply import the workflows API function `start()` and provide
a list of objects:

.. code-block:: python

    from invenio.modules.workflows.api import start
    eng = start(workflow_name="myworkflow", data=[5, 10])

*Here we are passing simple data objects in form integers.*

As usual, the `start()` function returns the `eng` instance that ran the
workflow. You can query this object to retrieve the data you sent in:

.. code-block:: python

    len(eng.objects)  # outputs: 4

Why 4 objects when we only shipped 2 objects? Well, we take initial snapshots
(copy of BibWorkflowObject) of the original data. In the example above,
we get 4 objects back as each object passed have a snapshot created.

.. sidebar:: Object versions and YOU

    The data you pass to the workflows API is wrapped in a BibWorkflowObject.

    This object have a `version` property which tells you the state of object.
    For example, if the object is currently *halted* in the middle of a
    workflow, or if it is an *initial* object.

    *initial* objects are basically snapshots of the BibWorkflowObject just
    before the workflow started. These are created to allow for objects to
    be easily restarted in the workflow with the initial data intact.

You can also query the engine instance to only give you the objects which are in
a certain state.

.. code-block:: python

    len(eng.initial_objects)  # outputs: 2

    len(eng.halted_objects)  # outputs: 2

    len(eng.completed_objects)  # outputs: 0

    len(eng.running_objects)  # outputs: 0

    len(eng.waiting_objects)  # outputs: 0

    len(eng.error_objects)  # outputs: 0

(`eng.completed_objects` is empty because both objects passed is halted.)

This output is actually representative of snapshots of the objects, not the
objects themselves. The _default_ snapshotting behaviour is also evident here:
There is one snapshot taken in the beginning of the execution and one
when the object reaches one of the other states. A snapshot can only be in a
single state.

No object will ever be in the `running` state under usual operation.

Moreover, to retrieve the data from the first object, you can use
`get_data()` as with single objects:

.. code-block:: python

    res = halted_objects[0].get_data()
    print res
    # outputs: 25

Run workflows asynchronously
============================

So far we have in been running our workflows in the current process. However,
for long running processes we do not want to wait for the workflow to finish
before continuing the processing.

Luckily, there is API to do this:

`BibWorkflowObject.start_workflow(delayed=True)`
    as when running single objects, you can pass the delayed parameter to
    enable asynchronous execution.

`api.start_delayed()`
    The API provide this function `start_delayed()` to run a workflow
    asynchronously.

To use this functionality you need to make sure you are running a task queue
such as `Celery`_ that will run the workflow in a separate process.

.. note:: The delayed API returns a :py:class:`.worker_result.AsynchronousResultWrapper`
    instead of a :py:class:`.engine.BibWorkflowEngine` instance.

In order to communicate with such a task queue we make use of *worker plugins*.

Workers
=======
A worker is a plugin (or bridge) from the Invenio workflows module to some
distributed task queue. By default, we have provided workers for `Celery`_ and
`RQ`_.

These plugins are used by the :py:mod:`.worker_engine` to launch workflows
asynchronously in a task queue.

*We recommend to use Celery as the default asynchronous worker.*


Working with extra data
=======================

If you need to add some extra data to the :py:class:`.models.BibWorkflowObject` that is
not suitable to add to the ``obj.data`` attribute, you can make use if the
``obj.extra_data`` attribute.

The extra_data attribute is basically a normal dictionary that you can fill. However
it contains some additional information by default.

.. code-block:: python

    {
        "_tasks_results": {},
        "owner": {},
        "_task_counter": {},
        "_error_msg": None,
        "_last_task_name": "",
        "latest_object": -1,
        "_action": None,
        "redis_search": {},
        "source": "",
        "_task_history: [],
    }

This information is used by the :py:class:`.models.BibWorkflowObject` to store some additional
data related to the workflow execution and additional data added by tasks.

It also stores information that is integrated with Holding Pen - the graphical interface
for all the data objects.

===========
Holding Pen
===========

The graphical interface over all the data objects that have been executed in a workflow.

The name *Holding Pen* originates from a library use case of having some incoming bibliographical
meta-data records on "hold" - awaiting some human curator to analyze the record and decide if
the record should be inserted into the repository.

One common usage of this interface is acceptance of user submissions.

We will take this concept of record approval further throughout this guide as we explain the
most common use cases for the Holding Pen.

.. note:: The Holding Pen is accessible under `/admin/holdingpen`


Data object display in Holding Pen
==================================

To properly represent a data objects in the Holding Pen, the workflow definition
explained above can be further enriched by adding some static functions to the class.

    * `get_title`: return the "title" of the data object shown in the table display.
       E.g. title of meta-data record
    * `get_description`: return a short desciption of the data object shown in the table display.
       E.g. identifiers and categories
    * `formatter`: used in the object detailed display to render the data in the object for the user.
       E.g. the detailed record format of a meta-data record.


Actions in Holding Pen
======================

An action in Holding Pen is a generic term describing an action that can be taken
on a data object.

To use the example of record approval, we basically mean adding GUI buttons to
accept or reject a data object. The action taken (the button pressed) on the data object
is then connected to a custom action back-end that may then decide to
e.g. continue the workflow or simply delete the object.

.. sidebar:: Approval action

    In our example of the *approval action* we will make use of front-end assets
    (JavaScript/HTML/templates) to display and listen to events on buttons and
    a Python back-end plugin to react on the chosen action.


Adding an action
----------------

By default we have added an approval action which can be used to allow a data object
to continue the workflow or be deleted.

`workflows/actions/approval.py`
    Action back-end located in ``workflows/actions/approval.py`` that implements
    ``render()``, ``render_mini()`` and ``resolve()``. ``resolve()`` handles the
    continuation or deletion of the data object using the workflows API.

`templates/workflows/actions/approval_(main|mini|side).html`
    jinja templates used to render the action UI. There are different templates
    in play here depending on position.

        * `mini`: displayed in the main table (for a quick action).
        * `side`: displayed on the right side of the object details page.
        * `main`: displayed in the middle of the object details page.

`static/workflows/actions/approval.js`
    JavaScript file listening to events in the approval UI to call the backend
    via ajax calls.

To enable the JavaScript to be loaded via requireJS, you need to override the
actions "init" JavaScript file `static/workflows/actions/init.js` on your overlay
and add any initialization code for the action (e.g. attaching events).

Using an action
---------------

There are two ways of activating an action:

    * **When halting a workflow:** :py:meth:`.engine.BibWorkflowEngine.halt` has
      a parameter that allows you to set an action that needs to be taken in
      the Holding Pen - along with a message to be displayed.

    * **Directly using the :py:class:`.models.BibWorkflowObject` API**. :py:meth:`.models.BibWorkflowObject.set_action`
      :py:meth:`.models.BibWorkflowObject.remove_action` :py:meth:`.models.BibWorkflowObject.get_action`.


Task results in Holding Pen
===========================

If you want to add some special task results to be displayed on the details page
of the data object in Holding Pen, you can use the task results API available
in :py:class:`.models.BibWorkflowObject`.

The API provides functions to manipulate the task results:

:py:meth:`.models.BibWorkflowObject.add_task_result`
    Adds a task result to the end of a list associated with a label (name).

:py:meth:`.models.BibWorkflowObject.update_task_results`
    Update task result for a specific label (name).

:py:meth:`.models.BibWorkflowObject.get_tasks_results`
    Return all tasks results as a dictionary as ``{ name: [result, ..] }``


The *task result* is a dictionary given as context to the template
when rendered. The result given here is added to a list of results
for this name.

.. code-block:: python

        obj = BibWorkflowObject()  # or BibWorkflowObject.query.get(id)
        obj.add_task_result("foo", my_result, "path/to/template")

See sample templates under `templates/workflows/results/*.html`.


.. _workflows-module: https://pypi.python.org/pypi/workflow/1.01
.. _Celery: http://www.celeryproject.org/
.. _RQ: http://python-rq.org/
"""
