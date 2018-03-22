..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Merging pull requests
=====================

.. _check-it-from-the-helicopter:

1. **Check it from the helicopter.** If it ain’t green, it ain’t finished. If it
   ain’t understandable, it ain’t documented.

.. _beware-of-inter-module-relations:

2. **Beware of inter-module relations.** Changing API? Perhaps this pull request
   may break other modules. Check outside usage. Check the presence of
   ``versionadded``, ``versionmodified``, ``deprecated`` docstring directives.

.. _beware-of-inter-service-relations:

3. **Beware of inter-service relations.** Changing pre-existing tests? Perhaps
   this pull request does not fit the needs of other Invenio services.

.. _avoid-self-merges:

6. **Avoid self merges.** Each pull request should be seen by another pair of
   eyes. Was it authored and reviewed by two different persons? Good. Were the
   two different persons coming from two different service teams? Better.
