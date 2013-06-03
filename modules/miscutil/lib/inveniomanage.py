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


import os
import sys
from pprint import pformat
from flask.ext.script import Manager
from flask.ext.script.commands import ShowUrls  # , Clean
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR, CFG_SITE_SECRET_KEY
from invenio.pluginutils import PluginContainer
from invenio.sqlalchemyutils import db
from invenio.webinterface_handler_flask import create_invenio_flask_app


def change_command_name(action, new_name):
    def decorator(f):
        f.__name__ = new_name
        return action(f)
    return decorator


def generate_secret_key():
    import string
    import random
    return ''.join([random.choice(string.letters + string.digits)
                    for dummy in range(0, 256)])

# Fixes problems with empty secret key in config manager.
if 'config' in sys.argv and \
        (not CFG_SITE_SECRET_KEY or CFG_SITE_SECRET_KEY == ''):
    create_invenio_flask_app = create_invenio_flask_app(
        SECRET_KEY=generate_secret_key())

manager = Manager(create_invenio_flask_app)


@manager.shell
def make_shell_context():
    """Extend shell context."""
    from flask import current_app
    return dict(current_app=current_app, db=db)


def _invenio_manager_plugin_builder(plugin_name, plugin_code):
    """
    Handy function to bridge pluginutils with (Invenio) blueprints.
    """
    if 'manager' in dir(plugin_code):
        candidate = getattr(plugin_code, 'manager')
        if isinstance(candidate, Manager):
            return candidate
    raise ValueError('%s is not a valid manager plugin' % plugin_name)

## Let's load all the managers that are composing this Invenio manage CLI
_MANAGERS = PluginContainer(
    os.path.join(CFG_PYLIBDIR, 'invenio', '*_manager.py'),
    plugin_builder=_invenio_manager_plugin_builder)

## Let's report about broken plugins
open(os.path.join(CFG_LOGDIR, 'broken-managers.log'), 'w').write(
    pformat(_MANAGERS.get_broken_plugins()))

for manager_name, plugin in _MANAGERS.iteritems():
    name = manager_name[:-len('_manager')]
    manager.add_command(name, plugin)


@manager.command
def version():
    """ Get running version of Invenio """
    from invenio.config import CFG_VERSION
    return CFG_VERSION


@change_command_name(manager.command, 'detect-system-name')
def detect_system_details():
    """
    Detect and print system details such as Apache/Python/MySQL
    versions etc. (useful for debugging problems on various OS)
    """
    import sys
    import socket
    print ">>> Going to detect system details..."
    print "* Hostname: " + socket.gethostname()
    print "* Invenio version: " + version()
    print "* Python version: " + sys.version.replace("\n", " ")

    try:
        from invenio.apache_manager import version as detect_apache_version
        print "* Apache version: " + detect_apache_version(
            separator=";\n                  ")
    except ImportError:
        print >> sys.stderr, '* Apache manager could not be imported.'

    try:
        from invenio.database_manager import \
            mysql_info, \
            version as detect_database_driver_version, \
            driver as detect_database_driver_name

        print "* " + detect_database_driver_name() + " version: " + \
            detect_database_driver_version()
        try:
            out = mysql_info(separator="\n", line_format="    - %s: %s")
            print "* MySQL version:\n", out
        except Exception, e:
            print >> sys.stderr, "* Error:", e
    except ImportError:
        print >> sys.stderr, '* Database manager could not be imported.'

    print ">>> System details detected successfully."


#FIXME clean command is broken
#manager.add_command("clean", Clean())
manager.add_command("show-urls", ShowUrls())


def main():
    manager.run()

if __name__ == "__main__":
    main()
