Overview
========
 
What is a maintainer?
---------------------

(Clearly inspired by the `Docker
<https://github.com/docker/docker/blob/master/MAINTAINERS>`_ project)


There are different types of maintainers in the Invenio project, with
different responsibilities, but all of them have this **rights and 
responsibilities** in common:

1. Have merge rights in the repositories they are maintainers of, but no pull
   request can be merged until all checks have passed and at least one
   maintainer signs off. (If one maintainer is making a pull request another
   maintainer should sign off, this will prevent self merges)
2. Have the final word about architectural or API significant changes,
   ensuring always that the [Invenio deprecation policies](#orgheadline1) are
   followed.
3. Will review pull requests within a reasonable time range, offering
   constructive and objective comments in a respectful manner.
4. Will participate in feature development and bug fixing, proactively
   verifying that the nightly builds are successful.
5. Will prepare releases following the Invenio standards.
6. Will answer questions and help users in the `Invenio Gitter chat room
   <https://gitter.im/inveniosoftware/invenio>`_.
7. 

Core maintainers
----------------

The core maintainers are the architectural team who shapes and drives the
Invenio project and, as a consequence, they are the ultimate reponsible of
the success of it. 

They are ghostbusters of the project: when there's a problem others can't
solve, they show up and fix it with bizarre devices and weaponry.
Some maintainers work on the project Invenio full-time, although this is not
a requirement.

For each release (including minor releases), a "release captain" is assigned
by the core maintainers from the pool of module maintainers. Rotation is
encouraged across all maintainers, to ensure the release process is clear
and up-to-date. The release can't be done without a core maintainer
approvals. 

Any of the core maintainers can propose new module maintainers at any time,
see `Becoming a maintainer`_ for more information.

Module maintainers
------------------

Module maintainers are exceptionally knowledgeable about some but not
necessarily all areas of the Invenio project, and are often selected due to
specific domain knowledge that complements the project (but a willingness to
continually contribute to the project is most important!).

The duties of a module maintainer are very similar to those of a core
maintainer, but they are limited to modules of the Invenio project where the
module maintainer is knowledgeable.
hose who have write
access to the Invenio-X repository**. All maintainers can review pull
requests and add LGTM labels as appropriate, in fact everyone is encourage
to do so!

Becoming a maintainer
---------------------

Don't forget: being a maintainer is a time investment. Make sure you will
have time to make yourself available. You don't have to be a maintainer to
make a difference on the project!

Usually to become a module maintainer, one of the core maintainers makes a
pull request in the opensource project to propose the new maintainer. This
pull request needs the approval from other core maintainer and from at least
one of the module maintainers (if the module has any).

To become a core maintainer the process is slightly different. Before being
a core maintainer canditate one needs the make sustained contributions to
the project over a period of time (usually more than 3 months), show
willingness to help Invenio users on GitHub and in the `Invenio Gitter chat
room <https://gitter.im/inveniosoftware/invenio>`_, and, overall, a friendly
attitude.
Once the avobe is out of question, the core maintainer who sponsors the
future one will present him to the team and, if he gets the confiance of
all of the current core maintaners, his sponsor will make a pull
request to the opensource repository adding his name to the list.

Stepping down as maintainer
---------------------------

Stepping down as a maintainer is done also via pull request to the
opensource GitHub repository.
It can be the maintainer himself who makes the pull request and, as before,
this type of pull requests need to be approved by one core maintainer and at
least one of the module maintainers (if any). 

Exceptionally the core maintainers can propose another maintainer, core or
module maintainer, to stepdown. All core maintainers must unanimously agree
before making any pull request.

In both cases, we encourage the maintainers to give a brief explanation of
their reasons to step down.
