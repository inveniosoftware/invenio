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
"""
Create a workflow for your data using functions as individual tasks. This
module allows you to easily push your data through a determined set of tasks
and stop/continue execution if necessary.


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

.. sidebar:: Naming things
    :subtitle: A valid workflow must:

    (a) Have matching class name and file-name or (b) map the class
    name using ``__all__ = ["myname"]`` notation.

    The workflows registry will make sure pick up any files under `workflows/`.

Save it as a new file in your module located under `workflows/` with the same
name as the class. For example at `yourmodule/workflows/myworkflow.py`.

The `workflow` attribute should be a list of functions
(or list of lists of tasks) as per the conditions of the
underlying `workflows-module`_.

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

Run workflows
-------------

Finally, to run your workflow you there are mainly two use-cases. Run only one
object through a workflow, or run several workflows. The former use the
:py:class:`.models.BibWorkflowObject` model API, and the latter use the
:py:mod:`.api` API.

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

    myobj.get_data()
    # outputs: 30


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

    len(eng.objects)
    # outputs: 4

Why 4 objects when we only shipped 2 objects?

.. topic:: Object versions and YOU

    The data you pass to the workflows API is wrapped in a BibWorkflowObject.

    This object have a `version` property which tells you the state of object.
    For example, if the object is currently *halted* in the middle of a
    workflow, or if it is an *initial* object.

    *initial* objects are basically snapshots of the BibWorkflowObject just
    before the workflow started. These are created to allow for objects to
    be easily restarted in the workflow with the initial data intact.

    In the example above, we get 4 objects back as each object passed have
    a snapshot created.

You can also query the engine instance to only give you the completed, halted
or initial objects.

.. code-block:: python

    len(eng.initial_objects)
    # outputs: 2

    len(eng.halted_objects)
    # outputs: 2

    len(eng.completed_objects)
    # outputs: 0

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
before continuing.

Luckily, there is API to do this:

`BibWorkflowObject.start_workflow(delayed=True)`
    as when running single objects, you can pass the delayed parameter to
    enable asynchronous execution.

`api.start_delayed()`
    The API provide this function `start_delayed()` to run a workflow
    asynchronously.


.. _workflows-module: https://pypi.python.org/pypi/workflow/1.01

"""
