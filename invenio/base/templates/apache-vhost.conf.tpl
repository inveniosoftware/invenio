{#-
## This file is part of Invenio.
## Copyright (C) 2013, 2015 CERN.
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
#}
{#-
Apache configuration template
=============================

variables:
----------
- cfg: configuration data
- schemes: list of schemes (http, https)

-#}
AddDefaultCharset UTF-8
ServerTokens Prod
<Files *.pyc>
    deny from all
</Files>
<Files *~>
    deny from all
</Files>

# WSGI
WSGIRestrictStdout Off
WSGIPythonHome {{ cfg.sys_prefix }}
{{ '#' if not cfg.wsgi.socket_directive_needed }}WSGISocketPrefix {{ cfg.wsgi.socket_prefix }}
WSGIDaemonProcess {{ cfg.wsgi.process_name }} processes={{ cfg.wsgi_processes }} threads=1 user={{ cfg.wsgi.user }} display-name=%{GROUP} inactivity-timeout=3600 maximum-requests=10000
WSGIImportScript {{ cfg.wsgi.script_fullpath }} process-group={{ cfg.wsgi.process_group }} application-group=%{GLOBAL}

{% if 'https' in schemes %}
# SSL
SSLEngine On
<IfVersion >= 2.3.3>
     SSLStaplingCache shmcb:/var/run/ocsp(128000)
</IfVersion>
{% endif %}

{%- for scheme in schemes %}

{{ '#' if not cfg.listen_directive_needed(scheme) }}Listen {{ cfg.vhosts[scheme].port }}
<IfVersion < 2.3.11>
{{ '#' if not cfg.listen_directive_needed(scheme) }}NameVirtualHost {{ cfg.vhost_ip_address }}
</IfVersion>

<VirtualHost {{ cfg.vhost_ip_address }}:{{ cfg.vhosts[scheme].port }}>
    ServerName {{ cfg.vhosts[scheme].hostname }}
    {{ '#' if not cfg.vhosts[scheme].server_alias }} ServerAlias {{ cfg.vhosts[scheme].server_alias }}
    ServerAdmin {{ cfg.admin_email }}

    {%- if scheme == 'https' %}
    # SSL
    {% if cfg.ssl.pem %}SSLCertificateFile {{ cfg.ssl.pem }}{% endif %}
    {% if cfg.ssl.crt %}SSLCertificateFile {{ cfg.ssl.crt }}
    {% elif cfg.ssl.key %}SSLCertificateKeyFile {{ cfg.ssl.key }}{% endif %}
    SSLProtocol             all -SSLv2 -SSLv3
    SSLCipherSuite          HIGH:MEDIUM:!ADH:!RC4
    SSLHonorCipherOrder     On
    SSLCompression          off  # Defend against CRIME attacks
    <IfVersion >= 2.3.3>
        SSLUseStapling                     On
        SSLStaplingResponderTimeout        5
        SSLStaplingReturnResponderErrors   off
    </IfVersion>
    # HSTS (mod_headers is required) (15768000 seconds = 6 months)
    Header always add Strict-Transport-Security "max-age=15768000"
    {% endif %}

    DocumentRoot {{ cfg.collect_static_root }}
    <Directory {{ cfg.collect_static_root }}>
        DirectorySlash Off
        Options FollowSymLinks MultiViews
        AllowOverride None
        <IfVersion >= 2.4>
            Require all granted
        </IfVersion>
        <IfVersion < 2.4>
            Order allow,deny
            Allow from all
        </IfVersion>
    </Directory>

    ErrorLog {{ cfg.log.err[scheme] }}
    LogLevel warn
    LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\" %D" combined_with_timing
    CustomLog {{ cfg.log.out[scheme] }} combined_with_timing

    AliasMatch /sitemap-(.*) {{ cfg.xsfpdirs.web }}/sitemap-$1

    # Name of the WSGI entry point.
    SetEnv WSGI_SCRIPT_ALIAS {{ cfg.wsgi.script_alias }}
    WSGIScriptAlias {{ cfg.wsgi.script_alias }} {{ cfg.wsgi.script_fullpath }}
    WSGIPassAuthorization On

    RewriteEngine On
    RewriteCond {{ cfg.collect_static_root }}%{REQUEST_FILENAME} !-f
    RewriteCond {{ cfg.collect_static_root }}%{REQUEST_FILENAME} !-d
    {# Temporary manual handling of /admin, to work around the presence of
    a folder admin/ in root #}
    RewriteRule ^admin$ {{ cfg.wsgi.script_alias}}/admin/ [PT,L]
    RewriteRule ^(.*)$ {{ cfg.wsgi.script_alias }}$1 [PT,L]

    {%- if scheme == 'https' %} RedirectMatch /sslredirect/(.*) http://$1 {% endif %}

    {{'#' if not cfg.bibdocfile_use_xsendfile }}XSendFile On

    {% for xsfpdir in cfg.dir %}
    {% if xsfpdir %}{{ '#' if not cfg.bibdocfile_use_xsendfile }}XSendFilePath {{ xsfpdir }}{% endif %}
    {% endfor -%}

    <Directory {{ cfg.wsgi.dir }}>
        WSGIProcessGroup {{ cfg.wsgi.process_group }}
        WSGIApplicationGroup %{GLOBAL}
        Options FollowSymLinks MultiViews
        AllowOverride None
        <IfVersion >= 2.4>
            Require all granted
        </IfVersion>
        <IfVersion < 2.4>
            Order allow,deny
            Allow from all
        </IfVersion>
    </Directory>

    {%- if cfg.webstyle_http_use_compression %}
        ## Configuration snippet taken from:
        ## <http://httpd.apache.org/docs/2.2/mod/mod_deflate.html>
        <IfModule mod_deflate.c>
            <IfModule mod_filter.c>
                SetOutputFilter DEFLATE
                SetEnvIfNoCase Request_URI \.(?:gif|jpe?g|png)$ no-gzip
            </IfModule>
        </IfModule>
    {% endif %}

    # Don't do etags for files since in a load balanced environment, two
    # servers will compute different etags for the same component.
    FileETag None

    {%- if scheme == 'https' %}
        {% if cfg.sso.enabled %}
        <Location ~ "{{ cfg.sso_login_url }}|Shibboleth.sso/">
            SSLRequireSSL
            AuthType              shibboleth
            ShibRequireSession    On
            ShibRequireAll        On
            ShibExportAssertion   Off
            Require               valid-user
        </Location>
        {%- endif -%}
    {%- endif %}
</VirtualHost>
{%- endfor -%}
