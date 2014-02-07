# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

from invenio import config

## Broker settings
## ---------------
BROKER_URL = getattr(config, "CFG_BROKER_URL", "amqp://guest:guest@localhost:5672//")

# Extra modules with tasks which should be loaded
# The Invenio Celery loader automatically takes care of loading tasks defined
# in *_tasks.py files in 'invenio' package.
CELERY_INCLUDE = ["invenio.bibworkflow_workers.worker_celery"]

## Result backend
## --------------
CELERY_RESULT_BACKEND = getattr(config, "CFG_CELERY_RESULT_BACKEND", "redis://localhost/0")
CELERY_RESULT_SERIALIZER = getattr(config, "CFG_CELERY_RESULT_SERIALIZER", "msgpack")

## Routing
## -------
# ...

## Task execution
## --------------
CELERY_ALWAYS_EAGER = False
CELERY_IGNORE_RESULT = False
CELERY_TASK_SERIALIZER = getattr(config, "CFG_CELERY_TASK_SERIALIZER", "msgpack")

## Worker
## ------
CELERYD_MAX_TASKS_PER_CHILD = getattr(config, "CFG_CELERYD_MAX_TASKS_PER_CHILD", 1000)

## Error emails
## ------------
CELERY_SEND_TASK_ERROR_EMAILS = bool(getattr(config, "CFG_SITE_ADMIN_EMAIL_EXCEPTIONS", False))
try:
    ADMINS = [('', x.strip()) for x in getattr(config, "CFG_SITE_EMERGENCY_EMAIL_ADDRESSES", {})['*'].explode(",")]
except Exception:
    ADMINS = ()
SERVER_EMAIL = getattr(config, "CFG_SITE_ADMIN_EMAIL", "celery@localhost")
EMAIL_HOST = getattr(config, "CFG_MISCUTIL_SMTP_HOST", "localhost")
EMAIL_HOST_USER = getattr(config, "CFG_MISCUTIL_SMTP_USER", "")
EMAIL_HOST_PASSWORD = getattr(config, "CFG_MISCUTIL_SMTP_PASS", "")
EMAIL_PORT = getattr(config, "CFG_MISCUTIL_SMTP_PORT", "25")
EMAIL_USE_TLS = getattr(config, "CFG_MISCUTIL_SMTP_TLS", False)

## Scheduler
## ---------
CELERYBEAT_SCHEDULE = {
}
