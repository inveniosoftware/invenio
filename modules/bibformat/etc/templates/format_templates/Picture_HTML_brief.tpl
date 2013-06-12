<div class="media htmlbrief">
    <span class="pull-left">

    </span>
    <span class="pull-right">
        {# {{ bfe_altmetric(badgetype='donut', popover='left', no_script='1', prefix="<br>") }} #}
        {{ bfe_photo_resources_brief(bfo, ) }}
    </span>
    <div class="media-body">
        <p>
            <span class="label">{{ record.get('imprint.date', '') }}</span>
            {{ bfe_doi(bfo, prefix='<span class="label label-warning">', suffix='</span>') }}
            {{ bfe_primary_report_number(bfo, prefix='<span class="label label-important">', suffix='</span>') }}
            {{ bfe_additional_report_numbers(bfo, prefix='<span class="label label-inverse">', suffix="</span>",
                                             separator='</span> <span class="label label-inverse">', link="no") }}
            <i class="icon icon-picture"></i>
        </p>

        <h4 class="media-heading muted_a">
            <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
                {{ record.get('title.title', '') }}
            </a>
            <small>
                <br/>
                <a href="{{ url_for('record.metadata', recid=record['recid']) }}" class="muted">
                    {{ record.get('title_parallel.title', '')}}
                </a>
            </small>
        </h4>

        <p>
            {# bfe_title_brief(bfo, prefix="<b>", suffix="</b>", highlight="no") #}

            {{ bfe_abstract(bfo, limit="1", prefix='<p>', prefix_en="<i>Abstract</i>: ", prefix_fr="<br/><i>Résumé</i>: ", suffix="</p>", highlight="no", print_lang='en') }}

            {{ bfe_keywords(bfo, separator=", ", prefix="<br/> <i>Keyword</i>: ") }}

            {{ bfe_field(bfo, tag="909CPt", prefix="<br/><I>Available picture(s)</i>: ") }}

        </p>
    </div>
</div>
