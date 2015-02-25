{#-
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
-#}
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
  <channel>
{#- FIXME add i18n support -#}
    <title>{{ config.CFG_SITE_NAME if not config.CFG_CERN_SITE else 'CERN' }}
      {%- if collection and collection.name != config.CFG_SITE_NAME -%}
      : {{ collection.name }}
      {%- endif -%}
    </title>
    <link>{{ config.CFG_SITE_URL }}</link>
    <description>{{ config.CFG_SITE_NAME if not config.CFG_CERN_SITE else 'CERN' }} latest documents
      {%- if collection and collection.name != config.CFG_SITE_NAME -%}
      {{ ' ' }}in {{ collection.name }}
      {%- endif -%}
    </description>
    <language>{{ config.CFG_SITE_LANG }}</language>
    <pubDate>{{ time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()) }}</pubDate>
    <category></category>
    <generator>Invenio {{ config.CFG_VERSION }}</generator>
    <webMaster>{{ config.CFG_SITE_SUPPORT_EMAIL }}</webMaster>
    <ttl>{{ config.CFG_WEBSEARCH_RSS_TTL }}</ttl>
    <atom:link rel="previous" href="%s" />'
    <atom:link rel="next" href="%s" />'
    <atom:link rel="self" href="%s" />'
    <image>
        <url>{{ config.CFG_SITE_URL }}/img/site_logo_rss.png</url>
        <title>{{ config.CFG_SITE_NAME }}</title>
        <link>{{ config.CFG_SITE_URL }}</link>
    </image>
    <itunes:owner>
    <itunes:email>{{ config.CFG_SITE_ADMIN_EMAIL }}</itunes:email>
    </itunes:owner>
    {% for recid in recids %}
    {{ format_record(recid, of)|indent() }}
    {% endfor %}
  </channel>
</rss>
