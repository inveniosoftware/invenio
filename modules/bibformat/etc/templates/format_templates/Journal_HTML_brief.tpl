<div class="media htmlbrief">
    <span class="pull-left">
        {# <BFE_ICON />} #}
    </span>
    <span class="pull-right">
        {# {{ bfe_altmetric(badgetype='donut', popover='left', no_script='1', prefix="<br>") }} #}
    </span>
    <div class="media-body">
        <p>
            {{ bfe_doi(bfo, prefix='<span class="label label-warning">', suffix='</span>') }}
            {{ bfe_primary_report_number(bfo, prefix='<span class="label label-important">', suffix='</span>') }}
            {{ bfe_additional_report_numbers(bfo, prefix='<span class="label label-inverse">', suffix="</span>",
                                             separator='</span> <span class="label label-inverse">', link="no") }}
        </p>

        <h4 class="media-heading muted_a">
            <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
                {{ record.get('title.title', '') }}
            </a>
        </h4>

        <p>
            {% set authors = record.get('authors[:].full_name', []) %}
            {% set sep = joiner("; ") %}
            {% for full_name in authors[0:4] %} {{ sep() }}
              <a href="{{ url_for('search.search', p='author:"' + full_name + '"') }}">
                {{ full_name }}
              </a>
            {% endfor %}
            {% if record.get('number_of_authors', 0) > 4 %}
            {{ sep() }}
            <a href="#authors_{{ record['recid'] }}"
               class="muted" data-toggle="collapse"
               data-target="#authors_{{ record['recid'] }}">
                <em>{{ _(' et al') }}</em>
            </a>
            {% endif %}
            <div id="authors_{{ record['recid'] }}" class="collapse" style="height: 0px; display: block-inline;">
            {% for full_name in authors[4:] %} {{ sep() }}
              <a href="{{ url_for('search.search', p='author:"' + full_name + '"') }}">
                {{ full_name }}
              </a>
            {% endfor %}
            </div>
        </p>

        <p>
            {{ bfe_abstract(bfo, limit="3", escape="4", prefix="<small>", suffix="</small>", highlight="no", contextual="no") }}
        </p>
        <p>
            <small>Published in: <a href="{{ bfe_server_info(bfo, var="CFG_SITE_URL") }}journal/AtlantisTimes/">Atlantis Times {{ bfe_field(bfo, tag="773__n", instances_separator=", ") }}</a></small>
        </p>

        <p>
            {{ bfe_fulltext(bfo, prefix='<br /><small>', style="note",
                            show_icons="yes", suffix="</small>",
                            focus_on_main_file="yes") }}
        </p>
    </div>
</div>
