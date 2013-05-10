# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from flask.ext.script import Manager
from invenio.inveniomanage import change_command_name

manager = Manager(usage="Perform configuration operations")


def get_conf():
    try:
        from invenio.config import CFG_ETCDIR
    except:
        CFG_ETCDIR = None
    from invenio.inveniocfg import prepare_conf

    class TmpOptions(object):
        conf_dir = CFG_ETCDIR

    return prepare_conf(TmpOptions())


@manager.command
def get(name):
    """
    Return value of VARNAME read from CONF files.  Useful for
    third-party programs to access values of conf options such as
    CFG_PREFIX.  Return None if VARNAME is not found.
    """
    import sys
    conf = get_conf()

    try:
        name = name.lower()
        # do not pay attention to section names yet:
        all_options = {}
        for section in conf.sections():
            for option in conf.options(section):
                all_options[option] = conf.get(section, option)
        varvalue = all_options.get(name, None)
        if varvalue is None:
            raise Exception('Value of "%s" is None.' % name)
        print varvalue
    except Exception, e:
        if e.message:
            print >> sys.stderr, e.message
        sys.exit(1)


@manager.command
def list():
    """
    Print a list of all conf options and values from CONF.
    """
    conf = get_conf()
    sections = conf.sections()
    sections.sort()
    for section in sections:
        options = conf.options(section)
        options.sort()
        for option in options:
            print option.upper(), '=', conf.get(section, option)


@manager.command
def update():
    """
    Update new config.py from conf options, keeping previous
    config.py in a backup copy.
    """
    from invenio.inveniocfg import update_config_py
    conf = get_conf()
    update_config_py(conf)

config_create = Manager(usage="Creates variables in config file.")
manager.add_command("create", config_create)


@change_command_name(config_create.command, 'secret-key')
def secret_key(key=None):
    """Generate and append CFG_SITE_SECRET_KEY to invenio-local.conf.
    Useful for the installation process."""
    import os
    import sys
    import string
    import random
    from invenio.inveniocfg import _grep_version_from_executable
    print ">>> Going to generate random CFG_SITE_SECRET_KEY..."
    try:
        from invenio.config import CFG_ETCDIR, CFG_SITE_SECRET_KEY
    except ImportError:
        print "ERROR: please run 'inveniocfg --update-config-py' first."
        sys.exit(1)
    if CFG_SITE_SECRET_KEY is not None and len(CFG_SITE_SECRET_KEY) > 0:
        print "ERROR: CFG_SITE_SECRET_KEY is already filled."
        sys.exit(1)
    invenio_local_path = CFG_ETCDIR + os.sep + 'invenio-local.conf'
    if _grep_version_from_executable(invenio_local_path, 'CFG_SITE_SECRET_KEY'):
        print "WARNING: invenio-local.conf already contains CFG_SITE_SECRET_KEY."
        print "You may want to run 'inveniocfg --update-all'' now."
        print ">>> No need to generate secret key."
    else:
        if key is None:
            key = ''.join([random.choice(string.letters + string.digits)
                          for dummy in range(0, 256)])
        with open(invenio_local_path, 'a') as f:
            f.write('\nCFG_SITE_SECRET_KEY = %s\n' % (key, ))
        print ">>> CFG_SITE_SECRET_KEY appended to `%s`." % (invenio_local_path, )


def main():
    from invenio.webinterface_handler_flask import create_invenio_flask_app
    app = create_invenio_flask_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
