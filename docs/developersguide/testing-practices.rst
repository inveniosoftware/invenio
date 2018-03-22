..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Testing practices
=================

It is a good practice to add test cases to each Invenio module. Tests are
normally organized in:

1. unit and functional testing: test cases run against the Flask app defined in
   the module, often as example app. They can be found in ``tests`` or
   ``tests/unit`` package.

2. end-to-end functional testing: run by launching a browser and a live server
   on the test Flask app and executing test cases through `Selenium`_.

Invenio uses `pytest`_ as test framework.

.. _Selenium: http://www.seleniumhq.org/
.. _pytest: https://pypi.python.org/pypi/pytest

Unit functional testing
-----------------------

To be completed

End-to-end functional testing
-----------------------------

To run end-to-end tests, the requirements are:

- Invenio installed, with modules that are covered by the tests
- an Elastic Search running instance
- a Redis running instance
- a web browser driver (check `Selenium WebDriver`_ documentation to see how to
  install it)

SQLite database will be created (if it doesn't exist) when tests are launched.

To run the end-to-end test, just ``py.test tests/e2e/``.

The ``tests\e2e\conftest.py`` is the entry point for pytest, which will set up
all the defined fixtures respecting the ``scope`` and ``autouse`` settings.
See `pytest documentation`_ for more details.

To be able to run the live server for Selenium, the package `pytest-flask`_
provides some extra fixtures which will update the test Flask app configuration
by setting the ``SERVER_NAME`` of the live server launched.
To do so, ``pytest-flask`` expects to find a fixture named ``app`` which should
return the Flask app created for the tests.

To fire up the live server, a test case should inject the ``live_server``
fixture. For example:

.. code-block:: python

    def test_mytestcase(live_server, browser):

Selenium driver is available through the ``browser`` fixture and it can be used
to perform actions on the HTML page to verify behaviours. For example:

.. code-block:: python

    browser.find_element_by_xpath("//a[contains(@href, '/login/')]").click()

To get the full list of available actions, see `selenium-python`_ documentation.

.. _Selenium WebDriver: http://www.seleniumhq.org/projects/webdriver/
.. _pytest documentation:  https://pytest.readthedocs.io
.. _pytest-flask: https://pypi.python.org/pypi/pytest-flask
.. _pytest-flask-documentation: https://pytest-flask.readthedocs.io
.. _selenium-python: http://selenium-python.readthedocs.io
