# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""BibSched - task management, scheduling and executing system for Invenio
"""

__revision__ = "$Id$"

import os
import sys
import time
import re
import marshal
import getopt
from socket import gethostname
import signal

from invenio.bibtask_config import \
    CFG_BIBTASK_VALID_TASKS, \
    CFG_BIBTASK_MONOTASKS, \
    CFG_BIBTASK_FIXEDTIMETASKS

from invenio.config import \
     CFG_PREFIX, \
     CFG_BIBSCHED_REFRESHTIME, \
     CFG_BIBSCHED_LOG_PAGER, \
     CFG_BINDIR, \
     CFG_LOGDIR, \
     CFG_BIBSCHED_GC_TASKS_OLDER_THAN, \
     CFG_BIBSCHED_GC_TASKS_TO_REMOVE, \
     CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE, \
     CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS, \
     CFG_SITE_URL, \
     CFG_BIBSCHED_NODE_TASKS
from invenio.dbquery import run_sql, real_escape_string
from invenio.textutils import wrap_text_in_a_box
from invenio.errorlib import register_exception, register_emergency
from invenio.shellutils import run_shell_command

CFG_VALID_STATUS = ('WAITING', 'SCHEDULED', 'RUNNING', 'CONTINUING', '% DELETED', 'ABOUT TO STOP', 'ABOUT TO SLEEP', 'STOPPED', 'SLEEPING', 'KILLED', 'NOW STOP')


def get_editor():
    """
    Return the first available editor.
    """
    for editor in os.environ.get('EDITOR'), '/usr/bin/vim', '/usr/bin/emacs', '/usr/bin/vi', '/usr/bin/nano':
        if editor and os.path.exists(editor):
            return editor

shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    try:
        date = time.time()
        factors = {"d":24*3600, "h":3600, "m":60, "s":1}
        m = shift_re.match(var)
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
    except:
        return None

def get_my_pid(process, args=''):
    if sys.platform.startswith('freebsd'):
        COMMAND = "ps -o pid,args | grep '%s %s' | grep -v 'grep' | sed -n 1p" % (process, args)
    else:
        COMMAND = "ps -C %s o '%%p%%a' | grep '%s %s' | grep -v 'grep' | sed -n 1p" % (process, process, args)
    answer = os.popen(COMMAND).read().strip()
    if answer == '':
        answer = 0
    else:
        answer = answer[:answer.find(' ')]
    return int(answer)

def get_task_pid(task_name, task_id, ignore_error=False):
    """Return the pid of task_name/task_id"""
    try:
        pid = int(open(os.path.join(CFG_PREFIX, 'var', 'run', 'bibsched_task_%d.pid' % task_id)).read())
        os.kill(pid, signal.SIGUSR2)
        return pid
    except (OSError, IOError):
        if ignore_error:
            return 0
        register_exception()
        return get_my_pid(task_name, str(task_id))

def is_task_scheduled(task_name):
    """Check if a certain task_name is due for execution (WAITING or RUNNING)"""
    sql = "SELECT COUNT(proc) FROM schTASK WHERE proc = %s AND (status='WAITING' OR status='RUNNING')"
    return run_sql(sql, (task_name,))[0][0] > 0

def get_task_ids_by_descending_date(task_name, statuses=['SCHEDULED']):
    """Returns list of task ids, ordered by descending runtime."""
    sql = "SELECT id FROM schTASK WHERE proc=%s AND (" + \
          " OR ".join(["status = '%s'" % x for x in statuses]) + ") ORDER BY runtime DESC"
    return [x[0] for x in run_sql(sql, (task_name,))]

def get_task_options(task_id):
    """Returns options for task_id read from the BibSched task queue table."""
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s", (task_id,))
    try:
        return marshal.loads(res[0][0])
    except IndexError:
        return list()

def gc_tasks(verbose=False, statuses=None, since=None, tasks=None):
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
            write_message('Deleted %s %s tasks (created before %s) with %s' % (res, task, date, status_query))
        elif task in CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE:
            run_sql("""INSERT INTO hstTASK(id,proc,host,user,
                    runtime,sleeptime,arguments,status,progress)
                SELECT id,proc,host,user,
                    runtime,sleeptime,arguments,status,progress
                FROM schTASK WHERE proc=%%s AND %s AND
                    runtime<%%s""" % status_query, (task, date))
            res = run_sql("""DELETE FROM schTASK WHERE proc=%%s AND %s AND
                             runtime<%%s""" % status_query, (task, date))
            write_message('Archived %s %s tasks (created before %s) with %s' % (res, task, date, status_query))

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
        return run_sql("UPDATE schTASK SET status=%s WHERE id=%s", (status, task_id))
    else:
        return run_sql("UPDATE schTASK SET status=%s WHERE id=%s AND status=%s", (status, task_id, when_status_is))

def bibsched_set_progress(task_id, progress):
    """Update the progress of task_id."""
    return run_sql("UPDATE schTASK SET progress=%s WHERE id=%s", (progress, task_id))

def bibsched_set_priority(task_id, priority):
    """Update the priority of task_id."""
    return run_sql("UPDATE schTASK SET priority=%s WHERE id=%s", (priority, task_id))

def bibsched_send_signal(proc, task_id, signal):
    """Send a signal to a given task."""
    if bibsched_get_host(task_id) != gethostname():
        return False
    pid = get_task_pid(proc, task_id, True)
    if pid:
        try:
            os.kill(pid, signal)
            return True
        except OSError:
            return False
    return False

class Manager:
    def __init__(self, old_stdout):
        import curses
        import curses.panel
        from curses.wrapper import wrapper
        self.old_stdout = old_stdout
        self.curses = curses
        self.helper_modules = CFG_BIBTASK_VALID_TASKS
        self.running = 1
        #self.footer_move_mode = "[KeyUp/KeyDown Move] [M Select mode] [Q Quit]"
        self.footer_auto_mode = "Automatic Mode [A Manual] [1/2/3 Display] [P Purge] [l/L Log] [O Opts] [E Edit motd] [Q Quit]"
        self.footer_select_mode = "Manual Mode [A Automatic] [1/2/3 Display Type] [P Purge] [l/L Log] [O Opts] [E Edit motd] [Q Quit]"
        self.footer_waiting_item = "[R Run] [D Delete] [N Priority]"
        self.footer_running_item = "[S Sleep] [T Stop] [K Kill]"
        self.footer_stopped_item = "[I Initialise] [D Delete] [K Acknowledge]"
        self.footer_sleeping_item   = "[W Wake Up] [T Stop] [K Kill]"
        self.item_status = ""
        self.rows = []
        self.panel = None
        self.display = 2
        self.first_visible_line = 0
        #self.move_mode = 0
        self.auto_mode = 0
        self.currentrow = None
        self.current_attr = 0
        self.header_lines = 2
        self.hostname = gethostname()
        self.allowed_task_types = CFG_BIBSCHED_NODE_TASKS.get(self.hostname, CFG_BIBTASK_VALID_TASKS)
        try:
            motd_path = os.path.join(CFG_PREFIX, "var", "run", "bibsched.motd")
            self.motd = open(motd_path).read().strip()
            if len(self.motd) > 0:
                self.motd = "MOTD [%s] " % time.strftime("%Y-%m-%d %H:%M",time.localtime(os.path.getmtime(motd_path))) + self.motd
                self.header_lines = 3
        except IOError:
            self.motd = ""
        self.selected_line = self.header_lines
        wrapper(self.start)

    def handle_keys(self, chr):
        if chr == -1:
            return
        if self.auto_mode and (chr not in (self.curses.KEY_UP,
                                           self.curses.KEY_DOWN,
                                           self.curses.KEY_PPAGE,
                                           self.curses.KEY_NPAGE,
                                           ord("g"), ord("G"),
                                           ord("q"), ord("Q"), ord("a"),
                                           ord("A"), ord("1"), ord("2"), ord("3"),
                                           ord("p"), ord("P"), ord("o"), ord("O"),
                                           ord("l"), ord("L"), ord("e"), ord("E"))):
            self.display_in_footer("in automatic mode")
            self.stdscr.refresh()
        #elif self.move_mode and (chr not in (self.curses.KEY_UP,
                                             #self.curses.KEY_DOWN,
                                             #ord("m"), ord("M"), ord("q"),
                                             #ord("Q"))):
            #self.display_in_footer("in move mode")
            #self.stdscr.refresh()
        else:
            status = self.currentrow and self.currentrow[5] or None
            if chr == self.curses.KEY_UP:
                #if self.move_mode:
                    #self.move_up()
                #else:
                self.selected_line = max(self.selected_line - 1, self.header_lines)
                self.repaint()
            if chr == self.curses.KEY_PPAGE:
                self.selected_line = max(self.selected_line - 10, self.header_lines)
                self.repaint()
            elif chr == self.curses.KEY_DOWN:
                #if self.move_mode:
                    #self.move_down()
                #else:
                self.selected_line = min(self.selected_line + 1, len(self.rows) + self.header_lines - 1)
                self.repaint()
            elif chr == self.curses.KEY_NPAGE:
                self.selected_line = min(self.selected_line + 10, len(self.rows) + self.header_lines - 1)
                self.repaint()
            elif chr == self.curses.KEY_HOME:
                self.first_visible_line = 0
                self.selected_line = self.header_lines
            elif chr == ord("g"):
                self.selected_line = self.header_lines
                self.repaint()
            elif chr == ord("G"):
                self.selected_line = len(self.rows) + self.header_lines - 1
                self.repaint()
            elif chr in (ord("a"), ord("A")):
                self.change_auto_mode()
            elif chr == ord("l"):
                self.openlog()
            elif chr == ord("L"):
                self.openlog(err=True)
            elif chr in (ord("w"), ord("W")):
                self.wakeup()
            elif chr in (ord("n"), ord("N")):
                self.change_priority()
            elif chr in (ord("r"), ord("R")):
                if status in ('WAITING', 'SCHEDULED'):
                    self.run()
            elif chr in (ord("s"), ord("S")):
                self.sleep()
            elif chr in (ord("k"), ord("K")):
                if status in ('ERROR', 'DONE WITH ERRORS'):
                    self.acknowledge()
                elif status is not None:
                    self.kill()
            elif chr in (ord("t"), ord("T")):
                self.stop()
            elif chr in (ord("d"), ord("D")):
                self.delete()
            elif chr in (ord("i"), ord("I")):
                self.init()
            #elif chr in (ord("m"), ord("M")):
                #self.change_select_mode()
            elif chr in (ord("p"), ord("P")):
                self.purge_done()
            elif chr in (ord("o"), ord("O")):
                self.display_task_options()
            elif chr in (ord("e"), ord("E")):
                self.edit_motd()
            elif chr == ord("1"):
                self.display = 1
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                self.display_in_footer("only done processes are displayed")
            elif chr == ord("2"):
                self.display = 2
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                self.display_in_footer("only not done processes are displayed")
            elif chr == ord("3"):
                self.display = 3
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                self.display_in_footer("only archived processes are displayed")
            elif chr in (ord("q"), ord("Q")):
                if self.curses.panel.top_panel() == self.panel:
                    self.panel.bottom()
                    self.curses.panel.update_panels()
                else:
                    self.running = 0
                    return

    def openlog(self, err=False):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if err:
            logname = os.path.join(CFG_LOGDIR, 'bibsched_task_%d.err' % task_id)
        else:
            logname = os.path.join(CFG_LOGDIR, 'bibsched_task_%d.log' % task_id)
        if os.path.exists(logname):
            pager = CFG_BIBSCHED_LOG_PAGER or os.environ.get('PAGER', '/bin/more')
            if os.path.exists(pager):
                self.curses.endwin()
                os.system('%s %s' % (pager, logname))
                print >> self.old_stdout, "\rPress ENTER to continue",
                self.old_stdout.flush()
                raw_input()
                self.curses.panel.update_panels()

    def edit_motd(self):
        """Add, delete or change the motd message that will be shown when the
        bibsched monitor starts."""
        editor = get_editor()
        if editor:
            motdpath = os.path.join(CFG_PREFIX, "var", "run", "bibsched.motd")
            previous = self.motd
            self.curses.endwin()
            os.system("%s %s" % (editor, motdpath))
            self.curses.panel.update_panels()
            try:
                self.motd = open(motdpath).read().strip()
            except IOError:
                self.motd = ""
            if len(self.motd) > 0:
                self.motd = "MOTD [%s] " % time.strftime("%m-%d-%Y %H:%M",time.localtime(os.path.getmtime(motdpath))) + self.motd
            if previous[24:] != self.motd[24:]:
                if len(previous) == 0:
                    Log('motd set to "%s"' % self.motd.replace("\n", "|"))
                    self.selected_line += 1
                    self.header_lines += 1
                elif len(self.motd) == 0:
                    Log('motd deleted')
                    self.selected_line -= 1
                    self.header_lines -= 1
                else:
                    Log('motd changed to "%s"' % self.motd.replace("\n", "|"))
        else:
            self._display_message_box("No editor was found")

    def display_task_options(self):
        """Nicely display information about current process."""
        msg =  '        id: %i\n\n' % self.currentrow[0]
        pid = get_task_pid(self.currentrow[1], self.currentrow[0], True)
        if pid is not None:
            msg += '       pid: %s\n\n' % pid
        msg += '  priority: %s\n\n' % self.currentrow[8]
        msg += '      proc: %s\n\n' % self.currentrow[1]
        msg += '      user: %s\n\n' % self.currentrow[2]
        msg += '   runtime: %s\n\n' % self.currentrow[3].strftime("%Y-%m-%d %H:%M:%S")
        msg += ' sleeptime: %s\n\n' % self.currentrow[4]
        msg += '    status: %s\n\n' % self.currentrow[5]
        msg += '  progress: %s\n\n' % self.currentrow[6]
        arguments = marshal.loads(self.currentrow[7])
        if type(arguments) is dict:
            # FIXME: REMOVE AFTER MAJOR RELEASE 1.0
            msg += '   options : %s\n\n' % arguments
        else:
            msg += 'executable : %s\n\n' % arguments[0]
            msg += ' arguments : %s\n\n' % ' '.join(arguments[1:])
        msg += '\n\nPress q to quit this panel...'
        msg = wrap_text_in_a_box(msg, style='no_border')
        rows = msg.split('\n')
        height = len(rows) + 2
        width = max([len(row) for row in rows]) + 4
        try:
            self.win = self.curses.newwin(
                height,
                width,
                (self.height - height) / 2 + 1,
                (self.width - width) / 2 + 1
                )
        except self.curses.error:
            return
        self.panel = self.curses.panel.new_panel(self.win)
        self.panel.top()
        self.win.border()
        i = 1
        for row in rows:
            self.win.addstr(i, 2, row, self.current_attr)
            i += 1
        self.win.refresh()
        while self.win.getkey() != 'q':
            pass

    def count_processes(self, status):
        out = 0
        res = run_sql("SELECT COUNT(id) FROM schTASK WHERE status=%s GROUP BY status", (status,))
        try:
            out = res[0][0]
        except:
            pass
        return out

    def change_priority(self):
        task_id = self.currentrow[0]
        priority = self.currentrow[8]
        new_priority = self._display_ask_number_box("Insert the desired priority for task %s. The smaller the number the less the priority. Note that a number less than -10 will mean to always postpone the task while a number bigger than 10 will mean some tasks with less priority could be stopped in order to let this task run. The current priority is %s. New value:" % (task_id, priority))
        try:
            new_priority = int(new_priority)
        except ValueError:
            return
        bibsched_set_priority(task_id, new_priority)

    def wakeup(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        #if self.count_processes('RUNNING') + self.count_processes('CONTINUING') >= 1:
            #self.display_in_footer("a process is already running!")
        if status == "SLEEPING":
            if not bibsched_send_signal(process, task_id, signal.SIGCONT):
                bibsched_set_status(task_id, "ERROR", "SLEEPING")
            self.display_in_footer("process woken up")
        else:
            self.display_in_footer("process is not sleeping")
        self.stdscr.refresh()

    def _display_YN_box(self, msg):
        """Utility to display confirmation boxes."""
        msg += ' (Y/N)'
        msg = wrap_text_in_a_box(msg, style='no_border')
        rows = msg.split('\n')
        height = len(rows) + 2
        width = max([len(row) for row in rows]) + 4
        self.win = self.curses.newwin(
            height,
            width,
            (self.height - height) / 2 + 1,
            (self.width - width) / 2 + 1
            )
        self.panel = self.curses.panel.new_panel( self.win )
        self.panel.top()
        self.win.border()
        i = 1
        for row in rows:
            self.win.addstr(i, 2, row, self.current_attr)
            i += 1
        self.win.refresh()
        while 1:
            c = self.win.getch()
            if c in (ord('y'), ord('Y')):
                self.curses.panel.update_panels()
                return True
            elif c in (ord('n'), ord('N')):
                self.curses.panel.update_panels()
                return False

    def _display_ask_number_box(self, msg):
        """Utility to display confirmation boxes."""
        msg = wrap_text_in_a_box(msg, style='no_border')
        rows = msg.split('\n')
        height = len(rows) + 3
        width = max([len(row) for row in rows]) + 4
        self.win = self.curses.newwin(
            height,
            width,
            (self.height - height) / 2 + 1,
            (self.width - width) / 2 + 1
            )
        self.panel = self.curses.panel.new_panel( self.win )
        self.panel.top()
        self.win.border()
        i = 1
        for row in rows:
            self.win.addstr(i, 2, row, self.current_attr)
            i += 1
        self.win.refresh()
        self.win.move(height - 2, 2)
        self.curses.echo()
        ret = self.win.getstr()
        self.curses.noecho()
        return ret

    def _display_message_box(self, msg):
        """Utility to display message boxes."""
        rows = msg.split('\n')
        height = len(rows) + 2
        width = max([len(row) for row in rows]) + 3
        self.win = self.curses.newwin(
            height,
            width,
            (self.height - height) / 2 + 1,
            (self.width - width) / 2 + 1
            )
        self.panel = self.curses.panel.new_panel( self.win )
        self.panel.top()
        self.win.border()
        i = 1
        for row in rows:
            self.win.addstr(i, 2, row, self.current_attr)
            i += 1
        self.win.refresh()
        self.win.move(height - 2, 2)
        self.win.getkey()
        self.curses.noecho()

    def purge_done(self):
        """Garbage collector."""
        if self._display_YN_box("You are going to purge the list of DONE tasks.\n\n"
            "%s tasks, submitted since %s days, will be archived.\n\n"
            "%s tasks, submitted since %s days, will be deleted.\n\n"
            "Are you sure?" % (
                ','.join(CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE),
                CFG_BIBSCHED_GC_TASKS_OLDER_THAN,
                ','.join(CFG_BIBSCHED_GC_TASKS_TO_REMOVE),
                CFG_BIBSCHED_GC_TASKS_OLDER_THAN)):
            gc_tasks()
            self.display_in_footer("DONE processes purged")

    def run(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1].split(':')[0]
        status = self.currentrow[5]
        #if self.count_processes('RUNNING') + self.count_processes('CONTINUING') >= 1:
            #self.display_in_footer("a process is already running!")
        if status == "WAITING":
            if process in self.helper_modules:
                if run_sql("UPDATE schTASK SET status='SCHEDULED', host=%s WHERE id=%s and status='WAITING'", (self.hostname, task_id)):
                    program = os.path.join(CFG_BINDIR, process)
                    COMMAND = "%s %s > /dev/null 2> /dev/null &" % (program, str(task_id))
                    os.system(COMMAND)
                    Log("manually running task #%d (%s)" % (task_id, process))
                else:
                    ## Process already running (typing too quickly on the keyboard?)
                    pass
            else:
                self.display_in_footer("Process %s is not in the list of allowed processes." % process)
        else:
            self.display_in_footer("Process status should be SCHEDULED or WAITING!")

    def acknowledge(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status in ('ERROR', 'DONE WITH ERRORS'):
            bibsched_set_status(task_id, 'ACK ' + status, status)
            self.display_in_footer("Acknowledged error")

    def sleep(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1].split(':')[0]
        status = self.currentrow[5]
        if status in ('RUNNING', 'CONTINUING'):
            bibsched_set_status(task_id, 'ABOUT TO SLEEP', status)
            self.display_in_footer("SLEEP signal sent to task #%s" % task_id)
        else:
            self.display_in_footer("Cannot put to sleep non-running processes")

    def kill(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        if status in ('RUNNING', 'CONTINUING', 'ABOUT TO STOP', 'ABOUT TO SLEEP', 'SLEEPING'):
            if self._display_YN_box("Are you sure you want to kill the %s process %s?" % (process, task_id)):
                bibsched_send_signal(process, task_id, signal.SIGKILL)
                bibsched_set_status(task_id, 'KILLED')
                self.display_in_footer("KILL signal sent to task #%s" % task_id)
        else:
            self.display_in_footer("Cannot kill non-running processes")

    def stop(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        if status in ('RUNNING', 'CONTINUING', 'ABOUT TO SLEEP', 'SLEEPING'):
            if status == 'SLEEPING':
                bibsched_set_status(task_id, 'NOW STOP', 'SLEEPING')
                bibsched_send_signal(process, task_id, signal.SIGCONT)
                count = 10
                while bibsched_get_status(task_id) == 'NOW STOP':
                    if count <= 0:
                        bibsched_set_status(task_id, 'ERROR', 'NOW STOP')
                        self.display_in_footer("It seems impossible to wakeup this task.")
                        return
                    time.sleep(CFG_BIBSCHED_REFRESHTIME)
                    count -= 1
            else:
                bibsched_set_status(task_id, 'ABOUT TO STOP', status)
            self.display_in_footer("STOP signal sent to task #%s" % task_id)
        else:
            self.display_in_footer("Cannot stop non-running processes")

    def delete(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status not in ('RUNNING', 'CONTINUING', 'SLEEPING', 'SCHEDULED', 'ABOUT TO STOP', 'ABOUT TO SLEEP'):
            bibsched_set_status(task_id, "%s_DELETED" % status, status)
            self.display_in_footer("process deleted")
            self.selected_line = max(self.selected_line, self.header_lines)
        else:
            self.display_in_footer("Cannot delete running processes")

    def init(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status not in ('RUNNING', 'CONTINUING', 'SLEEPING'):
            bibsched_set_status(task_id, "WAITING")
            bibsched_set_progress(task_id, "")
            bibsched_set_host(task_id, "")
            self.display_in_footer("process initialised")
        else:
            self.display_in_footer("Cannot initialise running processes")

    #def change_select_mode(self):
        #if self.move_mode:
            #self.move_mode = 0
        #else:
            #status = self.currentrow[5]
            #if status in ("RUNNING" , "CONTINUING" , "SLEEPING"):
                #self.display_in_footer("cannot move running processes!")
            #else:
                #self.move_mode = 1
        #self.stdscr.refresh()

    def change_auto_mode(self):
        if self.auto_mode:
            program = os.path.join(CFG_BINDIR, "bibsched")
            COMMAND = "%s -q halt" % program
            os.system(COMMAND)

            self.auto_mode = 0
        else:
            program = os.path.join( CFG_BINDIR, "bibsched")
            COMMAND = "%s -q start" % program
            os.system(COMMAND)

            self.auto_mode = 1
            self.move_mode = 0
        self.stdscr.refresh()

    #def move_up(self):
        #self.display_in_footer("not implemented yet")
        #self.stdscr.refresh()

    #def move_down(self):
        #self.display_in_footer("not implemented yet")
        #self.stdscr.refresh()

    def put_line(self, row, header=False, motd=False):
        ## ROW: (id,proc,user,runtime,sleeptime,status,progress,arguments,priority,host)
        ##       0  1    2    3       4         5      6        7         8        9
        col_w = [7 , 25, 15, 21, 7, 11, 20, 60]
        maxx = self.width
        if self.y == self.selected_line - self.first_visible_line and self.y > 1:
            #if self.auto_mode:
                #attr = self.curses.color_pair(2) + self.curses.A_STANDOUT + self.curses.A_BOLD + self.current.A_REVERSE
            ##elif self.move_mode:
                ##attr = self.curses.color_pair(7) + self.curses.A_STANDOUT + self.curses.A_BOLD
            #else:
                #attr = self.curses.color_pair(8) + self.curses.A_STANDOUT + self.curses.A_BOLD + self.current.A_REVERSE
            self.item_status = row[5]
            self.currentrow = row
        if motd:
            attr = self.curses.color_pair(1) + self.curses.A_BOLD
        elif self.y == self.header_lines - 2:
            if self.auto_mode:
                attr = self.curses.color_pair(2) + self.curses.A_STANDOUT + self.curses.A_BOLD
            #elif self.move_mode:
                #attr = self.curses.color_pair(7) + self.curses.A_STANDOUT + self.curses.A_BOLD
            else:
                attr = self.curses.color_pair(8) + self.curses.A_STANDOUT + self.curses.A_BOLD
        elif row[5] == "DONE":
            attr = self.curses.color_pair(5) + self.curses.A_BOLD
        elif row[5] == "STOPPED":
            attr = self.curses.color_pair(6) + self.curses.A_BOLD
        elif row[5].find("ERROR") > -1:
            attr = self.curses.color_pair(4) + self.curses.A_BOLD
        elif row[5] == "WAITING":
            attr = self.curses.color_pair(3) + self.curses.A_BOLD
        elif row[5] in ("RUNNING","CONTINUING") :
            attr = self.curses.color_pair(2) + self.curses.A_BOLD
        elif not header and row[8]:
            attr = self.curses.A_BOLD
        else:
            attr = self.curses.A_NORMAL
        ## If the task is not relevant for this instance ob BibSched because
        ## the type of the task can not be run, or it is running on another
        ## machine: make it a different color
        if not header and (row[1].split(':')[0] not in self.allowed_task_types or
              (row[9] != '' and row[9] != self.hostname)):
            attr = self.curses.color_pair(6)
            if not row[6]:
                nrow = list(row)
                nrow[6] = 'Not allowed on this instance'
                row = tuple(nrow)
        if self.y == self.selected_line - self.first_visible_line and self.y > 1:
            self.current_attr = attr
            attr += self.curses.A_REVERSE
        if header: # Dirty hack. put_line should be better refactored.
            # row contains one less element: arguments
            ## !!! FIXME: THIS IS CRAP
            myline = str(row[0]).ljust(col_w[0]-1)
            myline += str(row[1]).ljust(col_w[1]-1)
            myline += str(row[2]).ljust(col_w[2]-1)
            myline += str(row[3]).ljust(col_w[3]-1)
            myline += str(row[4]).ljust(col_w[4]-1)
            myline += str(row[5]).ljust(col_w[5]-1)
            myline += str(row[6]).ljust(col_w[6]-1)
            myline += str(row[7]).ljust(col_w[7]-1)
        elif motd:
            myline = str(row[0])
        else:
             ## ROW: (id,proc,user,runtime,sleeptime,status,progress,arguments,priority,host)
             ##       0  1    2    3       4         5      6        7         8        9
            priority = str(row[8] and ' [%s]' % row[8] or '')
            myline = str(row[0]).ljust(col_w[0])[:col_w[0]-1]
            myline += (str(row[1])[:col_w[1]-len(priority)-2] + priority).ljust(col_w[1]-1)
            myline += str(row[2]).ljust(col_w[2])[:col_w[2]-1]
            myline += str(row[3]).ljust(col_w[3])[:col_w[3]-1]
            myline += str(row[4]).ljust(col_w[4])[:col_w[4]-1]
            myline += str(row[5]).ljust(col_w[5])[:col_w[5]-1]
            myline += str(row[9]).ljust(col_w[6])[:col_w[6]-1]
            myline += str(row[6]).ljust(col_w[7])[:col_w[7]-1]
        myline = myline.ljust(maxx)
        try:
            self.stdscr.addnstr(self.y, 0, myline, maxx, attr)
        except self.curses.error:
            pass
        self.y = self.y+1

    def display_in_footer(self, footer, i = 0, print_time_p=0):
        if print_time_p:
            footer = "%s %s" % (footer, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        maxx = self.stdscr.getmaxyx()[1]
        footer = footer.ljust(maxx)
        if self.auto_mode:
            colorpair = 2
        #elif self.move_mode:
            #colorpair = 7
        else:
            colorpair = 1
        try:
            self.stdscr.addnstr(self.y - i, 0, footer, maxx - 1, self.curses.A_STANDOUT + self.curses.color_pair(colorpair) + self.curses.A_BOLD )
        except self.curses.error:
            pass

    def repaint(self):
        if server_pid():
            self.auto_mode = 1
        else:
            if self.auto_mode == 1:
                self.curses.beep()
            self.auto_mode = 0
        self.y = 0
        self.stdscr.clear()
        self.height, self.width = self.stdscr.getmaxyx()
        maxy = self.height - 2
        #maxx = self.width
        if len(self.motd) > 0:
            self.put_line((self.motd.strip().replace("\n"," - ")[:79], "", "", "", "", "", "", "", ""), header=False, motd=True)
        self.put_line(("ID", "PROC [PRI]", "USER", "RUNTIME", "SLEEP", "STATUS", "HOST", "PROGRESS"), header=True)
        self.put_line(("","","","","","","", ""), header=True)
        if self.selected_line > maxy + self.first_visible_line - 1:
            self.first_visible_line = self.selected_line - maxy + 1
        if self.selected_line < self.first_visible_line + 2:
            self.first_visible_line = self.selected_line - 2
        for row in self.rows[self.first_visible_line:self.first_visible_line+maxy-2]:
            self.put_line(row)
        self.y = self.stdscr.getmaxyx()[0] - 1
        if self.auto_mode:
            self.display_in_footer(self.footer_auto_mode, print_time_p=1)
        #elif self.move_mode:
            #self.display_in_footer(self.footer_move_mode, print_time_p=1)
        else:
            self.display_in_footer(self.footer_select_mode, print_time_p=1)
            footer2 = ""
            if self.item_status.find("DONE") > -1 or self.item_status in ("ERROR", "STOPPED", "KILLED"):
                footer2 += self.footer_stopped_item
            elif self.item_status in ("RUNNING", "CONTINUING", "ABOUT TO STOP", "ABOUT TO SLEEP"):
                footer2 += self.footer_running_item
            elif self.item_status == "SLEEPING":
                footer2 += self.footer_sleeping_item
            elif self.item_status == "WAITING":
                footer2 += self.footer_waiting_item
            self.display_in_footer(footer2, 1)
        self.stdscr.refresh()

    def start(self, stdscr):
        os.environ['BIBSCHED_MODE'] = 'manual'
        if self.curses.has_colors():
            self.curses.start_color()
            self.curses.init_pair(8, self.curses.COLOR_WHITE, self.curses.COLOR_BLACK)
            self.curses.init_pair(1, self.curses.COLOR_WHITE, self.curses.COLOR_RED)
            self.curses.init_pair(2, self.curses.COLOR_GREEN, self.curses.COLOR_BLACK)
            self.curses.init_pair(3, self.curses.COLOR_MAGENTA, self.curses.COLOR_BLACK)
            self.curses.init_pair(4, self.curses.COLOR_RED, self.curses.COLOR_BLACK)
            self.curses.init_pair(5, self.curses.COLOR_BLUE, self.curses.COLOR_BLACK)
            self.curses.init_pair(6, self.curses.COLOR_CYAN, self.curses.COLOR_BLACK)
            self.curses.init_pair(7, self.curses.COLOR_YELLOW, self.curses.COLOR_BLACK)
        self.stdscr = stdscr
        self.base_panel = self.curses.panel.new_panel( self.stdscr )
        self.base_panel.bottom()
        self.curses.panel.update_panels()
        self.height, self.width = stdscr.getmaxyx()
        self.stdscr.clear()
        if server_pid():
            self.auto_mode = 1
        ring = 4
        if len(self.motd) > 0:
            self._display_message_box(self.motd + "\nPress any key to close")
        while self.running:
            if ring == 4:
                if self.display == 1:
                    table = "schTASK"
                    where = "and (status='DONE' or status LIKE 'ACK%')"
                    order = "runtime DESC"
                elif self.display == 2:
                    table = "schTASK"
                    where = "and (status<>'DONE' and status NOT LIKE 'ACK%')"
                    order = "runtime ASC"
                else:
                    table = "hstTASK"
                    order = "runtime DESC"
                    where = ''
                self.rows = run_sql("""SELECT id,proc,user,runtime,sleeptime,status,progress,arguments,priority,host,sequenceid FROM %s WHERE status NOT LIKE '%%_DELETED' %s ORDER BY %s""" % (table, where, order))
                ring = 0
                self.repaint()
            ring += 1
            char = -1
            try:
                char = timed_out(self.stdscr.getch, 1)
                if char == 27: # escaping sequence
                    char = self.stdscr.getch()
                    if char == 79: # arrow
                        char = self.stdscr.getch()
                        if char == 65: #arrow up
                            char = self.curses.KEY_UP
                        elif char == 66: #arrow down
                            char = self.curses.KEY_DOWN
                        elif char == 72:
                            char = self.curses.KEY_PPAGE
                        elif char == 70:
                            char = self.curses.KEY_NPAGE
                    elif char == 91:
                        char = self.stdscr.getch()
                        if char == 53:
                            char = self.stdscr.getch()
                            if char == 126:
                                char = self.curses.KEY_HOME
            except TimedOutExc:
                char = -1
            self.handle_keys(char)

class BibSched:
    def __init__(self):
        self.hostname = gethostname()
        self.helper_modules = CFG_BIBTASK_VALID_TASKS
        ## All the tasks in the queue that the node is allowed to manipulate
        self.node_relevant_bibupload_tasks = ()
        self.node_relevant_waiting_tasks = ()
        self.node_relevant_active_tasks = ()
        ## All tasks of all nodes
        self.active_tasks_all_nodes = ()

        self.allowed_task_types = CFG_BIBSCHED_NODE_TASKS.get(self.hostname, CFG_BIBTASK_VALID_TASKS)
        os.environ['BIBSCHED_MODE'] = 'automatic'

    def tie_task_to_host(self, task_id):
        """Sets the hostname of a task to the machine executing this script
        @return: True if the scheduling was successful, False otherwise,
            e.g. if the task was scheduled concurrently on a different host.
        """
        if not run_sql("SELECT id FROM schTASK WHERE id=%s AND host='' AND status='WAITING'", (task_id, )):
            ## The task was already tied?
            return False
        run_sql("UPDATE schTASK SET host=%s, status='SCHEDULED' WHERE id=%s AND host='' AND status='WAITING'", (self.hostname, task_id))
        return bool(run_sql("SELECT id FROM schTASK WHERE id=%s AND host=%s", (task_id, self.hostname, )))

    def filter_for_allowed_tasks(self):
        """ Removes all tasks that are not allowed in this Invenio instance
        """
        n_waiting = []
        n_active = []
        if "bibupload" not in self.allowed_task_types:
            self.node_relevant_bibupload_tasks = ()
        for id, proc, runtime, status, priority, host, sequenceid in self.node_relevant_waiting_tasks:
            procname = proc.split(':')[0]
            if procname in self.allowed_task_types:
                n_waiting.append((id, proc, runtime, status, priority, host, sequenceid))
        for id, proc, runtime, status, priority, host, sequenceid in self.node_relevant_active_tasks:
            procname = proc.split(':')[0]
            if procname in self.allowed_task_types:
                n_active.append((id, proc, runtime, status, priority, host, sequenceid))
        self.node_relevant_active_tasks = tuple(n_active)
        self.node_relevant_waiting_tasks = tuple(n_waiting)

    def is_task_safe_to_execute(self, proc1, proc2):
        """Return True when the two tasks can run concurrently."""
        return proc1 != proc2 # and not proc1.startswith('bibupload') and not proc2.startswith('bibupload')

    def get_tasks_to_sleep_and_stop(self, proc, task_set):
        """Among the task_set, return the list of tasks to stop and the list
        of tasks to sleep.
        """
        min_prio = None
        min_task_id = None
        min_proc = None
        min_status = None
        min_sequenceid = None
        to_stop = []
        ## For all the lower priority tasks...
        for (this_task_id, this_proc, this_priority, this_status, this_sequenceid) in task_set:
            if not self.is_task_safe_to_execute(this_proc, proc):
                to_stop.append((this_task_id, this_proc, this_priority, this_status, this_sequenceid))
            elif (min_prio is None or this_priority < min_prio) and this_status != 'SLEEPING':
                ## We don't put to sleep already sleeping task :-)
                min_prio = this_priority
                min_task_id = this_task_id
                min_proc = this_proc
                min_status = this_status
                min_sequenceid = this_sequenceid

        if len(task_set) < CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS and not to_stop:
            ## All the task are safe and there are enough resources
            return [], []
        else:
            if to_stop:
                return to_stop, []
            elif min_task_id:
                return [], [(min_task_id, min_proc, min_prio, min_status, min_sequenceid)]
            else:
                return [], []

    def split_active_tasks_by_priority(self, task_id, priority):
        """Return two lists: the list of task_ids with lower priority and
        those with higher or equal priority."""
        higher = []
        lower = []
        ### !!! We allready have this in node_relevant_active_tasks
        for other_task_id, task_proc, runtime, status, task_priority, task_host, sequenceid in self.node_relevant_active_tasks:
#        for other_task_id, task_proc, runtime, status, task_priority, task_host in self.node_relevant_active_tasks:
#        for other_task_id, task_proc, task_priority, status in self.get_running_tasks():
            if task_id == other_task_id:
                continue
            if task_priority < priority and task_host == self.hostname:
                lower.append((other_task_id, task_proc, task_priority, status, sequenceid))
            elif task_host == self.hostname:
                higher.append((other_task_id, task_proc, task_priority, status, sequenceid))
        return lower, higher

    def handle_task(self, task_id, proc, runtime, status, priority, host, sequenceid):
        """Perform needed action of the row representing a task.
        Return True when task_status need to be refreshed"""
        #Log('%s id: %s, proc: %s, runtime: %s, status: %s, priority: %s' % (task_status, task_id, proc, runtime, status, priority))
        #Log("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s" % (task_id, proc, runtime, status, priority))

        if (task_id, proc, runtime, status, priority, host, sequenceid) in self.node_relevant_waiting_tasks:
            #elif task_id in self.task_status['WAITING'] or task_id in self.task_status['SLEEPING']:
            #Log("Trying to run %s" % task_id)

            if priority < -10:
                return False

            lower, higher = self.split_active_tasks_by_priority(task_id, priority)
            #Log('lower: %s' % lower)
            #Log('higher: %s' % higher)
            for other_task_id, other_proc, other_runtime, other_status, other_priority, other_host, other_sequenceid in self.active_tasks_all_nodes:
                if not self.is_task_safe_to_execute(proc, other_proc):
                    ### !!! WE NEED TO CHECK FOR TASKS THAT CAN ONLY BE EXECUTED ON ONE MACHINE AT ONE TIME
                    ### !!! FOR EXAMPLE BIBUPLOADS WHICH NEED TO BE EXECUTED SEQUENTIALLY AND NEVER CONCURRENTLY
                    ## There's at least a higher priority task running that
                    ## cannot run at the same time of the given task.
                    ## We give up
                    #Log("Cannot run because task_id: %s, proc: %s is the queue and incompatible" % (other_task_id, other_proc))
                    return False

            if sequenceid:
                max_priority = run_sql("SELECT MAX(priority) FROM schTASK WHERE status='WAITING' AND sequenceid=%s", (sequenceid, ))[0][0]
                if run_sql("UPDATE schTASK SET priority=%s WHERE status='WAITING' AND sequenceid=%s", (max_priority, sequenceid)):
                    Log("Raised all waiting tasks with sequenceid %s to the max priority %s" % (sequenceid, max_priority))
                    ## Some priorities where raised
                    return False

            for other_task_id, other_proc, other_dummy, other_status, other_sequenceid in higher + lower:
                if sequenceid is not None and \
                    sequenceid == other_sequenceid and task_id > other_task_id:
                    Log('Task %s need to run after task %s since they have the same sequence id: %s' % (task_id, other_task_id, sequenceid))
                    ## If there is a task with same sequence number then do not run the current task
                    return False

            ## No higher priority task have issue with the given task.
            if proc not in CFG_BIBTASK_FIXEDTIMETASKS and len(higher) >= CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS:
                ### !!! THIS HAS TO BE ADAPTED FOR MULTINODE
                ### !!! Basically, the number of concurrent tasks should count per node
                ## Not enough resources.
                #Log("Cannot run because all resource (%s) are used (%s), higher: %s" % (CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS, len(higher), higher))
                return False

            ## We check if it is necessary to stop/put to sleep some lower priority
            ## task.
            tasks_to_stop, tasks_to_sleep = self.get_tasks_to_sleep_and_stop(proc, lower)
            #Log('tasks_to_stop: %s' % tasks_to_stop)
            #Log('tasks_to_sleep: %s' % tasks_to_sleep)

            if tasks_to_stop and priority < 100:
                ## Only tasks with priority higher than 100 have the power
                ## to put task to stop.
                #Log("Cannot run because there are task to stop: %s and priority < 100" % tasks_to_stop)
                return False

            procname = proc.split(':')[0]
            if not tasks_to_stop and not tasks_to_sleep:
                if status in ("SLEEPING", "ABOUT TO SLEEP"):
                    if host == self.hostname:
                        ## We can only wake up tasks that are running on our own host
                        bibsched_set_status(task_id, "CONTINUING", status)
                        if not bibsched_send_signal(proc, task_id, signal.SIGCONT):
                            bibsched_set_status(task_id, "ERROR", "CONTINUING")
                            Log("Task #%d (%s) woken up but didn't existed anymore" % (task_id, proc))
                            return True
                        Log("Task #%d (%s) woken up" % (task_id, proc))
                        return True
                    else:
                        return False
                elif procname in self.helper_modules:
                    program = os.path.join(CFG_BINDIR, procname)
                    ## Trick to log in bibsched.log the task exiting
                    exit_str = '&& echo "`date "+%%Y-%%m-%%d %%H:%%M:%%S"` --> Task #%d (%s) exited" >> %s' % (task_id, proc, os.path.join(CFG_LOGDIR, 'bibsched.log'))
                    if proc in CFG_BIBTASK_MONOTASKS:
                        ## okay, we have a synchronous monotask to run:
                        ## (won't be interrupted by any other task that may pop in)
                        COMMAND = "(%s %s > /dev/null 2> /dev/null %s)" % (program, str(task_id), exit_str) ### !!! THIS MEANS BIBUPLOADS BLOCK EVERYTHING
                    else:
                        COMMAND = "(%s %s > /dev/null 2> /dev/null %s) &" % (program, str(task_id), exit_str)
                    ### Set the task to scheduled and tie it to this host
                    if self.tie_task_to_host(task_id):
                        Log("Task #%d (%s) started" % (task_id, proc))
                        ### Relief the lock for the BibTask, it is save now to do so
                        os.system(COMMAND)
                        count = 10
                        while run_sql("SELECT status FROM schTASK WHERE id=%s AND status='SCHEDULED'", (task_id, )):
                            ## Polling to wait for the task to really start,
                            ## in order to avoid race conditions.
                            if count <= 0:
                                raise StandardError, "Process %s (task_id: %s) was launched but seems not to be able to reach RUNNING status." % (proc, task_id)
                            time.sleep(CFG_BIBSCHED_REFRESHTIME)
                            count -= 1
                    return True
                else:
                    raise StandardError, "%s is not in the allowed modules" % procname
            else:
                ## It's not still safe to run the task.
                ## We first need to stop task that should be stopped
                ## and to put to sleep task that should be put to sleep
                for (other_task_id, other_proc, other_priority, other_status, other_sequenceid) in tasks_to_stop:
                    Log("Send STOP signal to #%d (%s) which was in status %s" % (other_task_id, other_proc, other_status))
                    bibsched_set_status(other_task_id, 'ABOUT TO STOP', other_status)
                for (other_task_id, other_proc, other_priority, other_status, other_sequenceid) in tasks_to_sleep:
                    Log("Send SLEEP signal to #%d (%s) which was in status %s" % (other_task_id, other_proc, other_status))
                    bibsched_set_status(other_task_id, 'ABOUT TO SLEEP', other_status)
                time.sleep(CFG_BIBSCHED_REFRESHTIME)
                return True

    def watch_loop(self):
        def calculate_rows():
            """Return all the node_relevant_active_tasks to work on."""
            if run_sql("SELECT count(id) FROM schTASK WHERE status='ERROR' OR status='DONE WITH ERRORS'")[0][0] > 0:
                errors = run_sql("SELECT id,proc,status FROM schTASK WHERE status='ERROR' OR status='DONE WITH ERRORS'")
                errors = ["    #%s %s -> %s" % row for row in errors]
                raise StandardError('BibTask with ERRORS:\n%s' % "\n".join(errors))
            max_bibupload_priority = run_sql("SELECT max(priority) FROM schTASK WHERE status='WAITING' AND proc='bibupload' AND runtime<=NOW()")
            if max_bibupload_priority:
                run_sql("UPDATE schTASK SET priority=%s WHERE status='WAITING' AND proc='bibupload' AND runtime<=NOW()", ( max_bibupload_priority[0][0], ))
            ## The bibupload tasks are sorted by id, which means by the order they were scheduled
            self.node_relevant_bibupload_tasks = run_sql("SELECT id,proc,runtime,status,priority,host,sequenceid FROM schTASK WHERE status='WAITING' AND proc='bibupload' AND runtime<=NOW() ORDER BY id ASC LIMIT 1", n=1)
            ## The other tasks are sorted by priority
            self.node_relevant_waiting_tasks = run_sql("SELECT id,proc,runtime,status,priority,host,sequenceid FROM schTASK WHERE (status='WAITING' AND runtime<=NOW()) OR status='SLEEPING' ORDER BY priority DESC, runtime ASC, id ASC")
            self.node_relevant_active_tasks = run_sql("SELECT id,proc,runtime,status,priority,host,sequenceid FROM schTASK WHERE status IN ('RUNNING','CONTINUING','SCHEDULED','ABOUT TO STOP','ABOUT TO SLEEP')")
            self.active_tasks_all_nodes = tuple(self.node_relevant_active_tasks)
            ## Remove tasks that can not be executed on this host
            self.filter_for_allowed_tasks()

        ## Cleaning up scheduled task not run because of bibsched being
        ## interrupted in the middle.
        run_sql("UPDATE schTASK SET status='WAITING' WHERE status='SCHEDULED'")

        try:
            while True:
                #Log("New bibsched cycle")
                calculate_rows()
                ## Let's first handle running node_relevant_active_tasks.
                for task in self.node_relevant_active_tasks:
                    if self.handle_task(*task):
                        break
                else:
                    # If nothing has changed we can go on to run tasks.
                    for task in self.node_relevant_waiting_tasks:
                        if task[1] == 'bibupload' and self.node_relevant_bibupload_tasks:
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
        except Exception, err:
            register_exception(alert_admin=True)
            try:
                register_emergency('Emergency from %s: BibSched halted: %s' % (CFG_SITE_URL, err))
            except NotImplementedError:
                pass
            raise

class TimedOutExc(Exception):
    def __init__(self, value = "Timed Out"):
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        return repr(self.value)

def timed_out(f, timeout, *args, **kwargs):
    def handler(signum, frame):
        raise TimedOutExc()

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        result = f(*args, **kwargs)
    finally:
        signal.signal(signal.SIGALRM, old)
    signal.alarm(0)
    return result


def Log(message):
    log = open(CFG_LOGDIR + "/bibsched.log","a")
    log.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
    log.write(message)
    log.write("\n")
    log.close()

def redirect_stdout_and_stderr():
    "This function redirects stdout and stderr to bibsched.log and bibsched.err file."
    old_stdout = sys.stdout
    sys.stdout = open(CFG_LOGDIR + "/bibsched.log", "a")
    sys.stderr = open(CFG_LOGDIR + "/bibsched.err", "a")
    return old_stdout

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

Command options:
  -d, --daemon     \t Launch BibSched in the daemon mode (deprecated, use 'start')
General options:
  -h, --help       \t Print this help.
  -V, --version    \t Print version information.
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

    #sys.stderr.write("  -v, --verbose=LEVEL \t Verbose level (0=min, 1=default, 9=max).\n")
    sys.exit(exitcode)

pidfile = os.path.join(CFG_PREFIX, 'var', 'run', 'bibsched.pid')

def error(msg):
    print >> sys.stderr, "error: " + msg
    sys.exit(1)

def warning(msg):
    print >> sys.stderr, "warning: " + msg

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
        output = run_shell_command("ps p %s -o args=", (str(pid),))[1]
        if not 'bibsched' in output:
            warning("pidfile %s found referring to pid %s which does not correspond to bibsched: cmdline is %s" % (pidfile, pid, output))
            return None
    return pid

def start(verbose = True):
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
        open(pidfile, 'w').write('%d' % pid)
        return

    sys.stdin.close()
    redirect_stdout_and_stderr()

    sched = BibSched()
    try:
        sched.watch_loop()
    finally:
        try:
            os.remove(pidfile)
        except OSError:
            pass

    return

def halt(verbose=True, soft=False):
    pid = server_pid()
    if not pid:
        if soft:
            print >> sys.stderr, 'bibsched seems not to be running.'
            return
        else:
            error('bibsched seems not to be running.')

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        print >> sys.stderr, 'no bibsched process found'

    Log("daemon stopped (pid %d)" % pid)

    if verbose:
        print "stopping bibsched: pid %d" % pid
    os.unlink(pidfile)
    return

def monitor(verbose = True):
    old_stdout = redirect_stdout_and_stderr()
    manager = Manager(old_stdout)
    return

def write_message(msg, stream=None, verbose=1):
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

def report_queue_status(verbose=True, status=None, since=None, tasks=None):
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

        res = run_sql("""SELECT id,proc,user,runtime,sleeptime,status,progress,priority
                        FROM schTASK WHERE status=%%s %(task_query)s
                        %(since_query)s ORDER BY id ASC""" % {
                            'task_query' : task_query,
                            'since_query' : since_query
                        },
                    (status,))

        write_message("%s processes: %d" % (status, len(res)))
        for (proc_id, proc_proc, proc_user, proc_runtime, proc_sleeptime,
             proc_status, proc_progress, proc_priority) in res:
            write_message(' * ID="%s" PRIORITY="%s" PROC="%s" USER="%s" RUNTIME="%s" SLEEPTIME="%s" STATUS="%s" PROGRESS="%s"' % \
                          (proc_id, proc_priority, proc_proc, proc_user, proc_runtime,
                           proc_sleeptime, proc_status, proc_progress))
        return

    write_message("BibSched queue status report for %s:" % gethostname())
    mode = server_pid() and "AUTOMATIC" or "MANUAL"
    write_message("BibSched queue running mode: %s" % mode)
    if status is None:
        report_about_processes('Running', since, tasks)
        report_about_processes('Waiting', since, tasks)
    else:
        for state in status:
            report_about_processes(state, since, tasks)
    write_message("Done.")
    return

def restart(verbose = True):
    halt(verbose, soft=True)
    start(verbose)
    return

def stop(verbose=True):
    """
    * Stop bibsched
    * Send stop signal to all the running tasks
    * wait for all the tasks to stop
    * return
    """
    if verbose:
        print "Stopping BibSched if running"
    halt(verbose, soft=True)
    run_sql("UPDATE schTASK SET status='WAITING' WHERE status='SCHEDULED'")
    res = run_sql("SELECT id,proc,status FROM schTASK WHERE status NOT LIKE 'DONE' AND status NOT LIKE '%_DELETED' AND (status='RUNNING' OR status='ABOUT TO STOP' OR status='ABOUT TO SLEEP' OR status='SLEEPING' OR status='CONTINUING')")
    if verbose:
        print "Stopping all running BibTasks"
    for task_id, proc, status in res:
        if status == 'SLEEPING':
            bibsched_send_signal(proc, task_id, signal.SIGCONT)
            time.sleep(CFG_BIBSCHED_REFRESHTIME)
        bibsched_set_status(task_id, 'ABOUT TO STOP')
    while run_sql("SELECT id FROM schTASK WHERE status NOT LIKE 'DONE' AND status NOT LIKE '%_DELETED' AND (status='RUNNING' OR status='ABOUT TO STOP' OR status='ABOUT TO SLEEP' OR status='SLEEPING' OR status='CONTINUING')"):
        if verbose:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(CFG_BIBSCHED_REFRESHTIME)

    if verbose:
        print "\nStopped"
    Log("BibSched and all BibTasks stopped")
    return

def main():
    from invenio.bibtask import check_running_process_user
    check_running_process_user()

    verbose = True
    status = None
    since = None
    tasks = None

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hVdqS:s:t:", [
            "help","version","daemon", "quiet", "since=", "status=", "task="])
    except getopt.GetoptError, err:
        Log("Error: %s" % err)
        usage(1, err)

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage(0)

        elif opt in ["-V", "--version"]:
            print __revision__
            sys.exit(0)

        elif opt in ["-d", "--daemon"]:
            redirect_stdout_and_stderr()
            sched = BibSched()
            Log("daemon started")
            sched.watch_loop()

        elif opt in ['-q', '--quiet']:
            verbose = False

        elif opt in ['-s', '--status']:
            status = arg.split(',')

        elif opt in ['-S', '--since']:
            since = arg

        elif opt in ['-t', '--task']:
            tasks = arg.split(',')

        else:
            usage(1)

    try:
        cmd = args [0]
    except IndexError:
        cmd = 'monitor'

    try:
        if cmd in ('status', 'purge'):
            { 'status' : report_queue_status,
              'purge' : gc_tasks,
            } [cmd] (verbose, status, since, tasks)
        else:
            {'start':   start,
            'halt':    halt,
            'stop': stop,
            'restart': restart,
            'monitor': monitor} [cmd] (verbose)
    except KeyError:
        usage(1, 'unkown command: %s' % cmd)

    return

if __name__ == '__main__':
    main()
