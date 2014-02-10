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
