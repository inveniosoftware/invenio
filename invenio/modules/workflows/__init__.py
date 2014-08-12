# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
r"""
Create a workflow for your data using functions as individual tasks.

This module allows you to easily push your data through a determined set of tasks
and stop/continue execution if necessary.

.. sidebar:: Holding Pen

    Holding Pen (:py:mod:`.views.holdingpen`) is a web interface displaying
    all the data objects that ran through a workflow.

    Here you can interact with the workflows and data directly via a GUI.

Create a workflow
-----------------

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


Create tasks
------------

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
^^^^^^^^^^^^^^^^^^^^^^^^^

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


Run it
------

Finally, to run your workflow you there are mainly two use-cases:

    * run only a **single data object**, or
    * run **multiple data objects** through a workflow.

The former use the :py:class:`.models.BibWorkflowObject` model API, and
the latter use the :py:mod:`.api`.

Single object
^^^^^^^^^^^^^

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


Multiple objects
^^^^^^^^^^^^^^^^

.. note:: This method is recommended if you need to run several objects through a workflow.

To do this simply import the workflows API function `start()` and provide
a list of objects:

.. code-block:: python

    from invenio.modules.workflows.api import start
    eng = start(workflow_name="myworkflow", data=[5, 10])

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

You can also query the engine instance to only give you the completed, halted
or initial objects.

.. code-block:: python

    len(eng.initial_objects)  # outputs: 2

    len(eng.halted_objects)  # outputs: 2

    len(eng.completed_objects)  # outputs: 0

(`eng.completed_objects` is empty because both objects passed is halted.)

For example, to retrieve the data from the first object, you can use
`get_data()` as with single objects:

.. code-block:: python

    res = halted_objects[0].get_data()
    print res
    # outputs: 25

Run asynchronously
------------------

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
^^^^^^^
A worker is a plugin (or bridge) from the Invenio workflows module to some
distributed task queue. By default, we have provided workers for `Celery`_ and
`RQ`_.

These plugins are used by the :py:mod:`.worker_engine` to launch as task in
the task queue.


Additional features
-------------------

Add extra data
^^^^^^^^^^^^^^

If you need to add some additional data to the :py:class:`.models.BibWorkflowObject` that is
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
        "source": ""
    }

This information is used by the :py:class:`.models.BibWorkflowObject` to store some additional
data related to the workflow execution and additional data added by tasks. There
are two important concepts related to this: actions and task results.

Actions in Holding Pen
^^^^^^^^^^^^^^^^^^^^^^

Actions are simple GUI components that can be assigned to data objects for use
in Holding Pen. For example, it can be adding a GUI component for accepting or
rejecting a data object.

These actions consists of both a Python back-end and a front-end (jinja templates
+ JavaScript/CSS).

By default we have added an approval action which can be used to allow a data object
to continue the workflow or be deleted.

`workflows/actions/approval.py`
    Action back-end located in ``workflows/actions/approval.py`` that implements
    ``render()``, ``render_mini()`` and ``resolve()``. ``resolve()`` handles the
    continuation or deletion of the data object.

`templates/workflows/actions/approval_(main|mini|side).html`
    jinja templates used to render the action UI. There are different templates
    in play here depending on position.

        * `mini`: displayed in the main table (for quick action).
        * `side`: displayed on the right side of the object details page.
        * `main`: displayed in the middle of the object details page.

`static/workflows/actions/approval.js`
    JavaScript file listening to events in the approval UI to call the backend
    via ajax calls.


There are two ways of activating an action:

    * **When halting a workflow:** :py:meth:`.engine.BibWorkflowEngine.halt` has
      a parameter that allows you to set an action that needs to be taken in
      the Holding Pen - along with a message to be displayed.


    * **Using the :py:class:`.models.BibWorkflowObject` API**. :py:meth:`.models.BibWorkflowObject.set_action`
      :py:meth:`.models.BibWorkflowObject.remove_action` :py:meth:`.models.BibWorkflowObject.get_action`.


Display results in Holding Pen
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to add some special task results to be displayed in the Holding Pen, you
can use the task results API available in :py:class:`.models.BibWorkflowObject`.

The API provides functions to manipulate the task results:

:py:meth:`.models.BibWorkflowObject.add_task_result`
    Adds a task result to the end of a list associated with a label (name).

:py:meth:`.models.BibWorkflowObject.update_task_results`
    Update task result for a specific label (name).

:py:meth:`.models.BibWorkflowObject.get_tasks_results`
    Return all tasks results as a dictionary as ``{ name: [result, ..] }``


.. _workflows-module: https://pypi.python.org/pypi/workflow/1.01
.. _Celery: http://www.celeryproject.org/
.. _RQ: http://python-rq.org/
"""
