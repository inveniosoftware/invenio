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

"""Command line script to manage configuration operations."""

from __future__ import print_function, unicode_literals

import ast
import errno
import imp
import os.path
import sys

from pprint import pformat

from flask import current_app

from invenio.ext.script import Manager, change_command_name, \
    generate_secret_key

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

manager = Manager(usage="Perform configuration operations")


def default_keys():
    """Yield list of default configuration keys."""
    yield 'SECRET_KEY'
    for k in current_app.config.keys():
        if k.startswith('CFG_DATABASE'):
            yield k


def get_instance_config_object(filename='invenio.cfg', silent=True):
    """Get the configuration object from the given filename."""
    d = imp.new_module('config')
    d.__file__ = filename
    try:
        with current_app.open_instance_resource(filename) as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        if not (silent and e.errno in (errno.ENOENT, errno.EISDIR)):
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
    return d


@manager.command
def get(name):
    """
    Return value of VARNAME read from CONF files.

    Useful for third-party programs to access values of conf options.
    Return None if VARNAME is not found.

    """
    try:
        varvalue = current_app.config.get(name.upper(), None)
        if varvalue is None:
            raise Exception('Value of "%s" is None.' % name)
        print(varvalue)
    except Exception as e:
        if e.message:
            print(e.message, file=sys.stderr)
        sys.exit(1)


def set_(name, value, filename='invenio.cfg'):
    """Set instance config variable with `value`."""
    name = name.upper()
    try:
        d = get_instance_config_object(filename)
    except Exception as e:
        print("ERROR: ", str(e), file=sys.stderr)
        sys.exit(1)
    if name in d.__dict__:
        print("ERROR: %s is already filled." % (name, ))
        sys.exit(1)

    try:
        value = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass

    with current_app.open_instance_resource(filename, 'a') as config_file:
        print(name, '=', pformat(value), file=config_file)

# See http://bugs.python.org/issue7688
set_.__name__ = str('set')
manager.command(set_)


@manager.command
def locate(filename='invenio.cfg'):
    """Print the location of the configuration file."""
    try:
        with current_app.open_instance_resource(filename, 'r') as config_file:
            print(os.path.abspath(config_file.name))
    except IOError:
        print("ERROR: configuration file does not exist.", file=sys.stderr)
        return 1


def list_():
    """Print a list of all conf options and values from CONF."""
    for key, value in current_app.config.items():
        print(key, '=', pformat(value))

# See http://bugs.python.org/issue7688
list_.__name__ = str('list')
manager.command(list_)


@manager.command
def update(filename='invenio.cfg', silent=True):
    """Update new config.py from conf options.

    The previous config.py is kept in a backup copy.
    """
    d = get_instance_config_object(filename, silent)
    new_config = StringIO()
    keys = set(d.__dict__.keys()) | set(default_keys())
    keys = list(keys)
    keys.sort()
    for key in keys:
        if key != key.upper():
            continue
        value = d.__dict__.get(key, current_app.config[key])
        type_ = type(value)
        prmt = key + ' (' + type_.__name__ + ') [' + pformat(value) + ']: '

        new_value = raw_input(prmt)
        try:
            new_value = ast.literal_eval(new_value)
        except (SyntaxError, ValueError):
            pass

        print('>>>', key, '=', pformat(new_value))
        print(key, '=', pformat(new_value), file=new_config)

    with current_app.open_instance_resource(filename, 'w') as config_file:
        config_file.write(new_config.getvalue())


config_create = Manager(usage="Creates variables in config file.")
manager.add_command("create", config_create)


@config_create.command
@change_command_name
def secret_key(key=None, filename='invenio.cfg', silent=True):
    """Generate and append SECRET_KEY to invenio.cfg.

    Useful for the installation process.
    """
    print(">>> Going to generate random SECRET_KEY...")
    try:
        d = get_instance_config_object(filename)
    except Exception as e:
        print("ERROR: ", str(e), file=sys.stderr)
        sys.exit(1)
    if len(d.__dict__.get('SECRET_KEY', '')) > 0:
        print("ERROR: SECRET_KEY is already filled.")
        sys.exit(1)
    from invenio.base.config import SECRET_KEY
    if current_app.config.get('SECRET_KEY') != SECRET_KEY:
        print("WARNING: custom config package already contains SECRET_KEY.",
              file=sys.stderr)
        print(">>> No need to generate secret key.")
    else:
        if key is None:
            key = generate_secret_key()
        with current_app.open_instance_resource(filename, 'a') as config_file:
            print('SECRET_KEY =', pformat(key), file=config_file)
            print(">>> SECRET_KEY appended to `%s`." % (config_file.name, ))


def main():
    """Run the command line manager."""
    from invenio.base.factory import create_app
    manager.app = create_app()
    manager.run()


if __name__ == '__main__':
    main()
