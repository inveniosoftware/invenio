""" Elasticsearch extension for Invenio."""

from backend import ElasticSearchWrapper
from query_handler import QueryHandler
from results_handler import ResultsHandler


def index_record(sender, recid):
    """
    Index a given record.

    Used to connect to signal.

    :param recid: [int] recid to index
    """
    from .tasks import index_records
    return index_records.delay(sender, recid)


def create_index(sender, *args, **kwargs):
    from flask import current_app
    es = current_app.extensions.get("elasticsearch")
    es.create_index()


def drop_index(sender, *args, **kwargs):
    from flask import current_app
    es = current_app.extensions.get("elasticsearch")
    es.delete_index()


def setup_app(app):
    """Set up the extension for the given app."""
    es = ElasticSearchWrapper(app)

    # initiate the query handler
    es.set_query_handler(QueryHandler())

    # initiate the results handler
    es.set_results_handler(ResultsHandler())

    # initiate the enhancer FIXME initiate it here
    # es.set_enhancer(Enhancer())

    packages = app.extensions["registry"]["packages"]
    packages.register("invenio.ext.elasticsearch")
    from invenio.base import signals
    signals.record_after_create.connect(index_record)
    from invenio.base.scripts.database import recreate, drop, create
    signals.pre_command.connect(drop_index, sender=drop)
    signals.post_command.connect(create_index, sender=create)
    signals.pre_command.connect(drop_index, sender=recreate)
    signals.post_command.connect(create_index, sender=recreate)
