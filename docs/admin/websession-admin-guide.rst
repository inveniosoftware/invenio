..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _websession-admin-guide:

WebSession Admin Guide
======================

+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| WARNING: THIS ADMIN GUIDE IS NOT FULLY COMPLETED                                                                                                                                                                                                                                                                                                                                                   |
+====================================================================================================================================================================================================================================================================================================================================================================================================+
| This Admin Guide is not yet completed. Moreover, some admin-level functionality for this module exists only in the form of manual recipes. We are in the process of developing both the guide as well as the web admin interface. If you are interested in seeing some specific things implemented with high priority, please contact us at info@invenio-software.org. Thanks for your interest!   |
+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Guest User Sessions
-------------------

Guest users create a lot of entries in Atlantis Institute of Fictive
Science tables that are related to their web sessions, their search
history, personal baskets, etc. This data has to be garbage-collected
periodically. This is done via a bibsched program, the *Invenio Gargabe
Collector* (**InvenioGC**):

    ::

           $ inveniogc -s 1d


The Invenio Gargabe Collector can be used for keeping clean and slim
other areas of Invenio, too:

    ::

        Usage: /opt/cds-dev/bin/inveniogc [options]
        Command options:
          -l, --logs            Clean up/compress old logs and temporary files.
          -g, --guests          Clean up expired guest user related information. (default if nothing is specified)
          -d, --documents       Clean up delete documents and revisions older than 3650 days
          -a, --all             Calls every cleaning action.
        Scheduling options:
          -u, --user=USER       User name to submit the task as, password needed.
          -t, --runtime=TIME    Time to execute the task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26
          -s, --sleeptime=SLEEP Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d
        General options:
          -h, --help            Print this help.
          -V, --version         Print version information.
          -v, --verbose=LEVEL   Verbose level (0=min, 1=default, 9=max).


You can use InvenioGC for cleaning old logs (e.g. BibSched task logs)
and temporary files, by specfying the ``--logs`` option on the command
line, or very old revisions of documents, by specfying ``--documents``.

Please see also the `HOWTO
Run </help/admin/howto-run>`__ guide.
