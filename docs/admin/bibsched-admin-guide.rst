..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _bibsched-admin-guide:

BibSched Admin Guide
====================

Overview
--------

BibSched -- the bibliographic task scheduler -- is central unit of the
system that allows all other modules to access the bibliographic
database in a controlled manner, preventing sharing violation threats
and assuring the coherent execution of the database update tasks. The
module comes with an administrative interface that allows to monitor the
task queue including various possibilities of a manual intervention, for
example to re-schedule queued tasks, change the task order, etc.

You can run the administrative interface by doing:

    ::

        $ bibsched

Note that in general you should run bibsched with the same rights of the
Apache user of your system.

The ``bibsched`` can run in two modes: *automatic* and *manual*. In the
automatic mode, it will execute tasks automatically as they arrive in
the waiting queue. In the manual mode, the administrator has to launch
the tasks manually.

Bibsched graphical interface
----------------------------

bibsched interface is text mode graphical interface to display running
tasks. It has three views, one for listing done tasks, one for
scheduled/running/failed tasks and a third one for displaying archived
tasks. You can switch among these three views by pressing respectively
"``1``\ ", "``2``\ " or "``3``\ ".

With the harrows you can move from one task to the other

By pressing "``O``\ " you can see all the details of the selected task

If the task is running or is already run, you can press "l" (lower case
"``l``\ ") to access the standard output produced by the task, if any.
You can press "``L``\ " (upper case "``L``\ ") to access the standard
error produced by the task, if any.

By pressing "``P``\ " you can clean the list of DONE tasks and
archive/delete them.

By pressing "``Q``\ " you can Quit the interface.

By pressing "``A``\ " you can switch from Auto to Manual mode and
viceversa.

Manual mode
~~~~~~~~~~~

In manual mode, depending on the status of the task you are currently
selecting you're given different actions.

You can press "``R``\ " for running Waiting tasks

You can press "``D``\ " for deleting non running tasks

You can press "``N``\ " for changing the priority of a waiting task.
(the equivalent of the UNIX renice command)

On a running task you can press "``K``\ " to kill the task immediately
in case of emergency. "``T``\ " for stopping it cleanly. "``S``\ " for
putting it temporarily to sleep. A sleeping task can be waken up by
pressing "``W``\ ". Note that for stopping or putting to sleep a task, a
signal is sent to the given bibtask and this, in turn, will acknowledge
it and decide to stop or go to sleep whenever it thinks it's safe.

On a failed task you can press "``K``\ " the acknowledge the error. This
is necessary in case you wish to put bibsched back to automatic mode.

Automatic mode
~~~~~~~~~~~~~~

In automatic mode bibsched will take care of launching tasks based on
their priority and runtime schedule. The available option are only those
that allow you to query a given task (see the logs and the options).

If you have configured bibsched to allow for the execution of concurrent
bibtasks, bibsched will take care of launching compatible tasks
concurrently (note that this feature is currently experimental).
Bibupload tasks will always be executed in the chronological order (to
preserve input consistency).

Bibsched maintenance
--------------------

bibsched produce two log files. bibsched.log and bibsched.err, located
under the usual log directory of your Invenio installation. The former
will contain all the actions (either automatic of manual) that bibsched
has performed. The latter will contain all the exceptional errors.

In case of a bibtask failing while bibsched is in automatic mode,
bibsched will stop by switching to manual mode, and will send an email
to the administrator (and an emergency SMS in case it is configured to
do so). Note that in case of failed bibtasks, bibsched will refuse to be
put back to automatic mode, until either the task is reinitialized, or
deleted or the error is acknowledged.

Priorities
----------

A task can be scheduled with a given *priority*, represented by an
integer number. When at a given time two or more tasks might be
executed, the task with higher priority will be executed first.

When a task is running and is not a bibupload, the scheduler will allow
to run higher priority tasks that don't conflict with the former task,
by first putting to sleep the former task, if the resources are not
enough.

If a task has priority higher than 100 and there are currently other
task running, conflicting with the execution of this task (because the
other tasks should not run concurrently with this task), then the other
tasks are stopped (unless they are bibuploads).

If the priority is less than -10 than the task will never be executed
automatically.

Bibupload tasks are not affected by priority with respect to each other
and will always be executed in the proper order.

Task logging
------------

When executed each tasks will produced (if necessary) a couple of log
files. One called ``bibsched_task_{task_id}.log`` and the other
``bibsched_task_{task_id}.err``. In case of reschedulable task, each
time the task is rescheduled it is being assigned the same task\_id.
That means that log information of successive execution of the given
task will be appended at the end of already existing log files.

A log-rotation algorithm is applied when writing into the log file. By
default each log will be no bigger than 1MB. After this limit is reached
the log is rotated. Note that when viewing the log file inside the
bibsched monitor interface, only the latest log will be displayed.

Task concurrency
----------------

A recent experimental feature of bibsched is the concurrent execution of
compatible tasks. The current definition of when two tasks are
considered compatible is: "If a two tasks have the same name (e.g.
bibupload) then they're incompatible."

Sometimes you might want to consider compatible two tasks even when they
have the same name. For this you can add a name specification via the
bibtask command line option ``--name``. E.g. you might want to
distinguish a generic bibupload from a bibupload carrying only
preformatting information. For this just launch bibupload -N
"bibformat", and it will be considered compatible with all the other
bibuploads.

Configuration
-------------

Bibsched can be tweaked by adjusting some variables in the usual
``invenio(-local).conf`` file. Please refer to the documentation
associated with each variable inside this file.

Bibsched command line interface
-------------------------------

::

        Usage: /opt/invenio/bin/bibsched [options] [start|stop|restart|monitor|status]

        The following commands are available for bibsched:

        start      start bibsched in background
        stop       stop running bibtasks and the bibsched daemon safely
        halt       halt running bibsched while keeping bibtasks running
        restart    restart a running bibsched
        monitor    enter the interactive monitor
        status     get report about current status of the queue
        purge      purge the scheduler queue from old tasks

        Command options:
        -d, --daemon           Launch BibSched in the daemon mode (deprecated, use 'start')
        General options:
        -h, --help             Print this help.
        -V, --version          Print version information.
        Status options:
        -s, --status=LIST      Which BibTask status should be considered (default is Running,waiting)
        -S, --since=TIME       Since how long time to consider tasks e.g.: 30m, 2h, 1d (default
        is all)
        -t, --tasks=LIST       Comma separated list of BibTask to consider (default
        is all)
        Purge options:
        -s, --status=LIST      Which BibTask status should be considered (default is DONE)
        -S, --since=TIME       Since how long time to consider tasks e.g.: 30m, 2h, 1d (default
        is 30 days)
        -t, --tasks=LIST       Comma separated list of BibTask to consider (default
        is bibindex,bibreformat,webcoll,bibrank,inveniogc,bibupload,oairepositoryupdater)

Bibtasks command line interface
-------------------------------

Each bibtask has a common command interface in addition to the proper
bibtask related options.

::

      Scheduling options:
      -u, --user=USER       User name under which to submit this task.
      -t, --runtime=TIME    Time to execute the task. [default=now]
                            Examples: +15s, 5m, 3h, 2002-10-27 13:57:26.
      -s, --sleeptime=SLEEP Sleeping frequency after which to repeat the task.
                            Examples: 30m, 2h, 1d. [default=no]
      --fixed-time          Avoid drifting of execution time when using --sleeptime
      -I, --sequence-id=SEQUENCE-ID Sequence Id of the current process
      -L  --limit=LIMIT     Time limit when it is allowed to execute the task.
                            Examples: 22:00-03:00, Sunday 01:00-05:00.
                            Syntax: [Wee[kday]] [hh[:mm][-hh[:mm]]].
      -P, --priority=PRI    Task priority (0=default, 1=higher, etc).
      -N, --name=NAME       Task specific name (advanced option).

      General options:
      -h, --help            Print this help.
      -V, --version         Print version information.
      -v, --verbose=LEVEL   Verbose level (0=min, 1=default, 9=max).
      --profile=STATS       Print profile information. STATS is a comma-separated
                            list of desired output stats (calls, cumulative,
                            file, line, module, name, nfl, pcalls, stdname, time).
      --stop-on-error       In case of unrecoverable error stop the bibsched queue.
      --continue-on-error   In case of unrecoverable error don't stop the bibsched queue.
      --post-process=BIB_TASKLET_NAME[parameters]   Postprocesses the specified
                            bibtasklet with the given parameters between square
                            brackets.
                            Example:--post-process "bst_send_email[fromaddr=
                            'foo@xxx.com', toaddr='bar@xxx.com', subject='hello',
                            content='help']"

BibSched Tasklets
-----------------

If you have very particular needs to write your self a bibtask that can
be scheduled through the bibliographic scheduler, and you are able to
write a Python function you can write a **BibTaskLet**

Suppose that you have Python function:

::

    def foo(arg1, arg2='default'):
        pass

that you want to execute through the bibliographic scheduler. Just put
such a function in the
``/opt/cds-invenio/lib/python/invenio/bibsched_tasklets`` in a file
called e.g. ``bst_foo.py`` (the *bst\_* prefix and the *.py* extension
are compulsory) and rename the function to ``bst_foo`` (the name of the
function must be identical to the name of the file).

A BibTaskLet can be executed through the ``bibtasklet`` BibTask. E.g.:

::

    $ # To list the available bibtasklets
    $ sudo -u apache /opt/cds-invenio/bin/bibtasklet -l
    Available tasklets:


    ╔══════════════════════════════════════════════════════════════════╗
    ║ def bst_fibonacci(n=30)                                          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║     Small tasklets that prints the the Fibonacci sequence for n. ║
    ║     @param n: how many Fibonacci numbers to print.               ║
    ║     @type n: int                                                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝

    ╔════════════════════════════════════╗
    ║ def bst_foo(arg1, arg2='default')  ║
    ╠════════════════════════════════════╣
    ║                                    ║
    ║     No documentation.              ║
    ║                                    ║
    ╚════════════════════════════════════╝

    Broken tasklets:

    $ # To schedule a bibtasklet
    $ sudo -u apache /opt/cds-invenio/bin/bibtasklet -T bst_foo -a "arg1=bar"

All the above bibtask options are available for any bibtasklet.

See
``/opt/cds-invenio/lib/python/invenio/bibsched_tasklets/bst_fibonacci.py``
for an example on how a bibtasklet look like.
