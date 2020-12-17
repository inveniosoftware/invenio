..
    This file is part of Invenio.
    Copyright (C) 2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _user-interface-styling:

User interface styling
======================

In this documentation you will learn how Invenio integrates modern frontend
frameworks and web assets building to display nice looking user interfaces.
You will also read about how to customize the look and feel or add your own
web assets.

.. _semantic-ui-styling:

Semantic UI styling
-------------------

**Scope**

This section explains the basics of how the CSS framework Semantic UI is
integrated into Invenio. Invenio supports multiple CSS frameworks.
The default CSS framework is Semantic UI, and this section only describes
how you can customize the Semantic UI styling. It does not describe how to
replace e.g. Semantic UI with other CSS frameworks like Material Design
or Bootstrap.

**Intended audience**

This section is intended for developers of Invenio instances and modules, who
want to understand the fundamentals of how Semantic UI is integrated into
Invenio, and how to override the Semantic UI default styling.

Developers are expected to have prior experience with CSS and LESS.

**Prerequisites**

* Quick start: The entire section assumes you have followed the Quick Start to
  have a basic Invenio instance.
* Tutuorial: You are recommended to first follow the tutorials on customizing
  the look and feel.

Overview
^^^^^^^^

Semantic UI is a highly customizable CSS framework, that itself can be made to
partially look like other CSS frameworks such as Material Design and Bootstrap.
The section describes the following:

* Developing with Semantic UI - how you efficiently can change styles
  and quickly see the result via e.g. watching for changes.
* Rendering a page - explains how the CSS/JS is loaded on a rendered page.
* Understand the Semantic UI files - explains the build process and provides
  an overview of the files and their purpose.
* Theming - explains the basics behind theming Semantic UI.

Developing with Semantic UI
^^^^^^^^^^^^^^^^^^^^^^^^^^^

First of all, it's important to understand how to develop efficiently with the
Semantic UI.

**Config**

First, verify that the ``APP_THEME`` configuration variable in ``config.py``
is set like below:

.. code-block:: python

    APP_THEME = ['semantic-ui']

**Symlinks**

Assuming you have followed the Quick start, you should first export the
``FLASK_ENV`` environment variable if not already done:

.. code-block:: shell

    cd my-site/
    export FLASK_ENV=development

The ``FLASK_ENV`` variable is used during development to ensure CSS,
JavaScript and other static/assets files are symlinked into their build
location so that if you edit a file the changes are immediately available.

**Static files**

Next, collect all static files into the Flask instance folder
(``<VIRTUALENV>/var/instance/static/``). Usually this is e.g. images which
does not need to be part of the Webpack build.

.. code-block:: shell

    pipenv run invenio collect

**Clean Webpack build**

Once ``FLASK_ENV`` has been set, you need to clean the existing Webpack
project build to ensure that files are properly symlinked. If this step is
not applied, you risk having outdated files in your assets build, and none
of your changes being applied:

.. code-block:: shell

    pipenv run invenio webpack clean buildall

The above does the following:

* Removes the existing Webpack project in ``<VIRTUALENV>/var/instance/assets``.
* Creates the Webpack project in ``<VIRTUALENV>/var/instance/assets`` by
  collecting all assets from all Invenio modules and the Invenio instance.
* Installs the Node modules defined by the Webpack project's ``package.json``
  (e.g. Semantic UI is installed like this).
* Run the Webpack build.

The last two steps, is roughly equivalent of running the following commands:

.. code-block:: shell

    cd <VIRTUALENV>/var/instance/assets
    npm install
    npm run build

**Watching changes**

You now have a clean build of assets where files have been symlinked. You
start watching changes to the files by running:

.. code-block:: shell

    pipenv run invenio webpack run start

Note that this is a long-running operation, so it will "block" the shell
until you stop it, and therefore stop watching for changes.

If you edit a file, the Webpack project will be automatically rebuilt.

In a different shell, you can then start  the server:

.. code-block:: shell

    ./scripts/server

IMPORTANT: Watching for changes only works if you have followed above steps.
In particular:

* Files must have been symlinked by setting ``export FLASK_ENV=development``
  and performing a full wipe and rebuild of static and assets.
* The Python packages (e.g. your Invenio instance) was installed with Python
  develop mode (this is default for the Quick Start guide).
* Newly added/removed files are not automatically taken into account. If you
  add a new file, just must run ``pipenv run invenio webpack create build``.
  If you remove a file, just must rebuild the entire Webpack
  ``pipenv run invenio webpack clean buildall``

Rendering a page
^^^^^^^^^^^^^^^^

Before, diving deeper into how to change and add new styles, it's important
to understand how the CSS/JavaScript files generated by the Webpack project
are being included in the HTML documents.

**Jinja template rendering**

All HTML pages are being rendered in Flask via the Jinja template engine.
Below is a very simplified example of how such as Flask view looks like:

.. code-block:: python

    # a very simplified example of template rendering
    from flask import render_template

    @app.route('/')
    def index():
        return render_template('frontpage.html')

The ``render_template()`` will look for the ``frontpage.html`` in multiple
template search paths (see Web assets build system) and render an HTML
document.

**Including assets in templates**

A Jinja template like ``frontpage.html`` usually extends from a base template
implementing the overall layout called ``page.html``. If we remove all the
complexities, there's two template blocks in the template responsible for
including the built assets: ``css`` and ``javascript`` which looks like below:

.. code-block:: jinja

    {# simplified view of page.html in Invenio-Theme #}
    ...
    {% block css %}
        {{ webpack['theme.css'] }}
    {% endblock %}
    ...
    {% block javascript %}
        {{ webpack['base.js']} }
        {{ webpack['theme.js'] }}
        {{ webpack['i18n_app.js'] }}
    {% endblock %}
    ...

The key assets for Semantic UI is the ``theme.css`` and ``theme.js``. Both
of them come from a single Webpack entry point called ``theme`` defined
in Invenio-Theme.

**Webpack bundles and entry points**

In Invenio-Theme in ``webpack.py`` you'll find a Webpack theme bundle
defining the ``theme`` Webpack entry point. It looks somewhat like this:

.. code-block:: python

    # webpack.py in Invenio-Theme
    from invenio_assets.webpack import WebpackThemeBundle

    theme = WebpackThemeBundle(
        __name__,
        'assets',
        themes={
            'semantic-ui': {
                'entry': {
                    # Webpack entry point
                    'theme': './js/invenio_theme/theme.js',
                    # ...
                },
                'dependencies': {
                    # NPM dependencies
                    'semantic-ui-less': '~2.4.1',
                    'semantic-ui-css': '~2.4.1',
                    # ...
                },
            }
            # ...
        }
    )

The ``theme`` Webpack entry point is what allows you to use
``{{ webpack['theme.js'] }}`` and ``{{ webpack['theme.css'] }}`` in the
Jinja templates. Note that the ``.js`` and ``.css`` extensions is because
Webpack automatically splits CSS/JavaScript into separate files.

If you look inside the file ``./js/invenio_theme/theme.js`` you find the
following lines:

.. code-block:: javascript

    // theme.js in Invenio-Theme
    import "semantic-ui-css/semantic.js";
    import "semantic-ui-less/semantic.less";

.. note::

    Above is what kicks off the entire Semantic UI build. The entire
    customization and everything described in the following sections is started
    from this file. Thus, the ``theme`` Webpack entry point is the absolute
    critical piece which is responsible for the integrating Semantic UI
    in Invenio.

The Semantic UI build
^^^^^^^^^^^^^^^^^^^^^

The previous section shows how Invenio-Theme defines a Webpack entry point
called ``theme`` which is responsible for building the CSS and JavaScript
for Semantic UI.

**Webpack alias for the theme config**

The Webpack entry point ``theme`` relies on a file ``theme.config`` to be
provided by your Invenio instance. The way your Invenio instance provide
this file is via a Webpack bundle. The file looks similar to below:

.. code-block:: python

    # webpack.py in your Invenio instance
    from invenio_assets.webpack import WebpackThemeBundle

    theme = WebpackThemeBundle(
        __name__,
        'assets',
        default='semantic-ui',
        themes={
            'semantic-ui': dict(
                # ...
                aliases={
                    '../../theme.config$': 'less/my_site/theme.config',
                },
            ),
        }
    )


The Webpack bundle defines a Webpack alias ``../../theme.config$``, which
points to the ``theme.config`` file in your Invenio instance. The name exact
name ``../../theme.config$`` is very important because this is the name that
Semantic UI uses to import the config, similar to this

.. code-block:: less

    // Example from Semantic UI code
    @import (multiple) '../../theme.config';

**Theme configuration (``theme.config``)**

The ``theme.js`` in Invenio-Theme is central for the overall Semantic UI
build, however, the ``theme.config`` in your Invenio instance is the central
file for how you customize your Invenio instance's Semantic UI build. A part
of the fille is shown below:

.. code-block:: less

    /*

    ████████╗██╗  ██╗███████╗███╗   ███╗███████╗███████╗
    ╚══██╔══╝██║  ██║██╔════╝████╗ ████║██╔════╝██╔════╝
    ██║   ███████║█████╗  ██╔████╔██║█████╗  ███████╗
    ██║   ██╔══██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║
    ██║   ██║  ██║███████╗██║ ╚═╝ ██║███████╗███████║
    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝
    */

    /* Global */
    @site        : 'invenio';
    @reset       : 'default';

    /* Elements */
    @button      : 'invenio';
    @container   : 'invenio';

    // ...

    /* Path to site override folder */
    @siteFolder  : '../../less/my_site/site';

    // ...

**Theming overview**

Semantic UI theming inheritance is what provides the powerful customization
options of Semantic UI, and what allows Semantic UI to look partially
like Bootstrap or Material Design.

Semantic UI supports three layers of theme inheritance:

* *Default theme*: Semantic UI comes with defaults styled components, and
  defines a lot of variables that can be overwritten.
* *Package theme*: The packaged themes provides customizations on top of
  the default theme. This is here you can choose between e.g. Bootstrap,
  Material Design or your own packaged theme.
* *Site Theme*: The site theme provides customizations on top of the default
  and package themes. Usually it's here you set e.g. your brand color.

**Site folder**

The ``@siteFolder`` variable in ``theme.config`` is what defines where your
site theme is loaded from. By default, in your Invenio instance, you'll find
site folder next to your ``theme.config`` in ``site``:

.. code-block::

    .
    |-- site
    |   `-- globals
    |       |-- site.overrides
    |       `-- site.variables
    `-- theme.config

By default you'll find two files in there:

* ``globals/site.overrides`` - An ``.overrides`` file specifies additional
  CSS rules to be added to a definition for a theme.
* ``globals/site.variables`` - A ``.variables`` file specifies variables
  which should be adjusted for a theme.

Usually, you can add your custom CSS in ``site.overrides`` and your variable
definitions in ``site.variables``.

**Theme defintions**

The ``theme.config`` specifies theme definitions for specific components.
For instance:

.. code-block:: less

    @site        : 'invenio';

Above, tells Semantic UI to use the *packaged theme* ``invenio``. You can
change it to use e.g. the ``default`` package theme, or other themes like
``bootstrap`` or ``material``.

Overall the theming is divided into:

* Global site-wide overrides/variables that affect all components
  (e.g. fonts, colors, ..)
* Elements overrides/variables for e.g. buttons, labels, and lists.
* Collections overrides/variables for e.g. breadcrumbs, forms and tables.
* Views overrides/variables for e.g. comments, cards, statistics and similar.
* Modules overrides/variables for e.g. accordion, dropdown, modals etc.

For each component, you can choose a specific theme:

.. code-block:: less

    /* Global */
    @site        : 'invenio';
    @reset       : 'default';

    /* Elements */
    @button      : 'material';
    // ...

    /* Collections */
    // ...

    /* Modules */
    // ...

    /* Views */
    // ...

Note, that a theme may not define all components. For instance ``material``
theme defines only ``button`` and ``site`` components thus trying to do
this will fail:

.. code-block:: less

    // This will fail because 'material' theme is not defined for
    // the modal component:
    @modal       : 'material';

**Components and themes**

It's important to understand that you can customize Semantic UI at many
different levels. First of all, Semantic UI has a number of **components**
categorized into globals, elements, collections, views and modules.

Each **component** can be customized by a **theme** that is subject to the
theme inheritance.

As an example, the element component *button* can be customized by:

* Site theme - i.e. adding the files ``site/elements/button.overrides``
  and ``site/elements/button.variables`` in your Invenio instance.
* Package theme - i.e. by changing ``@button : `<theme>`` in ``theme.config``.

**The ``invenio`` packaged theme**

Invenio-Theme defines a **packaged theme** named ``invenio``, which you can
find in ``invenio_theme/assets/semantic-ui/less/invenio_theme/theme``. The
theme overrides some of the defaults for use with Invenio and defines
e.g. variables to make it easier to customize the sign up button and
search button colors.

**Further reading**

* `Semantic UI Glossary <https://semantic-ui.com/introduction/glossary.html>`_
* `Semantic UI Theming <https://semantic-ui.com/usage/theming.html>`_
* `Semantic UI Documentation <https://semantic-ui.com>`_
* `React-SemanticUI Documentation <https://react.semantic-ui.com>`_

Web assets
----------

Most of the user interfaces in Invenio use CSS for the layout and JavaScript
to improve user experience. Such web assets, injected in the Jinja templates,
are transformed from their original format to an optimized version thanks to
Node packages and the Webpack bundler.
For example, style sheets rules are written using the LESS language extension
and then converted to minified CSS, natively understandable by your browser.

Web assets with Python
^^^^^^^^^^^^^^^^^^^^^^

One of the first things to look at when working with modern web applications
is how to install and build web assets. Node packages, managed with
`npm <http://npmjs.org/>`_, and Webpack are probably the most well-known
tools in the front-end development ecosystem.

A common, minimal web assets build could look like:

* ``package.json``:

.. code-block:: json

    {
    "version": "0.0.1",
    "scripts": {
        "build": "webpack --config webpack.config.js"
    }
    "dependencies": {
        "lodash": "^4.17.0"
    }
    }

* ``webpack.config.js``:

.. code-block:: javascript

    var path = require("path");

    module.exports = {
        context: path.resolve(__dirname, "src"),
        entry: "./index.js",
        output: {
            filename: "[name].js",
            path: path.resolve(__dirname, "dist")
        }
    };

With the example above, executing ``npm install && npm run build`` will create
the final JS bundle in a ``dist`` folder.

Invenio uses a few extra packages to integrate web assets building with Python.
Below, you will find a brief introduction to these packages.

**Install npm packages**

Invenio uses `PyNPM <https://pynpm.readthedocs.io>`_ to execute ``npm``
commands with Python. This package's responsibility is to wrap the npm
binary and provide Python APIs for the most common commands, such as ``init``,
``install`` or ``test``. It does not expose command line commands.

**Build npm packages**

The `PyWebpack <https://pywebpack.readthedocs.io>`_ and
`Flask-WebpackExt <https://flask-webpackext.readthedocs.io>`_ packages take
care of integrating Webpack with the Python ecosystem. While the main
responsibility of the former is to wrap a Webpack build and enable its usage
with Python, for the latter is to integrate a Flask application, its
configurations and Jinja templates.

To build the web assets of your Flask project, you will need a folder,
e.g. ``assets``, containing a ``package.json`` and a ``webpack.config.js``
files.
Then, you instantiate a
`WebpackBundleProject <https://pywebpack.readthedocs.io/en/latest/api.html#pywebpack.project.WebpackBundleProject>`_:

.. code-block:: python

    from flask_webpackext import WebpackBundleProject

    project = WebpackBundleProject(
        __name__,
        project_folder="assets",
        config_path="build/config.json"
    )

As done in the example above, you can optionally pass a ``config_path``
file path (or a config ``dict``) parameter. Such Python config can be
injected in the Webpack configuration file to specify the location
of the generated output files and other settings. See
`flask_config <https://flask-webpackext.readthedocs.io/en/latest/api.html#flask_webpackext.project.flask_config>`_
the default configuration.

You can now execute the build. The built web assets will be created in the
``dist`` folder:

.. code-block:: shell

    flask webpack buildall

Along with the built web assets, one of the Webpack output file is
the ``manifest.json``: it contains a map with the name of each asset and
its "hashed" version:

.. code-block:: json

    {
        "main.js": "/static/dist/main.75244bb780acd727ebd3.js"
    }

This file is parsed and made available to the Python application so that
assets can be injected in the Jinja templates simply by their name. At
render time, the file name will be mapped to the hashed one:

.. code-block:: html

    <script src="/static/dist/main.75244bb780acd727ebd3.js"></script>

**Multiple Python packages**

With PyWebpack you can collect and build assets from different Python
packages via entry points. This is useful when having a main Flask
application that uses assets contained in other installed packages,
which is the case of Invenio.
Each Python package declares what assets needs, for example:

.. code-block:: python

    from flask_webpackext import WebpackBundle

    js = WebpackBundle(
        __name__,
        "./modules/module1/static",
        entry={
            "module1-app": "./js/module1-app.js",
        },
        dependencies={
            "lodash": "^4.17.0"
        }
    )

It then exposes them via entry points. In the ``setup.py``:

.. code-block:: python

    setup(
        ...
        entry_points={
            ...
            "webpack_bundles": [
                "mymodule1_js = mymodule.bundles:js",
            ],
    )

The main application, or the package responsible of building web assets,
defines the Webpack project:

.. code-block:: python

    from flask_webpackext import WebpackBundleProject

    project = WebpackBundleProject(
        __name__,
        project_folder="assets",
        config_path="build/config.json",
        bundles=bundles_from_entry_point("invenio_assets.webpack"),
    )

When running ``flask webpack buildall``, Pywebpack will discover all the
declared bundles, collect the dependencies and merge them into a final
``package.json`` in a temporary build folder. It will then run
``npm install`` and invoke the Webpack build.

In this section, you have learned how you can build web assets with npm
and Webpack using PyNPM, PyWebpack and Flask-WebpackExt in a Flask
application. You read more about each package in each documentation.

Invenio web assets
^^^^^^^^^^^^^^^^^^

In the next section you will learn how Invenio uses the web assets
integration with Python explained above and allows you define your own
templates and web assets.

The ``Invenio-Assets`` package defines the main Webpack project and
exposes the entry point name ``invenio_assets.webpack`` that can
be used by other Invenio packages:

.. code-block:: python

    from flask_webpackext import WebpackBundleProject

    project = WebpackBundleProject(
        __name__,
        project_folder="assets",
        config_path="build/config.json",
        bundles=bundles_from_entry_point("invenio_assets.webpack"),
    )

The ``assets`` folder contains:

* the base ``package.json``, which defines all the ``npm`` dependencies
  required to build web assets (webpack and plugins, babel, eslint,
  less/css loaders, etc.). Note that it does not contain CSS or JS
  packages for the Invenio layout;
* the ``build/webpack.config.js`` Webpack configuration file, which defines
  the build process;

The Invenio Webpack configuration includes the optimization of CSS and
JavaScript assets, the creation of the ``manifest.json`` needed for
the Jinja templates and it enables
`chunks <https://webpack.js.org/plugins/split-chunks-plugin/>`_ to minimize
the size of the downloaded assets in each web page.

**Building assets**

When bootstrapping Invenio, the ``/scripts/bootstrap`` will run the commands
``collect`` and ``webpack buildall``. By default, static files such as
Jinja templates, CSS and JavaScript files are copied in the
``<virtualenv>/var/instance/`` ``assets`` and ``static`` folders so that
they are available for the Webpack build. The ``assets`` folder is the
build directory used by Npm and Webpack.

The final CSS, JavaScripts, images and fonts files built by Webpack are
created in the ``static/dist`` folder. Each filename contains an unique
hash, e.g. ``theme.0346fcac8ffc95821e90.css``, which is different
at each build.

This allows to optimize how browsers will download static files,
given that they can be cached without expiration. There is a drawback:
assets cannot be easily added to Jinja templates, for example with
``<script type="application/javascript" src="main.js"></script>``,
because the filename is not known in advance when developing.

**Using assets in templates**

The ``dist/manifest.json`` is the registry of the built web assets and
contains the map with the chunks generated by the Webpack built. Thanks
to this, there is no need to manually add vendors or library bundles to
Jinja templates. Invenio provides some utilities that will automatically
inject assets dependencies to the generated HTML files.
For example, given the following ``WebpackBundle``:

.. code-block:: python

    from flask_webpackext import WebpackBundle

    js = WebpackBundle(
        __name__,
        "./modules/module1/static",
        entry={
            "module1-app": "./js/module1-app.js",
        },
        dependencies={
            "lodash": "^4.17.0",
            "react": "^17.0.0",
        }
    )

The Jinja template will look like:

.. code-block:: jinja

    ...
    {{ webpack['module1-app.js']}}
    ...

.. note:

    As you can see, the ``react`` or ``lodash`` dependencies needed by
    ``module1-app`` are not added to the template: the minimal amount of
    needed chunks will be automatically injected.

Themes
^^^^^^

Invenio comes with the support of multiple UI theming. This is because
the UI framework has been switched from Bootstrap 3 to Semantic UI.
To learn how to change the theme layout or integrate your own them, please
refer to the documentation :ref:`semantic-ui-styling`.

In this section you will learn how Invenio manages multiple themes.

In Invenio-Assets, the ``WebpackThemeBundle`` extends the concepts explained
above with the ``WebpackBundleProject`` configuration. It basically allows
to define multiple ``WebpackBundleProject``, namespaced by the name of
your theme.
In Invenio there are 2 themes defined (see ``Invenio-Theme`` for
more information):

.. code-block:: python

    from invenio_assets.webpack import WebpackThemeBundle

    theme = WebpackThemeBundle(
        __name__,
        "assets",
        default="bootstrap3",
        themes={
            "bootstrap3": dict(
                entry={
                    ...
                },
                dependencies={
                    ...
                }
            ),
            "semantic-ui": dict(
                entry={
                    ...
                },
                dependencies={
                    ...
                }
            ),
        }
    )

As you can see, the 2 themes ``bootstrap3`` and ``semantic-ui`` are listed
in the ``themes`` parameter. They correspond to two different
``WebpackBundleProject``. The global configuration variable ``APP_THEME``
will instruct Invenio, at runtime, which one to use. For example:

.. code-block:: python

    APP_THEME = ["semantic-ui"]

Each Invenio module that adds web assets can provide a different set
of assets per theme. The resolution mechanism ensures that only the web
assets for the current theme will be loaded and injected in Jinja templates.
The ``default`` option is used as a fallback in case that no theme is set
(``APP_THEME`` is not defined or empty).

**Jinja templates**

Jinja templates resolutoin supports themes. As for web assets, you can
create specific Jinja templates for your theme.
When resolving the Jinja template file to use, Invenio will prefix the
file path with the name of the theme that you have defined
with the ``APP_THEME`` configuration.

For example, in Invenio you can have the following:

.. code-block::

    templates/
    semantic-ui/
        <module-name>/
        index.html
    templates/
    <my-theme-name>/
        <module-name>/
        index.html

**Further reading**

* `PyNPM <https://pynpm.readthedocs.io>`_
* `PyWebpack <https://pywebpack.readthedocs.io>`_
* `Flask-WebpackExt <https://flask-webpackext.readthedocs.io>`_
* `Invenio-Assets <https://invenio-assets.readthedocs.io>`_
* `Invenio-Theme <https://invenio-theme.readthedocs.io>`_
