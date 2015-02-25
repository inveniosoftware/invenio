{#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
{%- block mail_header -%}
{% if header %}{{ header }}{% else %}{{ _("Hello:") }}<br/>{% endif %}
{%- endblock %}
{% block mail_content %}
{{ content }}
{% endblock -%}
{%- block mail_footer %}
{% if footer %}{{ footer }}{% else %}
<br/>
<br/>
<em>{{ _("Best regards") }}</em>
<hr />
<a href="{{ config.CFG_SITE_URL }}">
    <strong>
        {{ config.CFG_SITE_NAME_INTL.get(g.ln, config.CFG_SITE_NAME) }}
    </strong>
</a>
<br />
{{ _("Need human intervention?  Contact") }}
<a href="mailto:{{ config.CFG_SITE_SUPPORT_EMAIL }}">
    {{ config.CFG_SITE_SUPPORT_EMAIL }}
</a>
{% endif %}
{% endblock -%}
