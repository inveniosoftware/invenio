{% macro render_record_footer(number_of_displayed_authors) %}
    <p>
      {% if record.get('number_of_authors', 0) > 0 %}
      <i class="icon-user"></i> by
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
           class="muted" data-toggle="modal"
           data-target="#authors_{{ record['recid'] }}">
            <em>{{ _(' et al') }}</em>
        </a>
        {% endif %}

      |
      {% endif %}
      <i class="icon-calendar"></i> {{ record['creation_date']|invenio_format_date() }}
      {# Citations link #}
      {%- if config.CFG_BIBRANK_SHOW_CITATION_LINKS -%}
        {%- set num_citations = record['_cited_by_count'] -%}
        {%- if num_citations -%}
         |
        <a href="{{ url_for('.search', p="refersto:recid:%d" % recid) }}">
           <i class="icon-share"></i>
          {{ _("%i citations") % num_citations if num_citations > 1 else _("1 citation") }}
        </a>
        {%- endif -%}
      {%- endif -%}

      {# Comments link #}
      {%- if config.CFG_WEBCOMMENT_ALLOW_COMMENTS and config.CFG_WEBSEARCH_SHOW_COMMENT_COUNT -%}
        {%- set num_comments = record['_number_of_comments'] -%}
        {%- if num_comments -%}
         |
        <a href="{{ url_for('comments.comments', recid=recid) }}">
          <i class="icon-comment"></i>
          {{ _("%i comments") % num_comments if num_comments > 1 else _("1 comment") }}
        </a>
        {%- endif -%}
      {%- endif -%}

      {# Reviews link #}
      {%- if config.CFG_WEBCOMMENT_ALLOW_REVIEWS and config.CFG_WEBSEARCH_SHOW_REVIEW_COUNT -%}
        {%- set num_reviews = record['_number_of_reviews'] -%}
        {%- if num_reviews -%}
         |
        <a href="{{ url_for('comments.reviews', recid=recid) }}">
          <i class="icon-eye-open"></i>
          {{ _("%i reviews") % num_reviews if num_reviews > 1 else _("1 review") }}
        </a>
        {%- endif -%}
      {%- endif -%}

      | <a href="{{ url_for('search.search', p='recid:%s' % recid, rm='wrd') }}">{{ _("Similar records") }}</a>

      {% if record['keywords']|length %} | <i class="icon-tag"></i>
      {% for keyword in record['keywords'] %}
      <span class="label">
        <a href="{{ url_for('search.search', p='keyword:' + keyword['term']) }}">
          {{ keyword['term'] }}
        </a>
      </span>
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
  {{ bfe_primary_report_number(bfo, prefix='<i class="icon-qrcode"></i> ') }}
  {{ bfe_additional_report_numbers(bfo, prefix='<i class="icon-qrcode"></i> ',
                                   separator=' <i class="icon-qrcode"></i> ') }}

  {{ bfe_publi_info(bfo, prefix='| <i class="icon-book"></i> ') }}
  {{ bfe_doi(bfo, prefix='| <i class="icon-barcode"></i> ') }}
  {# '<a href="http://dx.doi.org/%(doi)s" title="DOI" target="_blank"><i class="icon-barcode"></i> %(doi)s</a>'|format(doi=record['doi']) if record.get('doi') #}

{% endmacro %}

{% block record_brief %}
<div class="htmlbrief">
    {{ bfe_fulltext(bfo, show_icons="yes", prefix='<ul class="nav nav-pills pull-right" style="margin-top: -10px;"><li class="dropdown"><a class="dropdown-toggle" data-toggle="dropdown" rel="tooltip" title="Download" href="#"><i class="icon-download-alt"></i><span class="caret"></span></a>', suffix='</li></ul>', focus_on_main_file="yes") }}
    {% block record_header %}
    <h4 class="media-heading">
        <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
            {{ record.get('title.title', '') }}
            {{- record.get('title.volume', '')|prefix(', ') }}
            {{- record.get('title.subtitle', '')|prefix(': ') }}
            {{- record.get('edition_statement', '')|prefix('; ') }}
        </a>
    </h4>
    {% endblock %}
    {% block record_content %}
    <div>
        <p class="record-abstract">
          {{ record.get('abstract.summary', '')|sentences(3) }}
        </p>

        <p class="record-info">
          {{ record_info() }}
        </p>
    </div>
    {% endblock %}

    <div class="clearfix"></div>
    {% block fulltext_snippets %}
        {{ render_fulltext_snippets() }}
    {% endblock %}

    {% block record_footer %}
        {{ render_record_footer(4) }}
    {% endblock %}
</div>
{% endblock %}
