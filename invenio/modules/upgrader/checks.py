# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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

"""
Checks to run before and/or after a complete upgrade to ensure certain
pre-/post-conditions are met (e.g. BibSched not running).
"""

from __future__ import absolute_import

import logging
import subprocess


#
# Global pre/post-checks
#
def pre_check_bibsched():
    """
    Check if bibsched is running
    """
    logger = logging.getLogger('invenio_upgrader')
    logger.info("Checking bibsched process...")

    output, error = subprocess.Popen(["bibsched", "status"],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE).communicate()

    is_manual = False
    is_0_running = False
    for line in (output + error).splitlines():
        if 'BibSched queue running mode: MANUAL' in line:
            is_manual = True
        if 'Running processes: 0' in line:
            is_0_running = True

    stopped = is_manual and is_0_running

    if not stopped:
        raise RuntimeError("Bibsched is running. Please stop bibsched "
                           "using the command:\n$ bibsched stop")


def post_check_bibsched():
    """
    Inform user to start bibsched again
    """
    logger = logging.getLogger('invenio_upgrader')
    logger.info("Remember to start bibsched again:\n$ bibsched start")
    return True
