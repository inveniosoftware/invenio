.. _developers-modules:

Modules
=======

Modules are application components that can be use within an application
or across aplications.  They can contains `SQLAlchemy`_ models, `Flask`_
views, `Jinja2`_ templates and other ref:`pluggable-objects`.

Discovery of modules is done based on configuration parameter called
``PACKAGES``, where expansion character `*` is supported at the end of
package path after last dot (e.g. ``foo.bar.something.*``).


Views
-----

Flask uses a concept of *blueprints* for making application components and
supporting common patterns within an application or across applications.
Blueprints can greatly simplify how large applications work and provide a
central means for Flask extensions to register operations on applications.
A :class:`Blueprint` object works similarly to a :class:`Flask`
application object, but it is not actually an application.  Rather it is a
*blueprint* of how to construct or extend an application.

Blueprints in Flask are intended for these cases:

* Factor an application into a set of blueprints.  This is ideal for
  larger applications; a project could instantiate an application object,
  initialize several extensions, and register a collection of blueprints.
* Register a blueprint on an application at a URL prefix and/or subdomain.
  Parameters in the URL prefix/subdomain become common view arguments
  (with defaults) across all view functions in the blueprint.
* Register a blueprint multiple times on an application with different URL
  rules.
* Provide template filters, static files, templates, and other utilities
  through blueprints.  A blueprint does not have to implement applications
  or view functions.
* Register a blueprint on an application for any of these cases when
  initializing a Flask extension.


Templates
---------

Jinja2 is a modern and designer friendly templating language for Python.
We will summarize adoption of Jinja2 web framework and describe best
practices for writing easily reusable and extendable templates.

.. note:: Please follow these simple rules when creating new templates, to
    allow different Invenio installations (CDS, Inspire, ZENODO, ...) to
    easily customize templates and keep in sync with updates to templates.
    Using the rules will greatly reduce the amount of copy/pasting the
    installations will have to do.


* ``<module>/views.py``::

    # ... some where in the blueprint code:
    render_template(['<module>_<name>.html'], ctx)


* ``<module>/templates/<module>/<name>_base.html``::

    {#
     # The base template usually extends from the main Invenio template, or perhaps
     # from a module specific main template. It contains nearly all the HTML code.
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
        {# Macros can be overwritten in child template, but only calls within the
         # child template will call the new macro. Hence, if you just want to
         # overwrite the action_bar macro in <module>_<name>.html, you must also
         # copy/paste the form_header and form_footer blocks where it's used,
         # otherwise the old macro will be used. To avoid this problem, please
         # instead just include a template inside the macro. This allow anther
         # Invenio installation to overwrite just this part
         #}
        {% include "<module>_<name>_action_bar.html"%}
    { endmarco %}

    {%- macro render_field(thisfield, with_label=True) %}
        {% include "<module>_<name>_render_field.html"%}
    {%- endmarco %}

    {#
     # Blocks
     #  * Think of template-blocks, as the API other Invenio installations will
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
     # base template. Doing it this way, allow an Invenio installation to overwrite
     # just the blocks they need, instead of having to implement the entire
     # template.
     #}
    {% extends "<module>_<name>_base.html" %}



* ``<mypackage>/templates/<module>/<name>.html``::

    {#
     # Here's an example of an Invenio installation which just overwrites the
     # necessary template block.
     #}
    {% extends "<module>_<name>_base.html" %}

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
.. _SQLAlchemy: http://www.sqlalchemy.org/
