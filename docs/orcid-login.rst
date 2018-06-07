..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

================
Login with ORCID
================
`ORCID <http://orcid.org/>`_ provides a persistent identifiers for researchers
and through integration in key research workflows such as manuscript and grant
submission, supports automated linkages between you and your professional
activities ensuring that your work is recognized.

This guide will show you how to enable your users to login with their ORCID
account in Invenio. The underlying authentication protocol is based on OAuth
which is the same used for enabling other social logins (like login with
Twitter, Google, etc).

ORCID API credentials
---------------------
In order to integrate your Invenio instance with ORCID the first step is to
`apply for a client id/secret
<https://orcid.org/content/register-client-application-sandbox>`_ to access the
ORCID Sandbox.

Please, follow the official ORCID documentation for this part.

After successful application for an API client application key you should
receive in your inbox an email with your ``Client ID`` and ``Client secret``.
You will need this information when configuring Invenio in the next step.

Redirect URI
~~~~~~~~~~~~
After a user have authenticated on the ORCID site, the user will be redirected
to a given page on the Invenio side. ORCID requires you to provide a list of
authorized URI prefixes that could be allowed for this redirection to happen.

Depending on the ``SERVER_NAME`` used to configure the Invenio installation,
you should fill this parameter with::

    https://<SERVER_NAME>/oauth/authorized/orcid/

Configuring Invenio
-------------------
In order to enable OAuth authentication for ORCID, just add these line to your
``var/instance/invenio.cfg`` file.

.. code-block:: python

    from invenio_oauthclient.contrib import orcid

    OAUTHCLIENT_REMOTE_APPS = dict(
            orcid=orcid.REMOTE_SANDBOX_APP,
    )

    ORCID_APP_CREDENTIALS = dict(
            consumer_key="<your-orcid-client-id>",
            consumer_secret="<your-orcid-client-secret>",
    )

where the client id and client secret are those provided by ORCID in the
previous step.

If you can now visit:::

    https://<SERVER_NAME>/login

you will be able to see ORCID authentication enabled:

.. image:: /_static/orcid-login.png
   :width: 500 px


Sign-up on first login
~~~~~~~~~~~~~~~~~~~~~~
The first time a user try to login with ORCID, they will be required to provide
a username and email address. This is because ORCID does provide this
information and it is required by Invenio in order to register an account.
