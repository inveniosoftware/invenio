# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

from __future__ import print_function

"""BibSched - task management, scheduling and executing system for Invenio
"""

import os
import sys
import time
import re
import datetime
import marshal
import getopt
from itertools import chain
from socket import gethostname
from subprocess import Popen
import signal

from invenio.legacy.bibsched.bibtask_config import \
    CFG_BIBTASK_VALID_TASKS, \
    CFG_BIBTASK_MONOTASKS, \
    CFG_BIBTASK_FIXEDTIMETASKS
from invenio.config import \
    CFG_TMPSHAREDDIR, \
    CFG_BIBSCHED_REFRESHTIME, \
    CFG_BINDIR, \
    CFG_LOGDIR, \
    CFG_RUNDIR, \
    CFG_BIBSCHED_GC_TASKS_OLDER_THAN, \
    CFG_BIBSCHED_GC_TASKS_TO_REMOVE, \
    CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE, \
    CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS, \
    CFG_SITE_URL, \
    CFG_BIBSCHED_NODE_TASKS, \
    CFG_INSPIRE_SITE, \
    CFG_BIBSCHED_INCOMPATIBLE_TASKS, \
    CFG_BIBSCHED_NON_CONCURRENT_TASKS, \
    CFG_VERSION, \
    CFG_BIBSCHED_NEVER_STOPS
from invenio.base.globals import cfg
from invenio.legacy.dbquery import run_sql, real_escape_string
from invenio.ext.logging import register_exception
from invenio.utils.shell import run_shell_command

CFG_VALID_STATUS = ('WAITING', 'SCHEDULED', 'RUNNING', 'CONTINUING',
                    '% DELETED', 'ABOUT TO STOP', 'ABOUT TO SLEEP', 'STOPPED',
                    'SLEEPING', 'KILLED', 'NOW STOP', 'ERRORS REPORTED')

CFG_MOTD_PATH = os.path.join(CFG_TMPSHAREDDIR, "bibsched.motd")

ACTIVE_STATUS = ('SCHEDULED', 'ABOUT TO SLEEP', 'ABOUT TO STOP',
                 'CONTINUING', 'RUNNING')


SHIFT_RE = re.compile(r"([-\+]{0,1})([\d]+)([dhms])")


def register_emergency(msg, recipients=None):
    """Launch an emergency. This means to send email messages to each
    address in 'recipients'. By default recipients will be obtained via
    get_emergency_recipients() which loads settings from
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES
    """
    from invenio.base.globals import cfg
    from invenio.ext.email import send_email
    if not recipients:
        recipients = get_emergency_recipients()
    recipients = set(recipients)
    recipients.add(cfg['CFG_SITE_ADMIN_EMAIL'])
    for address_str in recipients:
        send_email(
            cfg['CFG_SITE_SUPPORT_EMAIL'],
            address_str,
            "Emergency notification",
            msg
        )


def get_emergency_recipients(recipient_cfg=None, now=None):
    """
    Parse a list of appropriate emergency email recipients from
    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES, or from a provided dictionary
    comprised of 'time constraint' => 'comma separated list of addresses'

    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES format example:

    CFG_SITE_EMERGENCY_EMAIL_ADDRESSES = {
       'Sunday 22:00-06:00': '0041761111111@email2sms.foo.com',
       '06:00-18:00': 'team-in-europe@foo.com,0041762222222@email2sms.foo.com',
       '18:00-06:00': 'team-in-usa@foo.com',
       '*': 'john.doe.phone@foo.com'}
    """
    from invenio.base.globals import cfg
    from invenio.utils.date import parse_runtime_limit

    if recipient_cfg is None:
        recipient_cfg = cfg['CFG_SITE_EMERGENCY_EMAIL_ADDRESSES']

    if now is None:
        now = datetime.datetime.now()

    recipients = set()
    for time_condition, address_str in recipient_cfg.items():
        if time_condition and time_condition is not '*':
            current_range, dummy_range = parse_runtime_limit(time_condition,
                                                             now=now)
            if not current_range[0] <= now <= current_range[1]:
                continue

        recipients.add(address_str)
    return list(recipients)


def get_pager():
    """
    Return the first available pager.
    """
    paths = (
        os.environ.get('PAGER', ''),
        cfg['CFG_BIBSCHED_LOG_PAGER'],
        '/usr/bin/less',
        '/bin/more'
    )
    for pager in paths:
        if os.path.exists(pager):
            return pager


def get_editor():
    """
    Return the first available editor.
    """
    paths = (
        os.environ.get('EDITOR', ''),
        cfg['CFG_BIBSCHED_EDITOR'],
        '/usr/bin/vim',
        '/usr/bin/emacs',
        '/usr/bin/vi',
        '/usr/bin/nano',
    )
    for editor in paths:
        if os.path.exists(editor):
            return editor


class RecoverableError(StandardError):
    pass


def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    try:
        date = time.time()
        factors = {"d": 24*3600, "h": 3600, "m": 60, "s": 1}
        m = SHIFT_RE.match(var)
        if m:
            sign = m.groups()[0] == "-" and -1 or 1
            factor = factors[m.groups()[2]]
            value = float(m.groups()[1])
            date = time.localtime(date + sign * factor * value)
            date = time.strftime(format_string, date)
        else:
            date = time.strptime(var, format_string)
            date = time.strftime(format_string, date)
        return date
    except ValueError:
        return None


def get_my_pid(process, args=''):
    if sys.platform.startswith('freebsd'):
        command = "ps -o pid,args | grep '%s %s' | grep -v 'grep' | sed -n 1p" % (process, args)
    else:
        command = "ps -C %s o '%%p%%a' | grep '%s %s' | grep -v 'grep' | sed -n 1p" % (process, process, args)
    answer = run_shell_command(command)[1].strip()
    if answer == '':
        answer = 0
    else:
        answer = answer[:answer.find(' ')]
    return int(answer)


def get_task_pid(task_id):
    """Return the pid of task_name/task_id"""
    try:
        path = os.path.join(CFG_RUNDIR, 'bibsched_task_%d.pid' % task_id)
        pid = int(open(path).read())
        os.kill(pid, 0)
        return pid
    except (OSError, IOError):
        return None


def get_last_taskid():
    """Return the last taskid used."""
    return run_sql("SELECT MAX(id) FROM schTASK")[0][0]

def delete_task(task_id):
    """Delete the corresponding task."""
    run_sql("DELETE FROM schTASK WHERE id=%s", (task_id, ))

def is_task_scheduled(task_name):
    """Check if a certain task_name is due for execution (WAITING or RUNNING)"""
    sql = """SELECT COUNT(proc) FROM schTASK
             WHERE proc = %s AND (status='WAITING' OR status='RUNNING')"""
    return run_sql(sql, (task_name,))[0][0] > 0


def get_task_ids_by_descending_date(task_name, statuses=['SCHEDULED']):
    """Returns list of task ids, ordered by descending runtime."""
    sql = """SELECT id FROM schTASK
             WHERE proc=%s AND (%s)
             ORDER BY runtime DESC""" \
                        % " OR ".join(["status = '%s'" % x for x in statuses])
    return [x[0] for x in run_sql(sql, (task_name,))]


def get_task_options(task_id):
    """Returns options for task_id read from the BibSched task queue table."""
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s", (task_id,))
    try:
        return marshal.loads(res[0][0])
    except IndexError:
        return list()


def gc_tasks(verbose=False, statuses=None, since=None, tasks=None): # pylint: disable=W0613
    """Garbage collect the task queue."""
    if tasks is None:
        tasks = CFG_BIBSCHED_GC_TASKS_TO_REMOVE + CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE
    if since is None:
        since = '-%id' % CFG_BIBSCHED_GC_TASKS_OLDER_THAN
    if statuses is None:
        statuses = ['DONE']

    statuses = [status.upper() for status in statuses if status.upper() != 'RUNNING']

    date = get_datetime(since)

    status_query = 'status in (%s)' % ','.join([repr(real_escape_string(status)) for status in statuses])

    for task in tasks:
        if task in CFG_BIBSCHED_GC_TASKS_TO_REMOVE:
            res = run_sql("""DELETE FROM schTASK WHERE proc=%%s AND %s AND
                             runtime<%%s""" % status_query, (task, date))
            write_message('Deleted %s %s tasks (created before %s) with %s'
                                            % (res, task, date, status_query))
        elif task in CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE:
            run_sql("""INSERT INTO hstTASK(id,proc,host,user,
                       runtime,sleeptime,arguments,status,progress)
                       SELECT id,proc,host,user,
                       runtime,sleeptime,arguments,status,progress
                       FROM schTASK WHERE proc=%%s AND %s AND
                       runtime<%%s""" % status_query, (task, date))
            res = run_sql("""DELETE FROM schTASK WHERE proc=%%s AND %s AND
                             runtime<%%s""" % status_query, (task, date))
            write_message('Archived %s %s tasks (created before %s) with %s'
                                            % (res, task, date, status_query))


def spawn_task(command, wait=False):
    """
    Spawn the provided command in a way that is detached from the current
    group. In this way a signal received by bibsched is not going to be
    automatically propagated to the spawned process.
    """
    def preexec():  # Don't forward signals.
        os.setsid()

    devnull = open(os.devnull, "w")
    process = Popen(command, preexec_fn=preexec, shell=True,
                    stderr=devnull, stdout=devnull)
    if wait:
        process.wait()


def bibsched_get_host(task_id):
    """Retrieve the hostname of the task"""
    res = run_sql("SELECT host FROM schTASK WHERE id=%s LIMIT 1", (task_id, ), 1)
    if res:
        return res[0][0]


def bibsched_set_host(task_id, host=""):
    """Update the progress of task_id."""
    return run_sql("UPDATE schTASK SET host=%s WHERE id=%s", (host, task_id))


def bibsched_get_status(task_id):
    """Retrieve the task status."""
    res = run_sql("SELECT status FROM schTASK WHERE id=%s LIMIT 1", (task_id, ), 1)
    if res:
        return res[0][0]


def bibsched_set_status(task_id, status, when_status_is=None):
    """Update the status of task_id."""
    if when_status_is is None:
        return run_sql("UPDATE schTASK SET status=%s WHERE id=%s",
                       (status, task_id))
    else:
        return run_sql("UPDATE schTASK SET status=%s WHERE id=%s AND status=%s",
                       (status, task_id, when_status_is))


def bibsched_set_progress(task_id, progress):
    """Update the progress of task_id."""
    return run_sql("UPDATE schTASK SET progress=%s WHERE id=%s", (progress, task_id))


def bibsched_set_priority(task_id, priority):
    """Update the priority of task_id."""
    return run_sql("UPDATE schTASK SET priority=%s WHERE id=%s", (priority, task_id))

def bibsched_set_name(task_id, name):
    """Update the name of task_id."""
    return run_sql("UPDATE schTASK SET proc=%s WHERE id=%s", (name, task_id))

def bibsched_set_sleeptime(task_id, sleeptime):
    """Update the sleeptime of task_id."""
    return run_sql("UPDATE schTASK SET sleeptime=%s WHERE id=%s", (sleeptime, task_id))


def bibsched_set_runtime(task_id, runtime):
    """Update the sleeptime of task_id."""
    return run_sql("UPDATE schTASK SET runtime=%s WHERE id=%s", (runtime, task_id))


def bibsched_send_signal(task_id, sig):
    """Send a signal to a given task."""
    if bibsched_get_host(task_id) != gethostname():
        return False
    pid = get_task_pid(task_id)
    if pid:
        try:
            os.kill(pid, sig)
            return True
        except OSError:
            return False
    return False


def is_monotask(proc):
    #procname = proc.split(':')[0]
    return proc in CFG_BIBTASK_MONOTASKS

def stop_task(task):
    Log("Sending STOP signal to #%d (%s) which was in status %s" % (task.id, task.proc, task.status))
    bibsched_set_status(task.id, 'ABOUT TO STOP', task.status)


def sleep_task(task):
    Log("Sending SLEEP signal to #%d (%s) which was in status %s" % (task.id, task.proc, task.status))
    bibsched_set_status(task.id, 'ABOUT TO SLEEP', task.status)


def fetch_debug_mode():
    r = run_sql("SELECT value FROM schSTATUS WHERE name = 'debug_mode'")
    try:
        debug_mode = bool(int(r[0][0]))
    except (ValueError, IndexError):
        # We insert the missing configuration variable in the DB
        run_sql("INSERT INTO schSTATUS (name, value) VALUES ('debug_mode', '0')")
        debug_mode = False
    return debug_mode


class Task(object):
    def __init__(self, task_id, proc, runtime, status, priority, host, sequenceid):
        self.id = task_id
        self.proc = proc
        self.runtime = runtime
        self.status = status
        self.priority = priority
        self.host = host
        self.sequenceid = sequenceid

    @staticmethod
    def from_resultset(resultset):
        return [Task(*row) for row in resultset]

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    def __unicode__(self):
        msg = u"Task(id=%r, proc=%r, runtime=%r, status=%r, " \
              u"priority=%r, host=%r, sequenceid=%r"
        return msg % (self.id, self.proc, self.runtime, self.status,
                      self.priority, self.host, self.sequenceid)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return unicode(self)


class BibSched(object):
    def __init__(self, debug=False):
        self.cycles_count = 0
        self.debug = debug
        self.hostname = gethostname()
        self.helper_modules = CFG_BIBTASK_VALID_TASKS
        ## All the tasks in the queue that the node is allowed to manipulate
        self.node_relevant_bibupload_tasks = ()
        self.node_relevant_waiting_tasks = ()
        self.node_sleeping_tasks = ()
        self.node_active_tasks = ()
        ## All tasks of all nodes
        self.sleeping_tasks_all_nodes = ()
        self.waiting_tasks_all_nodes = ()
        self.active_tasks_all_nodes = ()
        self.mono_tasks_all_nodes = ()

        self.allowed_task_types = CFG_BIBSCHED_NODE_TASKS.get(self.hostname, CFG_BIBTASK_VALID_TASKS)

    def tie_task_to_host(self, task_id):
        """Sets the hostname of a task to the machine executing this script
        @return: True if the scheduling was successful, False otherwise,
            e.g. if the task was scheduled concurrently on a different host.
        """
        r = run_sql("""UPDATE schTASK SET host=%s, status='SCHEDULED'
                   WHERE id=%s AND status='WAITING'""",
                                            (self.hostname, task_id))
        return bool(r)

    def filter_for_allowed_tasks(self):
        """ Removes all tasks that are not allowed in this Invenio instance
        """

        def relevant_task(task):
            procname = task.proc.split(':')[0]
            if procname not in self.allowed_task_types:
                return False
            return True

        def filter_tasks(tasks):
            return tuple(t for t in tasks if relevant_task(t))

        self.node_relevant_bibupload_tasks = filter_tasks(self.node_relevant_bibupload_tasks)
        self.node_relevant_waiting_tasks = filter_tasks(self.waiting_tasks_all_nodes)

    def is_task_compatible(self, task1, task2):
        """Return True when the two tasks can run concurrently or can run when
        the other task is sleeping"""
        procname1 = task1.proc.split(':')[0]
        procname2 = task2.proc.split(':')[0]
        for non_compatible_tasks in CFG_BIBSCHED_INCOMPATIBLE_TASKS:
            if (task1.proc in non_compatible_tasks or procname1 in non_compatible_tasks) \
               and (task2.proc in non_compatible_tasks or procname2 in non_compatible_tasks):
                return False

        if task1.proc == task2.proc == 'bibupload':
            return True

        return task1.proc != task2.proc

    def is_task_non_concurrent(self, task1, task2):
        for non_concurrent_tasks in CFG_BIBSCHED_NON_CONCURRENT_TASKS:
            if (task1.proc.split(':')[0] in non_concurrent_tasks
                                        or task1.proc in non_concurrent_tasks):
                if (task2.proc.split(':')[0] in non_concurrent_tasks
                                        or task2.proc in non_concurrent_tasks):
                    return True
        return False

    def get_tasks_to_sleep_and_stop(self, task, task_set):
        """Among the task_set, return the list of tasks to stop and the list
        of tasks to sleep.
        """
        def minimum_priority_task(task_set):
            min_task = None

            ## For all the lower priority tasks...
            for t in task_set:
                if (min_task is None or t.priority < min_task.priority) \
                     and t.status != 'SLEEPING' and t.priority < task.priority \
                     and task.host == t.host:
                    # We don't put to sleep already sleeping task :-)
                    # And it only makes sense to free a spot on the local node
                    min_task = t

            return min_task

        to_stop = []
        to_sleep = []

        for t in task_set:
            if not self.is_task_compatible(task, t):
                to_stop.append(t)

        if is_monotask(task.proc):
            to_sleep = [t for t in task_set if t.status != 'SLEEPING']
        else:
            for t in task_set:
                if t.status != 'SLEEPING' and self.is_task_non_concurrent(task, t):
                    to_sleep.append(t)


        # Only needed if we are not freeing a spot already
        # So to_stop and to_sleep should be empty
        if not to_stop and not to_sleep and \
                len(self.node_active_tasks) >= CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS:
            min_task = minimum_priority_task(task_set)
            if min_task:
                to_sleep = [min_task]

        return to_stop, to_sleep

    def split_active_tasks_by_priority(self, task):
        """Return two lists: the list of task_ids with lower priority and
        those with higher or equal priority."""
        higher = []
        lower = []
        for t in self.node_active_tasks:
            if task.id == t.id:
                continue
            if t.priority < task.priority:
                lower.append(t)
            else:
                higher.append(t)
        return lower, higher

    def handle_task(self, task):
        """Perform needed action of the row representing a task.
        Return True when task_status need to be refreshed"""
        debug = self.debug
        Log(str(task), debug)

        # If the task is active, we do scheduling stuff here
        if task in self.node_active_tasks:
            # For multi-node
            # check if we need to sleep ourselves for monotasks
            # to be able to run
            for t in self.mono_tasks_all_nodes:
                # 2 cases here
                # If a monotask is running, we want to sleep
                # If a monotask is waiting, we want to sleep if our priority
                # is inferior
                if task.priority < t.priority or t.status in ACTIVE_STATUS:
                    # Sleep ourselves
                    if task.status not in ('ABOUT TO STOP', 'ABOUT TO SLEEP', 'SCHEDULED'):
                        Log("Sleeping ourselves because of a monotask: %s" % t, debug)
                        sleep_task(task)
                        return True
                    else:
                        Log("A monotask is running but already going to sleep/stop", debug)
                        return False

        # We try to run a task in waiting status here
        elif task in self.node_relevant_waiting_tasks:
            Log("Trying to run %r" % task, debug)

            if task.priority < -10:
                Log("Cannot run because priority < -10", debug)
                return False

            if task.host and task.host != self.hostname:
                Log("Cannot run because this task is bound to a different machine", debug)
                return False

            lower, higher = self.split_active_tasks_by_priority(task)
            Log('lower: %r' % lower, debug)
            Log('higher: %r' % higher, debug)

            for t in self.active_tasks_all_nodes:
                if task.id != t.id and not self.is_task_compatible(task, t):
                    ### !!! WE NEED TO CHECK FOR TASKS THAT CAN ONLY BE EXECUTED ON ONE MACHINE AT ONE TIME
                    ### !!! FOR EXAMPLE BIBUPLOADS WHICH NEED TO BE EXECUTED SEQUENTIALLY AND NEVER CONCURRENTLY
                    ## There's at least a higher priority task running that
                    ## cannot run at the same time of the given task.
                    ## We give up
                    Log("Cannot run because task_id: %s, proc: %s is in the queue and incompatible" % (t.id, t.proc), debug)
                    return False

            if task.sequenceid:
                ## Let's normalize the prority of all tasks in a sequenceid to the
                ## max priority of the group
                max_priority = run_sql("""SELECT MAX(priority) FROM schTASK
                                          WHERE status IN ('WAITING', 'RUNNING',
                                          'SLEEPING', 'ABOUT TO STOP',
                                          'ABOUT TO SLEEP',
                                          'SCHEDULED', 'CONTINUING')
                                          AND sequenceid=%s""",
                                       (task.sequenceid, ))[0][0]
                if run_sql("""UPDATE schTASK SET priority=%s
                              WHERE status IN ('WAITING', 'RUNNING',
                              'SLEEPING', 'ABOUT TO STOP', 'ABOUT TO SLEEP',
                              'SCHEDULED', 'CONTINUING') AND sequenceid=%s""",
                           (max_priority, task.sequenceid)):
                    Log("Raised all waiting tasks with sequenceid "
                        "%s to the max priority %s" % (task.sequenceid, max_priority))
                    ## Some priorities where raised
                    return True

                ## Let's normalize the runtime of all tasks in a sequenceid to
                ## the compatible runtime.
                current_runtimes = run_sql("""SELECT id, runtime FROM schTASK WHERE sequenceid=%s AND status='WAITING' ORDER by id""", (task.sequenceid, ))
                runtimes_adjusted = False
                if current_runtimes:
                    last_runtime = current_runtimes[0][1]
                    for the_task_id, runtime in current_runtimes:
                        if runtime < last_runtime:
                            run_sql("""UPDATE schTASK SET runtime=%s WHERE id=%s""", (last_runtime, the_task_id))
                            Log("Adjusted runtime of task_id %s to %s in order to be executed in the correct sequenceid order" % (the_task_id, last_runtime), debug)
                            runtimes_adjusted = True
                            runtime = last_runtime
                        last_runtime = runtime
                if runtimes_adjusted:
                    ## Some runtime have been adjusted
                    return True

            if task.sequenceid is not None:
                for t in chain(self.active_tasks_all_nodes,
                               self.waiting_tasks_all_nodes):
                    if task.sequenceid == t.sequenceid and task.id > t.id:
                        Log('Task %s need to run after task %s since they have the same sequence id: %s' % (task.id, t.id, task.sequenceid), debug)
                        ## If there is a task with same sequence number then do not run the current task
                        return False

            if is_monotask(task.proc) and higher:
                ## This is a monotask
                Log("Cannot run because this is a monotask and there are higher priority tasks: %s" % (higher, ), debug)
                return False

            ## Check for monotasks wanting to run
            for t in self.mono_tasks_all_nodes:
                if task.priority < t.priority:
                    Log("Cannot run because there is a monotask with higher priority: %s %s" % (t.id, t.proc), debug)
                    return False

            ## We check if it is necessary to stop/put to sleep some lower priority
            ## task.
            tasks_to_stop, tasks_to_sleep = self.get_tasks_to_sleep_and_stop(task, self.active_tasks_all_nodes)
            Log('tasks_to_stop: %s' % tasks_to_stop, debug)
            Log('tasks_to_sleep: %s' % tasks_to_sleep, debug)

            if tasks_to_stop and task.priority < 100:
                ## Only tasks with priority higher than 100 have the power
                ## to put task to stop.
                Log("Cannot run because there are task to stop: %s and priority < 100" % tasks_to_stop, debug)
                return False

            for t in tasks_to_sleep:
                if not t.priority < task.priority:
                    Log("Cannot run because #%s with priority %s cannot be slept by this task" % (t.id, t.priority), debug)
                    return False

            procname = task.proc.split(':')[0]
            if not tasks_to_stop and not tasks_to_sleep:
                if is_monotask(task.proc) and self.active_tasks_all_nodes:
                    Log("Cannot run because this is a monotask and there are other tasks running: %s" % (self.active_tasks_all_nodes, ), debug)
                    return False

                if task.proc not in CFG_BIBTASK_FIXEDTIMETASKS and len(self.node_active_tasks) >= CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS:
                    Log("Cannot run because all resources (%s) are used (%s), active: %s" % (CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS, len(self.node_active_tasks), self.node_active_tasks), debug)
                    return False

                for t in self.waiting_tasks_all_nodes:
                    if self.is_task_non_concurrent(task, t) and task.priority < t.priority:
                        Log("Cannot run because %s is non-concurrent and has higher priority" % t, debug)
                        return False

                if task.status in ("SCHEDULED",):
                    Log("Task is already scheduled", debug)
                    return False
                elif task.status in ("SLEEPING", "ABOUT TO SLEEP"):
                    if task.host != self.hostname:
                        Log("We can't wake up tasks that are not in the same node", debug)
                        return False

                    ## We can only wake up tasks that are running on our own host
                    for t in self.node_active_tasks:
                        ## But only if there are not other tasks still going to sleep, otherwise
                        ## we might end up stealing the slot for an higher priority  task.
                        if t.id != task.id and t.status in ('ABOUT TO SLEEP', 'ABOUT TO STOP'):
                            Log("Not yet waking up task #%d since there are other tasks (%s #%d) going to sleep (higher priority task incoming?)" % (task.id, t.proc, t.id), debug)
                            return False

                    bibsched_set_status(task.id, "CONTINUING", task.status)
                    if not bibsched_send_signal(task.id, signal.SIGCONT):
                        bibsched_set_status(task.id, "ERROR", "CONTINUING")
                        Log("Task #%d (%s) woken up but didn't existed anymore" % (task.id, task.proc))
                        return True
                    Log("Task #%d (%s) woken up" % (task.id, task.proc))
                    return True
                elif procname in self.helper_modules:
                    program = os.path.join(CFG_BINDIR, procname)
                    ## Trick to log in bibsched.log the task exiting
                    exit_str = '&& echo "`date "+%%Y-%%m-%%d %%H:%%M:%%S"` --> Task #%d (%s) exited" >> %s' % (task.id, task.proc, os.path.join(CFG_LOGDIR, 'bibsched.log'))
                    command = "%s %s %s" % (program, str(task.id), exit_str)
                    ### Set the task to scheduled and tie it to this host
                    if self.tie_task_to_host(task.id):
                        Log("Task #%d (%s) started" % (task.id, task.proc))
                        ### Relief the lock for the BibTask, it is safe now to do so
                        spawn_task(command, wait=is_monotask(task.proc))
                        count = 10
                        while run_sql("""SELECT status FROM schTASK
                                         WHERE id=%s AND status='SCHEDULED'""",
                                      (task.id, )):
                            ## Polling to wait for the task to really start,
                            ## in order to avoid race conditions.
                            if count <= 0:
                                Log("Process %s (task_id: %s) was launched but seems not to be able to reach RUNNING status." % (task.proc, task.id))
                                bibsched_set_status(task.id, "ERROR", "SCHEDULED")
                                return True
                            time.sleep(CFG_BIBSCHED_REFRESHTIME)
                            count -= 1
                    return True
                else:
                    raise StandardError("%s is not in the allowed modules" % procname)
            else:
                ## It's not still safe to run the task.
                ## We first need to stop task that should be stopped
                ## and to put to sleep task that should be put to sleep
                changes = False
                for t in tasks_to_stop:
                    if t.status not in ('ABOUT TO STOP', 'SCHEDULED'):
                        changes = True
                        stop_task(t)
                    else:
                        Log("Cannot run because we are waiting for #%s to stop" % t.id, debug)
                for t in tasks_to_sleep:
                    if t.status not in ('ABOUT TO SLEEP', 'SCHEDULED', 'ABOUT TO STOP'):
                        changes = True
                        sleep_task(t)
                    else:
                        Log("Cannot run because we are waiting for #%s to sleep" % t.id, debug)

                if changes:
                    time.sleep(CFG_BIBSCHED_REFRESHTIME)
                return changes

    def check_errors(self):
        errors = run_sql("""SELECT id,proc,status FROM schTASK
                            WHERE status = 'ERROR'
                            OR status = 'DONE WITH ERRORS'
                            OR status = 'CERROR'""")
        if errors:
            error_msgs = []
            error_recoverable = True
            for e_id, e_proc, e_status in errors:
                if run_sql("""UPDATE schTASK
                               SET status='ERRORS REPORTED'
                               WHERE id = %s AND (status='CERROR'
                               OR status='ERROR'
                               OR status='DONE WITH ERRORS')""", [e_id]):
                    msg = "    #%s %s -> %s" % (e_id, e_proc, e_status)
                    error_msgs.append(msg)
                    if e_status in ('ERROR', 'DONE WITH ERRORS'):
                        error_recoverable = False
            if error_msgs:
                msg = "BibTask with ERRORS:\n%s" % '\n'.join(error_msgs)
                if error_recoverable or CFG_BIBSCHED_NEVER_STOPS:
                    raise RecoverableError(msg)
                else:
                    raise StandardError(msg)

    def calculate_rows(self):
        """Return all the node_relevant_active_tasks to work on."""
        try:
            self.check_errors()
        except RecoverableError as msg:
            register_emergency('Light emergency from %s: BibTask failed: %s' % (CFG_SITE_URL, msg))

        max_bibupload_priority, min_bibupload_priority = run_sql(
            """SELECT MAX(priority), MIN(priority)
                FROM schTASK
                WHERE status IN ('WAITING', 'RUNNING', 'SLEEPING',
                        'ABOUT TO STOP', 'ABOUT TO SLEEP',
                        'SCHEDULED', 'CONTINUING')
                AND proc = 'bibupload'
                AND runtime <= NOW()""")[0]
        if max_bibupload_priority > min_bibupload_priority:
            run_sql(
                """UPDATE schTASK SET priority = %s
                   WHERE status IN ('WAITING', 'RUNNING', 'SLEEPING',
                                    'ABOUT TO STOP', 'ABOUT TO SLEEP',
                                    'SCHEDULED', 'CONTINUING')
                   AND proc = 'bibupload'
                   AND runtime <= NOW()
                   AND priority < %s""", (max_bibupload_priority,
                                          max_bibupload_priority))

        # The bibupload tasks are sorted by id,
        # which means by the order they were scheduled
        self.node_relevant_bibupload_tasks = Task.from_resultset(run_sql(
            """SELECT id, proc, runtime, status, priority, host, sequenceid
               FROM schTASK WHERE status IN ('WAITING', 'SLEEPING')
               AND proc = 'bibupload'
               AND runtime <= NOW()
               ORDER BY FIELD(status, 'SLEEPING', 'WAITING'),
                        id ASC LIMIT 1""", n=1))
        ## The other tasks are sorted by priority
        self.waiting_tasks_all_nodes = Task.from_resultset(run_sql(
            """SELECT id, proc, runtime, status, priority, host, sequenceid
               FROM schTASK WHERE (status = 'WAITING' AND runtime <= NOW())
               OR status = 'SLEEPING'
               ORDER BY priority DESC, runtime ASC, id ASC"""))

        self.sleeping_tasks_all_nodes = Task.from_resultset(run_sql(
            """SELECT id, proc, runtime, status, priority, host, sequenceid
               FROM schTASK WHERE status = 'SLEEPING'
               ORDER BY priority DESC, runtime ASC, id ASC"""))
        self.active_tasks_all_nodes = Task.from_resultset(run_sql(
            """SELECT id, proc, runtime, status, priority, host, sequenceid
               FROM schTASK WHERE status IN ('RUNNING', 'CONTINUING',
                                             'SCHEDULED', 'ABOUT TO STOP',
                                             'ABOUT TO SLEEP')"""))

        self.mono_tasks_all_nodes = tuple(t for t in
            chain(self.waiting_tasks_all_nodes, self.active_tasks_all_nodes)
                                                        if is_monotask(t.proc))
        ## Remove tasks that can not be executed on this host

        def filter_by_host(tasks):
            return tuple(t for t in tasks if t.host == self.hostname or not t.host)

        self.node_active_tasks = filter_by_host(self.active_tasks_all_nodes)
        self.node_sleeping_tasks = filter_by_host(self.sleeping_tasks_all_nodes)

        self.filter_for_allowed_tasks()

    def check_auto_mode(self):
        """Check if the queue is in automatic or manual mode"""
        r = run_sql("SELECT value FROM schSTATUS WHERE name = 'auto_mode'")
        try:
            status = int(r[0][0])
        except (ValueError, IndexError):
            # We insert the missing configuration variable in the DB
            run_sql("INSERT INTO schSTATUS (name, value) VALUES ('auto_mode', '1')")
            status = 1

        if not status:
            r = run_sql("SELECT value FROM schSTATUS WHERE name = 'resume_after'")
            try:
                date_string = r[0][0]
            except IndexError:
                pass
            else:
                if date_string:
                    resume_after = datetime.datetime(*(time.strptime(date_string, "%Y-%m-%d %H:%M:%S")[0:6]))
                    if datetime.datetime.now() > resume_after:
                        run_sql("UPDATE schSTATUS SET value = '' WHERE name = 'resume_after'")
                        run_sql("UPDATE schSTATUS SET value = '1' WHERE name = 'auto_mode'")
                        status = 1

        return status

    def check_for_crashed_tasks(self):
        for task in self.node_active_tasks:
            Log('Checking %s' % task.id)
            pid = get_task_pid(task.id)
            if not pid:
                Log('Task crashed %s' % task.id)
                run_sql("""UPDATE schTASK SET status = 'CERROR'
                           WHERE id = %%s AND status IN (%s)"""
                                 % ','.join("'%s'" % s for s in ACTIVE_STATUS),
                        [task.id])

    def check_debug_mode(self):
        debug_mode = fetch_debug_mode()

        if debug_mode and not self.debug:
            Log('Switching to debug mode')
        elif self.debug and not debug_mode:
            Log('Switching out of debug mode')
        self.debug = debug_mode

    def tick(self):
        Log("New bibsched cycle", self.debug)
        self.cycles_count += 1

        self.check_debug_mode()

        if self.cycles_count % 50 == 0:
            self.check_for_crashed_tasks()

        try:
            self.check_errors()
        except RecoverableError, msg:
            register_emergency('Light emergency from %s: BibTask failed: %s'
                                                         % (CFG_SITE_URL, msg))

        # Update our tasks list (to know who is running, sleeping, etc.)
        self.calculate_rows()

        # Let's first handle running tasks running on this node.
        for task in self.node_active_tasks:
            if self.handle_task(task):
                break
        else:
            # If nothing has changed we can go on to run tasks.
            for task in self.node_relevant_waiting_tasks:
                if task.proc == 'bibupload' \
                   and self.node_relevant_bibupload_tasks:
                    ## We switch in bibupload serial mode!
                    ## which means we execute the first next bibupload.
                    if self.handle_task(self.node_relevant_bibupload_tasks[0]):
                        ## Something has changed
                        break
                elif self.handle_task(task):
                    ## Something has changed
                    break
            else:
                time.sleep(CFG_BIBSCHED_REFRESHTIME)

    def watch_loop(self):
        ## Cleaning up scheduled task not run because of bibsched being
        ## interrupted in the middle.
        run_sql("""UPDATE schTASK
                   SET status = 'WAITING'
                   WHERE status = 'SCHEDULED'
                   AND host = %s""", (self.hostname, ))

        try:
            while True:
                auto_mode = self.check_auto_mode()
                if auto_mode:
                    self.tick()
                else:
                    # If nothing has changed we can go on to run tasks.
                    for task in self.node_relevant_waiting_tasks:
                        if task.proc == 'bibupload' and self.node_relevant_bibupload_tasks:
                            ## We switch in bibupload serial mode!
                            ## which means we execute the first next bibupload.
                            if self.handle_task(*self.node_relevant_bibupload_tasks[0]):
                                ## Something has changed
                                break
                        elif self.handle_task(*task):
                            ## Something has changed
                            break
                    else:
                        time.sleep(CFG_BIBSCHED_REFRESHTIME)
        except Exception as err:
            register_exception(alert_admin=True)
            try:
                register_emergency('Emergency from %s: BibSched halted: %s'
                                   % (CFG_SITE_URL, err))
            except NotImplementedError:
                pass
            raise


def Log(message, debug=None):
    if debug is False:
        return
    log = open(CFG_LOGDIR + "/bibsched.log", "a")
    log.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
    log.write(message)
    log.write("\n")
    log.close()


def redirect_stdout_and_stderr():
    "This function redirects stdout and stderr to bibsched.log and bibsched.err file."
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = open(CFG_LOGDIR + "/bibsched.log", "a")
    sys.stderr = open(CFG_LOGDIR + "/bibsched.err", "a")
    return old_stdout, old_stderr


def restore_stdout_and_stderr(stdout, stderr):
    sys.stdout = stdout
    sys.stderr = stderr


def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)

    sys.stderr.write("""\
Usage: %s [options] [start|stop|restart|monitor|status]

The following commands are available for bibsched:

   start      start bibsched in background
   stop       stop running bibtasks and the bibsched daemon safely
   halt       halt running bibsched while keeping bibtasks running
   restart    restart running bibsched
   monitor    enter the interactive monitor
   status     get report about current status of the queue
   purge      purge the scheduler queue from old tasks

General options:
  -h, --help       \t Print this help.
  -V, --version    \t Print version information.
  -q, --quiet      \t Quiet mode
  -d, --debug      \t Write debugging information in bibsched.log
Status options:
  -s, --status=LIST\t Which BibTask status should be considered (default is Running,waiting)
  -S, --since=TIME\t Since how long time to consider tasks e.g.: 30m, 2h, 1d (default
  is all)
  -t, --tasks=LIST\t Comma separated list of BibTask to consider (default
                  \t is all)
Purge options:
  -s, --status=LIST\t Which BibTask status should be considered (default is DONE)
  -S, --since=TIME\t Since how long time to consider tasks e.g.: 30m, 2h, 1d (default
  is %s days)
  -t, --tasks=LIST\t Comma separated list of BibTask to consider (default
                  \t is %s)

""" % (sys.argv[0], CFG_BIBSCHED_GC_TASKS_OLDER_THAN, ','.join(CFG_BIBSCHED_GC_TASKS_TO_REMOVE + CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE)))

    sys.exit(exitcode)

pidfile = os.path.join(CFG_RUNDIR, 'bibsched.pid')


def error(msg):
    print("error: %s" % msg, file=sys.stderr)
    sys.exit(1)


def warning(msg):
    print("warning: %s" % msg, file=sys.stderr)


def server_pid(ping_the_process=True, check_is_really_bibsched=True):
    # The pid must be stored on the filesystem
    try:
        pid = int(open(pidfile).read())
    except IOError:
        return None

    if ping_the_process:
        # Even if the pid is available, we check if it corresponds to an
        # actual process, as it might have been killed externally
        try:
            os.kill(pid, signal.SIGCONT)
        except OSError:
            warning("pidfile %s found referring to pid %s which is not running" % (pidfile, pid))
            return None

    if check_is_really_bibsched:
        output = run_shell_command("ps p %s -o args=", (str(pid), ))[1]
        if not 'bibsched' in output:
            warning("pidfile %s found referring to pid %s which does not correspond to bibsched: cmdline is %s" % (pidfile, pid, output))
            return None

    return pid


def write_server_pid(pid):
    open(pidfile, 'w').write('%d' % pid)


def start(verbose=True, debug=False):
    """ Fork this process in the background and start processing
    requests. The process PID is stored in a pid file, so that it can
    be stopped later on."""

    if verbose:
        sys.stdout.write("starting bibsched: ")
        sys.stdout.flush()

    pid = server_pid(ping_the_process=False)
    if pid:
        pid2 = server_pid()
        if pid2:
            error("another instance of bibsched (pid %d) is running" % pid2)
        else:
            warning("%s exist but the corresponding bibsched (pid %s) seems not be running" % (pidfile, pid))
            warning("erasing %s and continuing..." % (pidfile, ))
            os.remove(pidfile)

    if debug:
        pid = os.getpid()
        write_server_pid(pid)
    else:
        # start the child process using the "double fork" technique
        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        os.setsid()
        os.chdir('/')

        pid = os.fork()

        if pid > 0:
            if verbose:
                sys.stdout.write('pid %d\n' % pid)

            Log("daemon started (pid %d)" % pid)
            write_server_pid(pid)
            return

        sys.stdin.close()
        redirect_stdout_and_stderr()

    sched = BibSched(debug=debug)
    try:
        sched.watch_loop()
    finally:
        try:
            os.remove(pidfile)
        except OSError:
            pass


def halt(verbose=True, soft=False, debug=False): # pylint: disable=W0613
    pid = server_pid()
    if not pid:
        if soft:
            print('bibsched seems not to be running.', file=sys.stderr)
            return
        else:
            error('bibsched seems not to be running.')

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        print('no bibsched process found', file=sys.stderr)

    Log("daemon stopped (pid %d)" % pid)

    if verbose:
        print("stopping bibsched: pid %d" % pid)
    os.unlink(pidfile)


def write_message(msg, stream=None, verbose=1): # pylint: disable=W0613
    """Write message and flush output stream (may be sys.stdout or sys.stderr).
    Useful for debugging stuff."""
    if stream is None:
        stream = sys.stdout
    if msg:
        if stream == sys.stdout or stream == sys.stderr:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ",
                time.localtime()))
            try:
                stream.write("%s\n" % msg)
            except UnicodeEncodeError:
                stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
            stream.flush()
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)


def report_queue_status(verbose=True, status=None, since=None, tasks=None): # pylint: disable=W0613
    """
    Report about the current status of BibSched queue on standard output.
    """

    def report_about_processes(status='RUNNING', since=None, tasks=None):
        """
        Helper function to report about processes with the given status.
        """
        if tasks is None:
            task_query = ''
        else:
            task_query = 'AND proc IN (%s)' % (
                ','.join([repr(real_escape_string(task)) for task in tasks]))
        if since is None:
            since_query = ''
        else:
            # We're not interested in future task
            if since.startswith('+') or since.startswith('-'):
                since = since[1:]
            since = '-' + since
            since_query = "AND runtime >= '%s'" % get_datetime(since)

        res = run_sql("""SELECT id, proc, runtime, status, priority, host,
                         sequenceid
                         FROM schTASK WHERE status=%%s %(task_query)s
                         %(since_query)s ORDER BY id ASC""" % {
                            'task_query': task_query,
                            'since_query' : since_query},
                    (status,))

        write_message("%s processes: %d" % (status, len(res)))
        for t in Task.from_resultset(res):
            write_message(' * %s' % t)
        return

    write_message("BibSched queue status report for %s:" % gethostname())
    daemon_status = server_pid() and "UP" or "DOWN"
    write_message("BibSched daemon status: %s" % daemon_status)

    if run_sql("show tables like 'schSTATUS'"):
        r = run_sql("SELECT value FROM schSTATUS WHERE name = 'auto_mode'")
        try:
            mode = bool(int(r[0][0]))
        except (ValueError, IndexError):
            mode = True
    else:
        mode = False

    mode_str = mode and 'AUTOMATIC' or 'MANUAL'
    write_message("BibSched queue running mode: %s" % mode_str)
    if status is None:
        report_about_processes('Running', since, tasks)
        report_about_processes('Waiting', since, tasks)
    else:
        for state in status:
            report_about_processes(state, since, tasks)
    write_message("Done.")


def restart(verbose=True, debug=False):
    halt(verbose, soft=True, debug=debug)
    start(verbose, debug=debug)


def stop(verbose=True, debug=False):
    """
    * Stop bibsched
    * Send stop signal to all the running tasks
    * wait for all the tasks to stop
    * return
    """
    if verbose:
        print("Stopping BibSched if running")
    halt(verbose, soft=True, debug=debug)
    run_sql("UPDATE schTASK SET status='WAITING' WHERE status='SCHEDULED'")
    res = run_sql("""SELECT id, status FROM schTASK
                     WHERE status NOT LIKE 'DONE'
                     AND status NOT LIKE '%_DELETED'
                     AND (status='RUNNING'
                         OR status='ABOUT TO STOP'
                         OR status='ABOUT TO SLEEP'
                         OR status='SLEEPING'
                         OR status='CONTINUING')""")
    if verbose:
        print("Stopping all running BibTasks")
    for task_id, status in res:
        if status == 'SLEEPING':
            bibsched_send_signal(task_id, signal.SIGCONT)
            time.sleep(CFG_BIBSCHED_REFRESHTIME)
        bibsched_set_status(task_id, 'ABOUT TO STOP')
    while run_sql("""SELECT id FROM schTASK
                     WHERE status NOT LIKE 'DONE'
                     AND status NOT LIKE '%_DELETED'
                     AND (status='RUNNING'
                          OR status='ABOUT TO STOP'
                          OR status='ABOUT TO SLEEP'
                          OR status='SLEEPING'
                          OR status='CONTINUING')"""):
        if verbose:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(CFG_BIBSCHED_REFRESHTIME)

    if verbose:
        print("\nStopped")
    Log("BibSched and all BibTasks stopped")


def main():
    from invenio.legacy.bibsched.monitor import monitor
    from invenio.legacy.bibsched.bibtask import check_running_process_user
    check_running_process_user()

    verbose = True
    status = None
    since = None
    tasks = None
    debug = False

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hVdqS:s:t:", [
            "help", "version", "debug", "quiet", "since=", "status=", "task="])
    except getopt.GetoptError as err:
        Log("Error: %s" % err)
        usage(1, err)

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage(0)

        elif opt in ["-V", "--version"]:
            print(CFG_VERSION)
            sys.exit(0)

        elif opt in ['-q', '--quiet']:
            verbose = False

        elif opt in ['-s', '--status']:
            status = arg.split(',')

        elif opt in ['-S', '--since']:
            since = arg

        elif opt in ['-t', '--task']:
            tasks = arg.split(',')

        elif opt in ['-d', '--debug']:
            debug = True

        else:
            usage(1)

    try:
        cmd = args[0]
    except IndexError:
        cmd = 'monitor'

    try:
        if cmd in ('status', 'purge'):
            {'status' : report_queue_status,
              'purge' : gc_tasks}[cmd](verbose, status, since, tasks)
        else:
            {'start': start,
            'halt': halt,
            'stop': stop,
            'restart': restart,
            'monitor': monitor}[cmd](verbose=verbose, debug=debug)
    except KeyError:
        usage(1, 'unkown command: %s' % cmd)
