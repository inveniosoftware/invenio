..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Security policy
===============

Reporting security issues
-------------------------

.. note:

    **Short version:** Alert us privately at
  `info@inveniosoftware.org <info@inveniosoftware.org>`_.

Normal bugs should be reported to the specific Invenio module's GitHub
repository. However, due to sensitive nature of security issues, we ask that
you do **not** report in a public fashion. This will allow us to distribute a
security patch before potential attackers look at the issue.

If you believe you've found a security issue in Invenio, please send a
description of the issue to
`info@inveniosoftware.org <mailto:info@inveniosoftware.org>`_. Mails sent to
this email address is logged in our request tracking system where Invenio
architects have access to them.

You will first receive an automated notification from the request tracking
system. Afterwards an Invenio architect will acknowledge the receipt (normally
within 1-2 *working days*).

Supported versions
------------------

Please see our :ref:`maintenance-policy`. Note that only supported versions
are guaranteed to receive security fixes, and we only investigate if a given
issue is affecting any of the currently supported versions of Invenio.

Disclosure of security issues
-----------------------------

Advance notification
~~~~~~~~~~~~~~~~~~~~

We will notify 2-5 days in advance about an upcoming security release and the
severity level of the issue. The notification will not disclose any information
about the issue except the severity level, and the sole purpose of the
notification is to aid organisations to ensure they have staff available to
handle the issue.

The notifications are sent to:

  - Chatroom: https://gitter.im/inveniosoftware/invenio
  - Mailing list: project-invenio-announce@cern.ch

**Time-sensitive issues**

In case the issue is particularly time-sensitive (e.g. known exploits in the
wild) we may omit the advance notification.

**Upstream libraries/frameworks**

If an issue reported to us is affecting another library/framework we may report
the issue privately to the maintainers of the affected library/framework.

Public announcement
~~~~~~~~~~~~~~~~~~~
On the day of the disclosure we take the following steps:

  1. Apply patches to the Invenio source code
  2. Issue new releases of Invenio and the affected modules to PyPI and/or
     NPM.
  3. Notify the chatroom and mailing list (see above).
  4. Post an entry to the `Invenio blog <https://inveniosoftware.org/blog/>`_.

Severity levels
---------------

We classify security issues according to the following severity levels:

- **Critical**
- **High**
- **Moderate**
- **Low**

The severity level is based on our self-calculated CVSS score for each specific
vulnerability. CVSS is an industry standard vulnerability metric. You can learn
more about CVSS at `NIST NVD <https://nvd.nist.gov/vuln-metrics/cvss>`_.

**Credit**

This security policy have drawn heavy inspiration from Django's
`security policy <https://docs.djangoproject.com/en/2.2/internals/security/>`_.
