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

import StringIO
import errno
import imp
import os
import sys

from pprint import pformat
from flask import current_app
from invenio.ext.script import Manager, change_command_name, \
    generate_secret_key

manager = Manager(usage="Perform configuration operations")


def default_keys():
    yield 'SECRET_KEY'
    for k in current_app.config.keys():
        if k.startswith('CFG_DATABASE'):
            yield k


def get_instance_config_object(filename='invenio.cfg', silent=True):
    d = imp.new_module('config')
    d.__file__ = filename
    try:
        with current_app.open_instance_resource(filename) as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        if not (silent and e.errno in (errno.ENOENT, errno.EISDIR)):
            e.strerror = 'Unable to load configuration file (%s)' % e.strerror
            raise
        d.__dict__ = {}
    return d


def get_conf():
    try:
        from invenio.config import CFG_ETCDIR
    except:
        CFG_ETCDIR = None
    from invenio.legacy.inveniocfg import prepare_conf

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
    try:
        varvalue = current_app.config.get(name.upper(), None)
        if varvalue is None:
            raise Exception('Value of "%s" is None.' % name)
        print varvalue
    except Exception, e:
        if e.message:
            print >> sys.stderr, e.message
        sys.exit(1)


def set_(name, value, filename='invenio.cfg'):
    """Set instance config variable with `value`."""
    name = name.upper()
    try:
        d = get_instance_config_object(filename)
    except Exception as e:
        print >>sys.stderr, "ERROR: ", str(e)
        sys.exit(1)
    if name in d.__dict__:
        print "ERROR: %s is already filled." % (name, )
        sys.exit(1)

    try:
        type_ = type(current_app.config.get(name, value))
        value = type_(value)
    except:
        print '>>> Using default type ...'

    with current_app.open_instance_resource(filename, 'a') as config_file:
        print >>config_file, name, '=', pformat(value)

set_.__name__ = 'set'
manager.command(set_)


@manager.command
def list():
    """
    Print a list of all conf options and values from CONF.
    """
    for key, value in current_app.config.iteritems():
        print key, '=', pformat(value)


@manager.command
def update(filename='invenio.cfg', silent=True):
    """
    Update new config.py from conf options, keeping previous
    config.py in a backup copy.
    """
    d = get_instance_config_object(filename, silent)

    new_config = StringIO.StringIO()
    for key in set(d.__dict__.keys()) | set(default_keys()):
        if key != key.upper():
            continue
        value = d.__dict__.get(key, current_app.config[key])
        type_ = type(value)
        prmt = key + ' (' + type_.__name__ + ') [' + pformat(value) + ']: '
        while True:
            new_value = raw_input(prmt)
            try:
                if type_ is not type(None):
                    new_value = type_(new_value or value)
                else:
                    new_value = new_value if new_value != '' else None
                break
            except:
                pass
        print '>>>', key, '=', pformat(new_value)
        print >>new_config, key, '=', pformat(new_value)

    with current_app.open_instance_resource(filename, 'w') as config_file:
        config_file.write(new_config.getvalue())


config_create = Manager(usage="Creates variables in config file.")
manager.add_command("create", config_create)


@config_create.command
@change_command_name
def secret_key(key=None, filename='invenio.cfg', silent=True):
    """Generate and append SECRET_KEY to invenio.cfg.
    Useful for the installation process."""
    print ">>> Going to generate random SECRET_KEY..."
    try:
        d = get_instance_config_object(filename)
    except Exception as e:
        print >>sys.stderr, "ERROR: ", str(e)
        sys.exit(1)
    if len(d.__dict__.get('SECRET_KEY', '')) > 0:
        print "ERROR: SECRET_KEY is already filled."
        sys.exit(1)
    from invenio.base.config import SECRET_KEY
    if current_app.config.get('SECRET_KEY') != SECRET_KEY:
        print >>sys.stderr, "WARNING: custom config package already contains SECRET_KEY."
        print ">>> No need to generate secret key."
    else:
        if key is None:
            key = generate_secret_key()
        with current_app.open_instance_resource(filename, 'a') as config_file:
            print >>config_file, 'SECRET_KEY =', pformat(key)
            print ">>> SECRET_KEY appended to `%s`." % (config_file.name, )


def main():
    from invenio.base.factory import create_app
    manager.app = create_app()
    manager.run()

if __name__ == '__main__':
    main()
