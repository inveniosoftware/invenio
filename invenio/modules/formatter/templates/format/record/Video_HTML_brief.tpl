{% extends 'format/record/Default_HTML_brief.tpl' %}

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
        {% for resource in record['url'] if resource.get('public_note') == 'POSTER' %}
        <a class="thumbnail mejs-overlay" href="{{ url_for('record.metadata', recid=record['recid']) }}">
            <img src="{{ resource.get("url", "").replace(" ","") }}"
                 alt="{{ resource.get("caption", "") }}" border="0"/>
            <div class="mejs-overlay-button"></div>
        </a>
        {% endfor %}
    </span>
    <span class="pull-right">

    </span>

    <div class="media-body">
        <p class="record-abstract">
          {{ record.get('abstract.summary', '')|sentences(3) }}
        </p>
    </div>
</div>
{% endblock %}

{% block record_footer %}
    <p></p>
    {{ render_record_footer(4) }}
{% endblock %}
