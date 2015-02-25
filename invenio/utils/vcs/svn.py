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

"""Utilities for interaction with SVN repositories"""

import errno

from os import chdir
from subprocess import check_call as call
from invenio.base.globals import cfg
import tarfile
from tempfile import mkdtemp
from shutil import rmtree


def svn_exists():
    """
    Returns True if SVN is installed, else False
    """
    if cfg['CFG_PATH_SVN']:
        return True
    else:
        return False


def get_which_svn():
    """
    Gets which SVN is being used
    :returns: path to SVN
    """
    return cfg['CFG_PATH_SVN']


def harvest_repo(root_url, archive_path, tag=None, archive_mode='w:gz'):
    """
    Archives a specific tag in a specific SVN repository.
    :param root_url: This is the root url of the repo and should end in the
        repo name.
    :param archive_path: Where the archive will be stored - Must end in a
        valid extension that matches the archive_mode type. Default requires
        'tar.gz'
    :param tag: This is the tag you want to harvest, None=HEAD
    :param archive_mode: See 'tarfile.open' modes default w:gz > tar.gz
    """

    if not svn_exists():
        raise Exception("SVN not found. It probably needs installing.")

    clone_path = mkdtemp(dir=cfg['CFG_TMPDIR'])

    svn = get_which_svn()

    if tag:
        call([svn, 'co', root_url + '/tags/' + tag, clone_path])
    else:
        call([svn, 'co', root_url + '/trunk/', clone_path])

    chdir(cfg['CFG_TMPDIR'])
    tar = tarfile.open(name=archive_path, mode=archive_mode)
    tar.add(clone_path, arcname=root_url.split('/').pop())
    tar.close()

    try:
        rmtree(clone_path)
    except OSError as e:
        # Reraise unless ENOENT: No such file or directory
        # (ok if directory has already been deleted)
        if e.errno != errno.ENOENT:
            raise
