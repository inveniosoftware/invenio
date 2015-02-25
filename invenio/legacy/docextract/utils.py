# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

VERBOSITY = None
USE_BIBTASK = False

import sys
from datetime import datetime

from invenio.legacy.bibsched.bibtask import write_message as bibtask_write_message


def setup_loggers(verbosity, use_bibtask=False):
    global VERBOSITY, USE_BIBTASK

    if verbosity > 8:
        print('Setting up loggers: verbosity=%s' % verbosity)

    VERBOSITY = verbosity
    USE_BIBTASK = use_bibtask


def write_message(msg, stream=sys.stdout, verbose=1):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).
    Useful for debugging stuff."""
    if USE_BIBTASK:
        return bibtask_write_message(msg, stream, verbose)
    elif VERBOSITY and msg and VERBOSITY >= verbose:
        if VERBOSITY > 8:
            print(datetime.now().strftime('[%H:%M:%S] '), end=' ', file=stream)
        print(msg, file=stream)
