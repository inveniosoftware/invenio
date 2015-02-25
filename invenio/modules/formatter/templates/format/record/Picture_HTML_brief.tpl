{#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#}

{% extends 'format/record/Default_HTML_brief.tpl' %}

{% block record_header %}
    <a href="{{ url_for('record.metadata', recid=record['recid']) }}">
        {{ record.get('title.title', '') }}
    </a>
    {{ '/' if record.get('title_parallel.title') }}
    <small class="text-muted">
        {{ record.get('title_parallel.title', '')}}
    </small>
{% endblock %}

{% block record_media %}
    {% for resource in record['url'] if resource.get('nonpublic_note') == 'icon' %}
        <a class="thumbnail" href="{{ url_for('record.metadata', recid=record['recid']) }}">
            <img src="{{ resource.get("url", "").replace(" ","") }}"
                 alt="" border="0" style="max-width: 80px;"/>
        </a>
    {% endfor %}
{% endblock %}

{% block record_footer %}
    {{ render_record_footer(1) }}
{% endblock %}


