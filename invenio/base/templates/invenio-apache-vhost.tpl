{#
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
#}
{#
Apache configuration template
=============================

blocks:
-------
- configuration
    - header
    - virtual_host
        - server
        - directory_web
        - logging
        - alliases
        - wsgi
        - xsendfile_directive
        - directory_wsgi
        - deflate_directive
        - auth_shibboleth

variables:
----------
- log_suffix: adds string to apache log names `{% set log_suffix = '' %}`
              (default: '')

#}
{%-
 block configuration -%}
{%- block header -%}
WSGIRestrictStdout Off
{%- set pythonhome = config.get('APACHE_PYTHON_HOME', config.SYS_PREFIX) %}
{%- if pythonhome %}
WSGIPythonHome {{pythonhome}}
{%- endif %}

<Files *.pyc>
   deny from all
</Files>
<Files *~>
   deny from all
</Files>
{%- endblock header -%}
{%- block virtual_host %}
<VirtualHost {{ vhost_ip_address }}:{{ vhost_site_url_port }}>
    {%- block server %}
        ServerName {{ servername }}
        ServerAlias {{ config.get('APACHE_SERVER_ALIASES', serveralias) }}
        ServerAdmin {{ config.CFG_SITE_ADMIN_EMAIL }}
    {%- endblock server -%}
    {%- block directory_web %}
        DocumentRoot {{ config.COLLECT_STATIC_ROOT }}
        <Directory {{ config.COLLECT_STATIC_ROOT }}>
           DirectorySlash Off
           Options +FollowSymLinks +MultiViews -Indexes
           AllowOverride None
           <IfVersion >= 2.4>
           Require all granted
           </IfVersion>
           <IfVersion < 2.4>
           Order allow,deny
           Allow from all
           </IfVersion>
        </Directory>
    {%- endblock directory_web -%}
    {%- block logging %}
        ErrorLog {{ config.CFG_LOGDIR }}/apache{{ log_suffix }}.err
        LogLevel warn
        LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\" %D" combined_with_timing
        CustomLog {{ config.CFG_LOGDIR }}/apache{{ log_suffix }}.log combined_with_timing
    {%- endblock logging -%}
    {%- block aliases %}
        #FIXME DirectoryIndex index.en.html index.html
        AliasMatch /sitemap-(.*) {{ config.CFG_WEBDIR }}/sitemap-$1
    {%- endblock aliases -%}
    {%- block wsgi %}
        # Name of the WSGI entry point.
        # Change it at the *three* locations if you have to.
        {%- set script_alias = "/wsgi" %}
        SetEnv WSGI_SCRIPT_ALIAS {{ script_alias }}
        WSGIScriptAlias {{ script_alias }} {{ config.CFG_WSGIDIR }}/invenio.wsgi
        WSGIPassAuthorization On

        RewriteEngine on
        RewriteCond {{ config.COLLECT_STATIC_ROOT }}%{REQUEST_FILENAME} !-f
        RewriteRule ^(.*)$ {{ script_alias }}$1 [PT,L]
    {% endblock wsgi -%}
    {%- block xsendfile_directive %}
        {{ '#' if not config.CFG_BIBDOCFILE_USE_XSENDFILE }}XSendFile On
    {%- for xsfp in [config.CFG_BIBDOCFILE_FILEDIR,
                    config.CFG_WEBDIR,
                    config.CFG_WEBSUBMIT_STORAGEDIR,
                    config.DEPOSIT_STORAGEDIR,
                    config.CFG_TMPDIR,
                    [config.CFG_PREFIX, 'var', 'tmp', 'attachfile']|path_join,
                    [config.CFG_PREFIX, 'var', 'data', 'comments']|path_join,
                    [config.CFG_PREFIX, 'var', 'data', 'baskets', 'comments']|path_join,
                    '/tmp'] %}
        {% if xsfp %}{{ '#' if not config.CFG_BIBDOCFILE_USE_XSENDFILE }}XSendFilePath {{ xsfp }}{% endif %}
    {%- endfor -%}
    {%- endblock xsendfile_directive -%}
    {%- block directory_wsgi %}
        <Directory {{ config.CFG_WSGIDIR }}>
           WSGIProcessGroup invenio
           WSGIApplicationGroup %{GLOBAL}
           Options +FollowSymLinks +MultiViews
           AllowOverride None
           <IfVersion >= 2.4>
           Require all granted
           </IfVersion>
           <IfVersion < 2.4>
           Order allow,deny
           Allow from all
           </IfVersion>
        </Directory>
    {%- endblock directory_wsgi -%}
    {%- block deflate_directive %}
    {% if config.CFG_WEBSTYLE_HTTP_USE_COMPRESSION %}
        ## Configuration snippet taken from:
        ## <http://httpd.apache.org/docs/2.2/mod/mod_deflate.html>
        <IfModule mod_deflate.c>
            SetOutputFilter DEFLATE

            # Netscape 4.x has some problems...
            BrowserMatch ^Mozilla/4 gzip-only-text/html

            # Netscape 4.06-4.08 have some more problems
            BrowserMatch ^Mozilla/4\.0[678] no-gzip

            # MSIE masquerades as Netscape, but it is fine
            # BrowserMatch \bMSIE !no-gzip !gzip-only-text/html

            # NOTE: Due to a bug in mod_setenvif up to Apache 2.0.48
            # the above regex won't work. You can use the following
            # workaround to get the desired effect:
            BrowserMatch \bMSI[E] !no-gzip !gzip-only-text/html

            # Don't compress images
            SetEnvIfNoCase Request_URI \
                \.(?:gif|jpe?g|png)$ no-gzip dont-vary

            # Make sure proxies don't deliver the wrong content
            <IfModule mod_headers.c>
                Header append Vary User-Agent env=!dont-vary
            </IfModule>
        </IfModule>
        {% endif -%}
    {%- endblock deflate_directive -%}
    {%- block etags -%}
        # Don't do etags for files since in a load balanced environment, two
        # servers will compute different etags for the same component.
        FileETag None
    {%- endblock etags -%}
    {%- block auth_shibboleth -%}
        {%- if config.CFG_EXTERNAL_AUTH_USING_SSO %}
        <Location ~ "{{ config.SSO_LOGIN_URL }}|Shibboleth.sso/">
            SSLRequireSSL   # The modules only work using HTTPS
            AuthType shibboleth
            ShibRequireSession On
            ShibRequireAll On
            ShibExportAssertion Off
            require valid-user
        </Location>
        {% endif -%}
    {%- endblock auth_shibboleth %}
</VirtualHost>
{%- endblock virtual_host -%}
{%- endblock -%}
