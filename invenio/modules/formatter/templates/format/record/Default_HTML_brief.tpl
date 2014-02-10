{% extends "format/record/Default_HTML_brief_base.tpl" %}

{% from "format/record/Default_HTML_brief_macros.tpl" import render_record_footer, render_fulltext_snippets, record_info with context %}

{% block above_record_header %}
  {{ bfe_fulltext(bfo, show_icons="yes", prefix='<ul class="nav nav-pills pull-right" style="margin-top: -10px;"><li class="dropdown"><a class="dropdown-toggle" data-toggle="dropdown" rel="tooltip" title="Download" href="#"><i class="glyphicon glyphicon-download-alt"></i><span class="caret"></span></a>', suffix='</li></ul>', focus_on_main_file="yes") }}
{% endblock %}

{% block record_header %}
  <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
    {{ record.get('title.title', '') }}
    {{- record.get('title.volume', '')|prefix(', ') }}
    {{- record.get('title.subtitle', '')|prefix(': ') }}
    {{- record.get('edition_statement', '')|prefix('; ') }}
  </a>
{% endblock %}

{% block record_content %}
  {{ record.get('abstract.summary', '')|sentences(3) }}
{% endblock %}

{% block record_info %}
  {{ record_info() }}
{% endblock %}

{% block fulltext_snippets %}
  {{ render_fulltext_snippets() }}
{% endblock %}

{% block record_footer %}
  {{ render_record_footer(4) }}
{% endblock %}