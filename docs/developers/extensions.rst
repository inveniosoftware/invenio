..  This file is part of Invenio
    Copyright (C) 2014, 2015 CERN.

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

.. _developers-extensions:

Extensions
==========

What are extensions and what is their purpose? An extension is a small
piece of code that should ease the integration of a third party library.
Many such extensions have been already developed and one can find them in
the `Flask Extension Registry`_. Everyone should check first if there is
a usable extension before developing new one. When developing an extension,
follow the `Flask Extension Development`_ guideline that will help you get your
extension running.

.. _Flask Extension Registry: http://flask.pocoo.org/extensions/
.. _Flask Extension Development: http://flask.pocoo.org/docs/extensiondev/

Plugging an Existing Extension
------------------------------

All extensions are located in a package called ``flask_something``
where "something" is the name of the extension you want to bridge.
So for example if you plan to add support for an extension named
`login`, you would name your extension's package ``invenio.ext.login``.

Alternatively, if the extension only reads configuration from
``current_app.config``, you can just list in ``EXTENSIONS`` option
as ``flask_something:Something``, where ``Something`` has to accept
an application object as first argument::

    class Something(object):
        def __init__(self, app, optional=None):
            pass

So what do extensions actually look like?  An extension has to ensure
that it works with multiple Flask application instances at the same time.


Code structure
--------------

So let's get started with creating such an extension bridge.  This example
bridge will provide very basic support for `Flask Login`_.

First we'll create the following folder structure::

    invenio/ext/login/
        __init__.py
        legacy_user.py
        README

Here's the contents of the most important files:

* ``__init__.py`` contains :py:func:`~invenio.ext.login.setup_app` function:

.. code-block:: python

    from .legacy_user import UserInfo

    def setup_app(app):
        """Setup login extension."""

        # Let's create login manager.
        _login_manager = LoginManager(app)
        _login_manager.login_view = app.config.get('CFG_LOGIN_VIEW',
                                                   'webaccount.login')
        _login_manager.anonymous_user = UserInfo

        @_login_manager.user_loader
        def _load_user(uid):
            """
            Function should not raise an exception if uid is not valid
            or User was not found in database.
            """
            return UserInfo(int(uid))

        return app

* ``legacy_user.py`` contains implementation of the ``UserMixin`` object:

.. code-block:: python

    from flask_login import UserMixin
    from werkzeug.datastructures import CallbackDict, CombinedMultiDict

    class UserInfo(CombinedMultiDict, UserMixin):

        """
        This provides legacy implementations for methods that Flask-Login
        and Invenio 1.x expect user objects to have.
        """

        def __init__(self, uid=None, force=False):
            ...


.. _Flask Login: https://flask-login.readthedocs.org/en/latest/
