{#
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#}

<div class="record-brief">
  {% block above_record_header %}
  {% endblock %}
  <h4 class="record-header">
    {% block record_header %}
    {% endblock %}
  </h4>
  <div class="record-content">

    <span class="pull-left record-leftside">
      {% block record_media %}
      {% endblock %}
    </span>

    <p class="record-abstract">
      {% block record_content %}
      {% endblock %}
    </p>

    <p class="record-info">
      {% block record_info %}
      {% endblock %}
    </p>
  </div>

  {% block fulltext_snippets %}
  {% endblock %}

  {% block record_footer %}
  {% endblock %}
</div>
