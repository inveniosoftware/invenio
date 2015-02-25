# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Utilities for interaction with Git repositories"""

import errno

from subprocess import check_call as call
from invenio.base.globals import cfg
from os import chdir
from tempfile import mkdtemp
from shutil import rmtree


def git_exists():
    '''
    Returns True if Git is installed, else False
    '''
    if cfg['CFG_PATH_GIT']:
        return True
    else:
        return False


def get_which_git():
    """
    Gets which Git is being used
    :returns: path to Git
    """
    return cfg['CFG_PATH_GIT']


def harvest_repo(root_url, archive_path, tag=None, archive_format='tar.gz'):
    """
    Archives a specific tag in a specific Git repository.

    :param root_url: The URL to the Git repo
    - Supported protocols: git, ssh, http[s].
    :param archive_path: A temporary path to clone the repo to
    - Must end in .git
    :param tag: The path to which the .tar.gz will go to
    - Must end in the same as format (NOT inside clone_path)
    :param format: One of the following: tar.gz / tar / zip
    """

    if not git_exists():
        raise Exception("Git not found. It probably needs installing.")

    clone_path = mkdtemp(dir=cfg['CFG_TMPDIR'])

    git = get_which_git()

    call([git, 'clone', root_url, clone_path])
    chdir(clone_path)

    if tag:
        call([git, 'archive', '--format=' + archive_format, '-o',
              archive_path, tag])
    else:
        call([git, 'archive', '--format=' + archive_format, '-o',
              archive_path, 'HEAD'])

    try:
        rmtree(clone_path)
    except OSError as e:
        # Reraise unless ENOENT: No such file or directory
        # (ok if directory has already been deleted)
        if e.errno != errno.ENOENT:
            raise
