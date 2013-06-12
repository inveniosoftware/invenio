<div class="media htmlbrief">
    <div class="media-body">
        <p>
            <span class="label label-info">{{ bfe_creation_date(bfo, date_format="%d %M %Y") }}</span>
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
            {{ record.get('abstract.summary', '')|truncate(150) }}
        </p>
        <p>
            {{ bfe_publi_info(bfo, prefix="<br /><small>Published in <strong>", suffix="</strong></small>") }}
        </p>

        <p>
            {{ bfe_fulltext(bfo, prefix='<br /><small>', style="note",
                            show_icons="yes", suffix="</small>",
                            focus_on_main_file="yes") }}
        </p>
    </div>
</div>
