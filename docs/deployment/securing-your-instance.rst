..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _securing-your-instance:

Securing your instance
======================

Invenio has a core principle to always have secure defaults for settings, thus
we have already done a lot in order to secure your installation. It is however
still important to be aware of some important settings and risks.

Secret key
----------
Probably the most important security measure is to have a strong random secret
key set for you Invenio instance. The secret key is used for instance to sign
user session ids and encrypt certain database fields.

The secret key must be kept secret. If the key is leaked or stolen somehow, you
should immediately change it to a new key.

.. code-block:: python

    # config.py
    SECRET_KEY = '..put a long random value here..'

Good practices:

- Never commit your secret key in the source code repository (or any other
  password for that sake).
- Use different secret keys for different deployments (testing, staging,
  production)

Allowed hosts
-------------
Invenio has a configuration option called ``APP_ALLOWED_HOSTS`` which controls
which hosts/domain names that can be served. A client request to a web server
usually includes the domain name in the ``Host`` HTTP header:

.. code-block:: python

    GET /
    Host: example.org
    ...

The web server uses that for instance to host several website on the same
domain. Also, the host header is usually used in a load balanced environment
to generate links with the right domain name.

An attacker has full control of the host header and can thus change it to
whatever they like, and for instance have the application generate links to a
completely different domain.

Normally your load balancer/web server should only route requests with a
white-listed set of host to your application. It is however very easy to
misconfigure this in your web server, and thus Invenio includes a protective
measure.

Simply set ``APP_ALLOWED_HOSTS`` to a list of allowed hosts/domain names:

.. code-block:: python

    # config.py
    APP_ALLOWED_HOSTS = ['www.example.org']

Number of proxies
-----------------
Invenio is commonly used with both a load balancer and a web server in front
of the application server. The load balancer and web server both works as
proxies, which means that the clients remote address usually get's added in
the ``X-Forwarded-For`` HTTP header. Invenio will automatically extract the
clients IP address from the HTTP header, however to prevent clients from doing
IP spoofing you need to specify exactly how many proxies you have in front
of you application server:

.. code-block:: python

    # config.py
    WSGI_PROXIES = 2
