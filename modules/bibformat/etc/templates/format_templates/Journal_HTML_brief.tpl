{% extends 'format_templates/Default_HTML_brief.tpl' %}

{% block record_content %}
<div>
    <p>
            {{ bfe_abstract(bfo, limit="3", escape="4", prefix="<small>", suffix="</small>", highlight="no", contextual="no") }}
    </p>
    <p>
        {{ bfe_fulltext(bfo, prefix='<br /><small>', style="note",
                        show_icons="yes", suffix="</small>",
                        focus_on_main_file="yes") }}
    </p>
</div>
{% endblock %}

