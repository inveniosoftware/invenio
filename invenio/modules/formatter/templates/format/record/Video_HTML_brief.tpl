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
{% endblock %}

{% block record_media %}
    {% for resource in record['url'] if resource.get('public_note') == 'POSTER' %}
    <a class="thumbnail mejs-overlay" href="{{ url_for('record.metadata', recid=record['recid']) }}">
        <img src="{{ resource.get("url", "").replace(" ","") }}"
             alt="{{ resource.get("caption", "") }}" border="0"/>
        <div class="mejs-overlay-button"></div>
    </a>
    {% endfor %}
{% endblock %}

{% block record_content %}
      {{ record.get('abstract.summary', '')|sentences(3) }}
{% endblock %}
