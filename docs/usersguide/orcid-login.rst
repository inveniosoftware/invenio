..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

====================
Enabling ORCID login
====================

`ORCID <http://orcid.org/>`_ provides a persistent digital identifier that
distinguishes you from every other researcher and, through integration in key
research workflows such as manuscript and grant submission, supports automated
linkages between you and your professional activities ensuring that your work
is recognized.

Say that your institutional library or repository has decided to enable ORCID
integration, so that:

* user can login into your system through ORCID, thus being identified directly
  through their very personal and verified ORCID Id.
* the service can *pull from* or *push to* information related to the user and
  on behalf of the user, directly with ORCID

In this tutorial will be present the former point, while the latter depends on
the `invenio-orcid <https://github.com/inveniosoftware/invenio-orcid>`_ module
that is
currently subject to important changes.

Invenio support out-of-the-box authentication through the
`OAUTH <https://en.wikipedia.org/wiki/OAuth>`_ protocol, which is actually
used by the ORCID service to offer authentication.

Registering an ORCID member API client application
--------------------------------------------------
In order to integrate your Invenio instance with ORCID the first step is to
`apply for API keys
<https://orcid.org/content/register-client-application-sandbox>`_ to access the
ORCID Sandbox.

Please, follow the official ORCID documentation for this part.

After successful application for an API client application key you should
receive in your inbox an email with your ``Client ID`` and ``Client secret``.
You will need this information when configuring Invenio in the next step.


Notes on the redirect URI
~~~~~~~~~~~~~~~~~~~~~~~~~
As part of the OAUTH authentication process, after the user will have
authenticated on the ORCID site, the user will be redirected to a given page on
the Invenio side.
ORCID requires to provide a list of authorized URI prefixes that could be
allowed for this redirection to happen.

Depending on the ``SERVER_NAME`` used to configure the Invenio installation, you
should fill this parameter with:

    ``https://<SERVER_NAME>/oauth/authorized/orcid/``


Enabling OAUTH+ORCID in your Invenio instance
---------------------------------------------
In order to enable OAUTH authentication for ORCID, just add these line to your
``var/instance/invenio.cfg`` file.

::

    from invenio_oauthclient.contrib import orcid

    OAUTHCLIENT_REMOTE_APPS = dict(
            orcid=orcid.REMOTE_SANDBOX_APP,
    )

    ORCID_APP_CREDENTIALS = dict(
            consumer_key="Client ID",
            consumer_secret="Client secret",
    )

where the ``Client ID`` and ``Client secret`` are those provided by ORCID itself
in the previous step.

If you now visit:

    ``https://<SERVER_NAME>/login``

you will be able to see ORCID authentication enabled:

.. image:: /_static/orcid-login.png
   :width: 500 px

When a user land on Invenio after having passed the ORCID authentication phase,
Invenio will not be provided by ORCID with the user email address. For this
reason, upon the first time the user logs-in into your instance, the user will
be asked to fill in her email address that will have subsequently to be
confirmed.

Notes on setting up the OAUTH scope
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In OAUTH, the user actually authorize the given service (i.e. your Invenio
installation) to act on behalf of the user within a certain *scope*. By default,
ORCID will authorize Invenio to only know the ORCID ID of the authenticating
user.

If you plan to build more advanced services, such as pushing and pulling
information with ORCID, you might wish to enable broader OAUTH scopes, so that,
upon authentication, your Invenio instance is actually able to perform them.

E.g. the INSPIRE service is currently using this scope configuration in their
``invenio.cfg``:

::

    orcid.REMOTE_SANDBOX_APP['params']['request_token_params'] = {
        'scope': '/orcid-profile/read-limited '
                 '/activities/update /orcid-bio/update'
    }

Upon login with your Invenio instance through ORCID, your users will be
presented then with a screen similar to the following one:

.. image:: /_static/authorization.png


Where to go from here?
----------------------
In this tutorial, we have presented how to integrate ORCID authentication
into your Invenio instance.

As a developer, you will be able to extract the ORCID ID of the authenticating
user from her user by querying the ``RemoteAccount`` table.

For exchanging information with ORCID, this highly depends on the data model
implemented in your instance and what type of information you plan to exchange
with ORCID.

`invenio-orcid`_ module is
currently being developed in order to make it easier for Invenio instances to
build information exchange with ORCID.
