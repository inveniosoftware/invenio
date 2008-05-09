# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibSched - task management, scheduling and executing system for CDS Invenio
"""

__revision__ = "$Id$"

import os
import string
import sys
import time
import datetime
import re
import marshal
import getopt
from socket import gethostname
import signal
from tempfile import NamedTemporaryFile

from invenio.bibtask_config import CFG_BIBTASK_VALID_TASKS
from invenio.config import \
     CFG_PREFIX, \
     CFG_BIBSCHED_REFRESHTIME, \
     CFG_BIBSCHED_LOG_PAGER, \
     CFG_BINDIR, \
     CFG_LOGDIR, \
     CFG_TMPDIR, \
     CFG_BIBSCHED_GC_TASKS_OLDER_THAN, \
     CFG_BIBSCHED_GC_TASKS_TO_REMOVE, \
     CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE, \
     CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS
from invenio.dbquery import run_sql, escape_string
from invenio.textutils import wrap_text_in_a_box
from invenio.errorlib import register_exception

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
            #date = time.strftime(format_string, date)
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
    answer = string.strip(os.popen(COMMAND).read())
    if answer == '':
        answer = 0
    else:
        answer = answer[:string.find(answer,' ')]
    return int(answer)

def get_task_pid(task_name, task_id):
    """Return the pid of task_name/task_id"""
    try:
        pid = int(open(os.path.join(CFG_PREFIX, 'var', 'run', 'bibsched_task_%d.pid' % task_id)).read())
        os.kill(pid, signal.SIGUSR2)
        return pid
    except (OSError, IOError):
        register_exception()
        return get_my_pid(task_name, str(task_id))

def get_output_channelnames(task_id):
    "Construct and return filename for stdout and stderr for the task 'task_id'."
    filenamebase = "%s/bibsched_task_%d" % (CFG_LOGDIR, task_id)
    return [filenamebase + ".log", filenamebase + ".err"]

def is_task_scheduled(task_name):
    """Check if a certain task_name is due for execution (WAITING or RUNNING)"""
    sql = "SELECT COUNT(proc) FROM schTASK WHERE proc = %s AND (status = 'WAITING' or status = 'RUNNING')"
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
        return {}

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

    status_query = 'status in (%s)' % ','.join([repr(escape_string(status)) for status in statuses])

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

class Manager:
    def __init__(self, old_stdout):
        import curses
        import curses.panel
        from curses.wrapper import wrapper
        self.old_stdout = old_stdout
        self.curses = curses
        self.helper_modules = CFG_BIBTASK_VALID_TASKS
        self.running = 1
        self.footer_move_mode = "[KeyUp/KeyDown Move] [M Select mode] [Q Quit]"
        self.footer_auto_mode = "[A Manual mode] [1/2/3 Display] [P Purge Done] [Q Quit]"
        self.footer_select_mode = "[KeyUp/KeyDown/PgUp/PgDown Select] [L View Log] [1/2/3 Display Type] [M Move mode] [A Auto mode] [Q Quit]"
        self.footer_waiting_item = "[R Run] [D Delete]"
        self.footer_running_item = "[S Sleep] [T Stop] [K Kill]"
        self.footer_stopped_item = "[I Initialise] [D Delete]"
        self.footer_sleeping_item   = "[W Wake Up]"
        self.item_status = ""
        self.selected_line = 2
        self.rows = []
        self.panel = None
        self.display = 2
        self.first_visible_line = 0
        self.move_mode = 0
        self.auto_mode = 0
        self.currentrow = None
        wrapper(self.start)

    def handle_keys(self, chr):
        if chr == -1:
            return
        if self.auto_mode and (chr not in (self.curses.KEY_UP,
                                           self.curses.KEY_DOWN,
                                           self.curses.KEY_PPAGE,
                                           self.curses.KEY_NPAGE,
                                           ord("q"), ord("Q"), ord("a"),
                                           ord("A"), ord("1"), ord("2"), ord("3"),
                                           ord("p"), ord("P"), ord("o"), ord("O"),
                                           ord("l"), ord("L"))):
            self.display_in_footer("in automatic mode")
            self.stdscr.refresh()
        elif self.move_mode and (chr not in (self.curses.KEY_UP,
                                             self.curses.KEY_DOWN,
                                             ord("m"), ord("M"), ord("q"),
                                             ord("Q"))):
            self.display_in_footer("in move mode")
            self.stdscr.refresh()
        else:
            if chr == self.curses.KEY_UP:
                if self.move_mode:
                    self.move_up()
                else:
                    self.selected_line = max(self.selected_line - 1, 2)
                self.repaint()
            if chr == self.curses.KEY_PPAGE:
                self.selected_line = max(self.selected_line - 10, 2)
                self.repaint()
            elif chr == self.curses.KEY_DOWN:
                if self.move_mode:
                    self.move_down()
                else:
                    self.selected_line = min(self.selected_line + 1, len(self.rows) + 1 )
                self.repaint()
            elif chr == self.curses.KEY_NPAGE:
                self.selected_line = min(self.selected_line + 10, len(self.rows) + 1 )
                self.repaint()
            elif chr == self.curses.KEY_HOME:
                self.first_visible_line = 0
                self.selected_line = 2
            elif chr in (ord("a"), ord("A")):
                self.change_auto_mode()
            elif chr in (ord("l"), ord("L")):
                self.openlog()
            elif chr in (ord("w"), ord("W")):
                self.wakeup()
            elif chr in (ord("r"), ord("R")):
                self.run()
            elif chr in (ord("s"), ord("S")):
                self.sleep()
            elif chr in (ord("k"), ord("K")):
                self.kill()
            elif chr in (ord("t"), ord("T")):
                self.stop()
            elif chr in (ord("d"), ord("D")):
                self.delete()
            elif chr in (ord("i"), ord("I")):
                self.init()
            elif chr in (ord("m"), ord("M")):
                self.change_select_mode()
            elif chr in (ord("p"), ord("P")):
                self.purge_done()
            elif chr in (ord("o"), ord("O")):
                self.display_task_options()
            elif chr == ord("1"):
                self.display = 1
                self.first_visible_line = 0
                self.selected_line = 2
                self.display_in_footer("only done processes are displayed")
            elif chr == ord("2"):
                self.display = 2
                self.first_visible_line = 0
                self.selected_line = 2
                self.display_in_footer("only not done processes are displayed")
            elif chr == ord("3"):
                self.display = 3
                self.first_visible_line = 0
                self.selected_line = 2
                self.display_in_footer("only archived processes are displayed")
            elif chr in (ord("q"), ord("Q")):
                if self.curses.panel.top_panel() == self.panel:
                    self.panel.bottom()
                    self.curses.panel.update_panels()
                else:
                    self.running = 0
                    return

    def set_status(self, task_id, status):
        return run_sql("UPDATE schTASK set status=%s WHERE id=%s", (status, task_id))

    def set_progress(self, task_id, progress):
        return run_sql("UPDATE schTASK set progress=%s WHERE id=%s", (progress, task_id))

    def openlog(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        tmpfile = NamedTemporaryFile(dir=CFG_TMPDIR)
        try:
            tmpfile.write('bibsched_task_%d.log content\n' % task_id)
            tmpfile.write('-----------------------------------\n')
            tmpfile.write(open(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.log' % task_id)).read())
        except IOError:
            pass
        try:
            tmpfile.write('bibsched_task_%d.err content\n' % task_id)
            tmpfile.write('-----------------------------------\n')
            tmpfile.write(open(os.path.join(CFG_LOGDIR, 'bibsched_task_%d.err' % task_id)).read())
        except IOError:
            pass
        tmpfile.flush()
        pager = CFG_BIBSCHED_LOG_PAGER or os.environ.get('PAGER', '/bin/more')
        if os.path.exists(pager):
            self.curses.endwin()
            os.system('%s %s' % (pager, tmpfile.name))
            print >> self.old_stdout, "Press ENTER to continue",
            self.old_stdout.flush()
            raw_input()
            self.curses.panel.update_panels()

    def display_task_options(self):
        """Nicely display information about current process."""
        msg =  '        id: %i\n\n' % self.currentrow[0]
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
        msg += '\n\nPress a key to continue...'
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
            self.win.addstr(i, 2, row)
            i += 1
        self.win.refresh()
        self.win.getch()

    def count_processes(self, status):
        out = 0
        res = run_sql("SELECT COUNT(id) FROM schTASK WHERE status=%s GROUP BY status", (status,))
        try:
            out = res[0][0]
        except:
            pass
        return out

    def wakeup(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        if self.count_processes('RUNNING') + self.count_processes('CONTINUING') >= 1:
            self.display_in_footer("a process is already running!")
        elif status == "SLEEPING":
            mypid = get_task_pid(process, task_id)
            if mypid != 0:
                os.kill(mypid, signal.SIGCONT)
            self.display_in_footer("process woken up")
        else:
            self.display_in_footer("process is not sleeping")
        self.stdscr.refresh()

    def _display_YN_box(self, msg):
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
            self.win.addstr(i, 2, row)
            i += 1
        self.win.refresh()
        while 1:
            c = self.win.getch()
            if c in (ord('y'), ord('Y')):
                return True
            elif c in (ord('n'), ord('N')):
                return False

    def purge_done(self):
        if self._display_YN_box("You are going to purge the list of DONE tasks.\n\n"
            "%s tasks, submitted since %s days, will be archived.\n\n"
            "%s tasks, submitted since %s days, will be deleted.\n\n"
            "Are you sure?" % (
                ','.join(CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE),
                CFG_BIBSCHED_GC_TASKS_OLDER_THAN,
                ','.join(CFG_BIBSCHED_GC_TASKS_TO_REMOVE),
                CFG_BIBSCHED_GC_TASKS_OLDER_THAN)):
            gc_tasks()
            self.curses.panel.update_panels()
            self.display_in_footer("DONE processes purged")
        else:
            self.curses.panel.update_panels()

    def run(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        #if self.count_processes('RUNNING') + self.count_processes('CONTINUING') >= 1:
            #self.display_in_footer("a process is already running!")
        if status == "STOPPED" or status == "WAITING":
            if process in self.helper_modules:
                program = os.path.join(CFG_BINDIR, process)
                fdout, fderr = get_output_channelnames(task_id)
                COMMAND = "%s %s >> %s 2>> %s &" % (program, str(task_id), fdout, fderr)
                os.system(COMMAND)
                Log("manually running task #%d (%s)" % (task_id, process))
        else:
            self.display_in_footer("process status should be STOPPED or WAITING!")
        self.stdscr.refresh()

    def sleep(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        if status != 'RUNNING' and status != 'CONTINUING':
            self.display_in_footer("this process is not running!")
        else:
            mypid = get_task_pid(process, task_id)
            if mypid != 0:
                os.kill(mypid, signal.SIGUSR1)
                self.display_in_footer("USR1 signal sent to process #%s" % mypid)
            else:
                self.set_status(task_id, 'STOPPED')
                self.display_in_footer("cannot find process...")
        self.stdscr.refresh()

    def kill(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        mypid = get_task_pid(process, task_id)
        if mypid != 0:
            os.kill(mypid, signal.SIGKILL)
            self.set_status(task_id, 'STOPPED')
            self.display_in_footer("KILL signal sent to process #%s" % mypid)
        else:
            self.set_status(task_id, 'STOPPED')
            self.display_in_footer("cannot find process...")
        self.stdscr.refresh()

    def stop(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        mypid = get_task_pid(process, task_id)
        if mypid != 0:
            os.kill(mypid, signal.SIGTERM)
            self.display_in_footer("TERM signal sent to process #%s" % mypid)
        else:
            self.set_status(task_id, 'STOPPED')
            self.display_in_footer("cannot find process...")
        self.stdscr.refresh()

    def delete(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status not in ('RUNNING', 'CONTINUING', 'SLEEPING'):
            self.set_status(task_id, "%s_DELETED" % status)
            self.display_in_footer("process deleted")
            self.selected_line = max(self.selected_line, 2)
        else:
            self.display_in_footer("cannot delete running processes")
        self.stdscr.refresh()

    def init(self):
        task_id = self.currentrow[0]
        status = self.currentrow[5]
        if status != 'RUNNING' and status != 'CONTINUING' and status != 'SLEEPING':
            self.set_status(task_id, "WAITING")
            self.set_progress(task_id, "None")
            self.display_in_footer("process initialised")
        else:
            self.display_in_footer("cannot initialise running processes")
        self.stdscr.refresh()

    def change_select_mode(self):
        if self.move_mode:
            self.move_mode = 0
        else:
            status = self.currentrow[5]
            if status in ("RUNNING" , "CONTINUING" , "SLEEPING"):
                self.display_in_footer("cannot move running processes!")
            else:
                self.move_mode = 1
        self.stdscr.refresh()

    def change_auto_mode(self):
        if self.auto_mode:
            program = os.path.join(CFG_BINDIR, "bibsched")
            COMMAND = "%s -q stop" % program
            os.system(COMMAND)

            self.auto_mode = 0
        else:
            program = os.path.join( CFG_BINDIR, "bibsched")
            COMMAND = "%s -q start" % program
            os.system(COMMAND)

            self.auto_mode = 1
            self.move_mode = 0
        self.stdscr.refresh()

    def move_up(self):
        self.display_in_footer("not implemented yet")
        self.stdscr.refresh()

    def move_down(self):
        self.display_in_footer("not implemented yet")
        self.stdscr.refresh()

    def put_line(self, row, header=False):
        col_w = [5 , 15, 10, 21, 7, 11, 25]
        maxx = self.width
        if self.y == self.selected_line - self.first_visible_line and self.y > 1:
            if self.auto_mode:
                attr = self.curses.color_pair(2) + self.curses.A_STANDOUT + self.curses.A_BOLD
            elif self.move_mode:
                attr = self.curses.color_pair(7) + self.curses.A_STANDOUT + self.curses.A_BOLD
            else:
                attr = self.curses.color_pair(8) + self.curses.A_STANDOUT + self.curses.A_BOLD
            self.item_status = row[5]
            self.currentrow = row
        elif self.y == 0:
            if self.auto_mode:
                attr = self.curses.color_pair(2) + self.curses.A_STANDOUT + self.curses.A_BOLD
            elif self.move_mode:
                attr = self.curses.color_pair(7) + self.curses.A_STANDOUT + self.curses.A_BOLD
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
        if header: # Dirty hack. put_line should be better refactored.
            # row contains one less element: arguments
            myline = str(row[0]).ljust(col_w[0])
            myline += str(row[1]).ljust(col_w[1])
            myline += str(row[2])[:19].ljust(col_w[2])
            myline += str(row[3]).ljust(col_w[3])
            myline += str(row[4]).ljust(col_w[4])
            myline += str(row[5]).ljust(col_w[5])
            myline += str(row[6]).ljust(col_w[6])
        else:
            myline = str(row[0]).ljust(col_w[0])
            myline += (str(row[1]) + (row[8] and ' [%s]' % row[8] or '')).ljust(col_w[1])
            myline += str(row[2]).ljust(col_w[2])
            myline += str(row[3])[:19].ljust(col_w[3])
            myline += str(row[4]).ljust(col_w[4])
            myline += str(row[5]).ljust(col_w[5])
            myline += str(row[6]).ljust(col_w[6])
        myline = myline.ljust(maxx)
        self.stdscr.addnstr(self.y, 0, myline, maxx, attr)
        self.y = self.y+1

    def display_in_footer(self, footer, i = 0, print_time_p=0):
        if print_time_p:
            footer = "%s %s" % (footer, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        maxx = self.stdscr.getmaxyx()[1]
        footer = footer.ljust(maxx)
        if self.auto_mode:
            colorpair = 2
        elif self.move_mode:
            colorpair = 7
        else:
            colorpair = 1
        self.stdscr.addnstr(self.y - i, 0, footer, maxx - 1, self.curses.A_STANDOUT + self.curses.color_pair(colorpair) + self.curses.A_BOLD )

    def repaint(self):
        self.y = 0
        self.stdscr.clear()
        self.height, self.width = self.stdscr.getmaxyx()
        maxy = self.height - 2
        #maxx = self.width
        self.put_line(("ID", "PROC [PRI]", "USER", "RUNTIME", "SLEEP", "STATUS", "PROGRESS"), True)
        self.put_line(("---", "---------", "----", "-------------------", "-----", "-----", "--------"), True)
        if self.selected_line > maxy + self.first_visible_line - 1:
            self.first_visible_line = self.selected_line - maxy + 1
        if self.selected_line < self.first_visible_line + 2:
            self.first_visible_line = self.selected_line - 2
        for row in self.rows[self.first_visible_line:self.first_visible_line+maxy-2]:
            self.put_line(row)
        self.y = self.stdscr.getmaxyx()[0] - 1
        if self.auto_mode:
            self.display_in_footer(self.footer_auto_mode, print_time_p=1)
        elif self.move_mode:
            self.display_in_footer(self.footer_move_mode, print_time_p=1)
        else:
            self.display_in_footer(self.footer_select_mode, print_time_p=1)
            footer2 = ""
            if self.item_status.find("DONE") > -1 or self.item_status == "ERROR" or self.item_status == "STOPPED":
                footer2 += self.footer_stopped_item
            elif self.item_status == "RUNNING" or self.item_status == "CONTINUING":
                footer2 += self.footer_running_item
            elif self.item_status == "SLEEPING":
                footer2 += self.footer_sleeping_item
            elif self.item_status == "WAITING":
                footer2 += self.footer_waiting_item
            self.display_in_footer(footer2, 1)
        self.stdscr.refresh()

    def start(self, stdscr):
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
        while self.running:
            if ring == 4:
                if self.display == 1:
                    table = "schTASK"
                    where = "and status='DONE'"
                    order = "runtime DESC"
                elif self.display == 2:
                    table = "schTASK"
                    where = "and status<>'DONE'"
                    order = "priority DESC, runtime ASC"
                else:
                    table = "hstTASK"
                    order = "runtime DESC"
                    where = ''
                self.rows = run_sql("""SELECT id,proc,user,runtime,sleeptime,status,progress,arguments,priority FROM %s WHERE status NOT LIKE '%%DELETED%%' %s ORDER BY %s""" % (table, where, order))
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
        self.helper_modules = CFG_BIBTASK_VALID_TASKS
        self.running = {}
        self.sleep_done = {}
        self.sleep_sent = {}
        self.stop_sent = {}
        self.suicide_sent = {}
        self.scheduled = None

    def set_status(self, task_id, status):
        return run_sql("UPDATE schTASK set status=%s WHERE id=%s", (status, task_id))

    def tasks_safe_p(self, proc1, proc2):
        """Return True when the two tasks can run concurrently."""
        return proc1 != proc2

    def get_tasks_to_sleep_and_stop(self, proc, task_set):
        """Among the task_set (built after the set of tasks with lower priority
        than proc), return the dict of task to stop and the dict of task to sleep.
        """
        min_prio = None
        min_task_id = None
        min_proc = None
        to_stop = {}
        for this_task_id, (this_proc, this_priority) in task_set.iteritems():
            if self.tasks_safe_p(proc, this_proc):
                if min_prio is None or this_priority < min_prio:
                    min_prio = this_priority
                    min_task_id = this_task_id
                    min_proc = this_proc
            else:
                to_stop[this_task_id] = (this_proc, this_priority)
        if len(task_set) < CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS and not to_stop:
            ## All the task are safe and there are enough resources
            return {}, {}
        else:
            return to_stop, {min_task_id : (min_proc, min_prio)}

    def split_running_tasks_by_priority(self, task_id, priority):
        """Return two sets (by dict): the set of task_ids with lower priority and
        those with higher or equal priority."""
        higher = {}
        lower = {}
        for other_task_id, (task_proc, task_priority) in self.running.iteritems():
            if task_id == other_task_id:
                continue
            if task_priority < priority:
                lower[other_task_id] = (task_proc, task_priority)
            else:
                higher[other_task_id] = (task_proc, task_priority)
        return lower, higher

    def get_running_processes(self):
        return run_sql("SELECT id,proc,priority FROM schTASK "\
                      "WHERE status IN ('RUNNING', 'CONTINUING')")

    def bibupload_in_the_queue(self, task_id):
        """Check if bibupload is scheduled/running before runtime."""
        return run_sql("SELECT id, status FROM schTASK WHERE proc='bibupload' AND id<%s AND status in ('RUNNING', 'WAITING', 'CONTINUING', 'SLEEPING', 'SCHEDULED', 'SUICIDE', 'STOP', 'STOP_SENT', 'SLEEP', 'SLEEP SENT', 'SUICIDE SENT')", (task_id, ))

    def handle_row(self, task_id, proc, runtime, status, priority):
        """Perform needed action of the row representing a task."""
        #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s" % (task_id, proc, runtime, status, priority))
        if status == "SLEEP":
            if task_id in self.running:
                self.set_status(task_id, "SLEEP SENT")
                self.send_signal(task_id, signal.SIGUSR1)
                self.sleep_sent[task_id] = self.running[task_id]
        elif status == "SLEEPING":
            if task_id in self.sleep_sent:
                self.sleep_done[task_id] = self.sleep_sent[task_id]
                del self.sleep_sent[task_id]
                del self.running[task_id]
        if status == "WAKEUP":
            if task_id in self.sleep_done:
                self.running[task_id] = self.sleep_done[task_id]
                del self.sleep_done[task_id]
                self.send_signal(task_id, signal.SIGCONT)
                self.set_status(task_id, "CONTINUING")
        elif status == "STOP":
            if task_id in self.running:
                self.set_status(task_id, "STOP SENT")
                self.send_signal(task_id, signal.SIGTERM)
                self.stop_sent[task_id] = self.running[task_id]
        elif status == "STOPPED" and task_id in self.stop_sent:
            if task_id in self.running:
                del self.running[task_id]
            del self.stop_sent[task_id]
        elif status == "SUICIDE":
            if task_id in self.running:
                self.set_status(task_id, "SUICIDE SENT")
                self.send_signal(task_id, signal.SIGABRT)
                self.suicide_sent[task_id] = self.running[task_id]
        elif status == "SUICIDED" and task_id in self.suicide_sent:
            if task_id in self.running:
                del self.running[task_id]
            del self.suicide_sent[task_id]
        elif 'DONE' in status and task_id in self.running:
            del self.running[task_id]
        elif status == "SCHEDULED" or (status in ("WAITING", "SLEEPING") and runtime <= datetime.datetime.now()):
            if task_id in self.running:
                del self.running[task_id]
            #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s" % (task_id, proc, runtime, status, priority))
            if self.scheduled is not None and self.scheduled != task_id:
                ## Another task is scheduled for running.
                #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s cannot run because task_id: %s is scheduled" % (task_id, proc, runtime, status, priority, self.scheduled))
                return

            res = self.bibupload_in_the_queue(task_id)
            if res:
                ## All bibupload must finish before.
                for (atask_id, astatus) in res:
                    if astatus in ('STOP', 'SUICIDED', 'ERROR'):
                        raise StandardError('BibSched had to halt because a bibupload with id %s has status %s. Please do your checks and delete/reinitialize the failed bibupload.' % (atask_id, astatus))
                #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s cannot run because these bibupload are scheduled: %s" % (task_id, proc, runtime, status, priority, res))
                return

            self.scheduled = task_id
            ## Schedule the task for running.

            lower, higher = self.split_running_tasks_by_priority(task_id, priority)
            for other_task_id, (other_proc, dummy) in higher.iteritems():
                if not self.tasks_safe_p(proc, other_proc):
                    ## There's at least a higher priority task running that
                    ## can not run at the same time of the given task.
                    ## We give up
                    #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s cannot run because task_id: %s, proc: %s is scheduled and incompatible" % (task_id, proc, runtime, status, priority, other_task_id, other_proc))
                    return

            ## No higer priority task have issue with the given task.
            if len(higher) >= CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS:
                ## Not enough resources.
                #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s cannot run because all resource (%s) are used (%s), higher: %s" % (task_id, proc, runtime, status, priority, CFG_BIBSCHED_MAX_NUMBER_CONCURRENT_TASKS, len(higher), higher))
                return

            ## We check if it is necessary to stop/put to sleep some lower priority
            ## task.
            tasks_to_stop, tasks_to_sleep = self.get_tasks_to_sleep_and_stop(proc, lower)

            if tasks_to_stop and priority < 10:
                ## Only tasks with priority higher than 10 have the power
                ## to put task to stop.
                #write_message("task_id: %s, proc: %s, runtime: %s, status: %s, priority: %s cannot run because there are task to stop: %s and priority < 10" % (task_id, proc, runtime, status, priority, task_to_stop))
                return

            procname = proc.split(':')[0]
            if not tasks_to_stop and not tasks_to_sleep:
                self.scheduled = None
                if status == "SLEEPING":
                    if task_id in self.sleep_done:
                        self.running[task_id] = self.sleep_done[task_id]
                        del self.sleep_done[task_id]
                        self.send_signal(task_id, signal.SIGCONT)
                        self.set_status(task_id, "CONTINUING")
                elif procname in self.helper_modules:
                    program = os.path.join(CFG_BINDIR, procname)
                    fdout, fderr = get_output_channelnames(task_id)
                    COMMAND = "%s %s >> %s 2>> %s" % (program, str(task_id), fdout, fderr)
                    Log("task #%d (%s) started" % (task_id, proc))
                    self.set_status(task_id, "WAITING")
                    os.system(COMMAND)
                    Log("task #%d (%s) ended" % (task_id, proc))
                    self.running[task_id] = (get_task_pid(proc, task_id), priority)
            else:
                ## It's not still safe to run the task.
                self.set_status(task_id, "SCHEDULED")
                self.scheduled = task_id

                for other_task_id in tasks_to_stop:
                    if other_task_id not in self.stop_sent:
                        self.set_status(task_id, "STOP SENT")
                        self.send_signal(task_id, signal.SIGTERM)
                        self.stop_sent[task_id] = self.running[task_id]
                for other_task_id in tasks_to_sleep:
                    if other_task_id not in self.sleep_sent:
                        self.set_status(task_id, "SLEEP SENT")
                        self.send_signal(task_id, signal.SIGUSR1)
                        self.sleep_sent[task_id] = self.running[task_id]

    def send_signal(self, task_id, signal):
        """Send a signal to a given task."""
        try:
            os.kill(self.running[task_id][0], signal)
        except OSError:
            self.set_status(task_id, "ERROR")
        except KeyError:
            register_exception()

    def watch_loop(self):
        try:
            running_process = self.get_running_processes()
            for task_id, proc, prio in running_process:
                if get_task_pid(proc, task_id):
                    self.running[task_id] = (get_task_pid(proc, task_id), prio)
                else:
                    self.set_status(task_id, "ERROR")
            rows = []
            while 1:
                rows = run_sql("SELECT id,proc,runtime,status,priority FROM schTASK WHERE status NOT LIKE '%%DELETED%%' ORDER BY priority DESC, runtime ASC")
                for row in rows:
                    self.handle_row(*row)
                time.sleep(CFG_BIBSCHED_REFRESHTIME)
        except:
            register_exception(alert_admin=True)
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
   stop       stop a running bibsched
   restart    restart a running bibsched
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

def server_pid():
    # The pid must be stored on the filesystem
    try:
        pid = int(open(pidfile).read())
    except IOError:
        return None

    # Even if the pid is available, we check if it corresponds to an
    # actual process, as it might have been killed externally
    try:
        os.kill(pid, signal.SIGCONT)
    except OSError:
        return None

    return pid

def start(verbose = True):
    """ Fork this process in the background and start processing
    requests. The process PID is stored in a pid file, so that it can
    be stopped later on."""

    if verbose:
        sys.stdout.write("starting bibsched: ")
        sys.stdout.flush()

    pid = server_pid()
    if pid:
        error("another instance of bibsched (pid %d) is running" % pid)

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
    sched.watch_loop()

    return

def stop(verbose=True, soft=False):
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
                ','.join([repr(escape_string(task)) for task in tasks]))
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
    if status is None:
        report_about_processes('Running', since, tasks)
        report_about_processes('Waiting', since, tasks)
    else:
        for state in status:
            report_about_processes(state, since, tasks)
    write_message("Done.")
    return

def restart(verbose = True):
    stop(verbose, soft=True)
    start(verbose)
    return

def main():
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
            'stop':    stop,
            'restart': restart,
            'monitor': monitor} [cmd] (verbose)
    except KeyError:
        usage(1, 'unkown command: %s' % cmd)

    return

if __name__ == '__main__':
    main()
