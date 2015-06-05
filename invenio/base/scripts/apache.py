# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""Apache configuration generator.

Configuration Settings
----------------------
The configuration generation relies on the following variables.

=================================== =============================================
`APACHE_GUESS_CERT_PATHS`           Whether to guess certificate paths instead
                                    of expecting them to be set manually in the
                                    configuration.
                                    **Default:** 0
`APACHE_LISTEN_DIRECTIVE_HTTP`      Enable a `Listen: <port>` directive in the
                                    generated apache configuration for HTTP.
                                    **Default:** 0
`APACHE_LISTEN_DIRECTIVE_HTTPS`     Enable a `Listen: <port>` directive in the
                                    generated apache configuration for HTTPS.
                                    **Default:** 1
`APACHE_WSGI_PROCESS_GROUP`         Internal WSGI process group that will be
                                    used by the webserver.
                                    **Default:** "invenio"
`APACHE_WSGI_PROCESS_NAME`          Internal WSGI process name that will be used
                                    by the webserver.
                                    **Default:** "invenio"
`APACHE_SERVER_HTTP_ALIASES`        Space-delimited aliases for HTTP.
                                    **Default:** None
`APACHE_SERVER_HTTPS_ALIASES`       Space-delimited aliases for HTTPS.
                                    **Default:** None
`APACHE_CERTIFICATE_FILE`           Full path to certificate file.
                                    **Default:** None
`APACHE_CERTIFICATE_KEY_FILE`       Full path to KEY file.
                                    **Default:** None
`APACHE_CERTIFICATE_PEM_FILE`       Full path to PEM file.
                                    **Default:** None
`APACHE_WSGI_DAEMON_PROCESSES`      Number of WSGI processes to spawn.
                                    **Default:** 5 (Overriden to 1 on DEBUG mode)
`APACHE_RUNNING_AS_USER`            User that apache is running as.
                                    **Default:** "www-data"
`CFG_SITE_ADMIN_EMAIL`              Admin email for the entire website.
                                    **Default:** "info@invenio-software.org"
`CFG_BIBDOCFILE_USE_XSENDFILE`      Whether to use Xsendfile.
                                    **Default:** 0
`CFG_WEBSTYLE_HTTP_USE_COMPRESSION` Whether to use HTTP compression.
                                    **Default:** 0
=================================== =============================================
"""
from __future__ import print_function

import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
from distutils.sysconfig import get_python_lib
import warnings
from distutils import dir_util
from os import path
from urlparse import urlparse

import pkg_resources
from flask import current_app
from werkzeug.utils import cached_property

from invenio.base.utils import staticproperty, classproperty
from invenio.ext.script import Manager, change_command_name
from invenio.ext.template import render_template_to_string
from invenio.utils.deprecation import RemovedInInvenio22Warning
from invenio.utils.shell import which


manager = Manager(usage=__doc__)
app_cfg = current_app.config


def _detect_ip_address():
    """Detect IP address of this computer.

    Useful for creating Apache vhost conf snippet on RHEL like machines.
    However, if wanted site is 0.0.0.0, then use that, since we are running
    inside Docker.

    :return: IP address, or '*' if cannot detect
    :rtype: string

    .. note:: creates socket for real in order to detect real IP address,
              not the loopback one.
    """
    from invenio.base.globals import cfg
    if '0.0.0.0' in cfg.get('CFG_SITE_URL'):
        return '0.0.0.0'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('invenio-software.org', 0))
        return s.getsockname()[0]
    except Exception:
        return '*'


def _grep_version_from_executable(path_to_exec, version_regexp):
    """Try to detect a program version.

    Grep in its binary PATH_TO_EXEC and looking for VERSION_REGEXP.  Return
    program version as a string.  Return empty string if not succeeded.
    """
    from invenio.utils.shell import run_shell_command
    exec_version = ""
    if os.path.exists(path_to_exec):
        dummy1, cmd2_out, dummy2 = run_shell_command(
            "strings %s | grep %s", (path_to_exec, version_regexp))
        if cmd2_out:
            for cmd2_out_line in cmd2_out.split("\n"):
                if len(cmd2_out_line) > len(exec_version):
                    # the longest the better
                    exec_version = cmd2_out_line
    return exec_version


@manager.command
def version(separator='\n', formatting='{version} [{executable}]'):
    """Detect version of apache binary.

    :returns: user-readable apache version strings
    :rtype: ((apache_version, binary_fullpath), ...)
    """
    def _version():
        known_apache_binary_names = ('apache2', 'apache', 'httpd')

        for binary_name in known_apache_binary_names:
            binary_fullpath = which(binary_name)
            if not binary_fullpath:
                continue
            v_out = subprocess.check_output([binary_fullpath, "-v"])
            try:
                apache_version = re.findall('(Apache/.*)', v_out)[0]
            except IndexError:
                apache_version = 'No version string found!'
            finally:
                yield apache_version, binary_fullpath

    out = []
    for apache_version, binary_fullpath in _version():
        out.append(formatting.format(version=apache_version,
                                     executable=binary_fullpath))

    if separator is None:
        return out
    return separator.join(out)

@manager.command
@manager.option('--no-ssl', dest='no_ssl', action='store_true')
@manager.option('-f', '--force', dest='force', action='store_true')
@change_command_name
def create_config(force=False, no_ssl=False):
    """Create Apache configuration files for this site.

    Keep previous files in a backup copy.
    """
    class Cfg(object):
        """HTTP configuration resolver."""

        CANDIDATE_PATHS = {
            'apache': '/etc/apache/ssl',
            'apache2': '/etc/apache2/ssl',
            'tls': '/etc/pki/tls'
        }
        KNOWN_CERT_DIRECTIVES = (
            'APACHE_CERTIFICATE_FILE',
            'APACHE_CERTIFICATE_KEY_FILE',
            'APACHE_CERTIFICATE_PEM_FILE'
        )

        def __init__(self):
            """Initialize easily resolvable values."""
            self.sys_prefix = sys.prefix
            self.python_lib_dir = get_python_lib()
            self.admin_email = app_cfg['CFG_SITE_ADMIN_EMAIL']
            self.collect_static_root = app_cfg['COLLECT_STATIC_ROOT']
            self.bibdocfile_use_xsendfile = \
                app_cfg['CFG_BIBDOCFILE_USE_XSENDFILE']
            self.webstyle_http_use_compression = \
                app_cfg['CFG_WEBSTYLE_HTTP_USE_COMPRESSION']
            self.wsgi_processes = app_cfg.get('APACHE_WSGI_DAEMON_PROCESSES', 5)
            # Debug
            if app_cfg['DEBUG']:
                print('DEBUG enabled: Overriding wsgi_processes of Apache to 1')
                self.wsgi_processes = 1

        @staticproperty
        def sso():
            """Compile SSO authentication settings.

            :returns: {
                'enabled': whether to enable SSO,
                'login_url': SSO login URL
                }
            :rtype: dict
            """
            sso = {
                'enabled': app_cfg['CFG_EXTERNAL_AUTH_USING_SSO'],
                'login_url': app_cfg.get('SSO_LOGIN_URL', None)
            }
            if sso['enabled']:
                assert sso['login_url'], "SSO enabled by URL not set"
            return sso

        @staticproperty
        def log():
            """Return full paths for logging.

            :returns: {
                'logpath': {
                    'out': {
                        'http': suffix for http logs
                        'https': suffix for https logs
                    },
                    'err': {
                        'http': suffix for http error logs
                        'https': suffix for https error logs
                    }
                }
            :rtype: dict
            """
            def generate_fullpath(type_, stream):
                return path.join(
                    app_cfg['CFG_LOGDIR'],
                    'apache{type}.{stream}'
                    .format( type='-' + type_ if type_ else '', stream=stream))
            return {
                'out': {
                    'http': generate_fullpath('', 'log'),
                    'https': generate_fullpath('ssl', 'log')
                },
                'err': {
                    'http': generate_fullpath('', 'err'),
                    'https': generate_fullpath('ssl', 'err')
                }
            }

        @classproperty
        def _resolved_dir(cls):
            """Return the SSL path that was found in the filesystem."""
            for candidate_path in cls.CANDIDATE_PATHS.values():
                if path.isdir(candidate_path):
                    return candidate_path
            # For-loop never returned
            print("Cannot continue unless one of these paths is present: {}"
                  .format(cls.CANDIDATE_PATHS), file=sys.stderr)
            sys.exit(1)

        @staticproperty
        def vhosts():
            """Resolve URI information.

            :returns: {
                'http': urlparse.ParseResult for http site with `server_alias`
                'https': urlparse.ParseResult for https site with `server_alias`
                }
            :rtype: dict
            """
            vhost_site = urlparse(app_cfg['CFG_SITE_URL'])
            vhost_site_secure = urlparse(app_cfg['CFG_SITE_SECURE_URL'])

            if not vhost_site.port:
                vhost_site.port = 80
            if not vhost_site_secure.port:
                vhost_site_secure.port = 443

            vhost_site.server_alias = \
                app_cfg.get('APACHE_SERVER_HTTP_ALIASES')
            vhost_site_secure.server_alias = \
                app_cfg.get('APACHE_SERVER_HTTPS_ALIASES')

            if vhost_site.scheme not in ('http', 'https'):
                raise AssertionError("Scheme must be http or https, "
                                        "not `{0}`".format(vhost_site.scheme))

            return {'http': vhost_site, 'https': vhost_site_secure}

        def listen_directive_needed(self, scheme):
            """Whether apache `Listen` directive is required.

            :param scheme: 'http' or 'https'
            :type scheme: str

            :returns: whether a listen directive should be added to config
            :rtype: bool
            """
            assert scheme in ('http', 'https')
            if app_cfg.get('APACHE_GUESS_LISTEN_DIRECTIVE'):
                needed = {
                    Cfg.CANDIDATE_PATHS['apache']: True,
                    Cfg.CANDIDATE_PATHS['apache2']: False,
                    Cfg.CANDIDATE_PATHS['tls']: True
                }[self._resolved_dir]
                if (scheme == 'http' and self.vhosts[scheme].port == 80) or \
                        (scheme == 'https' and self.vhosts[scheme].port == 443):
                    return needed
                else:
                    return True
            else:
                cfg_key = 'APACHE_LISTEN_DIRECTIVE_' + scheme.upper()
                return bool(app_cfg[cfg_key])

        # XXX: Unused
        @staticproperty
        def aliases():
            """Resolve static root aliases."""
            def listdir_fullpath(d):
                return [path.join(d, f) for f in os.listdir(d)]

            static_root = app_cfg['COLLECT_STATIC_ROOT']
            dir_util.mkpath(static_root)

            for entity in listdir_fullpath(static_root):
                basename = path.basename(entity)
                if path.isdir(entity):
                    yield '/{}/'.format(basename)
                else:
                    yield '/{}'.format(basename)

        # TODO: Perhaps this is no longer neccessary. Test on CentOS.
        @cached_property
        def vhost_ip_address(self):
            """Get vhost IP address.

            :returns: '*' or the IP address of the vhost in case the environment
            needs it in order to function.
            :rtype: str
            """
            vhost_ip_address_needed = {
                Cfg.CANDIDATE_PATHS['apache']: False,
                Cfg.CANDIDATE_PATHS['apache2']: False,
                Cfg.CANDIDATE_PATHS['tls']: True
            }[self._resolved_dir]

            if vhost_ip_address_needed:
                from invenio.legacy.inveniocfg import _detect_ip_address
                return _detect_ip_address()
            else:
                return '*'

        @classproperty
        def _user_supplied_custom_files(cls):
            """Resolve whether the user supplied custom certificate paths."""
            return bool(tuple((i for i in cls.KNOWN_CERT_DIRECTIVES
                               if i in app_cfg)))

        @cached_property
        def ssl(self):
            """Resolve ssl file paths.

            :returns: {
                'pem': pem path
                'crt': crt path
                'key': key path
                }
            :rtype: dict
            """
            if app_cfg.get('APACHE_GUESS_CERT_PATHS', False):
                if self._resolved_dir in (Cfg.CANDIDATE_PATHS['apache'],
                                            Cfg.CANDIDATE_PATHS['apache2']):
                    pem_path = path.join(self._resolved_dir, 'server.pem')
                    crt_path = path.join(self._resolved_dir, 'server.crt')
                    key_path = path.join(self._resolved_dir, 'server.key')
                elif self._resolved_dir == Cfg.CANDIDATE_PATHS['tls']:
                    pem_path = ''
                    crt_path = path.join(self._resolved_dir, 'localhost.crt')
                    key_path = path.join(self._resolved_dir, 'localhost.key')
                ssl = {
                    'pem': pem_path,
                    'crt': crt_path,
                    'key': key_path,
                }
                # Drop files based on OS guesswork
                ssl_pem_directive_needed = {
                    Cfg.CANDIDATE_PATHS['apache']: False,
                    Cfg.CANDIDATE_PATHS['apache2']: True,
                    Cfg.CANDIDATE_PATHS['tls']: False
                }[self._resolved_dir]
                if not ssl_pem_directive_needed:
                    del ssl['pem']
                else:
                    del ssl['crt']
            elif self._user_supplied_custom_files:
                ssl = {key: val for key, val in (
                    ('pem', app_cfg.get('APACHE_CERTIFICATE_PEM_FILE')),
                    ('crt', app_cfg.get('APACHE_CERTIFICATE_CRT_FILE')),
                    ('key', app_cfg.get('APACHE_CERTIFICATE_KEY_FILE')),
                ) if val}
            else:
                raise AssertionError("Please provide at least one certificate file "
                                    "or enable APACHE_GUESS_CERT_PATHS.")
            return ssl

        @cached_property
        def xsfpdirs(self):
            """Get list of XPF directories.

            :returns: {
                'web': str
                'bibdocfile': str
                'websubmit_storage': str
                'tmp': str
                }
            :rtype: dict
            """
            xsfpdirs = {
                'web': 'CFG_WEBDIR',
                'bibdocfile': 'CFG_BIBDOCFILE_FILEDIR',
                'websumit_storage': 'CFG_WEBSUMIT_STORAGEDIR',
                'deposit_storage': 'CFG_DEPOSIT_STORAGEDIR',
                'tmp': 'CFG_TMPDIR',
            }
            for key, val in xsfpdirs.items():
                try:
                    xsfpdirs[key] = app_cfg[val]
                except KeyError:
                    print(">>> Variable {} not set. Skipping.."
                          .format(val), file=sys.stderr)
                    del xsfpdirs[key]

            xsfpdirs.update({
                'attachfile': path.join(app_cfg['CFG_TMPDIR'], 'attachfile'),
                'comments': path.join(app_cfg['CFG_DATADIR'], 'comments'),
                'baskets': path.join(app_cfg['CFG_DATADIR'], 'baskets'),
                'tmp': app_cfg['CFG_TMPDIR']
            })
            return xsfpdirs

        @cached_property
        def wsgi(self):
            """Get WSGI-related settings.

            :returns: {
                'dir': str
                'process_group': str
                'process_name': str
                'script_alias': str
                'script_fullpath': str
                'socket_directive_needed': str
                'socket_prefix': str
                'user': str
                }
            :rtype: dict
            """
            wsgi = {}

            try:
                wsgi['user'] = app_cfg['APACHE_RUNNING_AS_USER']
            except KeyError:
                current_user = pwd.getpwuid(os.getuid())[0]
                print(">>> Variable {} not set. Using {} (current user)"
                      .format('APACHE_RUNNING_AS_USER', current_user),
                      file=sys.stderr)
                wsgi['user'] = current_user

            try:
                wsgi['dir'] = app_cfg['CFG_WSGIDIR']
            except KeyError:
                wsgi_dir = path.abspath(
                    pkg_resources.resource_filename('invenio', '')
                )
                print(">>> Variable {} not set. Using {}"
                      .format('CFG_WSGIDIR', wsgi_dir),
                      file=sys.stderr)
                wsgi['dir'] = wsgi_dir

            wsgi['script_alias'] = '/wsgi'
            # TODO: Test if this is useful anymore
            wsgi['socket_directive_needed'] = {
                Cfg.CANDIDATE_PATHS['apache']: False,
                Cfg.CANDIDATE_PATHS['apache2']: False,
                Cfg.CANDIDATE_PATHS['tls']: True
                }[self._resolved_dir]
            wsgi['process_name'] = app_cfg['APACHE_WSGI_PROCESS_NAME']
            wsgi['process_group'] = app_cfg['APACHE_WSGI_PROCESS_GROUP']
            wsgi['socket_prefix'] = path.join(app_cfg['CFG_RUNDIR'], 'run')
            wsgi['script_fullpath'] = path.join(wsgi['dir'], 'invenio.wsgi')
            return wsgi

    if force:
        warnings.warn('Option --force has no effect and will be removed.',
                      RemovedInInvenio22Warning)
    if no_ssl:
        warnings.warn('Option --no-ssl will be removed.',
                      RemovedInInvenio22Warning)

    apache_cfg = Cfg()

    # Resolve requested schemes
    vhosts = apache_cfg.vhosts
    if vhosts['http'].port == vhosts['https'].port and \
            vhosts['http'].scheme == vhosts['https'].scheme:
        schemes = {vhosts['http'].scheme}
    elif vhosts['http'].port != vhosts['https'].port and \
        vhosts['http'].scheme != vhosts['https'].scheme:
        schemes = {vhosts['http'].scheme, vhosts['https'].scheme}
    else:
        raise AssertionError("Different protocols with different ports (or "
                             "different ports with the same protocol) are not "
                             "allowed.")
    if no_ssl:
        schemes = schemes ^ {'https'}

    if not schemes:
        raise AssertionError("No vhost set (both http and https disabled)!")

    conf_file = 'apache-vhost.conf'
    # Create conf dir
    apache_conf_dir = path.join(current_app.instance_path, 'apache')
    dir_util.mkpath(apache_conf_dir)
    # Backup old file
    apache_vhost_file = path.join(apache_conf_dir, conf_file)
    if path.exists(apache_vhost_file):
        shutil.copy(apache_vhost_file,
                    apache_vhost_file + '.bak')
    # Write new file
    with open(apache_vhost_file, 'w') as f:
        out = render_template_to_string("{}.tpl".format(conf_file),
                                        cfg=apache_cfg, schemes=schemes)
        print(out, file=f)

    print("""\
Apache virtual host configuration file for your site was created.
You may enable them by adding the following to your httpd.conf:

Include {}

Please see the INSTALL file for more details.
                             """.format(apache_vhost_file))


def main():
    """Generate apache configuration."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()


if __name__ == '__main__':
    main()
