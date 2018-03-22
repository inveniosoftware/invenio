..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _setting-up-your-environment:

Setting up your development environment
=======================================
Some rules should be applied when developing for Invenio. Here are some hints
to set up your environment so these rules will be respected.

Git
---

Set up git
~~~~~~~~~~

Git should be aware of your name and your e-mail address. To do so, run these
commands:

.. code-block:: bash

    git config --global user.name "Nice Unicorn"
    git config --global user.email "nice@unicorn.com"


Editor
------

The most important rules are to make your editor print 4 spaces for indentation
(instead of tabs) and limit the number of characters per line to 79.

Then, you can add automatic PEP8 checks if you want.
