{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_content %}
<div>
    <p>
        {{ record.get('abstract.summary', '')|truncate(150) }}
    </p>
    <p class="record-info">
        {{ record_info() }}
    </p>
</div>
{% endblock %}
