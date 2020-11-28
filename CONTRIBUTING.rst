Contribution guide
==================

Interested in contributing to the Invenio project? There are lots of ways to
help.

.. rubric:: Code of conduct

Overall, we're **open, considerate, respectful and good to each other**. We
contribute to this community not because we have to, but because we want to.
If we remember that, our :ref:`code-of-conduct` will come naturally.

.. rubric:: Get in touch

See :ref:`Link <getting-help>`. Don't hesitate to get in touch with the
Invenio maintainers. The maintainers can help you kick start your contribution.

Types of contributions
----------------------

Report bugs
~~~~~~~~~~~
- **Found a bug? Want a new feature?** Open a GitHub issue on the applicable
  repository and get the conversation started (do search if the issue has
  already been reported). Not sure exactly where, how, or what to do?
  See :ref:`Link <getting-help>`.

- **Found a security issue?** Alert us privately at
  `info@inveniosoftware.org <info@inveniosoftware.org>`_, this will allow us to
  distribute a security patch before potential attackers look at the issue.

Translate
~~~~~~~~~
- **Missing your favourite language?** Translate Invenio on
  `Transifex <https://www.transifex.com/inveniosoftware/invenio/>`_

- **Missing context for a text string?** Add context notes to
  translation strings or report the issue as a bug (see above).

- **Need help getting started?** See our :ref:`translation-guide`.

Write documentation
~~~~~~~~~~~~~~~~~~~
- **Found a typo?** You can edit the file and submit a pull request directly on
  GitHub.

- **Debugged something for hours?** Spare others time by writing up a short
  troubleshooting piece on
  https://github.com/inveniosoftware/troubleshooting/.

- **Wished you knew earlier what you know now?** Help write both non-technical
  and technical topical guides.

Write code
~~~~~~~~~~
- **Need help getting started?** See our :ref:`quickstart`.

- **Need help setting up your editor?** See our
  :ref:`setting-up-your-environment` guide which helps your automate the
  tedious tasks.

- **Want to refactor APIs?** Get in touch with the maintainers and get the
  conversation started.

- **Troubles getting green light on Travis?** Be sure to check our
  :ref:`style-guide` and the :ref:`setting-up-your-environment`. It will make
  your contributor life easier.

- **Bootstrapping a new awesome module?** Use our Invenio cookiecutter
  templates for `modules
  <http://github.com/inveniosoftware/cookiecutter-invenio-module>`_,
  `instances
  <http://github.com/inveniosoftware/cookiecutter-invenio-instance>`_
  or `data models
  <http://github.com/inveniosoftware/cookiecutter-invenio-datamodel>`_

Style guide (TL;DR)
-------------------
Travis CI is our style police officer who will check your pull
request against most of our :ref:`style-guide`, so do make sure you get a green
light from him.

**ProTip:** Make sure your editor is setup to do checking, linting, static
analysis etc. so you don't have to think. Need help setting up your editor? See
:ref:`setting-up-your-environment`.

Commit messages
~~~~~~~~~~~~~~~
Commit message is first and foremost about the content. You are communicating
with fellow developers, so be clear and brief.

(Inspired by `How to Write a Git Commit Message
<https://chris.beams.io/posts/git-commit/>`_)

1. `Separate subject from body with a blank line
   <https://chris.beams.io/posts/git-commit/#separate>`_
2. `Limit the subject line to 50 characters
   <https://chris.beams.io/posts/git-commit/#limit-50>`_
3. Indicate the component follow by a short description
4. `Do not end the subject line with a period
   <https://chris.beams.io/posts/git-commit/#end>`_
5. `Use the imperative mood in the subject line
   <https://chris.beams.io/posts/git-commit/#imperative>`_
6. `Wrap the body at 72 characters
   <https://chris.beams.io/posts/git-commit/#wrap-72>`_
7. `Use the body to explain what and why vs. how, using bullet points <https://chris.beams.io/posts/git-commit/#why-not-how>`_

**ProTip**: Really! Spend some time to ensure your editor is top tuned. It will
pay off many-fold in the long run. See :ref:`setting-up-your-environment`.

For example::

    component: summarize changes in 50 char or less

    * More detailed explanatory text, if necessary. Formatted using
      bullet points, preferably `*`. Wrapped to 72 characters.

    * Explain the problem that this commit is solving. Focus on why you
      are making this change as opposed to how (the code explains that).
      Are there side effects or other unintuitive consequences of this
      change? Here's the place to explain them.

    * The blank line separating the summary from the body is critical
      (unless you omit the body entirely); various tools like `log`,
      `shortlog` and `rebase` can get confused if you run the two
      together.

    * Use words like "Adds", "Fixes" or "Breaks" in the listed bullets to help
      others understand what you did.

    * If your commit closes or addresses an issue, you can mention
      it in any of the bullets after the dot. (closes #XXX) (addresses
      #YYY)

    Co-authored-by: John Doe <john.doe@example.com>

**Git signature:** The only signature we use is ``Co-authored-by`` (see above)
to provide credit to co-authors. Previously we required a ``Signed-off-by``
signature, however this is no longer required.

Pull requests
-------------
Need help making your first pull request? Check out the GitHub guide
`Forking Projects <https://guides.github.com/activities/forking/>`_.

When making your pull request, please keep the following in mind:

- Create logically separate commits for logically separate things.
- Include tests and don't decrease test coverage.
- Do write documentation. We all love well-documented frameworks, right?
- Run tests locally using ``run-tests.sh`` script.
- Make sure you have the rights if you include third-party code (and do credit
  the original creator). Note, you cannot include GPL or AGPL licensed code.
  LGPL and other more permissive open source license or fine.
- Green light on all GitHub status checks is required in order to merge your
  PR.

.. rubric:: Work in progress (WIP)

Do publish your code as pull request sooner than later. Just prefix the pull
request title with ``WIP`` (=work in progress) if it is not quite ready.

.. rubric:: Allow edits from maintainers

To speed up the integration process, it helps if on GitHub you `allow
maintainers to edit your pull request
<https://help.github.com/articles/allowing-changes-to-a-pull-request-branch-created-from-a-fork/>`_
so they can fix small issues autonomously.

.. rubric: Review guidelines

A pull request will probably be reviewed by someone in a different location,
maybe even a different time zone. Therefore, avoiding blockings and
misunderstandings is key. The following ideas could help ease and speed
up the review process:

- Be clear when something is ready to be reviewed (see `WIP` above).
- If a PR requires changes, say so explicitly, but politely (use emojis!).
- When something is ready to be merged say it explicitly. If the reviewer does
  not have permission to merge, (s)he should ping the corresponding person.
- When reviewing, rate your comments. This would help to understand if
  a comment must be addressed (e.g. it has substantial implications) or it is
  something the reviewer thought of but is a matter of "take it or leave it". A
  proposed scale is:
  1. Comment/Doubt/Question: exactly that. A doubt, a question or a comment.
  2. Minor: a change that the reviewer thinks might need change. However, it
  is not blocking, it is up to the developer to choose if and how to change
  it. It can be merged!
  3. Moderate/Normal (Default): a change that requires further discussion
  (e.g. breaking changes). It cannot be merged, unless explicitly stated by
  the reviewer (e.g. choose a solution proposed by the reviewer and implement
  it). Depending on the nature of the change a new review
  might be needed, use common sense.
  4. Major: a change that needs further discussion, probably a chat. Even the
  opinion of an architect. It has high implications. It cannot be merged.
  5. Shelved: a suggestion that will be treated later on as part of a
  different issue. It is a good practice to reference the issue. Note that
  any of the previous (comment, minor, moderate and major) can be shelved if
  agreed by the PR creator and the reviewer.

Here is an example:

  minor: I think this variable name should be plural since it refers to a list.

If no level is given, assume it is of "moderate" level within reason (might
clearly be minor or major). GitHub suggestions for instance are typically
minor, so no need to tag them all the time.

Following these guidelines builds trust over time. As a reviewer, you know
your comments will be heard and as a submitter, you know someone has taken the
time to go over your work and help you solve the problem you were tackling. In
both cases, it's done in a friendly and efficient manner.
