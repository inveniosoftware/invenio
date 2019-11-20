..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Integrity checks
================

`Invenio-Files-REST <https://invenio-files-rest.readthedocs.io/>`_ provides
Celery task-based mechanism for ensuring files integrity. It consists of two
dedicated functions (Celery tasks) in :py:mod:`invenio_files_rest.tasks`.

Main task ``invenio_files_rest.tasks.schedule_checksum_verification`` should be
periodically called through `celery beat <https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#id1>`_
and will run integrity checks ``invenio_files_rest.tasks.verify_checksum`` on
the files.

Configuration
-------------

First, you need to `start the celery beat service
<https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#starting-the-scheduler>`_:

.. code-block:: console

    $ celery -A proj beat

Once celery beat service is running, you need to define a task for it in your
application's ``config.py``.

.. code-block:: python

    CELERY_BEAT_SCHEDULE = {
        'file-checks': {
           'task': 'invenio_files_rest.tasks.schedule_checksum_verification',
           'schedule': timedelta(hours=1),
        }
    }


Once ``celerybeat`` is executing
``invenio_files_rest.tasks.schedule_checksum_verification``
task, it schedules a subtask ``invenio_files_rest.tasks.verify_checksum``
for every present file in order to ensure it's integrity by verifying the checksum.

We suggest scheduling these tasks on a separate low priority queue.

.. console::

    $ celery -A proj worker -l info -Q low

And assign these tasks to queue - `low` by adding the following lines in your
`config.py`.

.. code-block:: python

    CELERY_TASK_ROUTES = {
        'invenio_files_rest.tasks.verify_checksum': {'queue': 'low'},
    }
