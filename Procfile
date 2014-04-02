web: inveniomanage runserver
cache: redis-server
worker: celery worker --purge -E -A invenio.celery.celery --loglevel=DEBUG --workdir=$VIRTUAL_ENV
workermon: flower --broker=redis://localhost:6379/1
