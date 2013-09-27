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

from invenio.ext.script import Manager, change_command_name

manager = Manager(usage="Perform Apache operations.")


@manager.command
def version(separator='\n'):
    """
    Try to detect Apache version by localizing httpd or apache
    executables and grepping inside binaries.  Return list of all
    found Apache versions and paths.  (For a given executable, the
    returned format is 'apache_version [apache_path]'.)  Return empty
    list if no success.
    """
    from invenio.legacy.inveniocfg import _grep_version_from_executable
    from invenio.shellutils import run_shell_command
    out = []
    dummy1, cmd_out, dummy2 = run_shell_command("locate bin/httpd bin/apache")
    for apache in cmd_out.split("\n"):
        apache_version = _grep_version_from_executable(apache, '^Apache\/')
        if apache_version:
            out.append("%s [%s]" % (apache_version, apache))
    return separator.join(out)


@manager.option('-f', '--force', dest='force')
@manager.option('--no-ssl', dest='no_ssl')
@change_command_name
def create_config(force=False, no_ssl=True):
    """
    Create Apache configuration files for this site, keeping previous
    files in a backup copy.
    """
    import os
    import pwd
    import sys
    import shutil
    from flask import current_app
    from jinja2 import TemplateNotFound
    from invenio.ext.template import render_template_to_string
    from invenio.utils.text import wrap_text_in_a_box
    from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO

    CFG_PREFIX = current_app.config.get('CFG_PREFIX', '')

    def get_context():
        from invenio.legacy.inveniocfg import _detect_ip_address

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

        apc1 = {'vhost_site_url_port': vhost_site_url_port,
                'servername': vhost_site_url,
                'serveralias': vhost_site_url.split('.')[0],
                'vhost_ip_address': vhost_ip_address_needed and
                _detect_ip_address() or '*',
                'wsgi_socket_directive_needed': wsgi_socket_directive_needed,
                'listen_directive_needed': listen_directive_needed,
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
                }

        return [apc1, apc2]

    current_app.config.update(
        CFG_RUNNING_AS_USER=pwd.getpwuid(os.getuid())[0],
        CFG_EXTERNAL_AUTH_USING_SSO=CFG_EXTERNAL_AUTH_USING_SSO,
        CFG_WSGIDIR=os.path.join(CFG_PREFIX, 'var', 'www-wsgi'))

    apache_conf_dir = current_app.config.get('CFG_ETCDIR') + os.sep + 'apache'

    print ">>> Going to create Apache conf files..."
    conf_files = ['invenio-apache-vhost.conf', 'invenio-apache-vhost-ssl.conf']
    conf_files = conf_files[:1 if no_ssl else 2]

    if not os.path.exists(apache_conf_dir):
        os.mkdir(apache_conf_dir)

    for local_file, context in zip(conf_files,
                                   get_context()[:1 if no_ssl else 2]):
        print ">>> Writing %s ..." % local_file

        try:
            apache_vhost_file = apache_conf_dir + os.sep + local_file
            if os.path.exists(apache_vhost_file):
                shutil.copy(apache_vhost_file,
                            apache_vhost_file + '.OLD')

            with open(apache_vhost_file, 'w') as f:
                out = render_template_to_string(local_file + '.tpl', os=os,
                                                **context)
                print >> f, out

        except TemplateNotFound:
            print >> sys.stderr, "Could not find template %s" % local_file

    print wrap_text_in_a_box("""\
Apache virtual host configuration file(s) for your Invenio site
was(were) created.  Please check created file(s) and activate virtual
host(s).  For example, you can put the following include statements in
your httpd.conf:\n

%s

%s


Please see the INSTALL file for more details.
    """ % tuple(map(lambda x: "Include " + apache_conf_dir.encode('utf-8') + os.sep + x,
                    list(conf_files))))
    print ">>> Apache conf files created."


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
