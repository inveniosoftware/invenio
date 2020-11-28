Statistics bundle (beta)
------------------------

.. note::

    This bundle is in beta. The modules are being used in production systems
    but are still missing some minor changes as well as documentation.

The statistics bundle contains all modules related to counting statistics such
as file downloads, record views or any other type of events. It supports the
COUNTER Code of Practice as well as Making Data Count Code of Practice
including e.g. double-click detection.

Included modules:

- `invenio-stats <https://invenio-stats.readthedocs.io>`_
    - Event collection, processing and aggregation in time-based indicies in
      Elasticsearch.
- `invenio-queues <https://invenio-queues.readthedocs.io>`_
    - Event queue management module.
- `counter-robots <https://counter-robots.readthedocs.io>`_
    - Module providing the list of robots according to the COUNTER Code of
      Practice.
