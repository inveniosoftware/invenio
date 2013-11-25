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


def default_config(config):
    """
    Provide default configuration for Celery
    """
    ## Broker settings
    ## ---------------
    config.setdefault("BROKER_URL", "redis://localhost:6379/1")

    # Extra modules with tasks which should be loaded
    # The Invenio Celery loader automatically takes care of loading tasks
    # defined in *_tasks.py files in 'invenio' package.
    config.setdefault("CELERY_INCLUDE", [
        #"invenio.celery.tasks",
        #"invenio.bibworkflow_workers.worker_celery",
    ])

    ## Result backend
    ## --------------
    config.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    config.setdefault("CELERY_RESULT_SERIALIZER", "msgpack")

    ## Routing
    ## -------
    # ...

    ## Task execution
    ## --------------
    config.setdefault("CELERY_ALWAYS_EAGER", False)
    config.setdefault("CELERY_IGNORE_RESULT", False)
    config.setdefault("CELERY_TASK_SERIALIZER", "msgpack")

    ## Worker
    ## ------
    config.setdefault("CELERYD_MAX_TASKS_PER_CHILD", 1000)

    ## Error emails
    ## ------------
    config.setdefault("CELERY_SEND_TASK_ERROR_EMAILS", False)

    if "CFG_SITE_EMERGENCY_EMAIL_ADDRESSES" in config:
        try:
            ADMINS = [
                ('', x.strip()) for x in
                config["CFG_SITE_EMERGENCY_EMAIL_ADDRESSES"]['*'].explode(",")
            ]
            config.setdefault("ADMINS", ADMINS)
        except Exception:
            pass

    config.setdefault(
        "SERVER_EMAIL", config.get("CFG_SITE_ADMIN_EMAIL", "celery@localhost")
    )
    config.setdefault(
        "EMAIL_HOST", config.get("CFG_MISCUTIL_SMTP_HOST", "localhost")
    )
    config.setdefault(
        "EMAIL_HOST_USER", config.get("CFG_MISCUTIL_SMTP_USER", "")
    )
    config.setdefault(
        "EMAIL_HOST_PASSWORD", config.get("CFG_MISCUTIL_SMTP_PASS", "")
    )
    config.setdefault(
        "EMAIL_PORT", config.get("CFG_MISCUTIL_SMTP_PORT", "25")
    )
    config.setdefault(
        "EMAIL_USE_TLS", config.get("CFG_MISCUTIL_SMTP_TLS", False)
    )

    ## Scheduler
    ## ---------
    config.setdefault("CELERYBEAT_SCHEDULE", {})

    return config
