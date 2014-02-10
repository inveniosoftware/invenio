{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_content %}
  <small>{{ record.get('abstract.summary', '')|sentences(3) }}</small>
{% endblock %}
