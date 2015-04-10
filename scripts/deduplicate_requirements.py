#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

r"""
Deduplicator for pip requiremts.

Use it as part of a pipe, e.g.
    cat requirements.txt requirements-dev.txt requirements-extra.txt \
            | deduplicate_requirements.py > requirements-final.txt
"""

import fileinput
import re

# requirement lines sorted by importance
# also collect other pip commands
high = dict()
low = dict()
stuff = []


def parse(line):
    """Parse one line of a pip requirements file."""
    line = line.strip()

    # see https://pip.readthedocs.org/en/1.1/requirements.html
    if line.startswith("-e"):
        splitted = line.split("#egg=")
        high[splitted[1]] = line

    elif line.startswith("-r"):
        splitted = re.split("-r\\s+", line)
        try:
            with open(splitted[1]) as f:
                for line in f:
                    parse(line)
        except IOError:
            pass

    elif line.startswith("-"):
        stuff.append(line)

    else:
        splitted = re.split("[>=]=", line)
        low[splitted[0]] = line

# get all lines from stdin
for line in fileinput.input():
    parse(line)

# set of requirements we already emitted
already = set()

# emit lines
# first unknown commands
# then high level requirements
# then low level requirements

for line in stuff:
    print(line)

for k, v in high.iteritems():
    if k not in already:
        already.add(k)
        print(v)

for k, v in low.iteritems():
    if k not in already:
        already.add(k)
        print(v)
