.. _developers-extensions:

Extensions
==========

What are extension and what is their purpose? Small piece of code that
should ease the integration of a third party library. As such many of
extensions have been already developed and one can find them in the
`Flask Extension Registry`_. Everyone should check first if there is
a usable extensions before developing new one according to
`Flask Extension Development`_ guideline that will help you get your
extension running.

.. _Flask Extension Registry: http://flask.pocoo.org/extensions/
.. _Flask Extension Development: http://flask.pocoo.org/docs/extensiondev/

Pluging an Existing Extension
-----------------------------

Extensions are all located in a package called ``flask_something``
where "something" is the name of the extension you want to bridge.
So for example if you plan to add support for an extension named
`login`, you would name your extension's package ``invenio.ext.login``.

Alternatively, if the extension reads only configuration from
``current_app.config``, you can just list in ``EXTENSIONS`` option
as ``flask.ext.something:Something``, where ``Something`` has to accept
application object as first argument::

    class Something(object):
        def __init__(self, app, optional=None):
            pass

But how do extensions look like themselves?  An extension has to ensure
that it works with multiple Flask application instances at once.


Code structure
--------------

So let's get started with creating such a extension bridge.  The bridge
we want to create here will provide very basic support for `Flask Login`_.

First we create the following folder structure::

    invenio/ext/login/
        __init__.py
        legacy_user.py
        README

Here's the contents of the most important files:

* ``__init__.py`` contains :func:`~invenio.ext.login.setup_app` function::

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

* ``legacy_user.py`` contains implementation ``UserMixin`` object::

    from flask.ext.login import UserMixin
    from werkzeug.datastructures import CallbackDict, CombinedMultiDict

    class UserInfo(CombinedMultiDict, UserMixin):
        """
        This provides legacy implementations for the methods that Flask-Login
        and Invenio 1.x expects user objects to have.
        """

        def __init__(self, uid=None, force=False):
            ...


.. _Flask Login: https://flask-login.readthedocs.org/en/latest/
