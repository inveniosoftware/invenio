..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _style-guide:

Style guide TODO
================

Python
------
We follow `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ and `PEP-257
<https://www.python.org/dev/peps/pep-0257/>`_ and sort imports via ``isort``.
Please plug corresponding linters such as ``flake8`` to your editor.


Commit message
--------------

.. todo::

    Needs to be combined from existing parts and write the missing parts.

Indicate the component follow by a short description
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Maintainers
-----------

The Invenio project follows a similar maintainer phylosofy as `docker
<https://github.com/docker/docker/blob/master/MAINTAINERS>`_. If you want to
know more about it or take part, you can read our `Maintainer's guide
<http://invenio.readthedocs.io/en/feature-ils/community/maintainers-guide/index.html>`_.


FAQ
---
