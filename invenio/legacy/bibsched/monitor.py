# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2015 CERN.
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

"""BibSched - ncurses monitor for task management"""

import os
import time
import marshal
from socket import gethostname
from datetime import datetime, timedelta
from itertools import chain
import signal
import textwrap

from invenio.legacy.bibsched.bibtask_config import \
    CFG_BIBTASK_VALID_TASKS, \
    CFG_BIBSCHED_LOGDIR
from invenio.config import \
     CFG_BIBSCHED_REFRESHTIME, \
     CFG_BINDIR, \
     CFG_LOGDIR, \
     CFG_TMPSHAREDDIR, \
     CFG_BIBSCHED_GC_TASKS_OLDER_THAN, \
     CFG_BIBSCHED_GC_TASKS_TO_REMOVE, \
     CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE, \
     CFG_BIBSCHED_NODE_TASKS, \
     CFG_BIBSCHED_MAX_ARCHIVED_ROWS_DISPLAY, \
     CFG_BIBSCHED_LOG_PAGER, \
     CFG_BIBSCHED_EDITOR
from invenio.legacy.dbquery import run_sql
from invenio.utils.text import wrap_text_in_a_box
from invenio.legacy.bibsched.cli import bibsched_get_status, \
                             bibsched_set_host, \
                             bibsched_set_progress, \
                             bibsched_set_status, \
                             bibsched_send_signal, \
                             bibsched_set_priority, \
                             bibsched_set_name, \
                             bibsched_set_sleeptime, \
                             bibsched_set_runtime, \
                             spawn_task, \
                             gc_tasks, \
                             Log, \
                             server_pid, \
                             redirect_stdout_and_stderr, \
                             restore_stdout_and_stderr, \
                             get_task_pid, \
                             fetch_debug_mode
from invenio.legacy.bibsched.bibtask import (get_sleeptime,
                             task_get_options,
                             task_log_path)


CFG_MOTD_PATH = os.path.join(CFG_TMPSHAREDDIR, "bibsched.motd")


def get_user():
    return os.environ.get('SUDO_USER', None)


def log(message, debug=None):
    user = get_user()
    if user:
        message = "%s by %s" % (message, user)
    return Log(message, debug)


def get_pager():
    """
    Return the first available pager.
    """
    paths = (
        os.environ.get('PAGER', ''),
        CFG_BIBSCHED_LOG_PAGER,
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
        CFG_BIBSCHED_EDITOR,
        '/usr/bin/vim',
        '/usr/bin/emacs',
        '/usr/bin/vi',
        '/usr/bin/nano',
    )
    for editor in paths:
        if os.path.exists(editor):
            return editor


class TimedOutExc(Exception):
    def __init__(self, value="Timed Out"):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


def timed_out(f, timeout, *args, **kwargs):
    def handler(signum, frame):  # pylint: disable=W0613
        raise TimedOutExc()

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        result = f(*args, **kwargs)
    finally:
        signal.signal(signal.SIGALRM, old)
    signal.alarm(0)
    return result


class Manager(object):
    def __init__(self, old_stdout):
        import curses
        import curses.panel
        from curses.wrapper import wrapper
        self.old_stdout = old_stdout
        self.curses = curses
        self.helper_modules = CFG_BIBTASK_VALID_TASKS
        self.running = 1
        self.footer_auto_mode = "Automatic Mode [A Manual] [1/2/3 Display] [H Help] [l/L Log] [O Opts] [E Edit motd] [Q Quit]"
        self.footer_manual_mode = "Manual Mode%s [A Automatic] [1/2/3 Display Type] [H help] [l/L Log] [O Opts] [E Edit motd] [Q Quit]"
        self.footer_waiting_item = "[R Run] [D Delete] [N Priority]"
        self.footer_running_item = "[S Sleep] [T Stop] [K Kill]"
        self.footer_stopped_item = "[I Initialise] [D Delete] [K Acknowledge]"
        self.footer_sleeping_item = "[W Wake Up] [T Stop] [K Kill]"
        self.item_status = ""
        self.rows = []
        self.panel = None
        self.display = 2
        self.first_visible_line = 0
        self.auto_mode = 0
        self.currentrow = None
        self.current_attr = 0
        self.hostname = gethostname()
        self.allowed_task_types = CFG_BIBSCHED_NODE_TASKS.get(self.hostname, CFG_BIBTASK_VALID_TASKS)
        self.motd = ""
        self.header_lines = 2
        self.read_motd()
        self.selected_line = self.header_lines
        wrapper(self.start)

    def read_motd(self):
        """Get a fresh motd from disk, if it exists."""
        self.motd = ""
        self.header_lines = 2
        try:
            if os.path.exists(CFG_MOTD_PATH):
                motd = open(CFG_MOTD_PATH).read().strip()
                if motd:
                    self.motd = "MOTD [%s] " % time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(CFG_MOTD_PATH))) + motd
                    self.header_lines = 3
        except IOError:
            pass

    def handle_keys(self, char):
        if char == -1:
            return
        if self.auto_mode and (char not in (self.curses.KEY_UP,
                                           self.curses.KEY_DOWN,
                                           self.curses.KEY_PPAGE,
                                           self.curses.KEY_NPAGE,
                                           ord("g"), ord("G"), ord("n"),
                                           ord("q"), ord("Q"), ord("a"),
                                           ord("A"), ord("1"), ord("2"), ord("3"),
                                           ord("p"), ord("P"), ord("o"), ord("O"),
                                           ord("l"), ord("L"), ord("e"), ord("E"),
                                           ord("z"), ord("Z"), ord("b"), ord("B"),
                                           ord("h"), ord("H"), ord("D"), ord("c"),
                                           ord("f"), ord("j"), ord("4"))):
            self.display_in_footer("in automatic mode")
        else:
            status = self.currentrow and self.currentrow[5] or None
            if char == self.curses.KEY_UP:
                self.selected_line = max(self.selected_line - 1,
                                         self.header_lines)
                self.repaint()
            if char == self.curses.KEY_PPAGE:
                self.selected_line = max(self.selected_line - 10,
                                         self.header_lines)
                self.repaint()
            elif char == self.curses.KEY_DOWN:
                self.selected_line = min(self.selected_line + 1,
                                        len(self.rows) + self.header_lines - 1)
                self.repaint()
            elif char == self.curses.KEY_NPAGE:
                self.selected_line = min(self.selected_line + 10,
                                        len(self.rows) + self.header_lines - 1)
                self.repaint()
            elif char == self.curses.KEY_HOME:
                self.first_visible_line = 0
                self.selected_line = self.header_lines
            elif char == ord("g"):
                self.selected_line = self.header_lines
                self.repaint()
            elif char == ord("G"):
                self.selected_line = len(self.rows) + self.header_lines - 1
                self.repaint()
            elif char in (ord("a"), ord("A")):
                self.display_change_queue_mode_box()
            elif char == ord("l"):
                self.open_task_log()
            elif char == ord("c"):
                self.change_task_name()
            elif char == ord("f"):
                self.change_task_sleeptime()
            elif char == ord("j"):
                self.change_task_runtime()
            elif char == ord("L"):
                self.open_task_log(err=True)
            elif char in (ord("w"), ord("W")):
                self.wakeup_task()
            elif char in (ord("n"), ord("N")):
                self.change_task_priority()
            elif char in (ord("r"), ord("R")):
                if status in ('WAITING', 'SCHEDULED'):
                    self.run_task()
            elif char in (ord("s"), ord("S")):
                self.sleep_task()
            elif char in (ord("k"), ord("K")):
                if status in ('ERROR', 'DONE WITH ERRORS', 'ERRORS REPORTED'):
                    self.acknowledge_task()
                elif status is not None:
                    self.kill_task()
            elif char in (ord("t"), ord("T")):
                self.stop_task()
            elif char == ord("d"):
                self.delete_task()
            elif char == ord("D"):
                self.debug_task()
            elif char in (ord("i"), ord("I")):
                self.init_task()
            elif char in (ord("p"), ord("P")):
                self.purge_done()
            elif char in (ord("o"), ord("O")):
                self.display_task_options()
            elif char in (ord("z"), ord("Z")):
                self.toggle_debug_mode()
            elif char in (ord("b"), ord("B")):
                self.open_bibsched_log()
            elif char in (ord("h"), ord("H")):
                self.display_help()
            elif char in (ord("e"), ord("E")):
                self.edit_motd()
                self.read_motd()
            elif char == ord("1"):
                self.display = 1
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                # We need to update the display to display done tasks
                self.update_rows()
                self.repaint()
                self.display_in_footer("only done processes are displayed")
            elif char == ord("2"):
                self.display = 2
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                # We need to update the display to display not done tasks
                self.update_rows()
                self.repaint()
                self.display_in_footer("only not done processes are displayed")
            elif char == ord("3"):
                self.display = 3
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                # We need to update the display to display archived tasks
                self.update_rows()
                self.repaint()
                self.display_in_footer("only archived processes are displayed")
            elif char == ord("4"):
                self.display = 4
                self.first_visible_line = 0
                self.selected_line = self.header_lines
                # We need to update the display to display archived tasks
                self.update_rows()
                self.repaint()
                self.display_in_footer("only non periodic processes are displayed")
            elif char in (ord("q"), ord("Q")):
                if self.curses.panel.top_panel() == self.panel:
                    self.panel = None
                    self.curses.panel.update_panels()
                else:
                    self.running = 0
                    return

    def display_help(self):
        msg = """Help
====
Q - Quit
b - View bibsched log
P - Purge
e - Edit motd
1 - View completed tasks
2 - View running/waiting tasks
3 - View archived tasks
z - Toggle debug mode
a - Toggle automatic mode
g - Go to the beginning of the task list
G - Go to the end of the task list
\t
Shortcuts that act on the selected task:
l - View task log
o - Display task options
i - Reinitialize task
d - Delete task
t - Stop task
k - Acknowledge task
s - Sleep task
r - Run task
n - Change task priority
c - Change task name
f - Change task sleeptime
j - Change task runtime
w - Wake up task
D - Debug mode for remote task
"""
        self._display_message_box(msg)

    def openlog(self, logname):
        if os.path.exists(logname):
            pager = get_pager()
            if os.path.exists(pager):
                self.curses.endwin()
                os.system('%s %s' % (pager, logname))
                print >> self.old_stdout, "\rPress ENTER to continue",
                self.old_stdout.flush()
                raw_input()
                # We need to redraw the bibsched task list
                # since we are displaying "Press ENTER to continue"
                self.repaint()
            else:
                self._display_message_box("No pager was found")

    def open_task_log(self, err=False):
        task_id = self.currentrow[0]
        if err:
            log_path = task_log_path(task_id, 'err')
        else:
            log_path = task_log_path(task_id, 'log')
        self.openlog(log_path)

    def open_bibsched_log(self):
        logname = os.path.join(CFG_LOGDIR, 'bibsched.log')
        self.openlog(logname)

    def edit_motd(self):
        """Add, delete or change the motd message that will be shown when the
        bibsched monitor starts."""
        editor = get_editor()
        if editor:
            previous = self.motd
            self.curses.endwin()
            if not os.path.isfile(CFG_MOTD_PATH) or not open(CFG_MOTD_PATH).read():
                f = open(CFG_MOTD_PATH, 'w')
                try:
                    f.write('<reason>')
                finally:
                    f.close()
            os.system("%s %s" % (editor, CFG_MOTD_PATH))

            # Add the user in front of the motd:
            # <user>, <reason>
            user = get_user()
            if user:
                f = open(CFG_MOTD_PATH, 'r')
                try:
                    new_motd = f.read()
                finally:
                    f.close()
                # Remove the user part of the motd
                # It should be in this format:
                # <user>, <reason>
                new_motd = new_motd.split(',')[-1].strip()

                if new_motd.strip():
                    f = open(CFG_MOTD_PATH, 'w')
                    try:
                        f.write('%s, %s' % (user, new_motd))
                    finally:
                        f.close()

            # We need to redraw the MOTD part
            self.read_motd()
            self.repaint()

            if previous[24:] != self.motd[24:]:
                if len(previous) == 0:
                    log('motd set to "%s"' % self.motd.replace("\n", "|"))
                    self.selected_line += 1
                    self.header_lines += 1
                elif len(self.motd) == 0:
                    log('motd deleted')
                    self.selected_line -= 1
                    self.header_lines -= 1
                else:
                    log('motd changed to "%s"' % self.motd.replace("\n", "|"))
        else:
            self._display_message_box("No editor was found")

    def display_task_options(self):
        """Nicely display information about current process."""
        msg = '        id: %i\n\n' % self.currentrow[0]
        pid = get_task_pid(self.currentrow[0])
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
            args_str = ' '.join(arguments[1:])
            if len(args_str) > 500:
                args_str = args_str[:500] + '...'
            msg += ' arguments : %s\n\n' % args_str
        msg += '\n\nPress q to quit this panel...'
        msg = wrap_text_in_a_box(msg, style='no_border', break_long=True)
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
        self.panel = None

    def count_processes(self, status):
        return run_sql("""SELECT COUNT(id) FROM schTASK
                         WHERE status=%s GROUP BY status""", (status,))[0][0]

    def change_task_name(self):
        task_id = self.currentrow[0]
        try:
            base_name, task_name = self.currentrow[1].split(':', 1)
        except ValueError:
            base_name = self.currentrow[1]
            task_name = ""
        name = self._display_ask_string_box('Enter the new task name:',
                                            default=task_name)
        if name:
            new_name = '%s:%s' % (base_name, name)
        else:
            new_name = base_name

        bibsched_set_name(task_id, new_name)
        # We need to update the tasks list with our new priority
        # to be able to display it
        self.update_rows()
        # We need to update the priority number next to the task
        self.repaint()

    def change_task_sleeptime(self):
        task_id = self.currentrow[0]
        sleeptime = self.currentrow[4]
        new_sleeptime = self._display_ask_string_box('Enter the new task sleeptime:',
                                                     default=sleeptime)

        bibsched_set_sleeptime(task_id, new_sleeptime)
        # We need to update the tasks list with our new priority
        # to be able to display it
        self.update_rows()
        # We need to update the priority number next to the task
        self.repaint()

    def change_task_runtime(self):
        task_id = self.currentrow[0]
        runtime = self.currentrow[3]
        new_runtime = self._display_ask_string_box('Enter the new task runtime:',
                                                     default=runtime.strftime("%Y-%m-%d_%H:%M:%S"))

        bibsched_set_runtime(task_id, new_runtime)
        # We need to update the tasks list with our new priority
        # to be able to display it
        self.update_rows()
        # We need to update the priority number next to the task
        self.repaint()

    def change_task_priority(self):
        task_id = self.currentrow[0]
        priority = self.currentrow[8]
        new_priority = self._display_ask_string_box("Insert the desired \
priority for task %s. The smaller the number the less the priority. Note that \
a number less than -10 will mean to always postpone the task while a number \
bigger than 10 will mean some tasks with less priority could be stopped in \
order to let this task run. The current priority is %s. New value:"
                                                        % (task_id, priority),
                                                        default=str(priority))
        try:
            new_priority = int(new_priority)
        except ValueError:
            return
        bibsched_set_priority(task_id, new_priority)

        # We need to update the tasks list with our new priority
        # to be able to display it
        self.update_rows()
        # We need to update the priority number next to the task
        self.repaint()

    def wakeup_task(self):
        if not self.currentrow:
            self.display_in_footer("no task selected")
            return

        task_id = self.currentrow[0]
        status = self.currentrow[5]
        #if self.count_processes('RUNNING') + self.count_processes('CONTINUING') >= 1:
            #self.display_in_footer("a process is already running!")
        if status == "SLEEPING":
            if not bibsched_send_signal(task_id, signal.SIGCONT):
                bibsched_set_status(task_id, "ERROR", "SLEEPING")
            self.update_rows()
            self.repaint()
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
        self.panel = self.curses.panel.new_panel(self.win)
        self.panel.top()
        self.win.border()
        i = 1
        for row in rows:
            self.win.addstr(i, 2, row, self.current_attr)
            i += 1
        self.win.refresh()
        try:
            while 1:
                c = self.win.getch()
                if c in (ord('y'), ord('Y')):
                    return True
                elif c in (ord('n'), ord('N')):
                    return False
        finally:
            self.panel = None

    def _display_ask_string_box(self, msg, default=""):
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
        self.panel = self.curses.panel.new_panel(self.win)
        self.panel.top()
        self.win.border()
        i = 1
        for row in rows:
            self.win.addstr(i, 2, row, self.current_attr)
            i += 1
        self.win.refresh()
        self.win.move(height - 2, 2)
        self.curses.echo()
        for c in reversed(default):
            self.curses.ungetch(c)
        ret = self.win.getstr()
        self.curses.noecho()
        self.panel = None
        return ret

    def _display_message_box(self, msg):
        """Utility to display message boxes."""
        rows = list(chain(*(textwrap.wrap(line, self.width-6) for line in msg.split('\n'))))
        height = len(rows) + 2
        width = max([len(row) for row in rows]) + 4
        self.win = self.curses.newwin(
            height,
            width,
            (self.height - height) / 2 + 1,
            (self.width - width) / 2 + 1
        )
        self.panel = self.curses.panel.new_panel(self.win)
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
        self.panel = None

    def display_change_queue_mode_box(self, extend_time=False):
        """Utility to display confirmation boxes."""
        # We do not need a confirmation box for putting the queue back
        # to automatic mode
        if not self.auto_mode and not extend_time:
            self.change_auto_mode(True)
            return

        height = 6
        width = 38

        options = (
            (5*60, "5 min"),
            (3600, "1 hour"),
            (-1, "forever"),
        )
        state = {'selected_option': 5*60}

        def draw_options():
            msg = "Change queue to manual mode".center(width-3)
            self.win.addstr(1, 2, msg, self.current_attr)
            i = 2
            for value, name in options:
                row = name.center(11)
                if value == state['selected_option']:
                    color = self.curses.color_pair(9)
                else:
                    color = self.current_attr
                self.win.addstr(3, i, row, color)
                i += len(row)
                if not value == options[-1][0]:
                    self.win.addstr(3, i, '|', self.current_attr)
                i += 1
            self.win.addstr(4, 2, ' ', self.current_attr)

        def find_selected_index():
            for i, v in enumerate(options):
                if v[0] == state['selected_option']:
                    return i

        def move_selection(offset):
            selected_index = find_selected_index()
            requested_index = selected_index + offset
            if 0 <= requested_index < len(options):
                state['selected_option'] = options[requested_index][0]
                draw_options()

        self.win = self.curses.newwin(
            height,
            width,
            (self.height - height) / 2 + 1,
            (self.width - width) / 2 + 1
        )
        self.panel = self.curses.panel.new_panel(self.win)
        self.panel.top()
        self.win.border()
        draw_options()
        self.win.refresh()
        try:
            while True:
                c = self.win.getch()
                if c == ord('q'):
                    return
                elif c in (self.curses.KEY_RIGHT, 67):
                    move_selection(1)
                elif c in (self.curses.KEY_LEFT, 68):
                    move_selection(-1)
                elif c in (self.curses.KEY_ENTER, 10):
                    # Require a motd if the duration is more than 5min
                    if 0 < state['selected_option'] <= 5*60:
                        self.change_auto_mode(False, state['selected_option'])
                        return
                    else:
                        # Forever selected
                        # Change to manual mode with no duration
                        self.edit_motd()
                        self.read_motd()
                        if self.motd and len(self.motd) > 30:
                            self.change_auto_mode(False, duration=None)
                            return
                        else:
                            self.win.border()
                            draw_options()
                            self.win.addstr(4, 2, 'motd too short', self.current_attr)
        finally:
            self.panel = None
            self.update_rows()
            self.repaint()

    def purge_done(self):
        """Garbage collector."""
        if self._display_YN_box(
            "You are going to purge the list of DONE tasks.\n\n"
            "%s tasks, submitted since %s days, will be archived.\n\n"
            "%s tasks, submitted since %s days, will be deleted.\n\n"
            "Are you sure?" % (
                ', '.join(CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE),
                CFG_BIBSCHED_GC_TASKS_OLDER_THAN,
                ', '.join(CFG_BIBSCHED_GC_TASKS_TO_REMOVE),
                CFG_BIBSCHED_GC_TASKS_OLDER_THAN)):
            gc_tasks()
            # We removed some tasks from our list
            self.update_rows()
            self.repaint()
            self.display_in_footer("DONE processes purged")

    def run_task(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1].split(':')[0]
        status = self.currentrow[5]

        if status == "WAITING":
            if process in self.helper_modules:
                if run_sql("""UPDATE schTASK SET status='SCHEDULED', host=%s
                              WHERE id=%s and status='WAITING'""",
                           (self.hostname, task_id)):
                    program = os.path.join(CFG_BINDIR, process)
                    command = "%s %s" % (program, str(task_id))
                    spawn_task(command)
                    log("manually running task #%d (%s)" % (task_id, process))
                    # We changed the status of one of our tasks
                    self.update_rows()
                    self.repaint()
                else:
                    ## Process already running (typing too quickly on the keyboard?)
                    pass
            else:
                self.display_in_footer("Process %s is not in the list of allowed processes." % process)
        else:
            self.display_in_footer("Process status should be SCHEDULED or WAITING!")

    def acknowledge_task(self):
        task_id = self.currentrow[0]
        task_name = self.currentrow[1]
        status = self.currentrow[5]
        if status in ('ERROR', 'DONE WITH ERRORS', 'ERRORS REPORTED'):
            argv = task_get_options(task_id, task_name)
            sleeptime = get_sleeptime(argv)
            if not sleeptime or self._display_YN_box("WARNING! This is a periodic task.\n\nAre you sure you want to acknowledge the %s process %s?" % (task_name, task_id)):
                bibsched_set_status(task_id, 'ACK ' + status, status)
                self.update_rows()
                self.repaint()
                self.display_in_footer("Acknowledged error")

    def debug_task(self):
        task_id = self.currentrow[0]
        bibsched_send_signal(task_id, signal.SIGUSR2)
        self.display_in_footer("Task set in debug mode")

    def sleep_task(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status in ('RUNNING', 'CONTINUING'):
            bibsched_set_status(task_id, 'ABOUT TO SLEEP', status)
            self.update_rows()
            self.repaint()
            self.display_in_footer("SLEEP signal sent to task #%s" % task_id)
        else:
            self.display_in_footer("Cannot put to sleep non-running processes")

    def kill_task(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        if status in ('RUNNING', 'CONTINUING', 'ABOUT TO STOP', 'ABOUT TO SLEEP', 'SLEEPING'):
            if self._display_YN_box("Are you sure you want to kill the %s process %s?" % (process, task_id)):
                bibsched_send_signal(task_id, signal.SIGKILL)
                bibsched_set_status(task_id, 'KILLED')
                self.update_rows()
                self.repaint()
                self.display_in_footer("KILL signal sent to task #%s" % task_id)
        else:
            self.display_in_footer("Cannot kill non-running processes")

    def stop_task(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status in ('RUNNING', 'CONTINUING', 'ABOUT TO SLEEP', 'SLEEPING'):
            if status == 'SLEEPING':
                bibsched_set_status(task_id, 'NOW STOP', 'SLEEPING')
                bibsched_send_signal(task_id, signal.SIGCONT)
                count = 10
                while bibsched_get_status(task_id) == 'NOW STOP':
                    if count <= 0:
                        bibsched_set_status(task_id, 'ERROR', 'NOW STOP')
                        self.update_rows()
                        self.repaint()
                        self.display_in_footer("It seems impossible to wakeup this task.")
                        return
                    time.sleep(CFG_BIBSCHED_REFRESHTIME)
                    count -= 1
            else:
                bibsched_set_status(task_id, 'ABOUT TO STOP', status)
            self.update_rows()
            self.repaint()
            self.display_in_footer("STOP signal sent to task #%s" % task_id)
        else:
            self.display_in_footer("Cannot stop non-running processes")

    def delete_task(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status not in ('RUNNING', 'CONTINUING', 'SLEEPING', 'SCHEDULED',
                          'ABOUT TO STOP', 'ABOUT TO SLEEP'):
            msg = 'Are you sure you want to delete this task?'
            if self._display_YN_box(msg):
                bibsched_set_status(task_id, "%s_DELETED" % status, status)
                self.display_in_footer("process deleted")
                self.update_rows()
                self.repaint()
        else:
            self.display_in_footer("Cannot delete running processes")

    def init_task(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status not in ('RUNNING', 'CONTINUING', 'SLEEPING'):
            bibsched_set_status(task_id, "WAITING")
            bibsched_set_progress(task_id, "")
            bibsched_set_host(task_id, "")
            self.update_rows()
            self.repaint()
            self.display_in_footer("process initialised")
        else:
            self.display_in_footer("Cannot initialise running processes")

    def fetch_auto_mode(self):
        # If the daemon is not running at all, we are in manual mode
        if not server_pid():
            status = 0
        else:
            # Otherwise check the daemon status
            r = run_sql("""SELECT value FROM "schSTATUS" WHERE name = 'auto_mode'""")
            try:
                status = int(r[0][0])
            except (ValueError, IndexError):
                status = 0
        return status

    def check_auto_mode(self):
        new_status = self.fetch_auto_mode()
        if self.auto_mode == 1 and new_status == 0:
            self.curses.beep()
        self.auto_mode = new_status

    def change_auto_mode(self, new_mode, duration=None):
        if not server_pid():
            program = os.path.join(CFG_BINDIR, "bibsched")
            COMMAND = "%s -q start" % program
            os.system(COMMAND)

        # Enable automatic mode
        if new_mode:
            run_sql("""UPDATE "schSTATUS" SET value = '' WHERE name = 'resume_after'""")
            run_sql("""UPDATE "schSTATUS" SET value = '1' WHERE name = 'auto_mode'""")
            log('queue changed to automatic mode')
        # Enable manual mode
        else:
            run_sql("""UPDATE "schSTATUS" SET value = '0' WHERE name = 'auto_mode'""")
            if duration:
                resume_after = datetime.now() + timedelta(seconds=duration)
                resume_after = resume_after.strftime("%Y-%m-%d %H:%M:%S")
            else:
                resume_after = ""
            run_sql("""REPLACE INTO "schSTATUS" (name, value) VALUES ('resume_after', %s)""", [resume_after])
            if duration:
                log('queue changed to manual mode for %ss' % duration)
            else:
                log('queue changed to manual mode')

        self.auto_mode = not self.auto_mode

        # We need to refresh the color of the header and footer
        self.repaint()

    def toggle_debug_mode(self):
        if self.debug_mode:
            self.display_in_footer("Deactivating debug mode")
            self.debug_mode = 0
            value = "0"
        else:
            self.display_in_footer("Activating debug mode")
            self.debug_mode = 1
            value = "1"

        run_sql("""UPDATE "schSTATUS" SET value = %s WHERE name = 'debug_mode' """,
                [value])



    def put_line(self, row, header=False, motd=False):
        ## ROW: (id,proc,user,runtime,sleeptime,status,progress,arguments,priority,host)
        ##       0  1    2    3       4         5      6        7         8        9
        col_w = [8 , 25, 15, 21, 7, 12, 21, 60]
        maxx = self.width
        if self.y == self.selected_line - self.first_visible_line and self.y > 1:
            self.item_status = row[5]
            self.currentrow = row
        if motd:
            attr = self.curses.color_pair(1) + self.curses.A_BOLD
        elif self.y == self.header_lines - 2:
            if self.auto_mode:
                attr = self.curses.color_pair(2) + self.curses.A_STANDOUT + self.curses.A_BOLD
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
        elif row[5] in ("RUNNING", "CONTINUING"):
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
        if header:  # Dirty hack. put_line should be better refactored.
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
        self.y += 1

    def display_in_footer(self, footer, i=0, print_time_p=0):
        if print_time_p:
            footer = "%s %s" % (footer, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        maxx = self.stdscr.getmaxyx()[1]
        footer = footer.ljust(maxx)
        if self.auto_mode:
            colorpair = 2
        else:
            colorpair = 1
        try:
            self.stdscr.addnstr(self.y - i, 0, footer, maxx - 1, self.curses.A_STANDOUT + self.curses.color_pair(colorpair) + self.curses.A_BOLD)
        except self.curses.error:
            pass

    def tick(self):
        self.update_rows()
        self.repaint()

        self.debug_mode = fetch_debug_mode()

        if self.manual_mode_time_left and self.manual_mode_time_left.seconds < 10:
            self.display_change_queue_mode_box(extend_time=True)

    def repaint(self):
        self.check_auto_mode()
        self.y = 0
        self.stdscr.erase()
        self.height, self.width = self.stdscr.getmaxyx()
        maxy = self.height - 2
        #maxx = self.width
        if len(self.motd) > 0:
            self.put_line((self.motd.strip().replace("\n", " - ")[:self.width-1], "", "", "", "", "", "", "", ""), header=False, motd=True)
        self.put_line(("ID", "PROC [PRI]", "USER", "RUNTIME", "SLEEP", "STATUS", "HOST", "PROGRESS"), header=True)
        self.put_line(("", "", "", "", "", "", "", ""), header=True)
        if self.selected_line > maxy + self.first_visible_line - 1:
            self.first_visible_line = self.selected_line - maxy + 1
        if self.selected_line < self.first_visible_line + 2:
            self.first_visible_line = self.selected_line - 2
        for row in self.rows[self.first_visible_line:self.first_visible_line+maxy-2]:
            self.put_line(row)
        self.y = self.stdscr.getmaxyx()[0] - 1
        if self.debug_mode:
            debug_footer = "DEBUG MODE!! "
        else:
            debug_footer = ""
        if self.auto_mode:
            self.display_in_footer(debug_footer + self.footer_auto_mode,
                                   print_time_p=1)
        else:
            if self.manual_mode_time_left:
                time_left = " %02d:%02d remaining" % (self.manual_mode_time_left.seconds / 60, self.manual_mode_time_left.seconds % 60)
            else:
                time_left = ""
            footer = self.footer_manual_mode % time_left
            self.display_in_footer(debug_footer + footer,
                                   print_time_p=1)
            footer2 = ""
            if self.item_status.find("DONE") > -1 or self.item_status in ("ERROR", "STOPPED", "KILLED", "ERRORS REPORTED"):
                footer2 += self.footer_stopped_item
            elif self.item_status in ("RUNNING", "CONTINUING", "ABOUT TO STOP", "ABOUT TO SLEEP"):
                footer2 += self.footer_running_item
            elif self.item_status == "SLEEPING":
                footer2 += self.footer_sleeping_item
            elif self.item_status == "WAITING":
                footer2 += self.footer_waiting_item
            self.display_in_footer(footer2, 1)
        self.stdscr.refresh()

    def update_rows(self):
        self.manual_mode_time_left = None
        r = run_sql("""SELECT value FROM "schSTATUS" WHERE name = 'resume_after'""")
        if r and r[0] and r[0][0]:
            date_string = r[0][0]
            resume_after = datetime(*(time.strptime(date_string, "%Y-%m-%d %H:%M:%S")[0:6]))
            now = datetime.now()
            if resume_after > now:
                self.manual_mode_time_left = resume_after - now

        try:
            selected_row = self.rows[self.selected_line - self.header_lines]
        except IndexError:
            selected_id = 0
        else:
            selected_id = selected_row[0]
        if self.display == 1:
            table = "schTASK"
            where = "WHERE status IN ('DONE', 'ACK DONE', 'ACK DONE WITH ERRORS', 'ACK ERROR', 'ACK ERRORS REPORTED')"
            order = "runtime DESC"
            limit = "LIMIT %s" % CFG_BIBSCHED_MAX_ARCHIVED_ROWS_DISPLAY
        elif self.display == 2:
            table = "schTASK"
            where = "WHERE status IN ('RUNNING', 'CONTINUING', 'SCHEDULED', 'ABOUT TO STOP', 'ABOUT TO SLEEP', 'SLEEPING', 'WAITING', 'ERRORS REPORTED', 'DONE WITH ERRORS', 'ERROR', 'CERROR', 'KILLED', 'STOPPED')"
            order = "runtime ASC"
            limit = ""
        elif self.display == 3:
            table = "hstTASK"
            order = "runtime DESC"
            where = ""
            limit = ""
        elif self.display == 4:
            table = "schTASK"
            where = "WHERE status IN ('RUNNING', 'CONTINUING', 'SCHEDULED', 'ABOUT TO STOP', 'ABOUT TO SLEEP', 'SLEEPING', 'WAITING', 'ERRORS REPORTED', 'DONE WITH ERRORS', 'ERROR', 'CERROR', 'KILLED', 'STOPPED') AND sleeptime = \"\""
            order = "runtime ASC"
            limit = ""

        self.rows = run_sql("""SELECT id, proc, user, runtime, sleeptime,
                               status, progress, arguments, priority, host,
                               sequenceid
                               FROM %s
                               %s
                               ORDER BY %s
                               %s""" % (table, where, order, limit))

        for row_index, row in enumerate(self.rows):
            if row[0] == selected_id:
                self.selected_line = row_index + self.header_lines
                break
        else:
            # Make sure we are not selecting a line that disappeared
            self.selected_line = min(self.selected_line,
                                     len(self.rows) + self.header_lines - 1)

    def start(self, stdscr):
        os.environ['BIBSCHED_MODE'] = 'manual'
        if self.curses.has_colors():
            self.curses.start_color()
            self.curses.init_pair(1, self.curses.COLOR_WHITE, self.curses.COLOR_RED)
            self.curses.init_pair(2, self.curses.COLOR_GREEN, self.curses.COLOR_BLACK)
            self.curses.init_pair(3, self.curses.COLOR_MAGENTA, self.curses.COLOR_BLACK)
            self.curses.init_pair(4, self.curses.COLOR_RED, self.curses.COLOR_BLACK)
            self.curses.init_pair(5, self.curses.COLOR_BLUE, self.curses.COLOR_BLACK)
            self.curses.init_pair(6, self.curses.COLOR_CYAN, self.curses.COLOR_BLACK)
            self.curses.init_pair(7, self.curses.COLOR_YELLOW, self.curses.COLOR_BLACK)
            self.curses.init_pair(8, self.curses.COLOR_WHITE, self.curses.COLOR_BLACK)
            self.curses.init_pair(9, self.curses.COLOR_BLACK, self.curses.COLOR_WHITE)
        self.stdscr = stdscr
        self.base_panel = self.curses.panel.new_panel(self.stdscr)
        self.base_panel.bottom()
        self.curses.panel.update_panels()
        self.height, self.width = stdscr.getmaxyx()
        self.stdscr.erase()
        self.check_auto_mode()
        self.debug_mode = fetch_debug_mode()
        ring = 4
        if len(self.motd) > 0:
            self._display_message_box(self.motd + "\nPress any key to close")
        while self.running:
            if ring == 4:
                self.read_motd()
                self.tick()
                ring = 0
            ring += 1
            char = -1
            try:
                char = timed_out(self.stdscr.getch, 1)
                if char == 27:  # escaping sequence
                    char = self.stdscr.getch()
                    if char == 79:  # arrow
                        char = self.stdscr.getch()
                        if char == 65:  # arrow up
                            char = self.curses.KEY_UP
                        elif char == 66:  # arrow down
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


def monitor(verbose=True, debug=False): # pylint: disable=W0613
    old_stdout, old_stderr = redirect_stdout_and_stderr()
    try:
        Manager(old_stdout)
    finally:
        restore_stdout_and_stderr(old_stdout, old_stderr)
