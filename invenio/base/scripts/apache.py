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

from __future__ import print_function

import os
import socket

from invenio.ext.script import Manager, change_command_name

manager = Manager(usage="Perform Apache operations.")


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
    """
    Try to detect Apache version by localizing httpd or apache
    executables and grepping inside binaries.  Return list of all
    found Apache versions and paths.  (For a given executable, the
    returned format is 'apache_version [apache_path]'.)  Return empty
    list if no success.
    """
    from invenio.utils.shell import run_shell_command
    out = []
    dummy1, cmd_out, dummy2 = run_shell_command("locate bin/httpd bin/apache")
    for apache in cmd_out.split("\n"):
        apache_version = _grep_version_from_executable(apache, '^Apache\/')
        if apache_version:
            out.append(formatting.format(version=apache_version,
                                         executable=apache))
    if separator is None:
        return out
    return separator.join(out)


@manager.option('-f', '--force', dest='force', action='store_true')
@manager.option('--no-ssl', dest='no_ssl', action='store_true')
@change_command_name
def create_config(force=False, no_ssl=False):
    """
    Create Apache configuration files for this site, keeping previous
    files in a backup copy.
    """
    import os
    import pwd
    import pkg_resources
    import sys
    import shutil
    from flask import current_app
    from jinja2 import TemplateNotFound
    from invenio.ext.template import render_template_to_string
    from invenio.utils.text import wrap_text_in_a_box

    CFG_PREFIX = current_app.config.get('CFG_PREFIX', '')

    def get_context():
        conf = current_app.config

        ## Apache vhost conf file is distro specific, so analyze needs:
        # Gentoo (and generic defaults):
        listen_directive_needed = True
        ssl_pem_directive_needed = False
        ssl_pem_path = CFG_PREFIX + '/etc/apache/ssl/apache.pem'
        ssl_crt_path = CFG_PREFIX + '/etc/apache/ssl/server.crt'
        ssl_key_path = CFG_PREFIX + '/etc/apache/ssl/server.key'
        vhost_ip_address_needed = False
        wsgi_socket_directive_needed = False
        # Debian:
        if os.path.exists(os.path.sep + 'etc' + os.path.sep + 'debian_version'):
            listen_directive_needed = False
            ssl_pem_directive_needed = True
            ssl_pem_path = '/etc/apache2/ssl/apache.pem'
            ssl_crt_path = '/etc/apache2/ssl/server.crt'
            ssl_key_path = '/etc/apache2/ssl/server.key'
        # RHEL/SLC:
        if os.path.exists(os.path.sep + 'etc' + os.path.sep + 'redhat-release'):
            listen_directive_needed = False
            ssl_crt_path = '/etc/pki/tls/certs/localhost.crt'
            ssl_key_path = '/etc/pki/tls/private/localhost.key'
            vhost_ip_address_needed = True
            wsgi_socket_directive_needed = True
        # maybe we are using non-standard ports?
        vhost_site_url = conf.get('CFG_SITE_URL').replace("http://", "")
        if vhost_site_url.startswith("https://"):
            ## The installation is configured to require HTTPS for any connection
            vhost_site_url = vhost_site_url.replace("https://", "")
        vhost_site_url_port = '80'
        vhost_site_secure_url = conf.get('CFG_SITE_SECURE_URL').replace("https://", "").replace("http://", "")
        vhost_site_secure_url_port = '443'
        if ':' in vhost_site_url:
            vhost_site_url, vhost_site_url_port = vhost_site_url.split(':', 1)
        if ':' in vhost_site_secure_url:
            vhost_site_secure_url, vhost_site_secure_url_port = vhost_site_secure_url.split(':', 1)
        if vhost_site_url_port != '80' or vhost_site_secure_url_port != '443':
            listen_directive_needed = True

        static_root = current_app.config['COLLECT_STATIC_ROOT']
        if not os.path.exists(static_root):
            os.mkdir(static_root)

        def prepare_alias(filename):
            if os.path.isdir(os.path.join(static_root, filename)):
                return '/%s/' % (filename, )
            return '/%s' % (filename, )

        aliases = map(prepare_alias, os.listdir(static_root))

        apc1 = {'vhost_site_url_port': vhost_site_url_port,
                'servername': vhost_site_url,
                'serveralias': vhost_site_url.split('.')[0],
                'vhost_ip_address': vhost_ip_address_needed and
                _detect_ip_address() or '*',
                'wsgi_socket_directive_needed': wsgi_socket_directive_needed,
                'listen_directive_needed': listen_directive_needed,
                'aliases': aliases,
                }

        apc2 = {'vhost_site_url_port': vhost_site_secure_url_port,
                'servername': vhost_site_secure_url,
                'serveralias': vhost_site_secure_url.split('.')[0],
                'vhost_ip_address': vhost_ip_address_needed and
                _detect_ip_address() or '*',
                'wsgi_socket_directive_needed': wsgi_socket_directive_needed,
                'ssl_pem_directive': ssl_pem_directive_needed and
                'SSLCertificateFile %s' % ssl_pem_path or
                '#SSLCertificateFile %s' % ssl_pem_path,
                'ssl_crt_directive': ssl_pem_directive_needed and
                '#SSLCertificateFile %s' % ssl_crt_path or
                'SSLCertificateFile %s' % ssl_crt_path,
                'ssl_key_directive': ssl_pem_directive_needed and
                '#SSLCertificateKeyFile %s' % ssl_key_path or
                'SSLCertificateKeyFile %s' % ssl_key_path,
                'listen_directive_needed': listen_directive_needed,
                'aliases': aliases,
                }

        return [apc1, apc2]

    current_app.config.update(
        SYS_PREFIX=sys.prefix,
        CFG_RUNNING_AS_USER=pwd.getpwuid(os.getuid())[0],
        CFG_WSGIDIR=os.path.abspath(
            pkg_resources.resource_filename('invenio', '')))

    apache_conf_dir = current_app.instance_path + os.sep + 'apache'

    print(">>> Going to create Apache conf files...")
    conf_files = ['invenio-apache-vhost.conf', 'invenio-apache-vhost-ssl.conf']
    conf_files = conf_files[:1 if no_ssl else 2]

    if not os.path.exists(apache_conf_dir):
        os.mkdir(apache_conf_dir)

    for local_file, context in zip(conf_files,
                                   get_context()[:1 if no_ssl else 2]):
        print(">>> Writing %s ..." % local_file)

        try:
            apache_vhost_file = apache_conf_dir + os.sep + local_file
            if os.path.exists(apache_vhost_file):
                shutil.copy(apache_vhost_file,
                            apache_vhost_file + '.OLD')

            with open(apache_vhost_file, 'w') as f:
                out = render_template_to_string(local_file + '.tpl', os=os,
                                                **context)
                print(out, file=f)

        except TemplateNotFound:
            print("Could not find template %s".format(local_file),
                  file=sys.stderr)

    print(wrap_text_in_a_box("""\
Apache virtual host configuration file(s) for your Invenio site
was(were) created.  Please check created file(s) and activate virtual
host(s).  For example, you can put the following include statements in
your httpd.conf:\n

%s

Please see the INSTALL file for more details.
    """ % '\n\n'.join(tuple(map(
        lambda x: "Include " + apache_conf_dir.encode('utf-8') + os.sep + x,
        list(conf_files[:1 if no_ssl else 2]))))))
    print(">>> Apache conf files created.")


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
