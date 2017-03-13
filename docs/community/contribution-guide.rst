Contribution guide
==================

Interested in contributing to the Invenio project? There are lots of ways to
help.

-------
Conduct
-------

Overall, we're **considerate, open, respectful and good to each other**. We
contribute to this community not because we have to, but because we want to.
If we remember that, our
`Code of Conduct
<http://invenio.readthedocs.io/en/feature-ils/community/code-of-conduct.html>`_
will come naturally.

--------------------------
File Bugs and Enhancements
--------------------------

Found a bug? Want to see a new feature? Have a request for the maintainers? 
Open a Github issue in the applicable repository and we’ll get the 
conversation started.

**Found a security issue? Alert us privately at 
<info@inveniosoftware.org>**, this will allow us to distribute a security
patch before potential attackers look at the issue.

Our official communication channel is Gitter, we have one
`main chat room <https://gitter.im/inveniosoftware/invenio>`_,
although there are several other chat rooms for individual repositories.

Don't know what the applicable repository for an issue is? Open up an issue
in the `Invenio <https://github.com/inveniosoftware/invenio>`_ repository or
chat with a maintainer in the
`Gitter main room <https://gitter.im/inveniosoftware/invenio>`_
and we will make sure it gets to the right place.

Additionally, take a look at our
`troubleshooting <https://github.com/inveniosoftware/troubleshooting/issues>`_
documentation for common issues. 

Before opening a new issue it's helpful to search and see if anyone has
already reported the problem. You can search through the entire list of
issues in `GitHub <https://github.com/pulls?utf8=✓&q=user%3Ainveniosoftware>`_.

-------------
Triage Issues
-------------

If you don't have time to code, consider helping with triage. The community
will thank you for saving them time by spending yours.

The purpose of issue triage process is to make sure all the Invenio issues
and tasks are well described, sorted out according to priorities into timely
milestones, and that they have well assigned a responsible person to tackle
them when the time comes.

-------------------
Write documentation
-------------------

We are always looking to improve our documentation. Most of our docs live in
the `Invenio <https://github.com/inveniosoftware/invenio>`_ repository. Simply
fork the project, update docs and send us a pull request (The same principle
applies for the individual Invenio modules).

Writing documentation is not much different that writing code, please check
the `Contribute Code`_ section for more information about the whole process.

--------------------
Improve Translations
--------------------

Found a translation missing? We use transifex to handle our translation
string, take a look `here <https://www.transifex.com/inveniosoftware/invenio/>`_.

If it your first time doing that, we have prepared a
`nice tutorial
<http://invenio.readthedocs.io/en/feature-ils/community/translation-guide.html>`_
that you can follow.

---------------
Contribute Code
---------------

We are always looking for help improving the Invenio ecosystem, new
modules, tooling, and test coverage. Interested in contributing code? Let's
chat about it in the `Invenio's Gitter main chat room
<https://gitter.im/inveniosoftware/invenio>`_ or ask any of the core maintainers
to point you in the right direction. Make sure to check out issues tagged easy
fix, they are a good starting point.

Before doing something that  will significantly alter the behavior of any
Invenio module, such as a new feature, major refactoring, or
API changes, contributors should first open an issue presenting their case,
see `File Bugs and Enhancements`_, also you can ask for the opinion of any of the
core maintainers.

Commit messages
---------------

(Inspired by `How to Write a Git Commit Message
<https://chris.beams.io/posts/git-commit/>`_)

1. `Separate subject from body with a blank line
   <https://chris.beams.io/posts/git-commit/#separate>`_
2. `Limit the subject line to 50 characters
   <https://chris.beams.io/posts/git-commit/#limit-50>`_
3. `Indicate the component follow by a short description`_
4. `Do not end the subject line with a period
   <https://chris.beams.io/posts/git-commit/#end>`_
5. `Use the imperative mood in the subject line
   <https://chris.beams.io/posts/git-commit/#imperative>`_
6. `Wrap the body at 72 characters
   <https://chris.beams.io/posts/git-commit/#wrap-72>`_
7. `Use the body to explain what and why vs. how using bullet points`_

For example::
  
    component: sumarize changes in 50 char or less
    
    * More detailed explanatory text, if necessary. Formatted ussing
      bullet points, preferabely `*`. Wrapped to 72 characters.
    
    * Explain the problem that this commit is solving. Focus on why you
      are making this change as opposed to how (the code explains that).
      Are there side effects or other unintuitive consequences of this
      change? Here's the place to explain them.
    
    * The blank line separating the summary from the body is critical
      (unless you omit the body entirely); various tools like `log`, 
      `shortlog` and `rebase` can get confused if you run the two 
      together.
    
    * Use words like "Adds", "Fixes" or "Breaks" to help others
      understand what you did.
    
    * If your commit closes or addresses somehow an issue, you can metion
      it in any of the bullets after the dot. (closses #XXX) (addresses
      #YYY)
    
    Co-authored-by: John Doe <john.doe@example.com>

Indicate the component follow by a short description 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We know space is precious and 50 characters is not much for the subject line,
but maintainers and other people in general will appreciate if you can narrow
the focus of your commit in the subject.

Normal components match to the python modules inside the repository, i.e. `api`,
`views`, or `config`.
There are other components which correspond to a wider scope like `tests` or
`docs`.
And finally there is third category which doesn't correspond to any file or
folder in particular:

- `installation`: use it when modifying things like requirements files or `setup.py`.
- `release`: only to be used by maintainers.

If one commit modifies more than one file, i.e. `api.py` and `views.py`, common
sense should be applied, what represents better the changes the commit makes?
Remember you can always as for the modules maintainer's opinion.

Use the body to explain what and why vs. how using bullet points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Take a look at the full diff and just think how much time you would be saving
fellow and future committers by taking the time to provide this context here and
now. If you don’t, it would probably be lost forever.

In most cases, you can leave out details about how a change has been made.

In most cases, you can leave out details about how a change has been made. Code
is generally self-explanatory in this regard (and if the code is so complex that
it needs to be explained in prose, that’s what source comments are for). Just
focus on making clear the reasons why you made the change in the first place—the
way things worked before the change (and what was wrong with that), the way they
work now, and why you decided to solve it the way you did. Using bullet points
will help you be precise and direct to the point.
 
If you find your self writing a rather long commit message, maybe it's time to
step back and consider if you are doing too many changes in just one commit and
whether or not it's worth splitting it in smaller peaces.

And remember, the future maintainer that thanks you for writing good commit
messages may be yourself!

Submitting a pull request
-------------------------

All proposed changes to any of the Invenio modules are made as GitHub pull
requests, if this is the first time you are making a contribution using
GitHub, please check `this <https://guides.github.com/activities/forking/>`_.

Once you are ready to make your pull request, please keep in mind the
following:

- Before creating your pull request run the `run-tests.sh` script, this will
  help you discover possible side effects of your code and ensure it follows
  `Invenio's style guidelines
  <http://invenio.readthedocs.io/en/feature-ils/community/style-guide.html>`_,
  check `Development Environment
  <http://invenio.readthedocs.io/en/feature-ils/developersguide/development-environment.html>`_
  for more information on how you can run this script.
- Every pull request should include tests to check the expected behavior of
  your changes and must not decrease test coverage. If it fixes a bug it
  should include a test which proves the incorrect behavior.
- Documenting is part of the development process, no pull request will be
  accepted if there is missing documentation.
- No pull request will be merged until all automatic checks are green and at
  least one maintainer approves it.


-----------
Maintainers
-----------

The Invenio project follows a similar maintainer phylosofy as `docker
<https://github.com/docker/docker/blob/master/MAINTAINERS>`_. If you want to
know more about it or take part, you can read our `Maintainer's guide
<http://invenio.readthedocs.io/en/feature-ils/community/maintainers-guide/index.html>`_.
