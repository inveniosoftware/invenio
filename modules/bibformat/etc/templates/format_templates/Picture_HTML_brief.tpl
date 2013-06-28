{% extends 'format_templates/Default_HTML_brief.tpl' %}

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
        {{ bfe_photo_resources_brief(bfo, ) }}
    </span>
    <span class="pull-right">

    </span>

    <div class="media-body">
        <p>
            {{ bfe_abstract(bfo, limit="1", prefix='<p>', prefix_en="<i>Abstract</i>: ", prefix_fr="<br/><i>Résumé</i>: ", suffix="</p>", highlight="no", print_lang='en') }}

            {{ bfe_field(bfo, tag="909CPt", prefix="<br/><I>Available picture(s)</i>: ") }}
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


