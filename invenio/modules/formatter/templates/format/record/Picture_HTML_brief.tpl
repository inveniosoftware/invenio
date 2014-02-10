{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_header %}
    <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
        {{ record.get('title.title', '') }}
    </a>
    {{ '/' if record.get('title_parallel.title') }}
    <small class="text-muted">
        {{ record.get('title_parallel.title', '')}}
    </small>
{% endblock %}

{% block record_media %}
    {% for resource in record['url'] if resource.get('nonpublic_note') == 'icon' %}
        <a class="thumbnail" href="{{ url_for('record.metadata', recid=record['recid']) }}">
            <img src="{{ resource.get("url", "").replace(" ","") }}"
                 alt="" border="0" style="max-width: 80px;"/>
        </a>
    {% endfor %}
{% endblock %}

{% block record_footer %}
    {{ render_record_footer(1) }}
{% endblock %}


