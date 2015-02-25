# -*- coding: utf-8 -*-
#
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

"""Jasmine test runner extension.

1. Ensure ``TESTING`` configuration variable is set to ``True``.
2. Reinstall assets (with ``TESTING = True``).

   .. code-block:: console

        (invenio)$ cdvirtualenv src/invenio-demosite
        (invenio)$ inveniomanage bower -i bower-base.json > bower.json
        (invenio)$ bower install
        (invenio)$ inveniomanage collect
        (invenio)$ inveniomanage assets build

3. Run tests by loading http://localhost:4000/jasmine/specrunner in your
   browser.

Missing features
----------------

* Console test runner (likely we will use Karma test runner).
* CI integration.


FlightJS tests
---------------

Following is an example of a very simple FlightJS component which is normally
added in your Invenio module under ``static/js/**/*.js``:

.. code-block:: javascript

    // invenio/modules/*/static/js/mycomponent.js
    define(function(require) {
        'use strict';

        var defineComponent = require('flight/lib/component');

        return defineComponent(mycomponent);

        function mycomponent() {
            this.attributes({
                myattr: 'somevalue',
            });

            // ...

            this.after('initialize', function() {
                // ...
            });
        }
    });

To test above FlightJS component, create a spec file in
``testsuite/js/**/*.spec.js``:

.. code-block:: javascript

    // invenio/modules/*/testsuite/js/mycomponent.spec.js
    'use strict';

    describeComponent('js/mycomponent', function() {
        // Initialize the component and attach it to the DOM
        beforeEach(function() {
            this.setupComponent();
        });

        it('should be defined', function() {
            expect(this.component).toBeDefined();
        });
    });


Fixtures
--------
To load fixtures (created under ``testsuite/js/**/*.html``) for the test.
Inside the spec file take following steps:

.. code-block:: javascript

   jasmine.getFixtures().fixturesPath =
       '/jasmine/spec/invenio.modules.<module_name>/';
   readFixtures('<fixture_name>')

See https://github.com/flightjs/jasmine-flight for further examples how to test
FlightJS components.

HOWTO
-----

Mock AJAX request
~~~~~~~~~~~~~~~~~

.. code-block: javascript

    'use strict';

    describeComponent('js/mycomponent', function() {

        // Initialize the component and attach it to the DOM
        beforeEach(function() {
            jasmine.Ajax.install();
            this.setupComponent();
        });

        afterEach(function() {
            jasmine.Ajax.uninstall();
        });

        it('should make ajax request', function() {
            // trigger some event that makes an AJAX request ...

            // Retrieve most recent request.
            var request = jasmine.Ajax.requests.mostRecent();
            expect(request.url).toBe('/foo/bar');
            expect(request.method).toBe('GET');

            // Fake response from server.
            request.response({
                status: 200,
                responseText: 'somevalue'
            })
        });
    });

See http://jasmine.github.io/2.0/ajax.html for further information.

"""

from __future__ import absolute_import

from .views import blueprint
from . import bundles
from ..assets.registry import bundles as bundles_registry
from .registry import specs as specs_registry


def setup_app(app):
    """Initialize Jasmine extensions."""
    if app.testing:
        # Register blueprint
        app.register_blueprint(blueprint)

        # Register bundles
        with app.app_context():
            bundles_registry.register((bundles, bundles.jasmine_js))
            bundles_registry.register((bundles, bundles.jasmine_styles))
            # invenio/invenio/base seems to be working dir here
            specs_registry.register(
                '../ext/jasmine/testsuite/js/jasmine_configuration.spec.js',
                'invenio.ext.jasmine/jasmine_configuration.spec.js'
            )
            specs_registry.register(
                '../ext/jasmine/testsuite/js/jquery_object_mock.js',
                'invenio.ext.jasmine/jquery_object_mock.js'
            )
            specs_registry.register(
                '../ext/jasmine/testsuite/js/initialization_checker.spec.js',
                'invenio.ext.jasmine/initialization_checker.spec.js'
            )
            specs_registry.register(
                '../ext/jasmine/testsuite/js/events_checker.spec.js',
                'invenio.ext.jasmine/events_checker.spec.js'
            )
            specs_registry.register(
                '../ext/jasmine/testsuite/js/simple_div.html',
                'invenio.ext.jasmine/simple_div.html'
            )
