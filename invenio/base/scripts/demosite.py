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

"""Perform demosite operations."""

from __future__ import print_function

import os
import sys
import warnings
from itertools import count

import pkg_resources

from invenio.base.utils import run_py_func
from invenio.ext.script import Manager


warnings.warn("Use of `inveniomanage demosite populate` is being deprecated. "
              "Please use `uploader` module to insert demo records.",
              PendingDeprecationWarning)




manager = Manager(usage=__doc__)

# Shortcuts for manager options to keep code DRY.
option_yes_i_know = manager.option('--yes-i-know', action='store_true',
                                   dest='yes_i_know', help='use with care!')
option_default_data = manager.option('--no-data', action='store_false',
                                     dest='default_data',
                                     help='do not populate tables with '
                                          'default data')
option_file = manager.option('-f', '--file', dest='files',
                             action='append', help='data file to use')
option_jobid = manager.option('-j', '--job-id', dest='job_id', type=int,
                              default=0, help='bibsched starting job id')
option_extrainfo = manager.option('-e', '--extra-info', dest='extra_info',
                                  action='append',
                                  help='extraneous parameters')
option_packages = manager.option('-p', '--packages', dest='packages',
                                 action='append',
                                 default=[],
                                 help='package import name (repeteable)')


@option_packages
@option_default_data
@option_file
@option_jobid
@option_extrainfo
@option_yes_i_know
def populate(packages=[], default_data=True, files=None,
             job_id=0, extra_info=None, yes_i_know=False):
    """Load demo records.  Useful for testing purposes."""
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user

    # Load cli interfaces for tools that we are going to need
    from invenio.legacy.bibupload.engine import main as bibupload
    from invenio.legacy.bibindex.engine import main as bibindex
    from invenio.legacy.bibformat.bibreformat import main as bibreformat
    from invenio.legacy.oairepository.updater import main as oairepositoryupdater
    from invenio.legacy.bibsort.daemon import main as bibsort
    from invenio.legacy.bibdocfile.cli import main as bibdocfile
    from invenio.legacy.bibrank.cli import main as bibrank

    ## Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box(
        "WARNING: You are going to override data in tables!"
    ))

    if not default_data:
        print('>>> Default data has been skiped (--no-data).')
        return
    if not packages:
        packages = ['invenio_demosite.base']

    from werkzeug.utils import import_string
    map(import_string, packages)

    from invenio.ext.sqlalchemy import db
    print(">>> Going to load demo records...")
    db.session.execute("TRUNCATE schTASK")
    db.session.commit()
    if files is None:
        files = [pkg_resources.resource_filename(
            'invenio',
            os.path.join('testsuite', 'data', 'demo_record_marc_data.xml'))]

    # upload demo site files:
    bibupload_flags = '-i'
    if extra_info is not None and 'force-recids' in extra_info:
        bibupload_flags = '-i -r --force'
    for f in files:
        job_id += 1
        for cmd in (
            (bibupload, "bibupload -u admin %s %s" % (bibupload_flags, f)),
            (bibupload, "bibupload %d" % (job_id))
        ):
            if run_py_func(*cmd, passthrough=True).exit_code:
                print("ERROR: failed execution of", *cmd)
                sys.exit(1)

    i = count(job_id + 1).next
    for cmd in (
        (bibdocfile, "bibdocfile --textify --with-ocr --recid 97"),
        (bibdocfile, "bibdocfile --textify --all"),
        (bibindex, "bibindex -u admin"),
        (bibindex, "bibindex %d" % i()),
        (bibindex, "bibindex -u admin -w global"),
        (bibindex, "bibindex %d" % i()),
        (bibreformat, "bibreformat -u admin -o HB"),
        (bibreformat, "bibreformat %d" % i()),
        (bibrank, "bibrank -u admin"),
        (bibrank, "bibrank %d" % i()),
        (bibsort, "bibsort -u admin -R"),
        (bibsort, "bibsort %d" % i()),
        (oairepositoryupdater, "oairepositoryupdater -u admin"),
        (oairepositoryupdater, "oairepositoryupdater %d" % i()),
        (bibupload, "bibupload %d" % i()),
    ):
        if run_py_func(*cmd, passthrough=True).exit_code:
            print("ERROR: failed execution of", *cmd)
            sys.exit(1)
    print(">>> Demo records loaded successfully.")


def main():
    """Start the commandline manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
