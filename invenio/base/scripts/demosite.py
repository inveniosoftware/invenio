# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

import warnings

warnings.warn("Use of `inveniomanage demosite populate` is being deprecated. "
              "Please use `uploader` module to insert demo records.",
              PendingDeprecationWarning)

import os
import pkg_resources
import sys

from invenio.ext.script import Manager

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
    from invenio.config import CFG_PREFIX
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
        for cmd in ["%s/bin/bibupload -u admin %s %s" % (CFG_PREFIX, bibupload_flags, f),
                    "%s/bin/bibupload %d" % (CFG_PREFIX, job_id)]:
            if os.system(cmd):
                print("ERROR: failed execution of", cmd)
                sys.exit(1)

    for cmd in ["bin/bibdocfile --textify --with-ocr --recid 97",
                "bin/bibdocfile --textify --all",
                "bin/bibindex -u admin",
                "bin/bibindex %d" % (job_id + 1,),
                "bin/bibindex -u admin -w global",
                "bin/bibindex %d" % (job_id + 2,),
                "bin/bibreformat -u admin -o HB",
                "bin/bibreformat %d" % (job_id + 3,),
                "bin/webcoll -u admin",
                "bin/webcoll %d" % (job_id + 4,),
                "bin/bibrank -u admin",
                "bin/bibrank %d" % (job_id + 5,),
                "bin/bibsort -u admin -R",
                "bin/bibsort %d" % (job_id + 6,),
                "bin/oairepositoryupdater -u admin",
                "bin/oairepositoryupdater %d" % (job_id + 7,),
                "bin/bibupload %d" % (job_id + 8,)]:
        cmd = os.path.join(CFG_PREFIX, cmd)
        if os.system(cmd):
            print("ERROR: failed execution of", cmd)
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
