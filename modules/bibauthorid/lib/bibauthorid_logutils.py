"""The logger facility of bibauthorid"""

import invenio.bibauthorid_config as bconfig
import sys
import os
from datetime import datetime
from math import floor
import multiprocessing as mp


class Logger(object):

    _pid = os.getpid
    _print_output = bconfig.DEBUG_OUTPUT
    _file_out = bconfig.DEBUG_LOG_TO_PIDFILE
    _file_prefix = '/tmp/bibauthorid_log_pid_'
    _newline = bconfig.DEBUG_UPDATE_STATUS_THREAD_SAFE

    status_len = 18
    comment_len = 40

    _terminator = '\r'
    if _newline or _file_out:
        _terminator = '\n'

    log_lock = mp.Lock()
    modify_lock = mp.Lock()

    def __init__(self, logger_name, stdout_only=False):

        self._name = logger_name

        if Logger._file_out:
            self._file_only = not stdout_only
        else:
            self._file_only = False
        self._pidfiles = dict()

        self._verbose = Logger._print_output

    def _generate_msg(self, *args):
        message = '[%s][%s][%s]: ' % (datetime.today(), Logger._pid(),
                                      self._name) + ' '.join(str(x) for x in args[0])
        return message

    def _bai_print(self, *args, **kwargs):
        to_file = kwargs.pop('to_file', self._file_only)
        in_line = kwargs.pop('in_line', False)
        if to_file:
            self._setup_file_out()
        for arg in args:
            print arg,
        if not in_line:
            print ""
        sys.stdout.flush()

    def _setup_file_out(self):
        try:
            sys.stdout = self._pidfiles[Logger._pid()]
        except KeyError:
            self._pidfiles[Logger._pid()] = open(Logger._file_prefix + str(Logger._pid()), 'w')
            sys.stdout = self._pidfiles[Logger._pid()]

    def _padd(self, stry, l):
        return stry[:l].ljust(l)


    def log(self, *args, **kwargs):
        in_line = kwargs.pop('in_line', False)
        if self._verbose and Logger._print_output:
            msg = self._generate_msg(args)
            with mp.Lock():
                self._bai_print(msg, in_line=in_line)

    def update_status(self, percent, comment=""):
        if Logger._print_output:
            filled = max(0, int(floor(percent * Logger.status_len)))
            bar = "[%s%s] " % ("#" * filled,
                               "-" * (Logger.status_len - filled))
            percent = ("%.2f%% done" % (percent * 100))
            progress = self._padd(bar + percent, Logger.status_len + 2)
            comment = self._padd(comment, Logger.comment_len)
            self.log(progress, comment, Logger._terminator, to_file=False, in_line=True)
            sys.stdout.flush()

    def update_status_final(self, comment=""):
        self.update_status(1., comment)
        if Logger._print_output:
            self._bai_print("", to_file=False)

    @property
    def verbose(self):
        '''
        Configure logging for this object.
        '''
        return self._verbose

    @verbose.setter
    def verbose(self, val):
        self._verbose = val

    @staticmethod
    def override_stdout_config(verbose=False, fileout=False, stdout=True):
        '''
        Globally configure logging.
        '''
        with mp.Lock():
            if fileout:
                Logger._file_out = True
            if stdout:
                Logger._file_out = False
            Logger._print_output = verbose
