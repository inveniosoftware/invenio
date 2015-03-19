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

"""Initialize and configure Flask-Script extension."""

from __future__ import print_function

import functools

import re

from types import FunctionType

from flask import current_app, flash
from flask_registry import ModuleAutoDiscoveryRegistry, RegistryProxy
from flask_script import Manager as FlaskExtManager
from flask_script.commands import Clean, Server, Shell, ShowUrls

from invenio.base.signals import post_command, pre_command

from six.moves import urllib

from werkzeug.utils import find_modules, import_string


def change_command_name(method=None, new_name=None):
    """Change command name to `new_name` or replace '_' by '-'."""
    if method is None:
        return functools.partial(change_command_name, new_name=new_name)

    if new_name is None:
        new_name = method.__name__.replace('_', '-')
    method.__name__ = new_name

    return method


def generate_secret_key():
    """Generate secret key."""
    import string
    import random
    return ''.join([random.choice(string.ascii_letters + string.digits)
                    for dummy in range(0, 256)])


def print_progress(p, L=40, prefix='', suffix=''):
    """Print textual progress bar."""
    bricks = int(p * L)
    print('\r', prefix, end=' ')
    print('[{0}{1}] {2}%'.format('#' * bricks, ' ' * (L - bricks),
                                 int(p * 100)), end=' ')
    print(suffix, end=' ')


def check_for_software_updates(flash_message=False):
    """Check for a new release of Invenio.

    :return: True if you have latest version, else False if you need to upgrade
             or None if server was not reachable.
    """
    from invenio.config import CFG_VERSION
    from invenio.base.i18n import _
    try:
        find = re.compile('Invenio v[0-9]+.[0-9]+.[0-9]+(\-rc[0-9])?'
                          ' is released')

        release_notes = 'https://raw.githubusercontent.com/' \
            'inveniosoftware/invenio/master/RELEASE-NOTES'

        webFile = urllib.request.urlopen(release_notes)

        temp = ""
        version = ""
        version1 = ""
        while 1:
            temp = webFile.readline()
            match1 = find.match(temp)
            try:
                version = match1.group()
                break
            except Exception:
                pass
            if not temp:
                break

        webFile.close()
        submatch = re.compile('[0-9]+.[0-9]+.[0-9]+(\-rc[0-9])?')
        version1 = submatch.search(version)
        web_version = version1.group().split(".")

        local_version = CFG_VERSION.split(".")

        if (web_version[0] > local_version[0] or
                web_version[0] == local_version[0] and
                web_version[1] > local_version[1] or
                web_version[0] == local_version[0] and
                web_version[1] == local_version[1] and
                web_version[2] > local_version[2]):
            if flash_message:
                flash(_('A newer version of Invenio is available for '
                        'download. You may want to visit '
                        '<a href="%(wiki)s">%()s</a>',
                        wiki='<a href=\"http://invenio-software.org/wiki/'
                             '/Installation/Download'), 'warning')

            return False
    except Exception as e:
        print(e)
        if flash_message:
            flash(_('Cannot download or parse release notes '
                    'from %(release_notes)s', release_notes=release_notes),
                  'error')
        return None
    return True


class Manager(FlaskExtManager):

    """Custom manager implementation with signaling support."""

    def add_command(self, name, command):
        """Wrap default ``add_command`` method."""
        sender = command.run if type(command.run) is FunctionType \
            else command.__class__

        class SignalingCommand(command.__class__):
            def __call__(self, *args, **kwargs):
                app = self.app if not len(args) else args[0]
                with app.test_request_context():
                    pre_command.send(sender, args=args, **kwargs)
                res = super(SignalingCommand, self).__call__(*args, **kwargs)
                with app.test_request_context():
                    post_command.send(sender, args=args, **kwargs)
                return res

        command.__class__ = SignalingCommand
        return super(Manager, self).add_command(name, command)


def set_serve_static_files(sender, *args, **kwargs):
    """Enable serving of static files for `runserver` command.

    Normally Apache serves static files, but during development and if you are
    using the Werkzeug standalone development server, you can set this flag to
    `True`, to enable static file serving.
    """
    current_app.config.setdefault('CFG_FLASK_SERVE_STATIC_FILES', True)

pre_command.connect(set_serve_static_files, sender=Server)


def register_manager(manager):
    """Register all manager plugins and default commands with the manager."""
    from six.moves.urllib.parse import urlparse
    managers = RegistryProxy('managers', ModuleAutoDiscoveryRegistry, 'manage')

    with manager.app.app_context():
        for script in find_modules('invenio.base.scripts'):
            manager.add_command(script.split('.')[-1],
                                import_string(script + ':manager'))
        for script in managers:
            if script.__name__ == 'invenio.base.manage':
                continue
            manager.add_command(script.__name__.split('.')[-2],
                                getattr(script, 'manager'))

    manager.add_command("clean", Clean())
    manager.add_command("show-urls", ShowUrls())
    manager.add_command("shell", Shell())
    parsed_url = urlparse(manager.app.config.get('CFG_SITE_URL'))
    port = parsed_url.port or 80
    host = parsed_url.hostname or '127.0.0.1'
    runserver = Server(host=host, port=port)
    manager.add_command("runserver", runserver)

    # FIXME separation of concerns is violated here.
    from invenio.ext.collect import collect
    collect.init_script(manager)

    from invenio.ext.assets import command, bower
    manager.add_command("assets", command)
    manager.add_command("bower", bower)
