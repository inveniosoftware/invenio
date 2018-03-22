..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Managing issues
===============

The purpose of `issue triage process
<https://en.wikipedia.org/w/index.php?title=Software_bug&redirect=no#Bug_management>`_
is to make sure all the Invenio issues and tasks are well described, sorted out
according to priorities into timely milestones, and that they have well assigned
a responsible person to tackle them. The triage process is done collectively by
the representatives of various Invenio distributed teams. The triage team
members make sure of the big picture, cross-consider issues and tasks among
interested services, help to note down, understand, prioritise, and follow-upon
them.

.. _every-issue-should-have-an-assignee:

1. **Every issue should have an assignee.** Issues without assignees are sad and
   likely to remain so. Each issue should have a driving force behind it.

.. _every-issue-should-have-a-milestone:

2. **Every issue should have a milestone.** Issues without milestones are sad
   and likely to remain unaddressed.

.. _use-additional-type-and-priority-labels:

3. **Use additional type and priority labels.** Helps to find related issues out
   quickly.

.. _use-additional-service-labels:

4. **Use additional service labels.** Helps to distinguish which issues are of
   utmost importance to which services. Helps to keep a service-oriented
   dashboard overview.

.. _nobody-in-sight-to-work-on-this-discuss-and-triage:

6. **Nobody in sight to work on this? Discuss and triage.** The triage team
   should take action if there is no natural candidate to work on an issue.

.. _no-time-to-realistically-tackle-this-use-someday-or-close:

7. **No time to realistically tackle this? Use "Someday" or close.** We don't
   want to have thousands of open issues. Issues from the someday open or closed
   pool can be revived later, should realistic manpower be found.


Triaging process
----------------

The process of triaging issues is being done continuously.  This
usually means that labels are being attached to issues, assignments
are being decided, progress is being tracked, dependencies being
clarified, questions being answered, etc.

The triaging team meets regularly (say once every 1-2 weeks) to go
over the list of open issues for any catch-up, follow-up, and
re-classification of issues with respect to milestones.

Issue labels
------------

The issues are attributed namespaced labels indicating the following
issue properties:

* type:

  - `t_bug`: bug fix
  - `t_enhancement`: new feature or improvement of existing feature

* priority:

  - `p_blocker`: highest priority, e.g. breaks home page
  - `p_critical`: higher priority, e.g. test case broken
  - `p_major`: normal priority, used for most tickets
  - `p_minor`: less priority, less visible user impact
  - `p_trivial`: lowest priority, cosmetics

* component:

  - `c_WebSearch`: search component
  - `c_WebSubmit`: submit component
  - etc

* status:

  - `in_work`: developer works on the topical branch
  - `in_review`: reviewer works on reviewing the work done
  - `in_integration`: integrator works on checking interplay with other services

* resolution:

  - `r_fixed`: issue fixed
  - `r_invalid`: issue is not valid
  - `r_wontfix`: issue will not be dealt with for one reason or another
  - `r_duplicate`: issue is a duplicate of another issue
  - `r_question`: issue is actually a user question
  - `r_rfc`: issue is actually an open RFC

* branch:

  - `maint-x.y`: issue applies to Invenio maint-x.y branch
  - `master`: issue applies to Invenio master branch
  - `next`: issue applies to Invenio next branch
  - `pu`: issue applies to Invenio pu branch

* version:

  - `v0.99.1`: issue was observed on version v0.99.1
  - `v1.1.3`: issue was observed on version v1.1.3
  - etc

The label types and values are coming from our Trac past and may be
amended e.g. to take into account new component names in Invenio v2.0.

Milestones and releases
-----------------------

Issues may be attributed milestones that are closely related with
feature-dependent and/or time-dependent release schedule of Invenio
releases.

There are two kinds of milestones: "release-oriented" milestones (say
v1.1.7) and "someday" milestones (say v1.1.x) for each given release
series (v1.1 in this case).  The release-oriented milestones may have
dates attached to them; the someday milestone may not.

Typically, a new issue is given (a) the closest milestone in the given
release series if its urgency is high, or (b) a later milestone in the
given release series depending on the estimated amount of work and
available resources, or is (c) left in the catch-all someday milestone
out of which the issue can be later cherry-picked and moved to one of
the concrete release-oriented milestones depending on available
resources.

Example: after Invenio v1.4.0 is released, all incoming bug reports
for this version will go to the "someday" milestone for this release
series, i.e. to "v1.4.x".  A new XSS vulnerability issue will go
straight to the next milestone "v1.4.1" because its release is urgent.
A typo in an English output phrase in the basket module will remain in
the someday milestone "v1.4.x" until it is picked for one of later
releases, say v1.4.7, depending on available resources in the basket
team.

The triaging team together with the release management team will
periodically review issues in a given release series and decide upon
the set of issues going into a concrete release-oriented milestone
(say these 15 issues for v1.4.1 milestone) after which the issue set
is freezed and a sprint may be co-organised to meet the target
deadline.  Once all the issues have been solved, a new Invenio bug-fix
release v1.4.1 is published and the release-oriented triaging cycle
starts anew with v1.4.2.

(Note that someday milestones are usually more useful for new feature
releases; they might remain relatively empty for bug fix releases.)
