..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _developers-templates:

Templates
=========

`Jinja2`_ is a modern and designer friendly templating language for Python.
We will summarize the adoption of Jinja2 web framework and describe best
practices for writing easily reusable and extendable templates.

.. note:: Please follow these simple rules when creating new templates to
    allow different Invenio installations (CDS, Inspire, ZENODO, ...) to
    easily customize templates and keep in sync with updates to templates.
    Using these rules will greatly reduce the amount of copy/pasting the
    installations will have to do.


* ``<module>/views.py``::

    # ... some where in the blueprint code:
    render_template(['<module>/<name>.html'], ctx)


* ``<module>/templates/<module>/<name>_base.html``::

    {#
     # The base template usually extends the main Invenio template, or perhaps
     # a module-specific main template. It contains nearly all the HTML code.
     #}
    {% extends "page.html" %}


    {#
     # Macros
     #  * Make template blocks more clear so you don't clutter up a lot of HTML with
     #    rendering logic - e.g. you wouldn't put your Python code in one big
     #    function, instead you split it up into small functions with clearly
     #    defined responsibilities.
     #  * Macros can be parameterized.
     #}
    {%- macro action_bar(show_delete=True) %}
        {# Macros can be overwritten in a child template, but only calls within the
         # child template will call the new macro. Hence, if you just want to
         # overwrite the action_bar macro in <module>/<name>.html, you must also
         # copy/paste the form_header and form_footer blocks where it's used,
         # otherwise the old macro will be used. To avoid this problem, please
         # just include a template inside the macro instead. This will allows another
         # Invenio installation to overwrite just this part.
         #}
        {% include "<module>/<name>_action_bar.html"%}
    { endmarco %}

    {%- macro render_field(thisfield, with_label=True) %}
        {% include "<module>/<name>_render_field.html"%}
    {%- endmarco %}

    {#
     # Blocks
     #  * Think of template-blocks as the API which other Invenio installations will
     #    use to customize the Invenio layout. An Invenio installation can override
     #    blocks defined in your templates so that they keep their own changes
     #    to a minimum, and don't copy/paste large parts of the template code.
     #  * Use blocks liberally - to allow customizations of your template.
     #  * Add the template block name to the {% endblock <name> %} to increase
     #    readability of template code.
     #}
    {% block body %}
    <div>
        {%- block form_header scoped %}{{action_bar()}}{% endblock form_header%}
        {%- block form_title scoped %}<h1>{{ form._title }}</h1>{% endblock form_title %}
        {%- block form_body scoped %}
            <fieldset>
            {%- for field in fields %}
                {#
                 # Use the "scoped" parameter, to make variables available inside
                 # the block. E.g. without the loop variable will not be available
                 # inside the block.
                 #}
                {%- block field_body scoped %}
                    {{ render_field(field) }}
                    {% if loop.last %}<hr />{% endif %}
                {%- endblock field_body %}
            {%- endfor %}
            </fieldset>
        {% endblock form_body %}
        {% block form_footer scoped %}{{action_bar(show_delete=False)}}{% endblock form_footer %}
    </div>
    {% endblock body %}



* ``<module>/templates/<module>/<name>.html``::

    {#
     # The template actually being rendered by the blueprint. It only extends the
     # base template. Doing it this way allows an Invenio installation to overwrite
     # just the blocks they need instead of having to implement the entire
     # template.
     #}
    {% extends "<module>/<name>_base.html" %}



* ``<mypackage>/templates/<module>/<name>.html``::

    {#
     # Here's an example of an Invenio installation which just overwrites the
     # necessary template block.
     #}
    {% extends "<module>/<name>_base.html" %}

    {%- block field_body %}
        {%- if field.name == 'awesomefield' %}
            {{ render_field(field, class="awesomeness") }}
        {% else %}
            {{ render_field(field) }}
        {%- endif %}
        {% if loop.last %}<hr />{% endif %}
    {%- endblock field_body %}


.. _Flask: http://flask.pocoo.org/
.. _Jinja2: http://jinja.pocoo.org/2/
