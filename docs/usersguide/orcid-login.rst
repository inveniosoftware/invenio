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
the `invenio-orcid <http://invenio-orcid.readthedocs.io/>`_ module that is
currently subject to important changes.

Invenio support out-of-the-box authentication through the
`OAUTH <https://en.wikipedia.org/wiki/OAuth>`_ protocol, which is actually
used by the ORCID service to offer authentication.

Registering an ORCID member API client application
==================================================
In order to integrate your Invenio instance with ORCID the first step is to
`apply for API keys
<https://orcid.org/content/register-client-application-sandbox>`_ to access the
ORCID Sandbox.

Please, follow the official ORCID documentation for this part.

After successful application for an API client application key you should
receive in your inbox an email with your ``Client ID`` and ``Client secret``.
You will need this information when configuring Invenio in the next step.


Notes on the redirect URI
-------------------------
As part of the OAUTH authentication process, after the user will have
authenticated on
the ORCID site, the user will be redirected to a given page on the Invenio side.
ORCID requires to provide a list of authorized URI prefixes that could be
allowed for
this redirection to happen.

Depending on the ``SERVER_NAME`` used to configure the Invenio installation, you
should fill
this parameter with:

    ``https://<SERVER_NAME>/oauth/authorized/orcid/``



Enabling OAUTH+ORCID in your Invenio instance
=============================================


Notes on setting up the OAUTH scope
-----------------------------------

Where to go from here?
======================
