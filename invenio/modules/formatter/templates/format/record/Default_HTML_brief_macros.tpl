{#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

{% macro render_record_footer(number_of_displayed_authors) %}
    <p>
      {% if record.get('number_of_authors', 0) > 0 %}
      <i class="glyphicon glyphicon-user"></i> by
        {% set authors = record.get('authors[:].full_name', []) %}
        {% set sep = joiner("; ") %}
        {% for full_name in authors[0:number_of_displayed_authors] %} {{ sep() }}
          <a href="{{ url_for('search.search', p='author:"' + full_name + '"') }}">
            {{ full_name }}
          </a>
        {% endfor %}
        {% if record.get('number_of_authors', 0) > number_of_displayed_authors %}
        {{ sep() }}
        <a href="#authors_{{ record['recid'] }}"
           class="text-muted" data-toggle="modal"
           data-target="#authors_{{ record['recid'] }}">
            <em>{{ _(' et al') }}</em>
        </a>
        {% endif %}

      |
      {% endif %}
      <i class="glyphicon glyphicon-calendar"></i> {{ record['creation_date']|invenio_format_date() }}
      {# Citations link #}
      {%- if config.CFG_BIBRANK_SHOW_CITATION_LINKS -%}
        {%- set num_citations = record['cited_by_count'] -%}
        {%- if num_citations -%}
         |
        <a href="{{ url_for('.search', p="refersto:recid:%d" % recid) }}">
           <i class="glyphicon glyphicon-share"></i>
          {{ "%i" % num_citations + _(" citations") if num_citations > 1 else _("1 citation") }}
        </a>
        {%- endif -%}
      {%- endif -%}

      {# Comments link #}
      {%- if config.CFG_WEBCOMMENT_ALLOW_COMMENTS and config.CFG_WEBSEARCH_SHOW_COMMENT_COUNT -%}
        {%- set num_comments = record['number_of_comments'] -%}
        {%- if num_comments -%}
         |
        <a href="{{ url_for('comments.comments', recid=recid) }}">
          <i class="glyphicon glyphicon-comment"></i>
          {{ _("%(x_num_of_comments)i comments", x_num_of_comments=num_comments if num_comments > 1 else _("1 comment")) }}
        </a>
        {%- endif -%}
      {%- endif -%}

      {# Reviews link #}
      {%- if config.CFG_WEBCOMMENT_ALLOW_REVIEWS and config.CFG_WEBSEARCH_SHOW_REVIEW_COUNT -%}
        {%- set num_reviews = record['number_of_reviews'] -%}
        {%- if num_reviews -%}
         |
        <a href="{{ url_for('comments.reviews', recid=recid) }}">
          <i class="glyphicon glyphicon-eye-open"></i>
          {{ _("%(x_num_of_reviews)i reviews", x_num_of_reviews=num_reviews if num_reviews > 1 else _("1 review")) }}
        </a>
        {%- endif -%}
      {%- endif -%}

      | <a href="{{ url_for('search.search', p='recid:%s' % recid, rm='wrd') }}">{{ _("Similar records") }}</a>

      {% if record['keywords']|length %} | <i class="glyphicon glyphicon-tag"></i>
      {% for keyword in record['keywords'] %}
      <span class="label label-default">
        <a href="{{ url_for('search.search', p='keyword:' + keyword['term']) }}">
          {{ keyword['term'] }}
        </a>
      </span>
      &nbsp
      {% endfor %}
      {% endif %}

      {# WebTags #}
      {{ tfn_webtag_record_tags(record['recid'], current_user.get_id())|prefix('|') }}
    </p>
    {% if record.get('number_of_authors', 0) > number_of_displayed_authors %}
    {% set sep = joiner("; ") %}
    <div id="authors_{{ record['recid'] }}" class="modal hide fade">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h3>{{ _('Authors') }}</h3>
      </div>
      <div class="modal-body">
        {% for full_name in authors %} {{ sep() }}
          <a href="{{ url_for('search.search', p='author:"' + full_name + '"') }}">
            {{ full_name }}
          </a>
        {% endfor %}
      </div>
    </div>
    {% endif %}
{% endmacro %}

{% macro render_fulltext_snippets() %}
  {{ tfn_get_fulltext_snippets(record['recid'], request.args['p'], qid, current_user) | wrap(prefix='<p><small>', suffix='</small></p>') }}
{% endmacro %}

{% macro record_info() %}
  {{ record.get('primary_report_number')|prefix('<i class="glyphicon glyphicon-qrcode"></i> ') }}
  {{ bfe_additional_report_numbers(bfo, prefix='<i class="glyphicon glyphicon-qrcode"></i> ',
                                   separator=' <i class="glyphicon glyphicon-qrcode"></i> ') }}

  {{ bfe_publi_info(bfo, prefix='| <i class="glyphicon glyphicon-book"></i> ') }}
  {{ bfe_doi(bfo, prefix='| <i class="glyphicon glyphicon-barcode"></i> ') }}
  {# '<a href="http://dx.doi.org/%(doi)s" title="DOI" target="_blank"><i class="glyphicon glyphicon-barcode"></i> %(doi)s</a>'|format(doi=record['doi']) if record.get('doi') #}

{% endmacro %}
