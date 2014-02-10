{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_header %}
    <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
        {{ record.get('title.title', '') }}
    </a>
{% endblock %}

{% block record_media %}
    {% for resource in record['url'] if resource.get('public_note') == 'POSTER' %}
    <a class="thumbnail mejs-overlay" href="{{ url_for('record.metadata', recid=record['recid']) }}">
        <img src="{{ resource.get("url", "").replace(" ","") }}"
             alt="{{ resource.get("caption", "") }}" border="0"/>
        <div class="mejs-overlay-button"></div>
    </a>
    {% endfor %}
{% endblock %}

{% block record_content %}
      {{ record.get('abstract.summary', '')|sentences(3) }}
{% endblock %}
