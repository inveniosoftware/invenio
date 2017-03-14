Understanding branches
======================

The official Invenio repository contains several branches for
maintenance and development purposes.  We roughly follow the usual git
model as described in
`man 7 gitworkflows <http://www.kernel.org/pub/software/scm/git/docs/gitworkflows.html>`_
and elsewhere.

In summary, the new patchlevel releases (X.Y.Z) happen from the ``maint``
branch, the new minor feature releases (X.Y) happen from the ``master``
branch, and new major feature releases (X) happen after they mature in the
optional ``next`` branch.  A more detailed description follows.

``maint``
~~~~~~~~~

This is the maintenance branch for the latest stable release.  There
can be several maintenance branches for every release series
(**maint-0.99**, **maint-1.0**, **maint-1.1**), but typically we use only
``maint`` for the latest stable release.

The code that goes to the maintenance branch is of bugfix nature
only.  It should not alter DB table schema, Invenio config file
schema, local configurations in the ``etc`` folder or template function
parameters in a backward-incompatible way.  If it contains any new
features, then they are switched off in order to be fully compatible
with the previous releases in this series.  Therefore, for
installations using any Invenio released X.Y series, it should be
always safe to upgrade the system at any moment in time by (1) backing
up their ``etc`` folder containing local configuration, (2) installing
the corresponding ``maint-X.Y`` branch updates, and (3) rolling back the
``etc`` folder with their customizations.  This upgrade process will be
automatized in the future via special ``inveniomanage`` options.

``master``
~~~~~~~~~~

The ``master`` branch is where the new features are being developed and
where the new feature releases are being made from.  The code in
``master`` is reviewed and verified, so that it should be possible to
make a new release out of this branch almost at any given point in
time.  However, Invenio installations that would like to track this
branch should be aware that DB table definitions are not frozen and
may change, the config is not frozen and may change, etc, until the
release time.  So while ``master`` is relatively stable for usage, it
should be treated with extreme care, because updates between day D1
and day D2 may require DB schema and ``etc`` configuration changes that
are not covered by usual ``inveniomanage`` update statements, so people
should be prepared to study the differences and update DB schemata and
config files themselves.
