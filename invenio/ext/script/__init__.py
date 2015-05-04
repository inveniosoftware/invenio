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

"""Initialize and configure Flask-Script extension.

Configuration
^^^^^^^^^^^^^
The following configuration variables are provided:

===================== =======================================================
`bind address`        Preferred binding address of the server. Can be used to
                      select a specific interface or to bind to all via
                      `0.0.0.0`.
`bind port`           Preferred binding port of the server. Can differ from
                      the one stated in `CFG_SITE_URL` so it can be accessed
                      via reverse proxy.
===================== =======================================================

They are assigned by the following parameters, in decreasing priority:

1. Command line arguments of `inveniomanage runserver`
2. `SERVER_BIND_ADDRESS` and `SERVER_BIND_PORT` configuration
3. Values guessed from `CFG_SITE_URL`
4. Defaults (`127.0.0.1:80`)
"""

from __future__ import print_function

import functools

import re

import ssl

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

    rng = random.SystemRandom()
    return ''.join(
        rng.choice(string.ascii_letters + string.digits)
        for dummy in range(0, 256)
    )


def print_progress(p, L=40, prefix='', suffix=''):
    """Print textual progress bar."""
    bricks = int(p * L)
    print('\r{prefix} [{bricks}{spaces}] {progress}% {suffix}'.format(
        prefix=prefix, suffix=suffix,
        bricks='#' * bricks, spaces=' ' * (L - bricks),
        progress=int(p * 100),
    ), end=' ')


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


def create_ssl_context(config):
    """Create :class:`ssl.SSLContext` from application config.

    :param config: Dict-like application configuration.
    :returns: A valid context or in case TLS is not enabled `None`.

    The following configuration variables are processed:

    ============================ ==============================================
    `SERVER_TLS_ENABLE`          If `True`, a SSL context will be created. In
                                 this case, the required configuration
                                 variables must be provided.
    `SERVER_TLS_KEY` (required)  Filepath (string) of private key provided as
                                 PEM file.
    `SERVER_TLS_CERT` (required) Filepath (string) of your certificate plus
                                 all intermediate certificate, concatenated in
                                 that order and stored as PEM file.
    `SERVER_TLS_KEYPASS`         If private key is encrypted, a password can be
                                 provided.
    `SERVER_TLS_PROTOCOL`        String that selects a protocol from
                                 `ssl.PROTOCOL_*`. Defaults to `SSLv23`. See
                                 :mod:`ssl` for details.
    `SERVER_TLS_CIPHERS`         String that selects possible ciphers according
                                 to the `OpenSSL cipher list format
                                 <https://www.openssl.org/docs/apps/
                                 ciphers.html>`_
    `SERVER_TLS_DHPARAMS`        Filepath (string) to parameters for
                                 Diffie-Helman key exchange. If not set the
                                 built-in parameters are used.
    `SERVER_TLS_ECDHCURVE`       Curve (string) that should be used for
                                 Elliptic Curve-based Diffie-Helman key
                                 exchange. If not set, the defaults provided by
                                 OpenSSL are used.
    ============================ ==============================================

    .. note:: In case `None` is returned because of a non-enabling
        configuration, TLS will be disabled. It is **not** possible to have a
        TLS and non-TLS configuration at the same time. So if TLS is activated,
        no non-TLS connection are accepted.

    .. important:: Keep in mind to change `CFG_SITE_URL` and
        `CFG_SITE_SECURE_URL` according to your TLS configuration. This does
        not only include the protocol (`http` vs `https`) but also the hostname
        that has to match the common name in your certificate. If a wildcard
        certificate is provided, the hostname stated in
        `CFG_SITE[_SECURE]_URL` must match the wildcard pattern.

    """
    ssl_context = None

    if config.get('SERVER_TLS_ENABLE', False):
        if 'SERVER_TLS_KEY' not in config \
                or 'SERVER_TLS_CERT' not in config:
            raise AttributeError(
                '`SERVER_TLS_KEY` and `SERVER_TLS_CERT` required!'
            )

        # CLIENT_AUTH creates a server context, so do not get confused here
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        if 'SERVER_TLS_PROTOCOL' in config:
            ssl_context.protocol = getattr(
                ssl,
                'PROTOCOL_{}'.format(config.get('SERVER_TLS_PROTOCOL'))
            )

        ssl_context.load_cert_chain(
            certfile=config.get('SERVER_TLS_CERT'),
            keyfile=config.get('SERVER_TLS_KEY'),
            password=config.get('SERVER_TLS_KEYPASS', None)
        )
        if 'SERVER_TLS_CIPHERS' in config:
            ssl_context.set_ciphers(
                config.get('SERVER_TLS_CIPHERS')
            )
        if 'SERVER_TLS_DHPARAMS' in config:
            ssl_context.load_dh_params(
                config.get('SERVER_TLS_DHPARAMS')
            )
        if 'SERVER_TLS_ECDHCURVE' in config:
            ssl_context.set_ecdh_curve(
                config.get('SERVER_TLS_ECDHCURVE')
            )

        # that one seems to be required for werkzeug
        ssl_context.check_hostname = False
    return ssl_context


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
    host = manager.app.config.get(
        'SERVER_BIND_ADDRESS',
        parsed_url.hostname or '127.0.0.1'
    )
    port = manager.app.config.get(
        'SERVER_BIND_PORT',
        parsed_url.port or 80
    )

    ssl_context = create_ssl_context(manager.app.config)

    runserver = Server(host=host, port=port, ssl_context=ssl_context)
    manager.add_command("runserver", runserver)

    # FIXME separation of concerns is violated here.
    from invenio.ext.collect import collect
    collect.init_script(manager)

    from invenio.ext.assets import command, bower
    manager.add_command("assets", command)
    manager.add_command("bower", bower)
