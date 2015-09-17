web: inveniomanage runserver
cache: redis-server
worker: celery worker --purge -E -A invenio_celery.celery --loglevel=DEBUG --workdir=$VIRTUAL_ENV
workermon: flower --broker=redis://localhost:6379/1
indexer: elasticsearch --config=elasticsearch.yml --path.data="$VIRTUAL_ENV/var/data/elasticsearch"  --path.logs="$VIRTUAL_ENV/var/log/elasticsearch"
