..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _maintenance-policy:

Maintenance Policy
==================

Our goal is to ensure that all Invenio releases are supported with bug and
security fixes for minimum one year after the release date and possibly longer.
We further aim at one Invenio release with new features every 6 months. We
strive our best to ensure that upgrades between minor versions are fairly
straight-forward to ensure users follow our latest releases.

The maintenance policy is striving to strike a balance between maintaining a
rock solid secure framework while ensuring that users migrate to latest
releases and ensuring that we have enough resources to support the maintenance
policy.

Types of releases
-----------------

**Major release**: Major versions such as ``v3`` allows us to introduce
major new features and make significant backward incompatible changes.

**Minor releases**: Minor versions such as ``v3.1`` allows us to introduce
new features, make minor backward incompatible changes and remove deprecated
features in a progressive manner.

**Patch releases**: Patch versions such as ``v3.0.1`` allows us fix bugs and
security issues in a manner that allow users to upgrade immediately without
breaking backward compatibility.

Policy
------

A minor release ``A.B`` (e.g. v3.0) is supported with bug and security fixes
(via patch releases) until the release of ``A.B+2`` (e.g. v3.2) and minimum one
year.

We may make exceptions to this policy for very serious security bugs.

End of life dates
-----------------

Following is an overview of future end of life (EOL) dates for currently
maintained releases:

+---------+-------------------+------------------+
| Release | Earliest EOL Date | Maintained until |
+=========+===================+==================+
| v3.3.x  | 2021-05-18        | v3.5.0           |
+---------+-------------------+------------------+
| v3.2.x  | 2020-12-20        | v3.4.0           |
+---------+-------------------+------------------+

End of life releases
--------------------

The following releases have reached end of life:

+---------+--------------+------------+
| Release | Release Date | EOL Date   |
+=========+==============+============+
| v3.1.x  | 2019-03-31   | 2020-05-18 |
+---------+--------------+------------+
| v3.0.x  | 2018-06-07   | 2019-12-20 |
+---------+--------------+------------+
| v2.x.y  |              | 2018-06-07 |
+---------+--------------+------------+
| v1.x.y  |              | 2018-06-07 |
+---------+--------------+------------+
