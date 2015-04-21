#!/usr/bin/env python2
#
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Generate minimal requirements from `setup.py` + `requirements-devel.txt`."""

from __future__ import print_function

import argparse
import re
import sys

import mock

import pkg_resources

import setuptools


def parse_set(string):
    """Parse set from comma separated string."""
    string = string.strip()
    if string:
        return set(string.split(","))
    else:
        return set()


def minver_error(pkg_name):
    """Report error about missing minimum version constraint and exit."""
    print(
        "ERROR: specify minimal version of '{}' using '>=' or '=='".format(pkg_name),
        file=sys.stderr
    )
    sys.exit(1)


def parse_pip_file(path):
    """Parse pip requirements file."""
    # requirement lines sorted by importance
    # also collect other pip commands
    rdev = dict()
    rnormal = []
    stuff = []

    try:
        with open(path) as f:
            for line in f:
                line = line.strip()

                # see https://pip.readthedocs.org/en/1.1/requirements.html
                if line.startswith("-e"):
                    # devel requirement
                    splitted = line.split("#egg=")
                    rdev[splitted[1].lower()] = line

                elif line.startswith("-r"):
                    # recursive file command
                    splitted = re.split("-r\\s+", line)
                    subrdev, subrnormal, substuff = parse_pip_file(splitted[1])
                    for k, v in subrdev.iteritems():
                        if k not in rdev:
                            rdev[k] = v
                    rnormal.extend(subrnormal)
                    result.extend(substuff)

                elif line.startswith("-"):
                    # another special command we don't recognize
                    stuff.append(line)

                else:
                    # ordenary requirement, similary to them used in setup.py
                    rnormal.append(line)
    except IOError:
        print(
            "Warning: could not parse requirements file '{}'!",
            file=sys.stderr
        )

    return rdev, rnormal, stuff

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Calculates requirements for different purposes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-l", "--level",
        choices=["min", "pypi", "dev"],
        default="pypi",
        help="Specifies desired requirements level."
             "'min' requests the minimal requirement that is specified, "
             "'pypi' requests the maximum version that satisfies the "
             "constrains and is available in PyPi. "
             "'dev' includes experimental developer versions for VCSs."
    )
    parser.add_argument(
        "-e", "--extras",
        default="",
        help="Comma separated list of extras.",
        type=parse_set
    )
    args = parser.parse_args()

    result = dict()
    requires = []
    stuff = []
    if args.level == "dev":
        result, requires, stuff = parse_pip_file("requirements-devel.txt")

    with mock.patch.object(setuptools, 'setup') as mock_setup:
        import setup
        assert setup  # silence warning about unused imports

    # called arguments are in `mock_setup.call_args`
    mock_args, mock_kwargs = mock_setup.call_args
    requires = mock_kwargs.get('install_requires', [])

    requires_extras = mock_kwargs.get('extras_require', {})
    for e in args.extras:
        if e in requires_extras:
            requires.extend(requires_extras[e])

    for pkg in pkg_resources.parse_requirements(requires):
        # skip things we already know
        # FIXME be smarter about merging things
        if pkg.key in result:
            continue

        specs = dict(pkg.specs)
        if ((">=" in specs) and (">" in specs)) \
                or (("<=" in specs) and ("<" in specs)):
            print(
                "ERROR: Do not specify such weird constraints! ('{}')".format(pkg),
                file=sys.stderr
            )
            sys.exit(1)

        if '==' in specs:
            result[pkg.key] = "{}=={}".format(pkg.project_name, specs['=='])

        elif '>=' in specs:
            if args.level == "min":
                result[pkg.key] = "{}=={}".format(pkg.project_name, specs['>='])
            else:
                result[pkg.key] = pkg

        elif '>' in specs:
            if args.level == "min":
                minver_error(pkg.project_name)
            else:
                result[pkg.key] = pkg

        else:
            if args.level == "min":
                minver_error(pkg.project_name)
            else:
                result[pkg.key] = pkg

    for s in stuff:
        print(s)

    for k in sorted(result.iterkeys()):
        print(result[k])
