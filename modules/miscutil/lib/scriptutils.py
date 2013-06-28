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


import functools
from functools import wraps
from flask.ext.script import Manager as FlaskExtManager
from invenio.signalutils import pre_command, post_command


def change_command_name(method=None, new_name=None):
    """Changes command name to `new_name` or replaces '_' by '-'."""
    if method is None:
        return functools.partial(change_command_name, new_name=new_name)

    if new_name is None:
        new_name = method.__name__.replace('_', '-')
    method.__name__ = new_name

    return method


def generate_secret_key():
    import string
    import random
    return ''.join([random.choice(string.letters + string.digits)
                    for dummy in range(0, 256)])


def print_progress(p, L=40, prefix='', suffix=''):
    bricks = int(p * L)
    print '\r', prefix,
    print '[{0}{1}] {2}%'.format('#' * bricks, ' ' * (L - bricks),
                                 int(p * 100)),
    print suffix,


class Manager(FlaskExtManager):
    def add_command(self, name, command):
        f = command.run

        @wraps(f)
        def wrapper(*args, **kwds):
            pre_command.send(f, *args, **kwds)
            result = f(*args, **kwds)
            post_command.send(f, *args, **kwds)
            return result
        command.run = wrapper
        return super(Manager, self).add_command(name, command)


def register_manager(manager):
    """
    Register all manager plugins and default commands with the manager.
    """
    from urlparse import urlparse
    from flask.ext.script.commands import Shell, Server, ShowUrls  # , Clean
    #from invenio.errorlib import register_exception
    from invenio.config import CFG_SITE_URL
    from invenio.importutils import autodiscover_modules

    # Call add_command() in inveniomanage module to register managers.
    modules = autodiscover_modules(['invenio'],
                                   '.+_manager\.py')
    for m in modules:
        name = m.__name__[len('invenio.'):-len('_manager')]
        if 'manager' in dir(m):
            candidate = getattr(m, 'manager')
            if isinstance(candidate, FlaskExtManager):
                manager.add_command(name, candidate)

    #FIXME clean command is broken
    #manager.add_command("clean", Clean())
    manager.add_command("show-urls", ShowUrls())
    manager.add_command("shell", Shell())
    parsed_url=  urlparse(CFG_SITE_URL)
    port = parsed_url.port or 80
    host = parsed_url.hostname or '127.0.0.1'
    manager.add_command("runserver", Server(host=host, port=port))
