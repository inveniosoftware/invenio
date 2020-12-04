..
    This file is part of Invenio.
    Copyright (C) 2018-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _invenio-modules:

.. _bundles:

Module Reference
================

Invenio is a highly modular framework with many modules that provide various
different functionality. We are packing related modules into bundles which is
released together at the same time.

Each module has a separate documentation which you can find linked below.

.. toctree::
   :maxdepth: 2

   base
   auth
   metadata
   files
   statistics
   deposit
   alpha
   utilities
   scaffolding
   documentation


Notes on license
----------------
Invenio is undergoing a change of license from GPLv2 to MIT License in most
cases. Thus, you may especially for alpha and beta modules see that the license
is still GPL v2 in the source code. This will be changed to MIT License for
all repositories before being finally released. The only module we are
currently aware of that can not be converted is Invenio-Query-Parser, which
has a dependency on a GPL-licensed library. Invenio-Query-Parser is however not
needed by most installations, as it only provides an Invenio v1.x compatible
query parser.
