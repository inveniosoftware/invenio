# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Perform demosite operations."""

from __future__ import print_function

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
def populate(packages=[], default_data=True, files=None,
             job_id=0, extra_info=None):
    """Load demo records.  Useful for testing purposes."""
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

    for f in files:
        job_id += 1
        for cmd in ["%s/bin/bibupload -u admin -i %s" % (CFG_PREFIX, f),
                    "%s/bin/bibupload %d" % (CFG_PREFIX, job_id)]:
            if os.system(cmd):
                print("ERROR: failed execution of", cmd)
                sys.exit(1)
    for cmd in ["bin/bibdocfile --textify --with-ocr --recid 97",
                "bin/bibdocfile --textify --all",
                "bin/bibindex -u admin",
                "bin/bibindex %d" % (job_id + 1,),
                "bin/bibreformat -u admin -o HB",
                "bin/bibreformat %d" % (job_id + 2,),
                "bin/webcoll -u admin",
                "bin/webcoll %d" % (job_id + 3,),
                "bin/bibrank -u admin",
                "bin/bibrank %d" % (job_id + 4,),
                "bin/bibsort -u admin -R",
                "bin/bibsort %d" % (job_id + 5,),
                "bin/oairepositoryupdater -u admin",
                "bin/oairepositoryupdater %d" % (job_id + 6,),
                "bin/bibupload %d" % (job_id + 7,)]:
        cmd = os.path.join(CFG_PREFIX, cmd)
        if os.system(cmd):
            print("ERROR: failed execution of", cmd)
            sys.exit(1)
    print(">>> Demo records loaded successfully.")


@option_packages
def create(packages=[]):
    """Populate database with demo site data."""
    from invenio.ext.sqlalchemy import db
    from invenio.config import CFG_PREFIX
    from invenio.modules.accounts.models import User
    from invenio.base.scripts.config import get_conf

    if not packages:
        packages = ['invenio_demosite.base']

    print(">>> Going to create demo site...")
    db.session.execute("TRUNCATE schTASK")
    try:
        db.session.execute("TRUNCATE session")
    except:
        pass
    User.query.filter(User.email == '').delete()
    db.session.commit()

    from werkzeug.utils import import_string
    map(import_string, packages)

    from invenio.base.scripts.database import load_fixtures
    load_fixtures(packages=packages, truncate_tables_first=True)

    db.session.execute("UPDATE idxINDEX SET stemming_language='en' WHERE name "
                       "IN ('global','abstract','keyword','title','fulltext'"
                       ",'miscellaneous')")
    db.session.commit()

    conf = get_conf()

    from invenio.legacy.inveniocfg import cli_cmd_reset_sitename, \
        cli_cmd_reset_siteadminemail, cli_cmd_reset_fieldnames

    cli_cmd_reset_sitename(conf)
    cli_cmd_reset_siteadminemail(conf)
    cli_cmd_reset_fieldnames(conf)  # needed for I18N demo ranking method names

    for cmd in ["%s/bin/webaccessadmin -u admin -c -r -D" % CFG_PREFIX,
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 1" % CFG_PREFIX,
                "%s/bin/bibsort -u admin --load-config" % CFG_PREFIX,
                "%s/bin/bibsort 2" % CFG_PREFIX, ]:
        if os.system(cmd):
            print("ERROR: failed execution of", cmd)
            sys.exit(1)
    print(">>> Demo site created successfully.")


def main():
    """Start the commandline manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
