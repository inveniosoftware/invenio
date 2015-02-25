# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

from __future__ import print_function

"""
Miscellaneous utlity functions that have the potential for re-use.
"""

__revision__ = "$Id$"

import tempfile
import os
import random
import stat
import textwrap
import re

def concat(list_of_lists):

    return [item for list in list_of_lists for item in list]

def cleave_pair(list):

    # Should really generalize this to the nth case; but I only need
    # pairs right now!

    """
    [1,2,3,4,5,6,7]

    becomes

    ([1,3,5,7], [2,4,6])
    """

    lefts = []
    rights = []
    k = (lefts, rights)

    for x in range(0, len(list)):
        k[x % 2].append(list[x])

    return (lefts, rights)

def merge_pair(lefts, rights):
    """
    [1,3,5,7], [2,4,6]

    becomes

    [1,2,3,4,5,6,7]
    """

    k = (lefts, rights)
    list = []

    for x in range(0, len(lefts) + len(rights)):
        (d, m) = divmod(x, 2)
        list.append(k[m][d])

    return list

def cr2lf(file):

    """
    Replace CRLF with LF. ie. Convert text file from DOS to Unix end
    of line conventions.
    """

    return file.replace("\r\n", "\n")

# Directory backup using mirrordir:

def backup_directory(original_directory, backup_directory):

    # Backing up the directory requires GNU mirrordir to be installed;
    # shutil.copytree won't do the job if there are pipes or fifos
    # etc. in my_directory.

    # Implementing mirrordir directly in python would be a
    # good project!

    # mkdir will throw the correct errors for us:
    os.mkdir(backup_directory)

    commandline = 'mirrordir ' + original_directory + ' ' + backup_directory

    # Run the process using popen3; possibly dodgy on Windows!
    # Need popen3 rather other popen function because we want to
    # grab stderr and hide it from the clients console.
    (stdin, stdout, stderr) = os.popen3(commandline, 'r')
    # Close straight away; mirrordir expects no input.

    # return the exist status:
    return stdout.close()

# Tempfile stuff:

def open_tempfile(mode='wb'):

    # We open in binary mode and write a non-unicode string and so
    # can be sure that python will write the data verbatim,
    # without fiddling with CRLFs etc.

    (tf_file_descriptor, tf_name) = tempfile.mkstemp()
    tf = os.fdopen(tf_file_descriptor, mode)
    return (tf, tf_name)

def write_to_and_return_tempfile_name(data):

    (tf, tf_name) = open_tempfile()
    tf.write(data)
    tf.close()
    return tf_name

def remove_tempfile(filename):
    """
    Tries to unlink the named tempfile. Catches the OSError if
    unlinking fails.
    """
    try:
        os.unlink(filename)
    except OSError:
        # Couldn't delete temp file; no big problem.
        pass

# Random string stuff:

def random_alphanum_string(length, chars='abcdefghijklmnopqrstuvwxyz' ):
    """
    Create a random string of given length, choosing each character
    with equal probability from the list given in string chars. For
    example: chars='aab' would cause each character to be 'a' with 2/3
    probability and 'b' with 1/3 probability (pseudorandomly
    speaking).
    """

    alphanums = list(chars)

    # Replicate list into a list of lists and map the random choice
    # function over it:
    choices = map(random.choice, [alphanums] * length)

    # Concat the choices into a string:
    return ''.join(choices)

def mapmany(functions, in_list):

    # If functions equals [phi, ... , alpha, beta, gamma] return
    # map(phi, ... map(alpha, map(beta, map(gamma, in_list))) ... )

    functions.reverse()

    g = lambda list, f: map(f, list)

    return reduce(g, functions, in_list)

def dict2file(dictionary, directory):
    """
    Take any dictionary, eg.:

    { 'title' : 'The loveliest title.',
      'name'  : 'Pete the dog.',
      'info'  : { 'age' : '21', 'evil' : 'yes' }
    }

    and create a set of files in the given directory:
    directory/title
    directory/name
    directory/info/age
    directory/info/evil
    so that each filename is a dictionary key, and the contents of
    each file is the value that the key pointed to.
    """

    def f((path, dictionary_or_data)):

        fullpath = os.path.join(directory, path)

        try:
            dictionary_or_data.has_key
        except AttributeError:
            open(fullpath, 'wb').write(dictionary_or_data)
        else:
            os.mkdir(fullpath)
            dict2file(dictionary_or_data, fullpath)

    print('dict.items', dictionary.items())

    map(f, dictionary.items())

    return None

def recursive_dir_contents(dir):

    files = []

    def f(arg, dirname, fnames):
        files.extend(map(lambda file: os.path.join(dirname, file), fnames))

    os.path.walk(dir, f, None)

    return files

def count_dotdot(path):
    path_parts = path.split(os.sep)
    dotdots = filter(lambda part: part == '..', path_parts)
    return len(dotdots)

def common_prefix(seq, default_empty=''):
    try:
        leng = 0
        for tuple in zip(*seq):
            if tuple[1:] != tuple[:-1]: break
            leng += 1
        return seq[0][:leng]
    except TypeError: return default_empty

def split_common_path(thePaths):
    # sanitze paths:
    f = lambda x: os.path.normpath(os.path.expanduser(x))
    thePaths = map(f, thePaths)

    # thePaths is a list of paths (strings)
    thePaths = map(lambda p: p.split(os.sep), thePaths)

    # chop common part off the paths
    theBase = common_prefix(thePaths, [])
    thePaths = map(lambda p, c=len(theBase): p[c:], thePaths)
    # convert back to strings
    if theBase == ['']:
        theBase = '/'
    else:
        theBase = os.sep.join(theBase)
    thePaths = map(os.sep.join, thePaths)
    return (theBase, thePaths)

def mkdir_parents(path):
    tree = dirtree(path)
    tree.reverse()

    for parent in tree:
        if os.path.exists(parent):
            if os.path.isdir(parent):
                continue
            else:
                # This will raise the correct OSError for us.
                os.chdir(parent)
        else:
            os.mkdir(parent)

def dirtree(dir):
    # sanitize path:
    dir = os.path.normpath(os.path.expanduser(dir))
    return _dirtree(dir)

def _dirtree(dir):
    """
    An example will explain:

    >>> elmsubmit_misc.dirtree('/hof/wim/sif/eff/hoo')
    ['/hof/wim/sif/eff/hoo',
     '/hof/wim/sif/eff',
     '/hof/wim/sif',
     '/hof/wim',
     '/hof',
     '/']
     """

    # POSIX allows // or / for the root dir.
    # And it seems the rules say you aren't allowed to collapse // into /.
    # I don't know why this is!
    if dir == '//' or dir == '/':
        return [dir]
    elif dir == '':
        return []
    else:
        return [dir] + _dirtree(os.path.dirname(dir))

def provide_dir_with_perms_then_exec(dir, function, perms, barrier_dir):
    # This function won't allow you to alter the root directories'
    # permissions: if your going to be changing the permissions on
    # your root directory, you probably need to do it more carefully
    # than with a python function!

    # sanitize path:
    dir = os.path.abspath(os.path.normpath(os.path.expanduser(dir)))

    # Check to see if we're already in the state we want to be in:
    try:
        targets_current_perms = get_perms(dir)
        targets_current_owner_uid = get_owner_uid(dir)
    except OSError as e:
        if e.errno == 2:
            # dir definitely doesn't exist.
            raise
        elif e.errno == 13:
            # don't have sufficient permissions to read the
            # permissions.
            dir_info_read = False
    else:
        dir_info_read = True

    if dir_info_read and targets_current_owner_uid != os.geteuid():
        # We don't own the file:
        raise OSError("file %s not owned by this process's effective user: cannot proceed" % (dir))
    elif dir_info_read and targets_current_perms & perms == perms:
        # This directory already has user bits set to at least perms,
        # so execute the given function:
        return function()

    # If we haven't exited the function already, we need to change the target dirs
    # permissions (or simply couldn't read the permissions!)

    # Get a list of all of the dirs parents:
    dir_list = dirtree(dir)

    if barrier_dir is not None:
        # sanitize path:
        barrier_dir = os.path.abspath(os.path.normpath(os.path.expanduser(barrier_dir)))

        # Check the barrier dir is one of the parents of dir:
        if not barrier_dir in dir_list[1:]:
            raise ValueError('argument barrier_dir must be a proper parent directory of argument dir')

        # Get a list of all the directories that lie between the
        # barrier dir and the target dir, including the barrier dir,
        # but excluding the target dir:
        barrier_dir_list = dirtree(barrier_dir)

        g = lambda d: (d == barrier_dir) or (not (d in barrier_dir_list or d == dir))
        operable_parent_dirs = filter(g, dir_list)
    else:
        operable_parent_dirs = dir_list
    # Make sure we have at least wx permissions on parent:
    parents_old_states = _get_perms_on(operable_parent_dirs, perms=0300)

    # Now stat the target dir if we didn't manage previously:
    if not dir_info_read:
        try:
            targets_current_perms = get_perms(dir)
            targets_current_owner_uid = get_owner_uid(dir)
        except OSError as e:
            if e.errno == 2:
                # race condition:
                raise OSError("Directory structure altered during processing: %s removed during processing" % (dir))
            elif e.errno == 13:
                # race condition:
                raise OSError("Directory structure %s altered during processing: permissions changed during processing" % (dir_list))

        if targets_current_owner_uid != os.geteuid():
            # We don't own this file and so can't chmod it: We
            # couldn't see this previously because we didn't
            # have permission to stat the dir. Undo the
            # permission changes we've already made and report
            # the error:
            _safely_chmod_dirlist(parents_old_states)
            raise OSError("file %s not owned by this process's effective user: cannot proceed" % (dir))
        elif targets_current_perms & perms == perms:
            # We already have the perms we need.
            try:
                return_value = function()
            finally:
                _safely_chmod_dirlist(parents_old_states)
            return return_value

    # Now change the permissions of our target directory:
    try:
        os.chmod(dir, perms | targets_current_perms)
    except OSError:
        # race condition:
        raise OSError("Directory structure %s altered during processing: permissions changed during processing" % (dir_list))

    try:
        # Now permissions are open, exec our function:
        return_value = function()
    finally:
        # Close up the permissions we had to open:
        _safely_chmod_dirlist([[dir, targets_current_perms]] + parents_old_states)

    # Return the input functions return value:
    return return_value

def _get_perms_on(dirlist, perms=0300):

    # Note: any comment labelling a particular error as "race
    # condition" is meant to indicate an error that can only arise if
    # another process is attempting to alter the directory strucutre
    # at the same time as us - this function _must not_ be used if
    # such a situation is possible.

    # User perms < rx doesn't make sense for this function. You need
    # at least wx bits on a directory to change the permissions on its
    # child directories.
    if perms < 0300: raise ValueError("argument perms must be >= 3 in the user byte")

    dir = dirlist[0]
    remaining_dirs = dirlist[1:]

    try:
        targets_current_perms = get_perms(dir)
        targets_current_owner_uid = get_owner_uid(dir)
    except OSError as e:
        if e.errno == 2:
            # dir definitely doesn't exist.
            raise
        elif e.errno == 13:
            # don't have sufficient permissions to read the
            # permissions.
            dir_info_read = False
    else:
        dir_info_read = True

    if dir_info_read and targets_current_owner_uid != os.geteuid():
        # We don't own the file:
        raise OSError("file %s not owned by this process's effective user: cannot proceed" % (dir))
    elif dir_info_read and targets_current_perms & perms == perms:
        # This directory already has user bits set to at least perms,
        # so nothing to do:
        return []
    elif dir_info_read and targets_current_perms & perms != perms:
        # We need to adjust the permissions. See if the parent will
        # let us:
        if remaining_dirs == []:
            # We have no parents available:
            raise OSError("no members of the given dirtree have sufficient permissions for us to chmod")
        else:
            parent = remaining_dirs[0]
            # Figure out if we're the owner of the parent and have permissions
            try:
                parents_current_perms = get_perms(parent)
                parents_current_owner_uid = get_owner_uid(parent)
            except OSError as e:
                if e.errno == 2:
                    # dir definitely doesn't exist.
                    raise
                elif e.errno == 13:
                    # don't have sufficient permissions to read the
                    # permissions.
                    parent_dir_info_read = False
            else:
                parent_dir_info_read = True

            if parent_dir_info_read and parents_current_owner_uid == os.geteuid() and parents_current_perms & 0300 == 0300:
                # We own the parent and have sufficient permission to chmod its contents:
                try:
                    os.chmod(dir, perms | targets_current_perms)
                except OSError:
                    # race condition:
                    raise OSError("Directory structure %s altered during processing: permissions changed during processing" % (dirlist))
                return [[dir, targets_current_perms]]
            else:
                # We need to step down a level:
                pass

    else: # dir info was not read.
        if remaining_dirs == []:
            raise OSError("no members of the given dirtree have sufficient permissions for us to chmod")

    # If the prior if-then-else didn't return or throw an error then
    # either we couldn't stat the given dir or we don't have
    # permission to change its permissions, so therefore we need to
    # step down a level:

    parents_old_states = _get_perms_on(remaining_dirs, perms)

    if not dir_info_read:
        try:
            targets_current_perms = get_perms(dir)
            targets_current_owner_uid = get_owner_uid(dir)
        except OSError as e:
            if e.errno == 2:
                # race condition:
                raise OSError("Directory structure altered during processing: %s removed during processing" % (dir))
            elif e.errno == 13:
                # race condition:
                raise OSError("Directory structure %s altered during processing: permissions changed during processing" % (dirlist))
        if targets_current_owner_uid != os.geteuid():
            # We don't own this file and so can't chmod it: We
            # couldn't see this previously because we didn't
            # have permission to stat the dir. Undo the
            # permission changes we've already made and report
            # the error:
            _safely_chmod_dirlist(parents_old_states)
            raise OSError("file %s not owned by this process's effective user: cannot proceed" % (dir))
        elif targets_current_perms & perms == perms:
            # current directory already has the permissions we
            # want; previously the parent's perms were preventing
            # us from seeing this:
            return parents_old_states
        else:
            # current directory's permissions need altering:
            # Set the user bits to at least perms:
            try:
                os.chmod(dir, perms | targets_current_perms)
            except OSError:
                # race condition:
                raise OSError("Directory structure %s altered during processing: permissions changed during processing" % (dirlist))
            return [[dir, targets_current_perms]] + parents_old_states
    else:
        # current directory's permissions need altering:
        # Set the user bits to at least perms:
        try:
            os.chmod(dir, perms | targets_current_perms)
        except OSError:
            # race condition:
            raise OSError("Directory structure %s altered during processing: permissions changed during processing" % (dirlist))
        return [[dir, targets_current_perms]] + parents_old_states

def _safely_chmod_dirlist(dirlist):
    return [os.chmod(dir, perms) for dir, perms in dirlist]

def get_perms(path):
    return stat.S_IMODE(os.stat(path)[stat.ST_MODE])

def get_owner_uid(path):
    return os.stat(path)[stat.ST_UID]

# Text utils:

def wrap_text(text, cols=80):
    print("text", text)
    parts = re.split(r'(\n(?:\s*\n))+', text)
    (paragraphs, whitespace) = cleave_pair(parts)
    for x in parts:
        print(">>", x)
    print("paras", paragraphs)
    print("white", whitespace)
    wrapped_paragraphs =  map(lambda t: textwrap.fill(t, width=cols), paragraphs)
    print(wrapped_paragraphs)
    return ''.join(merge_pair(wrapped_paragraphs, whitespace))

# Module utils:

def import_dots(string):
    """
    Note that if you execute:

    mod = __import__('one.two.three')

    then variable mod will point to module one, not module
    'one.two.three'.

    whereas:

    mod = import_dots('one.two.three')

    will point to module 'one.two.three'.
    """

    mod = __import__(string)
    components = string.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

