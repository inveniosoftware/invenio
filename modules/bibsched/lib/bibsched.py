# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

### -- local configuration section starts here ---

# which tasks are recognized as valid?
cfg_valid_processes = ["bibindex", "bibupload", "bibreformat",
                       "webcoll", "bibtaskex", "bibrank",
                       "oaiharvest", "oaiarchive", "sessiongc"]

### -- local configuration section ends here ---

import os
import string
import sys
import time
import re
import marshal
import getopt
import curses
import curses.panel
from curses.wrapper import wrapper
import signal

from invenio.config import \
     CFG_PREFIX, \
     CFG_BIBSCHED_REFRESHTIME, \
     bindir, \
     logdir
from invenio.dbquery import run_sql

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    try:
        date = time.time()
        shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
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
    answer = string.strip(os.popen(COMMAND).read())
    if answer == '':
        answer = 0
    else:
        answer = answer[:string.find(answer,' ')]
    return int(answer)

def get_task_pid(task_name, task_id):
    """Return the pid of task_name/task_id"""
    try:
        pid = open(os.path.join(CFG_PREFIX, 'var', 'run', 'bibsched_task_%d.pid' % task_id)).read()
    except IOError:
        return get_my_pid(task_name, str(task_id))

    try:
        os.kill(pid, signal.SIGCONT)
    except OSError:
        return get_my_pid(task_name, str(task_id))

    return int(pid)


def get_output_channelnames(task_id):
    "Construct and return filename for stdout and stderr for the task 'task_id'."
    filenamebase = "%s/bibsched_task_%d" % (logdir, task_id)
    return [filenamebase + ".log", filenamebase + ".err"]

class Manager:
    def __init__(self):
        self.helper_modules = cfg_valid_processes
        self.running = 1
        self.footer_move_mode = "[KeyUp/KeyDown Move] [M Select mode] [Q Quit]"
        self.footer_auto_mode = "[A Manual mode] [1/2 Display Type] [P Purge Done] [Q Quit]"
        self.footer_select_mode = "[KeyUp/KeyDown/PgUp/PgDown Select] [L View Log] [1/2 Display Type] [M Move mode] [A Auto mode] [Q Quit]"
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
        self.currentrow = ["", "", "", "", "", "", ""]
        wrapper(self.start)

    def handle_keys(self, chr):
        if chr == -1:
            return
        if self.auto_mode and (chr not in (curses.KEY_UP, curses.KEY_DOWN,
                                           curses.KEY_PPAGE, curses.KEY_NPAGE,
                                           ord("q"), ord("Q"), ord("a"),
                                           ord("A"), ord("1"), ord("2"),
                                           ord("p"), ord("P"))):
            self.display_in_footer("in automatic mode")
            self.stdscr.refresh()
        elif self.move_mode and (chr not in (curses.KEY_UP, curses.KEY_DOWN,
                                             ord("m"), ord("M"), ord("q"),
                                             ord("Q"))):
            self.display_in_footer("in move mode")
            self.stdscr.refresh()
        else:
            if chr == curses.KEY_UP:
                if self.move_mode:
                    self.move_up()
                else:
                    self.selected_line = max(self.selected_line - 1, 2)
                self.repaint()
            if chr == curses.KEY_PPAGE:
                self.selected_line = max(self.selected_line - 10, 2)
                self.repaint()
            elif chr == curses.KEY_DOWN:
                if self.move_mode:
                    self.move_down()
                else:
                    self.selected_line = min(self.selected_line + 1, len(self.rows) + 1 )
                self.repaint()
            elif chr == curses.KEY_NPAGE:
                self.selected_line = min(self.selected_line + 10, len(self.rows) + 1 )
                self.repaint()
            elif chr == curses.KEY_HOME:
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
            elif chr in (ord("q"), ord("Q")):
                if curses.panel.top_panel() == self.panel:
                    self.panel.bottom()
                    curses.panel.update_panels()
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
        if status != 'WAITING':
            tmpname = os.tmpnam()
            tmpfile = open(tmpname, "w")
            try:
                tmpfile.write(open(os.path.join(logdir, 'bibsched_task_%d.log' % task_id)).read())
            except IOError:
                pass
            try:
                tmpfile.write(open(os.path.join(logdir, 'bibsched_task_%d.err' % task_id)).read())
            except IOError:
                pass
            tmpfile.close()
            pager = os.environ.get('PAGER', '/bin/more')
            curses.endwin()
            os.spawnlp(os.P_WAIT, pager, pager, tmpname)
            os.remove(tmpname)
            curses.panel.update_panels()

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
        rows = msg.split('\n')
        height = len(rows) + 2
        width = max([len(row) for row in rows]) + 4
        self.win = curses.newwin(
            height,
            width,
            (self.height - height) / 2 + 1,
            (self.width - width) / 2 + 1
            )
        self.panel = curses.panel.new_panel( self.win )
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
        if self._display_YN_box("You are going to purge all the list of DONE tasks.\n"
            "This will definitely alter your task history.\nAre you sure?"):
            run_sql("DELETE FROM schTASK WHERE status='DONE'")
            curses.panel.update_panels()
            self.display_in_footer("DONE processes purged")
        else:
            curses.panel.update_panels()

    def run(self):
        task_id = self.currentrow[0]
        process = self.currentrow[1]
        status = self.currentrow[5]
        sleeptime = self.currentrow[4]
        if self.count_processes('RUNNING') + self.count_processes('CONTINUING') >= 1:
            self.display_in_footer("a process is already running!")
        elif status == "STOPPED" or status == "WAITING":
            if process in self.helper_modules:
                program = os.path.join(bindir, process)
                fdout, fderr = get_output_channelnames(task_id)
                COMMAND = "%s %s >> %s 2>> %s &" % (program, str(task_id), fdout, fderr)
                os.system(COMMAND)
                Log("manually running task #%d (%s)" % (task_id, process))
                if sleeptime:
                    new_runtime = get_datetime(sleeptime)
                    new_task_arguments = marshal.loads(self.currentrow[7])
                    new_task_arguments["runtime"] = new_runtime
                    new_task_id = run_sql("INSERT INTO schTASK (proc,user,runtime,sleeptime,arguments,status)"\
                                          " VALUES (%s,%s,%s,%s,%s,'WAITING')",
                                          (process, self.currentrow[2], new_runtime, sleeptime,
                                           self.currentrow[7]))
                    new_task_arguments["task"] = new_task_id
                    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""",
                            (marshal.dumps(new_task_arguments), new_task_id))

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
        #status = self.currentrow[5]
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
        #status = self.currentrow[5]
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
        #process = self.currentrow[1]
        status = self.currentrow[5]
        if status != 'RUNNING' and status != 'CONTINUING' and status != 'SLEEPING':
            self.set_status(task_id, "%s_DELETED" % status)
            self.display_in_footer("process deleted")
            self.selected_line = max(self.selected_line, 2)
        else:
            self.display_in_footer("cannot delete running processes")
        self.stdscr.refresh()

    def init(self):
        task_id = self.currentrow[0]
        #process = self.currentrow[1]
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
            if status in ( "RUNNING" , "CONTINUING" , "SLEEPING" ):
                self.display_in_footer("cannot move running processes!")
            else:
                self.move_mode = 1
        self.stdscr.refresh()

    def change_auto_mode(self):
        if self.auto_mode:
            program = os.path.join(bindir, "bibsched")
            COMMAND = "%s -q stop" % program
            os.system(COMMAND)

            self.auto_mode = 0
        else:
            program = os.path.join( bindir, "bibsched")
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

    def put_line(self, row):
        col_w = [ 5 , 11 , 21 , 21 , 7 , 11 , 25 ]
        maxx = self.width
        if self.y == self.selected_line - self.first_visible_line and self.y > 1:
            if self.auto_mode:
                attr = curses.color_pair(2) + curses.A_STANDOUT + curses.A_BOLD
            elif self.move_mode:
                attr = curses.color_pair(7) + curses.A_STANDOUT + curses.A_BOLD
            else:
                attr = curses.color_pair(8) + curses.A_STANDOUT + curses.A_BOLD
            self.item_status = row[5]
            self.currentrow = row
        elif self.y == 0:
            if self.auto_mode:
                attr = curses.color_pair(2) + curses.A_STANDOUT + curses.A_BOLD
            elif self.move_mode:
                attr = curses.color_pair(7) + curses.A_STANDOUT + curses.A_BOLD
            else:
                attr = curses.color_pair(8) + curses.A_STANDOUT + curses.A_BOLD
        elif row[5] == "DONE":
            attr = curses.color_pair(5) + curses.A_BOLD
        elif row[5] == "STOPPED":
            attr = curses.color_pair(6) + curses.A_BOLD
        elif row[5].find("ERROR") > -1:
            attr = curses.color_pair(4) + curses.A_BOLD
        elif row[5] == "WAITING":
            attr = curses.color_pair(3) + curses.A_BOLD
        elif row[5] in ("RUNNING","CONTINUING") :
            attr = curses.color_pair(2) + curses.A_BOLD
        else:
            attr = curses.A_BOLD
        myline = str(row[0]).ljust(col_w[0])
        myline += str(row[1]).ljust(col_w[1])
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
        self.stdscr.addnstr(self.y - i, 0, footer, maxx - 1, curses.A_STANDOUT + curses.color_pair(colorpair) + curses.A_BOLD )

    def repaint(self):
        self.y = 0
        self.stdscr.clear()
        self.height, self.width = self.stdscr.getmaxyx()
        maxy = self.height - 2
        #maxx = self.width
        self.put_line( ("ID", "PROC", "USER", "RUNTIME", "SLEEP", "STATUS", "PROGRESS") )
        self.put_line( ("---", "----", "----", "-------------------", "-----", "-----", "--------") )
        if self.selected_line > maxy + self.first_visible_line - 1:
            self.first_visible_line = self.selected_line - maxy + 1
        if self.selected_line < self.first_visible_line + 2:
            self.first_visible_line = self.selected_line - 2
        for row in self.rows[self.first_visible_line:self.first_visible_line+maxy-2]:
            task_id, proc, user, runtime, sleeptime, status, progress, arguments = row
            self.put_line( row )
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
        ring = 0
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        self.stdscr = stdscr
        self.base_panel = curses.panel.new_panel( self.stdscr )
        self.base_panel.bottom()
        curses.panel.update_panels()
        self.height, self.width = stdscr.getmaxyx()
        self.stdscr.clear()
        if server_pid (): self.auto_mode = 1
        if self.display == 1:
            where = "and status='DONE'"
            order = "DESC"
        else:
            where = "and status!='DONE'"
            order = "ASC"
        self.rows = run_sql("SELECT id,proc,user,runtime,sleeptime,status,progress,arguments FROM schTASK WHERE status NOT LIKE '%%DELETED%%' %s ORDER BY runtime %s" % (where, order))
        self.repaint()
        ring = 0
        while self.running:
            ring += 1
            char = -1
            try:
                char = timed_out(self.stdscr.getch, 1)
                if char == 27: # escaping sequence
                    char = self.stdscr.getch()
                    if char == 79: # arrow
                        char = self.stdscr.getch()
                        if char == 65: #arrow up
                            char = curses.KEY_UP
                        elif char == 66: #arrow down
                            char = curses.KEY_DOWN
                        elif char == 72:
                            char = curses.KEY_PPAGE
                        elif char == 70:
                            char = curses.KEY_NPAGE
                    elif char == 91:
                        char = self.stdscr.getch()
                        if char == 53:
                            char = self.stdscr.getch()
                            if char == 126:
                                char = curses.KEY_HOME
            except TimedOutExc:
                char = -1
            self.handle_keys(char)
            if ring == 4:
                if self.display == 1:
                    where = "and status='DONE'"
                    order = "DESC"
                else:
                    where = "and status!='DONE'"
                    order = "ASC"
                self.rows = run_sql("SELECT id,proc,user,runtime,sleeptime,status,progress,arguments FROM schTASK WHERE status NOT LIKE '%%DELETED%%' %s ORDER BY runtime %s" % (where, order))
                ring = 0
                self.repaint()


class BibSched:
    def __init__(self):
        self.helper_modules = cfg_valid_processes
        self.running = {}
        self.sleep_done = {}
        self.sleep_sent = {}
        self.stop_sent = {}
        self.suicide_sent = {}

    def set_status(self, task_id, status):
        return run_sql("UPDATE schTASK set status=%s WHERE id=%s", (status, task_id))

    def can_run( self, proc ):
        return len( self.running.keys() ) == 0

    def get_running_processes(self):
        row = None
        res = run_sql("SELECT id,proc,user,UNIX_TIMESTAMP(runtime),sleeptime,arguments,status FROM schTASK "\
                      " WHERE status='RUNNING' or status='CONTINUING' LIMIT 1")
        try:
            row = res[0]
        except:
            pass
        return row

    def handle_row( self, row ):
        task_id, proc, user, runtime, sleeptime, arguments, status = row
        if status == "SLEEP":
            if task_id in self.running.keys():
                self.set_status( task_id, "SLEEP SENT" )
                os.kill( self.running[task_id], signal.SIGUSR1 )
                self.sleep_sent[task_id] = self.running[task_id]
        elif status == "SLEEPING":
            if task_id in self.sleep_sent.keys():
                self.sleep_done[task_id] = self.sleep_sent[task_id]
                del self.sleep_sent[task_id]
        if status == "WAKEUP":
            if task_id in self.sleep_done.keys():
                self.running[task_id] = self.sleep_done[task_id]
                del self.sleep_done[task_id]
                os.kill( self.running[task_id], signal.SIGCONT )
                self.set_status( task_id, "RUNNING" )
        elif status == "STOP":
            if task_id in self.running.keys():
                self.set_status( task_id, "STOP SENT" )
                os.kill( self.running[task_id], signal.SIGTERM )
                self.stop_sent[task_id] = self.running[task_id]
                del self.running[task_id]
        elif status == "STOPPED" and task_id in self.stop_sent.keys():
            del self.stop_sent[task_id]
        elif status == "SUICIDE":
            if task_id in self.running.keys():
                self.set_status( task_id, "SUICIDE SENT" )
                os.kill( self.running[task_id], signal.SIGABRT )
                self.suicide_sent[task_id] = self.running[task_id]
                del self.running[task_id]
        elif status == "SUICIDED" and task_id in self.suicide_sent.keys():
            del self.suicide_sent[task_id]
        elif status.find("DONE") > -1 and task_id in self.running.keys():
            del self.running[task_id]
        elif self.can_run(proc) and status == "WAITING" and runtime <= time.time():
            if proc in self.helper_modules:
                program = os.path.join(bindir, proc)
                fdout, fderr = get_output_channelnames(task_id)
                COMMAND = "%s %s >> %s 2>> %s" % (program, str(task_id), fdout, fderr)
                Log("task #%d (%s) started" % (task_id, proc))
                os.system(COMMAND)
                Log("task #%d (%s) ended" % (task_id, proc))
                self.running[task_id] = get_task_pid(proc, task_id)
            if sleeptime:
                new_runtime = get_datetime(sleeptime)
                new_task_arguments = marshal.loads(arguments)
                new_task_arguments["runtime"] = new_runtime
                new_task_id = run_sql("INSERT INTO schTASK (proc,user,runtime,sleeptime,arguments,status)"\
                                      " VALUES (%s,%s,%s,%s,%s,'WAITING')",
                                      (proc, user, new_runtime, sleeptime, arguments))
                new_task_arguments["task"] = new_task_id
                run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""",
                        (marshal.dumps(new_task_arguments), new_task_id))

    def watch_loop(self):
        running_process = self.get_running_processes()
        if running_process:
            proc = running_process[ 1 ]
            task_id   = running_process[ 0 ]
            if get_task_pid(proc, task_id):
                self.running[task_id] = get_task_pid(proc, task_id)
            else:
                self.set_status(task_id,"ERROR")
        rows = []
        while 1:
            for row in rows:
                self.handle_row( row )
            time.sleep(CFG_BIBSCHED_REFRESHTIME)
            rows = run_sql("SELECT id,proc,user,UNIX_TIMESTAMP(runtime),sleeptime,arguments,status FROM schTASK ORDER BY runtime ASC")

class TimedOutExc(Exception):
    def __init__(self, value = "Timed Out"):
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
    log = open(logdir + "/bibsched.log","a")
    log.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
    log.write(message)
    log.write("\n")
    log.close()

def redirect_stdout_and_stderr():
    "This function redirects stdout and stderr to bibsched.log and bibsched.err file."
    sys.stdout = open(logdir + "/bibsched.log", "a")
    sys.stderr = open(logdir + "/bibsched.err", "a")

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)

    sys.stderr.write ("""\
Usage: %s [options] [start|stop|restart|monitor]

The following commands are available for bibsched:

  - start:   start bibsched in background
  - stop:    stop a running bibsched
  - restart: restart a running bibsched
  - monitor: enter the interactive monitor

Command options:
  -d, --daemon\t Launch BibSched in the daemon mode (deprecated, use 'start')
General options:
  -h, --help      \t\t Print this help.
  -V, --version   \t\t Print version information.
  """ % sys.argv [0])

    #sys.stderr.write("  -v, --verbose=LEVEL \t Verbose level (0=min, 1=default, 9=max).\n")
    sys.exit(exitcode)

pidfile = os.path.join(CFG_PREFIX, 'var', 'run', 'bibsched.pid')

def error (msg):
    print >> sys.stderr, "error: " + msg
    sys.exit (1)


def server_pid ():
    # The pid must be stored on the filesystem
    try:
        pid = int (open (pidfile).read ())
    except IOError:
        return None

    # Even if the pid is available, we check if it corresponds to an
    # actual process, as it might have been killed externally
    try:
        os.kill (pid, signal.SIGCONT)
    except OSError:
        return None

    return pid


def start (verbose = True):
    """ Fork this process in the background and start processing
    requests. The process PID is stored in a pid file, so that it can
    be stopped later on."""

    if verbose:
        sys.stdout.write ("starting bibsched: ")
        sys.stdout.flush ()

    pid = server_pid ()
    if pid:
        error ("another instance of bibsched (pid %d) is running" % pid)

    # start the child process using the "double fork" technique
    pid = os.fork ()
    if pid > 0: sys.exit (0)

    os.setsid ()
    os.chdir ('/')

    pid = os.fork ()

    if pid > 0:
        if verbose:
            sys.stdout.write ('pid %d\n' % pid)

        Log ("daemon started (pid %d)" % pid)
        open (pidfile, 'w').write ('%d' % pid)
        return

    sys.stdin.close ()
    redirect_stdout_and_stderr ()

    sched = BibSched()
    sched.watch_loop ()

    return

def stop (verbose = True):

    pid = server_pid ()
    if not pid:
        error ('bibsched seems not to be running.')

    try: os.kill (pid, signal.SIGKILL)
    except OSError:
        print >> sys.stderr, 'no bibsched process found'

    Log ("daemon stopped (pid %d)" % pid)

    if verbose: print "stopping bibsched: pid %d" % pid
    os.unlink (pidfile)
    return

def monitor(verbose = True):
    redirect_stdout_and_stderr()
    manager = Manager()
    return

def restart(verbose = True):
    stop(verbose)
    start(verbose)
    return

def main():
    verbose = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hVdq", [
            "help","version","daemon", "quiet"])
    except getopt.GetoptError, err:
        Log ("Error: %s" % err)
        usage(1, err)

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage (0)

        elif opt in ["-V", "--version"]:
            print __revision__
            sys.exit(0)

        elif opt in ["-d", "--daemon"]:
            redirect_stdout_and_stderr ()
            sched = BibSched()
            Log("daemon started")
            sched.watch_loop()

        elif opt in ['-q', '--quiet']:
            verbose = False

        else:
            usage(1)

    try:  cmd = args [0]
    except IndexError: cmd = 'monitor'

    try:
        { 'start':   start,
          'stop':    stop,
          'restart': restart,
          'monitor': monitor } [cmd] (verbose)

    except KeyError:
        usage (1, 'unkown command: %s' % `cmd`)

    return

if __name__ == '__main__':
    main()
