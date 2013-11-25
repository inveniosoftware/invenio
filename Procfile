web: inveniomanage runserver
cache: redis-server
worker: celeryd -E -A invenio.celery.celery --loglevel=INFO --workdir=$VIRTUAL_ENV
workermon: flower --broker=redis://localhost:6379/1
