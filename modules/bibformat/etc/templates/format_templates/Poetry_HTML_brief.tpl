{% extends 'format_templates/Default_HTML_brief.tpl' %}

{% block record_content %}
<div>
    <p>
        {{ record.get('abstract.summary', '')|truncate(150) }}
    </p>
    <p>
        {{ bfe_fulltext(bfo, prefix='<br /><small>', style="note",
                        show_icons="yes", suffix="</small>",
                        focus_on_main_file="yes") }}
    </p>
    <p class="record-info">
        {{ record_info() }}
    </p>
</div>
{% endblock %}
