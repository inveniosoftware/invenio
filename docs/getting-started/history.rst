..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

History
=======

From software to framework
--------------------------
Invenio v3 is a completely new framework that has been rewritten from scratch.
Why such a dramatic decision? To understand why the rewrite
was necessary we have to go back to when Invenio was called CDSWare, back to
August 1st 2002 when the first version of Invenio was released.

In 2002:

* First iPod had just hit the market (Nov 2001).
* The Budapest Open Access Initiative had just been signed (Feb, 2002).
* JSON had just been discovered (2001).
* Python 2.1 had just been released (2001).
* Apache Lucene had just joined the Apache Jakarta project (but not yet an
  official top-level project).
* MySQL v4.0 beta was released and did not even have transactions yet.
* Hibernate ORM was released.
* The first DOI had just been assigned to a dataset.

Following products did not even exists:

* Apache Solr (2004)
* Google Maps (2005)
* Google Scholar (2004)
* Facebook (2007)
* Django (2005)

A lot has happen since 2002. Many problems that Invenio originally had to deal
with now have open source off-the-shelf solutions available. In particular two
things happen:

* Search become pervasive with the exponential growth of data collected and
  created on the internet every day, and open source products to solve handles
  these needs like Elasticsearch became big business.
* Web frameworks for both front-end and back-end made it significant faster to
  develop web applications.

In addition to above technological changes, it also started to become more and
more difficult to adapt Invenio v1 to all the different use cases we wanted
to support. Preservation archives have vastly different requirements from
aggregators which have vastly different requirements from research data
management systems. We further started to see performance problems with larger
and larger number of records.

Last but not least, we had many uses cases where it was no longer beneficial
to store the records in MARC21, but instead adopt either newer or custom
data model.

All in all, new technologies, an aging product showing its cracks,
slow development and a wish to have other data models was key determining
factors in deciding to start from scratch and implement a framework rather than
a software application.

What happened to Invenio v2?
----------------------------
Initial in 2011 we started out on creating a hybrid application which would
allow us to progressively migrate features as we had the time. In 2013 we
launched Zenodo as the first site on the v2 development version which among
other things featured Jinja templates instead of the previous Python based
templates.

In theory everything was sound, however over the following years it became very
difficult to manage the inflow of changes from larger and larger teams on the
development side and operationally proved to be quite unstable compared to v1.

Last but not least, Invenio v1 was built in a time where the primary need was
publication repositories and v2 inherited this legacy making it difficult to
deal with very large research datasets.

Thus, in late 2015 we were being slowed so much down by our past legacy that we
saw no other way that starting over from scratch if we were to deal with the
next 20 years of challenges.
