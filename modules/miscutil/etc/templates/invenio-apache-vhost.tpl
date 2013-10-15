{#
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
{% if os.environ.get('VIRTUAL_ENV', False) %}WSGIPythonHome {{ os.environ['VIRTUAL_ENV'] }}{% endif %}

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
        ServerAlias {{ serveralias }}
        ServerAdmin {{ config.CFG_SITE_ADMIN_EMAIL }}
    {%- endblock server -%}
    {%- block directory_web %}
        DocumentRoot {{ config.CFG_WEBDIR }}
        <Directory {{ config.CFG_WEBDIR }}>
           Options FollowSymLinks MultiViews
           AllowOverride None
           Order allow,deny
           Allow from all
        </Directory>
    {%- endblock directory_web -%}
    {%- block logging %}
        ErrorLog {{ config.CFG_LOGDIR }}/apache{{ log_suffix }}.err
        LogLevel warn
        LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\" %D" combined_with_timing
        CustomLog {{ config.CFG_LOGDIR }}/apache{{ log_suffix }}.log combined_with_timing
    {%- endblock logging -%}
    {%- block aliases %}
        DirectoryIndex index.en.html index.html
        Alias /static/ {{ config.CFG_WEBDIR }}/static/
        Alias /img/ {{ config.CFG_WEBDIR }}/img/
        Alias /css/ {{ config.CFG_WEBDIR }}/css/
        Alias /js/ {{ config.CFG_WEBDIR }}/js/
        Alias /flash/ {{ config.CFG_WEBDIR }}/flash/
        Alias /export/ {{ config.CFG_WEBDIR }}/export/
        Alias /MathJax/ {{ config.CFG_WEBDIR }}/MathJax/
        Alias /jsCalendar/ {{ config.CFG_WEBDIR }}/jsCalendar/
        Alias /ckeditor/ {{ config.CFG_WEBDIR }}/ckeditor/
        Alias /mediaelement/ {{ config.CFG_WEBDIR }}/mediaelement/
        AliasMatch /sitemap-(.*) {{ config.CFG_WEBDIR }}/sitemap-$1
        Alias /robots.txt {{ config.CFG_WEBDIR }}/robots.txt
        Alias /favicon.ico {{ config.CFG_WEBDIR }}/favicon.ico
        Alias /apple-touch-icon-144-precomposed.png {{ config.CFG_WEBDIR }}/apple-touch-icon-144-precomposed.png
        Alias /apple-touch-icon-114-precomposed.png {{ config.CFG_WEBDIR }}/apple-touch-icon-114-precomposed.png
        Alias /apple-touch-icon-72-precomposed.png {{ config.CFG_WEBDIR }}/apple-touch-icon-72-precomposed.png
        Alias /apple-touch-icon-57-precomposed.png {{ config.CFG_WEBDIR }}/apple-touch-icon-57-precomposed.png
    {%- endblock aliases -%}
    {%- block wsgi %}
        WSGIScriptAlias / {{ config.CFG_WSGIDIR }}/invenio.wsgi
        WSGIPassAuthorization On
    {% endblock wsgi -%}
    {%- block xsendfile_directive %}
        {{ '#' if not config.CFG_BIBDOCFILE_USE_XSENDFILE }}XSendFile On
    {%- for xsfp in [config.CFG_BIBDOCFILE_FILEDIR,
                    config.CFG_WEBDIR,
                    config.CFG_WEBSUBMIT_STORAGEDIR,
                    config.CFG_WEBDEPOSIT_STORAGEDIR,
                    config.CFG_TMPDIR,
                    [config.CFG_PREFIX, 'var', 'tmp', 'attachfile']|path_join,
                    [config.CFG_PREFIX, 'var', 'data', 'comments']|path_join,
                    [config.CFG_PREFIX, 'var', 'data', 'baskets', 'comments']|path_join,
                    '/tmp'] %}
        {{ '#' if not config.CFG_BIBDOCFILE_USE_XSENDFILE }}XSendFilePath {{ xsfp }}
    {%- endfor -%}
    {%- endblock xsendfile_directive -%}
    {%- block directory_wsgi %}
        <Directory {{ config.CFG_WSGIDIR }}>
           WSGIProcessGroup invenio
           WSGIApplicationGroup %{GLOBAL}
           Options FollowSymLinks MultiViews
           AllowOverride None
           Order allow,deny
           Allow from all
        </Directory>
    {%- endblock directory_wsgi -%}
    {%- block deflate_directive -%}
    {%- if config.CFG_WEBSTYLE_HTTP_USE_COMPRESSION %}
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
    {%- block auth_shibboleth -%}
        {%- if config.CFG_EXTERNAL_AUTH_USING_SSO %}
        <Location ~ "/youraccount/login|Shibboleth.sso/">
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
