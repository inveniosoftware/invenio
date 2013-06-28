{% extends 'format_templates/Default_HTML_brief.tpl' %}

{% block record_header %}
<h4 class="media-heading">
    <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
        {{ record.get('title.title', '') }}
    </a>
</h4>
{% endblock %}

{% block record_content %}
<style>
.mejs-overlay-button {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100px;
    height: 100px;
    margin: -50px 0 0 -50px;
    background: url(/mediaelement/bigplay.svg) no-repeat;
}
.no-svg .mejs-overlay-button {
    background-image: url(/mediaelement/bigplay.png);
}
.mejs-overlay {
    position: relative;
}

.mejs-overlay:hover .mejs-overlay-button {
    background-position: 0 -100px ;
}
</style>
<div class="media">
    <span class="pull-left">
        <a class="thumbnail mejs-overlay"
           href="{{ url_for('record.metadata', recid=record['recid']) }}">
            {{ bfe_video_bigthumb(bfo, ) }}
            <div class="mejs-overlay-button"></div>
        </a>
    </span>
    <span class="pull-right">

    </span>

    <div class="media-body">
        <p>
            {{ bfe_abstract(bfo, limit="1", prefix='<p>', prefix_en="<i>Abstract</i>: ", prefix_fr="<br/><i>Résumé</i>: ", suffix="</p>", highlight="no", print_lang='en') }}
        </p>
    </div>
</div>
{% endblock %}

{% block record_footer %}
    <p></p>
    {{ render_record_footer(4) }}
{% endblock %}
