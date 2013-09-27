{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_header %}
<h4 class="media-heading">
    <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
        {{ record.get('title.title', '') }}
    </a>
    {{ '/' if record.get('title_parallel.title') }}
    <small class="muted">
        {{ record.get('title_parallel.title', '')}}
    </small>
</h4>
{% endblock %}

{% block record_content %}
<div class="media" style="margin-bottom: 10px;">
    <span class="pull-left">
        {% for resource in record['url'] if resource.get('nonpublic_note') == 'icon' %}
        <a class="thumbnail" href="{{ url_for('record.metadata', recid=record['recid']) }}">
            <img src="{{ resource.get("url", "").replace(" ","") }}"
                 alt="" border="0" style="max-width: 80px;"/>
        </a>
        {% endfor %}
    </span>
    <span class="pull-right">

    </span>

    <div class="media-body">
        <p class="record-abstract">
          {{ record.get('abstract.summary', '')|sentences(1) }}
        </p>
        <p class="record-info">
          {{ record_info() }}
        </p>
    </div>
</div>
{% endblock %}

{% block record_footer %}
    {{ render_record_footer(1) }}
{% endblock %}


