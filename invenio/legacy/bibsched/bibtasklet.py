# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""Invenio Bibliographic Tasklet BibTask.

This is a particular BibTask that execute tasklets, which can be any
function dropped into ``<package>.tasklets`` where ``<package>`` is defined
in ``PACKAGES``.
"""

from __future__ import print_function

import sys

from invenio.version import __version__
from invenio.legacy.bibsched.bibtask import (
    task_init, write_message, task_set_option, task_get_option,
    task_update_progress)
from invenio.utils.autodiscovery.helpers import get_callable_documentation
from invenio.utils.autodiscovery.checkers import check_arguments_compatibility
from invenio.modules.scheduler.registry import tasklets


_TASKLETS = tasklets


def cli_list_tasklets():
    """Print the list of available tasklets and broken tasklets."""
    print("""Available tasklets:""")
    for tasklet in _TASKLETS.values():
        print(get_callable_documentation(tasklet))

    sys.exit(0)


def task_submit_elaborate_specific_parameter(key, value,
                                             dummy_opts, dummy_args):
    """Check meaning of given string key.

    Eventually use the value for check. Usually it fills some key in the
    options dict. It must return True if it has elaborated the key, False,
    if it doesn't know that key.

    Example:

    .. code-block:: python

        if key in ('-n', '--number'):
            task_set_option('number', value)
            return True
        return False
    """
    if key in ('-T', '--tasklet'):
        task_set_option('tasklet', value)
        return True
    elif key in ('-a', '--argument'):
        arguments = task_get_option('arguments', {})
        try:
            key, value = value.split('=', 1)
        except NameError:
            print('ERROR: an argument must be in the form '
                  'param=value, not "%s"' % (value, ),
                  file=sys.stderr)
            return False
        arguments[key] = value
        task_set_option('arguments', arguments)
        return True
    elif key in ('-l', '--list-tasklets'):
        cli_list_tasklets()
        return True
    return False


def task_submit_check_options():
    """Check if a tasklet has been specified and the parameters are good."""
    tasklet = task_get_option('tasklet', None)
    arguments = task_get_option('arguments', {})
    if not tasklet:
        print('ERROR: no tasklet specified', file=sys.stderr)
        return False
    elif tasklet not in _TASKLETS:
        print('ERROR: "%s" is not a valid tasklet. Use '
              '--list-tasklets to obtain a list of the working tasklets.' %
              tasklet, file=sys.stderr)
        return False
    else:
        try:
            check_arguments_compatibility(_TASKLETS[tasklet], arguments)
        except ValueError as err:
            print('ERROR: wrong arguments (%s) specified for '
                  'tasklet "%s": %s' % (
                      arguments, tasklet, err), file=sys.stderr)
            return False
    return True


def task_run_core():
    """Run the specific tasklet."""
    tasklet = task_get_option('tasklet')
    arguments = task_get_option('arguments', {})
    write_message('Starting tasklet "%s" (with arguments %s)' % (
        tasklet, arguments))
    task_update_progress('%s started' % tasklet)
    ret = _TASKLETS[tasklet](**arguments)
    task_update_progress('%s finished' % tasklet)
    write_message('Finished tasklet "%s" (with arguments %s)' % (
        tasklet, arguments))
    if ret is not None:
        return ret
    return True


def main():
    """Main body of bibtasklet."""
    task_init(
        authorization_action='runbibtasklet',
        authorization_msg="BibTaskLet Task Submission",
        help_specific_usage="""\
  -T, --tasklet         Execute the specific tasklet
  -a, --argument        Specify an argument to be passed to tasklet in the form
                            param=value, e.g. --argument foo=bar
  -l, --list-tasklets   List the existing tasklets
""",
        version=__version__,
        specific_params=("T:a:l", ["tasklet=", "argument=", "list-tasklets"]),
        task_submit_elaborate_specific_parameter_fnc=(
            task_submit_elaborate_specific_parameter
        ),
        task_run_fnc=task_run_core,
        task_submit_check_options_fnc=task_submit_check_options)
