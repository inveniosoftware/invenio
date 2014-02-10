{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_content %}
<div>
    <p class="record-abstract">
        <small>{{ record.get('abstract.summary', '')|sentences(3) }}</small>
    </p>
    <p class="record-info">
        {{ record_info() }}
    </p>
</div>
{% endblock %}

