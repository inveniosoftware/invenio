..  This file is part of Invenio
    Copyright (C) 2015, 2016 CERN.

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

Releases
========

Release numbering scheme
------------------------

Invenio stable releases use the classical major.minor.patchlevel
release version numbering scheme that is commonly used in the
GNU/Linux world and elsewhere.  Each release is labelled by::

     major.minor.patchlevel

release version number.  For example, a release version 4.0.1 means::

       4 - 4th major version, i.e. the whole system has been already
           4th times either fully rewritten or at least in its very
           essential components.  The upgrade from one major version
           to another may be rather hard, may require new prerequisite
           technologies, full data dump, reload and reindexing, as
           well as other major configuration adapatations, possibly
           with an important manual intervention.

       0 - 0th minor version, i.e. the first minor release of the 4th
           major rewrite.  (Increments go usually 4.1, 4.2, ... 4.9,
           4.10, 4.11, 4.12, ... until some important rewrite is done,
           e.g. the database philosophy dramatically changes, leading
           to a non-trivial upgrade, and then we have either higher
           4.x in the series or directly 5.0.0.)  The upgrade from one
           minor version to another may be laborious but is relatively
           painless, in that some table changes and data manipulations
           may be necessary but they are somewhat smaller in nature,
           easier to grasp, and possibly done by a fully automated
           script.

       1 - 1st patch level release to 4.0 series, fixing bugs in 4.0.0
           but not adding any substantially new functionality.  That
           is, the only new functionality that is added is that of a
           bug fix nature.  The upgrade from one patch level to
           another is usually very straightforward.

           (Packages often seem to break this last rule, e.g. Linux
           kernel adopting new important functionality (such as
           ReiserFS) within the stable 2.4.x branch.  It can be easily
           seen that it is somewhat subjective to judge what is
           qualitatively more like a minor new functionality and what
           is more like a patch to the existing behaviour.  We have
           tried to distinguish this with respect to whether the table
           structure and/or the technology change require small or
           large upgrade jobs and eventual manual efforts.)

So, if we have a version 4.3.0, a bug fix would mean to release 4.3.1,
some minor new functionality and upgrade would mean to release 4.4.0,
some important database structure rewrite or an imaginary exchange of
Python for Common Lisp would mean to release 5.0.0, etc.

We follow `semantic versioning <http://semver.org/>`_ and `PEP-0440
<https://www.python.org/dev/peps/pep-0440/>`_ release numbering practices.

Invenio v3.x
------------

*Not released yet; however a developer preview is available on GitHub.*

Invenio v3.0 will be released when the Invenio code base is fully split into a
set of standalone independent Python packages.

Invenio v2.x
------------

*Semi-stable codebase.*

Invenio v2.x code base is our new code base architecture that uses Flask web
development framework. The most important modules take fully profit from the new
architecture (e.g. search, deposit), however some modules still rely on previous
v1.x legacy code base (e.g. baskets). Therefore its production suitability
depends on your use case.

Released versions include:

Invenio v2.1:

* `v2.1.1 <https://github.com/inveniosoftware/invenio/releases/tag/v2.1.1>`_ - released 2015-09-01
* `v2.1.0 <https://github.com/inveniosoftware/invenio/releases/tag/v2.1.0>`_ - released 2015-06-16

Invenio v2.0:

* `v2.0.6 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.6>`_ - released 2015-09-01
* `v2.0.5 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.5>`_ - released 2015-07-17
* `v2.0.4 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.4>`_ - released 2015-06-01
* `v2.0.3 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.3>`_ - released 2015-05-15
* `v2.0.2 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.2>`_ - released 2015-04-17
* `v2.0.1 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.1>`_ - released 2015-03-20
* `v2.0.0 <https://github.com/inveniosoftware/invenio/releases/tag/v2.0.0>`_ - released 2015-03-04

Invenio v1.x
------------

*Stable codebase.*

Invenio v1.x code base is suitable for stable production. It uses legacy
technology and custom web development framework.

Released versions include:

Invenio v1.2:

* `v1.2.1 <https://github.com/inveniosoftware/invenio/releases/tag/v1.2.1>`_ - released 2015-05-21
* `v1.2.0 <https://github.com/inveniosoftware/invenio/releases/tag/v1.2.0>`_ - released 2015-03-03

Invenio v1.1:

* `v1.1.6 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.6>`_ - released 2015-05-21
* `v1.1.5 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.5>`_ - released 2015-03-02
* `v1.1.4 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.4>`_ - released 2014-08-31
* `v1.1.3 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.3>`_ - released 2014-02-25
* `v1.1.2 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.2>`_ - released 2013-08-19
* `v1.1.1 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.1>`_ - released 2012-12-21
* `v1.1.0 <https://github.com/inveniosoftware/invenio/releases/tag/v1.1.0>`_ - released 2012-10-21

Invenio v1.0:

* `v1.0.9 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.9>`_ - released 2015-05-21
* `v1.0.8 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.8>`_ - released 2015-03-02
* `v1.0.7 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.7>`_ - released 2014-08-31
* `v1.0.6 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.6>`_ - released 2014-01-31
* `v1.0.5 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.5>`_ - released 2013-08-19
* `v1.0.4 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.4>`_ - released 2012-12-21
* `v1.0.3 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.3>`_ - released 2012-12-19
* `v1.0.2 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.2>`_ - released 2012-10-19
* `v1.0.1 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.1>`_ - released 2012-06-28
* `v1.0.0 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.0>`_ - released 2012-02-29
* `v1.0.0-rc0 <https://github.com/inveniosoftware/invenio/releases/tag/v1.0.0-rc0>`_ - released 2010-12-21

Invenio v0.x
------------

*Old codebase.*

Invenio v0.x code base was developed and used in production instances
since 2002. The code base is interesting only for archaeological purposes.

Released versions include:

* `v0.99.9 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.9>`_ - released 2014-01-31
* `v0.99.8 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.8>`_ - released 2013-08-19
* `v0.99.7 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.7>`_ - released 2012-12-18
* `v0.99.6 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.6>`_ - released 2012-10-18
* `v0.99.5 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.5>`_ - released 2012-02-21
* `v0.99.4 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.4>`_ - released 2011-12-19
* `v0.99.3 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.3>`_ - released 2010-12-13
* `v0.99.2 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.2>`_ - released 2010-10-20
* `v0.99.1 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.1>`_ - released 2008-07-10
* `v0.99.0 <https://github.com/inveniosoftware/invenio/releases/tag/v0.99.0>`_ - released 2008-03-27
* `v0.92.1 <https://github.com/inveniosoftware/invenio/releases/tag/v0.92.1>`_ - released 2007-02-20
* `v0.92.0. <https://github.com/inveniosoftware/invenio/releases/tag/v0.92.0>`_ - released 2006-12-22
* `v0.90.1 <https://github.com/inveniosoftware/invenio/releases/tag/v0.90.1>`_ - released 2006-07-23
* `v0.90.0 <https://github.com/inveniosoftware/invenio/releases/tag/v0.90.0>`_ - released 2006-06-30
* `v0.7.1 <https://github.com/inveniosoftware/invenio/releases/tag/v0.7.1>`_ - released 2005-05-04
* `v0.7.0 <https://github.com/inveniosoftware/invenio/releases/tag/v0.7.0>`_ - released 2005-04-06
* `v0.5.0 <https://github.com/inveniosoftware/invenio/releases/tag/v0.5.0>`_ - released 2004-12-17
* `v0.3.3 <https://github.com/inveniosoftware/invenio/releases/tag/v0.3.3>`_ - released 2004-07-16
* `v0.3.2 <https://github.com/inveniosoftware/invenio/releases/tag/v0.3.2>`_ - released 2004-05-12
* `v0.3.1 <https://github.com/inveniosoftware/invenio/releases/tag/v0.3.1>`_ - released 2004-03-12
* `v0.3.0 <https://github.com/inveniosoftware/invenio/releases/tag/v0.3.0>`_ - released 2004-03-05
* `v0.1.2 <https://github.com/inveniosoftware/invenio/releases/tag/v0.1.2>`_ - released 2003-12-21
* `v0.1.1 <https://github.com/inveniosoftware/invenio/releases/tag/v0.1.1>`_ - released 2003-12-19
* `v0.1.0 <https://github.com/inveniosoftware/invenio/releases/tag/v0.1.0>`_ - released 2003-12-04
* `v0.0.9 <https://github.com/inveniosoftware/invenio/releases/tag/v0.0.9>`_ - released 2002-08-01
