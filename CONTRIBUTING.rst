==============
 Contributing
==============

Bug reports, feature requests, and code contributions are encouraged
and welcome!

Bug reports and feature requests
--------------------------------

If you find a bug or have a feature request, please search for
`already reported problems
<https://github.com/inveniosoftware/invenio/issues>`_ before
submitting a new issue.

Code contributions
------------------

We follow typical `GitHub flow
<https://guides.github.com/introduction/flow/index.html>`_.

1. Fork this repository into your personal space.
2. Start a new topical branch for any contribution.  Name it sensibly,
   say ``improve-fix-search-user-preferences``.
3. Test your branch on a local site.  If everything works as expected,
   please `sign your commits
   <http://invenio-software.org/wiki/Tools/Git/Workflow#R2.Remarksoncommitlogmessages>`_
   to indicate its quality.
4. Create `logically separate commits
   <http://invenio-software.org/wiki/Tools/Git/Workflow#R1.Remarksoncommithistory>`_
   for logically separate things.
5. Please add any ``(closes #123)`` or ``(addresses #123)`` directives
   in your commit log message if your pull request closes or addresses
   an open issue.
6. Issue a pull request.  If the branch is not quite ready yet, please
   indicate ``WIP`` (=work in progress) in the pull request title.

Developer Guidelines
--------------------

Here is more detailed checklist of things to do when contributing code
to Invenio.

1. **Before starting any wider-impact changes, submit a ticket and use a
   discussion channel.**

   * Found a bug in a module and have a fix for it?  Great, please
     jump right in!

   * Have a new feature request or thinking of a new facility that
     would impact several modules?  Submit a ticket and discuss the
     change before starting any implementation.

   * Small intra-module changes?  Discuss even in small circles with
     the module maintainer.

   * Big inter-module changes?  Discuss in wider circle among module
     maintainers and lead developers.  Take advantage of the weekly
     developer forum.

   * Ensure there is a consensus about functionality and design before
     starting any implementation.

2. **Publish your code under GNU General Public License.**

   * Use GNU General Public License header following our usual style.
     Update copyright years.

   * If you include any code, style, or icons created by others, check
     the original license information to make sure it can be included.
     Do not forget to acknowledge the original author in the THANKS
     file.  When appropriate, commit in the original author's name,
     and commit your changes on top of them.

   * Willing to include your code under CERN copyright?  Please send
     an email about this to the Lead Developer.  Otherwise add a new
     copyright line for your institution in the files you have
     touched.

3. **Choose good starting point to build your topical branch upon.**

   * Fixing a bug in a given version?  Start from ``maint-x.y``.  Name
     your topical branch ``johndoe/999-bibfoo-fix-xyzzy`` using ticket
     number and a short branch description.

   * Introducing a new feature?  Always start from ``master``.

   * Must introduce new feature to ``maint-1.1``?  Really?  OK, so be
     it, but make it configurable via new ``CFG_BIBFOO_XYZZY``
     configuration variable.  Do not rely on its existence, since
     people can upgrade/downgrade within ``v1.1.x`` point releases
     frequently.  Have it imported in a try/except manner and provide
     fallback for older point releases. Example:
     ``CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_MISC`` in `47e4a33
     <https://github.com/inveniosoftware/invenio/commit/47e4a3364a9c84942fe9cddc88530466195663a6>`_.

   * Introducing a new experimental feature?  Start from ``next``.

4. **Make things easily configurable and reusable by others.**

   * Need some feature that may break existing functionality used by
     other production sites?  Need some feature that other production
     sites may want to switch off?  Take care and make things
     configurable to be able to easily share the code.

   * Use ``get_tag_from_name('journal title')`` vs hard-coded
     ``773__p``.

   * Enable/disable custom features via role-based access control
     system, e.g. action ``usebaskets``.

   * Ensure configurability of functionality via ``CFG_BIBFOO_XYZZY``
     variables.

   * Ensure configurability of code via ``pluginutils``.

   * Writing service-specific code or service-specific configuration?
     Use your service-specific overlay repository.

   * Writing generally-interested code that may be reused by others?
     Write against Invenio Atlantis defaults, not against local
     service specific overlay assumptions and context.

5. **Create logically separate commits for logically separate
   things.**

   * Fixing a minor problem on the site of the topic branch at hand?
     Create separate topical branch or at least a separate logical
     commit.

   * Having a basically working version and improving upon its
     performance?  Maintain two separate commits.

   * Committing partially working code and fixing it later?  Squash
     the commits together.

   * Commit early, commit often... all the while ensuring continuous
     integration principles.  Make sure the topical branch is
     merge-ready at almost any given moment in time, even when not
     completed.  Hence use of configurability upfront.

   * See `git workflow documentation on rebasing
     <http://invenio-software.org/wiki/Tools/Git/Workflow#R1.Remarksoncommithistory>`_
     for more.

6. **Use sensible commit messages and stamp them with QA and ticket
   directives.**

   * Describe what the patch does so that the commit message is
     self-understandable without reading the code.

   * If the patch closes a ticket, use ``(closes #123)`` ticket
     directive.  If the patch only addresses the issue, use
     ``(addresses #123)`` ticket directive.

   * If you tested your code thoroughly and stand by its perfection,
     use ``Signed-off-by`` commit QA stamp.  If you reviewed the code
     created by others, use ``Reviewed-by`` QA stamp.  Helps to get
     them onto fast integration track.

   * See `git workflow documentation on commit log messages
     <http://invenio-software.org/wiki/Tools/Git/Workflow#R2.Remarksoncommitlogmessages>`_
     for more.

7. **Include test cases with the code.**

   * Always write unit and functional tests alongside coding.  Helps
     making sure the code runs OK on all supported platforms.  Helps
     speeding up the review and integration processes.  Helps
     understanding the code written by others by looking at their unit
     test cases.

8. **Include documentation with the code.**

   * "It's not finished until it's documented." --This may originally
     have been said by Tom Limoncelli.

   * "Documentation isn't done until someone else understands
     it." --Originally submitted by William S. Annis on 12jan2000.

   * "Good code is its own best documentation. As you're about to add
     a comment, ask yourself, 'How can I improve the code so that this
     comment isn't needed?' Improve the code and then document it to
     make it even clearer."--Steve McConnell, "Code Complete"

   * "If the code and the comments disagree, then both are probably
     wrong." --attributed to Norm Schryer

   * "Incorrect documentation is often worse than no
     documentation." --Bertrand Meyer"

9. **Check the overall code kwalitee.**

   * Does your branch fully implement the functionality it promises to
     implement?  Are all corner cases covered?  E.g. citation history
     graph when there are no citations?

   * Are you changing DB schema?  Write an `upgrade recipe
     <http://invenio-software.org/wiki/Development/Modules/InvenioUpgrader>`_.

   * Does your branch pass all our standard kwalitee tests?  Have you
     run `invenio-check-branch
     <https://github.com/tiborsimko/invenio-devscripts#invenio-check-branch>`_
     locally?  Does your branch pass Travis or Jenkins builds?

   * Name things properly.  Use ``list_of_scores`` rather than
     ``list2``.  Use ``InvenioBibFooFatalError`` rather than
     ``MyFatalError``.

   * Do not forget to sanitise all your input arguments.  Escape your
     HTML outputs to protect against XSS.  Supply your ``run_sql()``
     arguments in a tuple to protect against SQL injection.  Avoid
     using ``eval()``.

   * Respect minimal requirements, e.g. write for Python-2.4 for
     production ``maint-x.y`` branches that still require it.  Use
     Vagrant `virtual development environment
     <http://invenio-software.org/wiki/Development/VirtualEnvironments>`_
     when necessary.

   * Make conditional use of optional dependencies, e.g. test
     ``feedparser`` existence via ``try/except`` importing.  Check
     that the rest of the site still works OK without ``feedparser``.

10. **Send the code for review and integration.**

    * Distinguish between design-review process (that should have
      happened earlier, already in the first step) and the code-review
      process (that happens now).

    * No API change, only bugfixes?  All commits duly signed by
      authors and responsible module maintainers aka integration
      lieutenants?  Fast integration track.

    * Possible API changes, possible user/admin feature changes?  Need
      to synchronise about needs and to ensure configurability and
      compatibility?  Slow integration track.

11. **Help improving overall development, deployment, and operational
    bandwidth.**

    * Developers can help by adopting good practices upfront early in
      the process.

    * Reviewers can help by using QA stamps and fast integration
      tracks in live sessions.

    * Testers can help by widening the test suite so that nightly
      builds can be relied upon for deployment.

    * Administrators can help by sharing needs, requirements,
      solutions, and "howto" recipes.

12. **Share thoughts, needs, requirements, solutions, "howto" recipes
    with others.**

    * Check existing list of known bugs and known feature requests for
      any given module.  Troubles with indexing?  Go to
      `Development/Modules/BibIndex
      <http://invenio-software.org/wiki/Development/Modules/BibIndex>`_.

    * Did you perform some service operation such as changing your
      site URL?  Did you logged the several steps needed to achieve
      this?  Document them.  `HowTo/HowToChangeSiteUrl
      <http://invenio-software.org/wiki/HowTo/HowToChangeSiteUrl>`_.

    * Have you tried to improve performance of some tools Invenio
      relies on?  Have you run experiments and obtained observations
      and tips on MySQL performance?  Document
      them. `Tools/MySQL/Tuning
      <http://invenio-software.org/wiki/Tools/MySQL/Tuning>`_.
