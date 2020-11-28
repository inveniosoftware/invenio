Auth bundle
-----------
The auth bundle contains all modules related to account and access management,
user profiles, session management and OAuth (provider and client)

Included modules:

- `invenio-access <https://invenio-access.readthedocs.io>`_
    - Role Based Access Control (RBAC) with object level permissions.
- `invenio-accounts <https://invenio-accounts.readthedocs.io>`_
    - User/role management, registration, password recovery, email
      verification, session theft protection, strong cryptographic hashing of
      passwords, hash migration, session activity tracking and CSRF protection
      of REST API via JSON Web Tokens.
- `invenio-oauth2server <https://invenio-oauth2server.readthedocs.io>`_
    - OAuth 2.0 Provider for REST API authentication via access tokens.
- `invenio-oauthclient <https://invenio-oauthclient.readthedocs.io>`_
    - User identity management and support for login via ORCID, GitHub, Google
      or other OAuth providers.
- `invenio-userprofiles <https://invenio-userprofiles.readthedocs.io>`_
    - User profiles for integration into registration forms.

The modules relies heavily on a suite of open source community projects:

- `flask-security <https://pythonhosted.org/Flask-Security/>`_
- `flask-login <https://flask-login.readthedocs.io/>`_
- `flask-principal <https://pythonhosted.org/Flask-Principal/>`_
- `flask-oauthlib <https://flask-oauthlib.readthedocs.io/>`_
- `passlib <https://passlib.readthedocs.io/en/stable/>`_
