..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.
    Copyright (C) 2017 TIND.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Services
========

In this documentation we will provide you an overview of the different services needed to run invenio.
We will explain what are their roles in the global architecture, and why they have been selected.

Invenio 3 has been designed to be highly scalable, low latency, and fast, therefore all the underlying services need to be respecting the same goals.

Here is an overview of the system:

.. graphviz::

    digraph {
        {
        "PostgreSQL" [shape ="cylinder"];
        "Elasticsearch" [shape="hexagon"];
        }
      "Invenio3" -> "Elasticsearch" [ label = "Search"];
      "Elasticsearch" -> "PostgreSQL" [ label = "Index DB content" ];
      "Invenio3" -> "PostgreSQL" [label = "CRUD"];
      "RabbitMQ" -> "Invenio3" [dir=both label = "Write/Read messages"];
      "RabbitMQ" -> "Celery" [dir=both label = "Write/Read messages"];
      "Invenio3" -> "Redis" [label = "Cache data"];
      "Nginx" -> "Invenio3" [label = "Serve content"];
      "HAProxy" -> "Nginx" [label = "Balance load"];
      "User" -> "HAProxy" [label = "Browse Invenio"];
    }


Elasticsearch
-------------

Invenio 3 is an external search engine service. It will take care of everything related to the search as indexing, ranking, searching.
It contains and ingest document under the form of JSON, but it is able to respect type. To be able to determine the data structure that you want to ingests and the type of the containing information, it requires you to create a mapping.

**A mapping** is a simple JSON structure which describes how should look an indexed document.

For example:

.. code-block:: python

   {
      "user" : {
        "properties" : {
          "name" : {
            "properties" : {
              "first" : {
                "type" : "string"
              }
            }
          }
        }
      }
   }

You can basically store in Elasticsearch almost everything, so it also means that you can make searchable almost any data on your Invenio 3 instances.

Elastic search is highly scalable, which means that it can spread the load on several instances of elasticsearch.
In production you will always try to have a dedicated Elasticsearch cluster. Indeed, without it, it is not revealing its full power. Each node is running several instances of Elasticsearch, this unit is named "Shards" it can either be replica instances or production ones.

This allow Invenio 3 to handle really large amount of records and keep the search time low.
You can find more information here_.

.. _here: https://www.elastic.co/guide/en/elasticsearch/reference/current/getting-started.html

Summary of elasticsearch position in Invenio3:

.. graphviz::

    digraph {
        {
        "PostgreSQL" [shape ="cylinder"];
        "Elasticsearch" [shape="hexagon"];
        }
      "Invenio3" -> "Elasticsearch" [ label = "Search"];
      "Elasticsearch" -> "PostgreSQL" [ label = "Index DB content" ];
    }

PostgreSQL
----------
PostgreSQL is currently the database selected for Invenio 3, it is replacing mysql/mariadb in Invenio 1, the version must be 9.4 or newer.

Elasticsearch is used to index and search data, but it is not here to persistently store data. It also doesn't include a transactional system to manage concurrent requests. We use a database to store in a persistent way data, Elasticsearch would feed from the database, before to be able to answer search requests.

PostgreSQL has been selected for its really high performances, even if it's not really scalable the transactions here will be mostly "write" operation, most of the read operation will be delegated to Elasticsearch.

PostgreSQL is the perfect fit for the Invenio 3, indeed, a everything is JSON, from the mappings to the schema and documents, and this database has all the necessary feature to be able to handle this data type efficiently. Most of the data are not represented as usual where we have a column per field. In the case of Invenio 3 the documents are JSON stored as JSON objects. Even if it not composed of column PostgreSQL is able to do operation of this kind of object.

PostgreSQL is abstracted in Invenio 3 code thanks to the use of the framework SQLAlchemy, it means that you don't need to know how to use PostgreSQL but python would be enough.

Summary of PostgreSQL in Invenio 3:

.. graphviz::

    digraph {
        {
        "PostgreSQL" [shape ="cylinder"];
        "Elasticsearch" [shape="hexagon"];
        }
      "Elasticsearch" -> "PostgreSQL" [ label = "Index DB content" ];
      "Invenio3" -> "PostgreSQL" [label = "CRUD"];
    }


RabbitMQ
--------

RabbitMQ is a messaging queue service which is used to make different processes communicating between each others by letting them exchange messages.

RabbitMQ is highly scalable and can make processes communicate between several nodes, it uses a system of broker to transmit the messages between the applications. It can handle a lot of messages in a fast and efficient way.

In the case of Invenio 3 the messaging queue is used to transmit messages between Invenio and Celery nodes.

Summary of RabbitMQ in Invenio 3:

.. graphviz::

    digraph {
      "RabbitMQ" -> "Invenio3" [dir=both label = "Write/Read messages"];
      "RabbitMQ" -> "Celery" [dir=both label = "Write/Read messages"];
    }


Celery/Flower
-------------

Celery is an asynchronous task queue, that can also act as a scheduler for reccuring tasks. In our case the tasks are transmitted thanks to RabbitMQ under the form of messages. Celery is reading in the message queue which tasks need to be executed, then it execute it, and write the result back in the queue.

Celery in Invenio 3 is used in different cases:

* The first one is for heavy process, we can't let a user hanging for a long time. So when we have an operation that should take a long time to execute it is sent to Celery to be executed as soon as possible.

* The second one is for reccuring tasks, it replaces BibSched in Invenio 1. Different modules in Invenio 3 can register tasks that will be executed when needed. An example can be the harvesting of some records.

Celery is working with RabbitMQ and can be highly scalable, the idea is that you can have as many computing nodes running celery connected to the messaging queue. It is then really easy to add more nodes if the load it too high.

It can be hard to know what is running in Celery which tasks did succeed and which one failed, therefore there is a tool that can help to monitor what is happening. It is named **Flower** it takes the form of a website that gives you an overview of what is happening.

Summary of Celery in Invenio 3:


.. graphviz::

    digraph {
      "RabbitMQ" -> "Invenio3" [dir=both label = "Write/Read messages"];
      "RabbitMQ" -> "Celery" [dir=both label = "Write/Read messages"];
    }

Redis
-----

Redis is a key value service that allows to store information that need to be retrieved with a really high access speed. It can be used to cache data, or as a messaging queue like RabbitMQ, it is currently possible to communicate with celery thanks to Redis instead of RabbitMQ.

In Invenio we mostly use it for caching data, and example is to cache the user session, it is way faster to store the data in Redis than in the database. Even if Redis can have some persistency we would prefer the database to store such data.

Redis is again a service which is really scalable it is possible to have it on separated nodes that will be dedicated to it. It can be really helpful as Redis will have a high consumption in memory, but really small need in terms of computing power.

Summary of Redis in Invenio 3:

.. graphviz::

    digraph {
      "Invenio3" -> "Redis" [label = "Cache data"];
    }

Nginx
-----

Nginx is a webserver that is extremely efficient for serving static files. It is used as a reverse proxy between the user and Invenio 3. It adds some logic and features linked to the connexion handling and the distribution of the requests. For example nginx can handle DDOS attacks.

Nginx will make the link between the front end of Invenio 3 that will be served as static files when possible and the RESTFUL api behind.


HAProxy
-------

HAProxy is a load balancer that will distribute HTTP requests amongst several servers. It is not mandatory, but it can be really useful if you have a really high traffic website. The idea is to spread the load to several webserver. This way we can avoid the saturation and then the unavailability of the webserver.



Summary of Nginx and HAProxy in Invenio 3:

.. graphviz::

    digraph {
      "HAProxy" -> "Nginx" [label = "Balance load"];
      "User" -> "HAProxy" [label = "Browse Invenio"];
    }
