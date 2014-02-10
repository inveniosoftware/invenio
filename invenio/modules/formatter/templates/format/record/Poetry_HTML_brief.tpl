{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_content %}
    {{ record.get('abstract.summary', '')|truncate(150) }}
{% endblock %}
