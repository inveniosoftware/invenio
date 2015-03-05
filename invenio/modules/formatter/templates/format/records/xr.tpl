{#-
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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
{%- set is_root_collection = collection and collection.name == config.CFG_SITE_NAME -%}
<rss version="2.0"
    xmlns:media="http://search.yahoo.com/mrss/"
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <channel>
{#- FIXME add i18n support -#}
    <title>{{ config.CFG_SITE_NAME|e }}
      {%- if not is_root_collection -%}
      : {{ collection.name|e }}
      {%- endif -%}
    </title>
    <link>{{ config.CFG_SITE_URL if is_root_collection else url_for('collections.collection', name=collection.name, _external=True) }}</link>
    <description>{{ config.CFG_SITE_NAME|e }}{{ _('latest documents') }}
      {%- if not is_root_collection -%}
      {{ ' ' }}in {{ collection.name|e }}
      {%- endif -%}
    </description>
    <language>{{ config.CFG_SITE_LANG }}</language>
    <pubDate>{{ time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()) }}</pubDate>
    <category></category>
    <generator>Invenio {{ config.CFG_VERSION }}</generator>
    <webMaster>{{ config.CFG_SITE_SUPPORT_EMAIL }}</webMaster>
    <ttl>{{ config.CFG_WEBSEARCH_RSS_TTL }}</ttl>
    {% set args = request.args.copy().to_dict() -%}
    <atom:link rel="self" href="{{ request.url|e }}" />
    {% if pagination.has_prev -%}
    {% do args.update({'jrec': jrec - rg }) %}
    <atom:link rel="prev" href="{{ url_for(request.endpoint, _external=True, **args)|e }}"/>
    {%- endif %}
    {% if pagination.has_next -%}
    {% do args.update({'jrec': jrec + rg}) %}
    <atom:link rel="next" href="{{ url_for(request.endpoint, _external=True, **args)|e }}"/>
    {%- endif %}
    <opensearch:startIndex>{{ jrec }}</opensearch:startIndex>
    <opensearch:itemsPerPage>{{ rg }}</opensearch:itemsPerPage>
    <image>
        <url>{{ config.CFG_SITE_URL }}/img/site_logo_rss.png</url>
        <title>{{ config.CFG_SITE_NAME }}</title>
        <link>{{ config.CFG_SITE_URL }}</link>
    </image>
    <atom:link
          rel="search"
          href="{{ config.CFG_SITE_URL }}/opensearchdescription"
          type="application/opensearchdescription+xml"
          title="Content Search" />

    <textInput>
      <title>Search </title>
      <description>Search this site:</description>
      <name>p</name>
      <link>{{ url_for('search.search', _external=True) }}</link>
    </textInput>
    {% for recid in recids[jrec:jrec+rg] %}
    {{ format_record(recid, of) }}
    {% endfor %}
  </channel>
</rss>
