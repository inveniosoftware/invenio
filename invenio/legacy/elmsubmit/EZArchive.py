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

__revision__ = "$Id$"

try:
    import bz2
    _got_bz2 = True
except ImportError:
    _got_bz2 = False

import gzip
import tarfile
import shutil
import os
import re
import tempfile
import sys

WARN_SKIP = True

from invenio.legacy.elmsubmit.filename_generator import calculate_filename_extension as _calculate_filename_extension
# from invenio.legacy.elmsubmit.filename_generator import generate_filename as _generate_filename
from invenio.legacy.elmsubmit.misc import write_to_and_return_tempfile_name as _write_to_and_return_tempfile_name
from invenio.legacy.elmsubmit.misc import provide_dir_with_perms_then_exec as _provide_dir_with_perms_then_exec
from invenio.legacy.elmsubmit.misc import dirtree as _dirtree
from invenio.legacy.elmsubmit.misc import count_dotdot as _count_dotdot
from invenio.legacy.elmsubmit.misc import random_alphanum_string as _random_alphanum_string
from invenio.legacy.elmsubmit.misc import backup_directory as _backup_directory
from invenio.legacy.elmsubmit.misc import open_tempfile as _open_tempfile
from invenio.legacy.elmsubmit.misc import split_common_path as _split_common_path
from invenio.legacy.elmsubmit.misc import recursive_dir_contents as _recursive_dir_contents
from invenio.legacy.elmsubmit.misc import mkdir_parents as _mkdir_parents

# Store all files written out in two lists:
# 1. remove_always is for temporary files, which we try to remove regardless.
# 2. remove_on_error is for files the user wants, but need removing if we
#    encounter an error.

def _validate_args(arg, received, allowed):
    if received not in allowed:
        raise ValueError('argument %s must be a value from set %s: got %s' % (arg, allowed, received))

_remove_on_error = []
_remove_always = []

def _remember_write(file_loc, error_only=False):
    if error_only:
        _remove_on_error.append(file_loc)
    else:
        _remove_always.append(file_loc)

def _delete_files(list):
    for item in list:
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.unlink(item)

def _calc_perms(permissions, umask):
    return permissions & (~umask)

# os.chmod('/tmp/thisthis', stat.S_IMODE(os.stat('/tmp')[stat.ST_MODE]))

def _check_mode(current_mode, allowed_mode):
    if  current_mode != allowed_mode: raise _ModeError


_valid_file_types = ['regular', 'dir', 'symlink', 'hardlink', 'char_dev', 'block_dev', 'fifo']

def _file_type(tarinfo_obj):
    if tarinfo_obj.isfile():
        return 'regular'
    elif tarinfo_obj.isdir():
        return 'dir'
    elif tarinfo_obj.issym():
        return 'symlink'
    elif tarinfo_obj.islnk():
        return 'hardlink'
    elif tarinfo_obj.ischr():
        return 'char_dev'
    elif tarinfo_obj.isblk():
        return 'block_dev'
    elif tarinfo_obj.isfifo():
        return 'fifo'

def _pick_compression_type(ext):
    # Fix the extension; for example if its a gzipped pdf,
    # calculate_filname_extension will return pdf.gz. To combat
    # this, we find the longest extension from: tar.gz, tar.bz2,
    # tar, gz, bz2.
    return re.sub(r'^.*?(tar\.gz|tar\.bz2|tar|gz|bz2)$', r'\1', string=ext, count=1)

def _verify_filename(name, seen_filenames, filename_collision, num_random_bits, rename_from_set):

    # name could be a filename or directory.

    if name in seen_filenames:
        seen_filenames[name] += 1
        times = seen_filenames[name]

        (dirname, basename) = os.path.split(name)

        if filename_collision == 'throw_error':
            raise EZArchiveError('filename collision: %s' % (name))
        elif filename_collision == 'rename_similar':

            # Just in case archive contains a list of
            # filenames that follow the same pattern as this
            # incrementing, we need to check the increment
            # doesn't collide as well:
            incremented_basename = str(times) + '.' + basename
            while os.path.join(dirname, incremented_basename) in seen_filenames:
                times += 1
                incremented_basename = str(times) + '.' + basename

            # Make a note of how many increments we've had to
            # do:
            seen_filenames[name] = times
            name = os.path.join(dirname, incremented_basename)

        elif filename_collision == 'rename_random':
            # Just in case of random collision, we introduce the while loop.
            randbasename = _random_alphanum_string(num_random_bits, chars=rename_from_set)
            tries = 1
            while os.path.join(dirname, randbasename) in seen_filenames:
                randbasename = _random_alphanum_string(num_random_bits, chars=rename_from_set)
                # If user gives small set rename_from_set and low number of bits,
                # then it is possible we will exhaust all posibile combinations:
                tries += 1
                if tries > 20:
                    raise EZArchiveError('20 random filename selections collided: perhaps you need to increase num_rand_bits?')
            seen_filenames[os.path.join(dirname, randbasename)] = 0
            name = os.path.join(dirname, randbasename)
        elif filename_collision == 'overwrite':
            pass
        elif filename_collision == 'skip':
            return ['skip']
    else:
        seen_filenames[name] = 0

    return name

def extract(input, # byte string of file location
            input_disposition='byte_string', # ['byte_string', 'file_location']
            compression_hint=None, # [None, 'gz', 'bz2', 'tar', 'tar.gz', 'tar.bz2', 'zip']
            extract_to='byte_strings', # ['byte_strings', 'my_directory', 'temp_directory']

            my_directory=None, # directory path
            backup_extension=None, # extension including dot, for backup of my_directory
            directory_structure='retain', # ['retain', 'flatten']

            file_handle = None, # [None, 'py', 'os']
            file_handle_mode = 'rb',

            force_file_permissions=None, # file permission bits. eg 0o777.
            force_dir_permissions=None, # file permission bits. eg 0o777.
            umask=None, # file permission bits. eg. 0o777 (assuming standard umask interpretation).

            allow_file_types=_valid_file_types, # list containing any of ['regular, dir, symlink, hardlink, char_dev, block_dev, fifo']
            on_find_invalid_file_type='throw_error', # ['throw_error', 'skip']

            filename_collision='rename_similar', # ['throw_error', 'rename_similar', 'rename_random', 'overwrite', 'skip']
            rename_from_set='abcdefghijklmnopqrstuvwxyz', # characters to use if filename_collision='rename_random'
            num_random_bits=8, # number of random bits to use in the random filename.

            allow_clobber=False, # [True, False]

            on_find_dotdot_path='throw_error', # ['throw_error', 'skip', 'allow']
            on_find_absolute_path='throw_error' # ['throw_error', 'skip', 'allow']

            # Shelved options:
            # file_name_regexp, non_matches='rename_safely', etc.
            # Hopefully to be implemented in the future.
            ):

    # Clean out the written files list:
    global _remove_on_error
    global _remove_always
    _remove_on_error = []
    _remove_always = []

    # Validate arguments.
    _validate_args('input_disposition', input_disposition, ['byte_string', 'file_location'])
    _validate_args('compression_hint', compression_hint, [None] + available_tools.keys())
    _validate_args('extract_to', extract_to, ['byte_strings', 'my_directory', 'temp_directory'])
    # _validate_args('extract_to', return_objects, [None, 'file_location', 'open_c_filehandles', 'open_py_file_handles'])
    f = lambda type: _validate_args('allow_file_types', type, _valid_file_types)
    map(f, allow_file_types)
    if not input: raise ValueError('argument input must specify a filename or a byte string')

    # From here on, we start writing things out to disk, so we wrap it
    # in a try loop and catch all exceptions. This allows us to clean
    # up the disk if we didn't succeed with the whole of the
    # extraction.

    try:
        # try/except/finally cannot be combined, so we have to nest:
        try:
            # Write input to a temp file if we are given a byte string.
            if input_disposition == 'byte_string':
                input_file_loc = _write_to_and_return_tempfile_name(input)
                _remember_write(input_file_loc)
            else:
                # input_disposition == 'file_location'
                # Check that the input file location we've been given exists;
                # stat will throw the right error for us:
                os.stat(input)

                # Check it is a file:
                if not os.path.isfile(input):
                    raise ValueError("argument input must be a path to an archive file if input_disposition='file_location': %s"
                                     % (input))
                input_file_loc = input

            # Make sure we know what type of file we're dealing with:
            if compression_hint is None:
                compression_ext = _calculate_filename_extension(filename=input_file_loc)
                compression_ext = _pick_compression_type(compression_ext)
            else:
                compression_ext = compression_hint

            # Select approriate archive/compression tool:
            try:
                tool_class = available_tools[compression_ext]
            except KeyError:
                raise EZArchiveError('Unrecognized archive type: %s' % (compression_ext))

            # Instantiate the tool:
            archive = tool_class(input_file_loc, mode='r', allow_clobber=allow_clobber)

            if extract_to == 'byte_strings':
                # If extract_to == byte_strings, permissions mean nothing.
                # However, because we use a temp directory to load the files
                # into byte strings, we force the permissions to be nice and
                # liberal inside the temp dir:
                force_file_permissions = 0700
                force_dir_permissions = 0700

            # Get extraction_root:
            if extract_to == 'byte_strings' or extract_to == 'temp_directory':
                # Need a temp directory to work in.
                extraction_root = tempfile.mkdtemp()

                if extract_to == 'byte_strings':
                    _remember_write(extraction_root, error_only=False)
                else:
                    # extract_to == 'temp_directory':
                    _remember_write(extraction_root, error_only=True)
            else:
                # extract_to == 'my_directory':

                if my_directory is None:
                    raise ValueError("my_directory must be specified if extract_to='my_directory'")

                # Make given directory into a nice sane one.
                my_directory = os.path.abspath(os.path.expanduser(os.path.normpath(my_directory)))

                # Check it exists, and we can stat it:
                # stat will throw the right error for us:
                os.stat(my_directory)

                # Check it is a dir.
                if not os.path.isdir(my_directory):
                    raise ValueError("argument my_directory must be a directory: %s" % (my_directory))

                # If we've been asked to back it up, do so:
                if backup_extension is not None:
                    backup_dir = my_directory + backup_extension
                    if _backup_directory(my_directory, backup_dir) is not None:
                        raise EZArchiveError('creation of backup directory using GNU mirrordir failed: %s' % (backup_dir))

                # Finally set the extraction root:
                extraction_root = my_directory

                # Logically we would also check we have write permissions
                # here.  But this is acutally better served by letting
                # builtin/other functions raise EnvironmentErrors when we fail
                # to write: Checking for write permissions is actually quite
                # complex: e.g. you'd have to check group membership to see if
                # the group bits allow write.

            # If we haven't been given a umask, use take the system umask as a
            # default. If we have been given a umask, set the system umask to
            # it, so all calls to builtin open/file apply the given umask:
            if umask is None:
                # It doesn't seem possible to read the umask without also
                # setting it. Hence this fudge:
                umask = os.umask(0o777)
                os.umask(umask)

            # Used in the extraction for loop to check for filename collisions
            # when flattening directory structure:
            seen_filenames = {}

            # Collect the returned file information here:
            return_data = []

            for mem in archive.list_all_members():
                name = mem['name']
                dir = mem['dir']
                file_type = mem['file_type']
                identity_object = mem['identity_object']

                # Check it is an allowed file type:
                if file_type not in allow_file_types:
                    if on_find_invalid_file_type=='skip':
                        continue
                    else:
                        # on_find_invalid_file_type='throw_error':
                        raise EZArchiveError("found disallowed file type '%s': %s" % (file_type, os.path.join(dir, name)))

                # Deal with dotdot paths:
                if on_find_dotdot_path == 'allow':
                    pass
                else:
                    # check if path contains '..'
                    dir_parts = dir.split(os.sep)
                    if '..' in dir_parts or name == '..':
                        if on_find_dotdot_path == 'throw_error':
                            raise EZArchiveError("tar entry's path contains '..' (*cautiously* consider on_find_dotdot_path='allow'): "
                                                 + os.path.join(dir, name))
                        else:
                            # on_find_dotdot_path == 'skip'
                            # next file please:
                            continue

                # Deal with absolute paths in a similar way:
                if on_find_absolute_path == 'allow':
                    pass
                else:
                    # check if path begins with '/'
                    if dir != '' and dir[0] == '/':
                        if on_find_absolute_path == 'throw_error':
                            raise EZArchiveError("tar entry's path is absolute (*cautiously* consider on_find_absolute_path='allow'): "
                                                 + os.path.join(dir, name))
                        else:
                            # on_find_absolute_path == 'skip'
                            # next file please:
                            continue

                # Deal with flattening of directories:
                if directory_structure == 'flatten':
                    dir = ''

                    if file_type == 'dir':
                        continue

                # tars allow multiple entries for same path/file:
                # extracting such tarballs with GNU/tar will just
                # cause the second entry to overwrite the first.  We
                # try to be more graceful:

                verified_fullname = _verify_filename(name=os.path.join(dir, name), seen_filenames=seen_filenames,
                                                     filename_collision=filename_collision, num_random_bits=num_random_bits,
                                                     rename_from_set=rename_from_set)

                if verified_fullname == ['skip']: continue
                name = os.path.basename(verified_fullname)

                archive.extract_member(identity_object=identity_object, root_dir=extraction_root, dir=dir, new_filename=name,
                                       umask=umask, force_file_permissions=force_file_permissions, force_dir_permissions=force_dir_permissions,
                                       allow_clobber=allow_clobber)

                fullname = os.path.join(extraction_root, dir, name)

                file_info = {}
                file_info['basename'] = name
                file_info['tar_dir'] = dir
                file_info['file_type'] = file_type

                if extract_to == 'byte_strings':
                    if file_type == 'regular':
                        file_info['file'] = open(fullname, 'rb').read()
                else:
                    # extract_to in ['my_directory', 'temp_directory']
                    file_info['fullname'] = fullname
                    file_info['dirname'] = os.path.join(extraction_root, dir)

                    if file_type == 'regular':
                        if file_handle == 'py':
                            file_info['fh'] = open(fullname, file_handle_mode)
                        elif file_handle == 'os':
                            file_info['fh'] = os.open(fullname, file_handle_mode)

                return_data.append(file_info)

            if extract_to == 'temp_directory':
                return (extraction_root, return_data)
            else:
                return return_data

        except:
            # Clean up non-temporary file if we get an error:
            _delete_files(_remove_on_error)
            raise
    finally:
        # Always clean up temporary files, error or not:
        _delete_files(_remove_always)

def create(input, # list of files or named ([['name', 'data...'], ...]) or anonymous ([[data...], ...]) byte strings.
           input_disposition='named_byte_strings', # ['file_locations', 'anonymous_byte_strings', 'named_byte_strings']

           compression='tar.gz', # ['gz', 'bz2', 'tar', 'tar.gz', 'tar.bz2', 'zip']

           compress_to = 'byte_string', # ['byte_string', 'my_file', 'temp_file']
           my_file=None, # name of output archive, if compress_to='my_file'
           recurse_dirs=True, # [True, False]

           directory_structure='retain', # ['retain', 'flatten']
           use_compression_root='calculate_minimum', # ['calculate_minimum', 'this_root']
           this_root=None, # root path for compression of files.

           filename_collision='rename_similar', # ['throw_error', 'rename_similar', 'rename_random', 'overwrite', 'skip']
           rename_from_set='abcdefghijklmnopqrstuvwxyz', # characters to use if filename_collision='rename_random'
           num_random_bits=8, # number of random bits to use in the random filename.

           force_file_permissions=None, # file permission bits. eg 0o777.
           force_dir_permissions=None, # file permission bits. eg 0o777.

           file_handle = None, # [None, 'py', 'os']
           file_handle_mode = 'rb',

           allow_clobber=False, # [True, False]
           ):

    # Basic idea: If we are told to output an archive (tar or zip)
    # then all files given in input are put into a single archive.  If
    # we are told to output compressed files (gz, bz2) then we must be
    # given a maximum of one archive file.

    # If we are given anonymous byte strings with no filename, we use
    # filename_generator.generate_filename() to provide a random
    # filename with hopefully a correct file extension.

    # Clean out written files list:
    global _remove_on_error
    global _remove_always
    _remove_on_error = []
    _remove_always = []

    # Validate arguments.
    # ??????????????????

    # From here on, we start writing things out to disk, so we wrap it
    # in a try loop and catch all exceptions. This allows us to clean
    # up the disk if we didn't succeed with the whole of the
    # extraction.

    try:
        # try/except/finally cannot be combined, so we have to nest:
        try:
            # Write input to a temp file if we are given a byte string.

            # Work out where the output archive file is going to go:
            if compress_to == 'my_file':
                if my_file is None:
                    raise ValueError("if compress_to == 'my_file' then argument my_file must be specified. got None.")

                # Make given file into a nice sane one:
                archive_fullname = os.path.abspath(os.path.expanduser(os.path.normpath(my_file)))

                # Should we remember this file or not?  If we get an error in
                # the middle of processing, should we delete a user specified
                # archive file? The decision is not so clear cut as with
                # temporary files (see next). My choice is not to remember
                # (and so not to delete on error)

            else:
                # compress_to in ['temp_file', 'byte_string']
                (tf, tf_name) = _open_tempfile(mode='wb')

                # close filehandle because we don't need it:
                tf.close()

                # delete the empty tempfile that open_tempfile
                # created, so we don't get ClobberError
                os.unlink(tf_name)
                del tf

                if compress_to == 'temp_file':
                    _remember_write(tf_name, error_only=True)
                else:
                    # compress_to == 'byte_string'
                    _remember_write(tf_name, error_only=False)

                archive_fullname = tf_name

            # Get an archive/compress tool:
            tool_class = available_tools[compression]
            archive = tool_class(file_loc=archive_fullname, mode='w', allow_clobber=allow_clobber)

            # Deal with the input:
            # We do this as follows:

            # 1. Take anonymous byte strings and turn them into byte strings
            # by generating a filename for each string, then set
            # input=[new list of named byte strings]
            # input_disposition='named_byte_strings'

            # 2. Take named byte strings and write them to a temporary
            # directory, chdir to this directory and set:
            # input = [glob of temp dir]
            # input_diposition = 'file_locations'

            if input_disposition == 'anonymous_byte_strings':
                # If input is anonymous byte strings, we need generate a filename
                # for each of the strings:
                seen_rand_names = []

                def f(bytstr):
                    rand_name = _random_alphanum_string(num_random_bits, chars=rename_from_set)
                    tries = 1
                    while rand_name in seen_rand_names:
                        rand_name = _random_alphanum_string(num_random_bits, chars=rename_from_set)
                        tries += 1
                        if tries > 20:
                            raise EZArchiveError('20 random filename selections collided: perhaps you need to increase num_rand_bits?')
                    seen_rand_names.append(rand_name)
                    return [rand_name, bytstr]

                input = map(f, input)
                input_disposition = 'named_byte_strings'

            if input_disposition == 'named_byte_strings':
                # Write the byte strings out to the temporary directory.
                temp_dir = tempfile.mkdtemp()
                _remember_write(temp_dir, error_only=False)

                if this_root is not None:
                    # santize:
                    this_root = os.path.abspath(os.path.expanduser(os.path.normpath(this_root)))
                    # chop off the root slashes:
                    this_root = re.sub(r'^/+', '', string=this_root, count=1)
                    # rejig the root dir to reflect the fact we've shoved
                    # everything under a psuedo-root temp directory:
                    this_root = os.path.join(temp_dir, this_root)

                new_input = []
                seen_filenames = {}

                for filename, bytestr in input:
                    # Sanitize the filename we've been given:
                    filename = os.path.abspath(os.path.expanduser(os.path.normpath(filename)))
                    # chop off the root slashes:
                    filename = re.sub(r'^/+', '', string=filename, count=1)

                    dirname = os.path.dirname(filename)

                    # Use temp_dir as a 'fake_root': (There is some possible
                    # dodginess here if the user names one of the files as if
                    # it were inside the not yet existant temp directory:
                    # unlikely scenario; should we work around it? I haven't.
                    _mkdir_parents(os.path.join(temp_dir, dirname))

                    filename = _verify_filename(name=filename, seen_filenames=seen_filenames,
                                                filename_collision=filename_collision, num_random_bits=num_random_bits,
                                                rename_from_set=rename_from_set)
                    if filename == ['skip']: continue

                    tempfile_fullname = os.path.join(temp_dir, filename)

                    open(tempfile_fullname, 'wb').write(bytestr)
                    new_input.append(tempfile_fullname)

                input = new_input
                input_disposition='file_locations'

            # At this point, input_disposition='file_locations' and input contains a list of filenames.

            # sanitize the list of filenames
            f = lambda x: os.path.abspath(os.path.expanduser(os.path.normpath(x)))
            input = map(f, input)

            # Expand any directories into filenames (excluding symlinks):
            new_input = []
            for item in input:
                if os.path.isdir(item):
                    new_input.append(item)
                    if recurse_dirs:
                        new_input.extend(_recursive_dir_contents(item))
                else:
                    new_input.append(item)
            input = new_input

            # calculate the compression root:
            if use_compression_root == 'calculate_minimum':
                first_input = input[0]
                if input == filter(lambda x: x == first_input, input):
                    # all of the filenames we've been given are the same:
                    compression_root = os.path.dirname(first_input)
                    files_to_compress = [os.path.basename(first_input)] * len(input)
                else:
                    # find out the common root of the filenames:
                    (compression_root, files_to_compress) = _split_common_path(input)
                    # if compression_root was also specified in input, it will
                    # have become a blank entry '' in files_to_compress:
                    files_to_compress = filter(lambda x: (x != '' and True) or False, files_to_compress)
            else:
                # use_compression_root == 'this_root':
                if this_root is None:
                    raise EZArchiveError("if compression_root=='this_root' then argument this_root must be specified")

                this_root = os.path.abspath(os.path.expanduser(os.path.normpath(this_root)))

                # check that this_root is indeed a prefix of all of the input
                # files we've been given:
                if input != filter(lambda file: this_root in _dirtree(file), input):
                    raise EZArchiveError('not all files specified in argument input are children of argument this_root')
                # get rid of the entries that are exactly this_root:
                input = filter(lambda file: file != this_root, input)

                compression_root = this_root

                # Chop off this_root from input:
                if this_root == '/' or this_root == '//':
                    this_root_len = len(this_root)
                else:
                    this_root_len = len(this_root + '/')
                files_to_compress = map(lambda file: file[this_root_len:], input)

            old_cwd = os.getcwd()
            os.chdir(compression_root)

            seen_filenames = {}
            for file_to_compress in files_to_compress:

                if directory_structure == 'flatten':
                    if os.path.isdir(file_to_compress):
                        continue

                    archive_name = os.path.basename(file_to_compress)

                    archive_name = _verify_filename(name=archive_name, seen_filenames=seen_filenames,
                                                    filename_collision=filename_collision,
                                                    num_random_bits=num_random_bits,
                                                    rename_from_set=rename_from_set)
                    if archive_name == ['skip']: continue

                    archive.add_member(file_loc=file_to_compress, archive_name=archive_name,
                                       force_file_permissions=force_file_permissions,
                                       force_dir_permissions=force_dir_permissions)

                else:
                    # directory_structure == 'retain':
                    archive.add_member(file_loc=file_to_compress, archive_name=None,
                                       force_file_permissions=force_file_permissions,
                                       force_dir_permissions=force_dir_permissions)

            # get rid of the archive object, which has an open
            # filehandle, mode 'wb' on the archive file:
            # not closing this would prevent us from seeing what
            # has been written to the files.
            del archive

            # now see if we need to return anything:
            if compress_to == 'my_file':
                return None
            elif compress_to == 'temp_file':
                return tf_name
            else:
                # compress_to == 'byte_string':
                return open(archive_fullname, 'rb').read()
        except:
            # Clean up non-temporary file if we get an error:
            _delete_files(_remove_on_error)
            raise
    finally:
        # Always clean up temporary files, error or not:
        _delete_files(_remove_always)
        try:
            os.chdir(old_cwd)
        except:
            pass

class ArchiveTool:

    def __init__(self, file_loc, mode, allow_clobber=False):
        raise Exception("method must be overided in child class")

    def list_all_members(self):
        raise Exception("method must be overided in child class")
        # Should return dictionary:
        # { filename =
        #   tar_location =
        #   new_location =
        #   file_type =
        # }

    def extract_member(self, identity_object, root_dir, dir, new_filename, umask, force_file_permissions=None,
                       force_dir_permissions=None, allow_clobber=False):
        raise Exception("method must be overided in child class")

    def add_member(self, file_loc, archive_name=None, force_file_permissions=None, force_dir_permissions=None):
        raise Exception("method must be overided in child class")

class tarArchiveTool(ArchiveTool):

    # Overide this in child classes tarbz2ArchiveTool and
    # targzArchiveTool to make the mode string reflect the required
    # compression.

    def _mode_string(string):
        return string + ':'

    _mode_string = staticmethod(_mode_string)

    def __init__(self, file_loc, mode, allow_clobber=False):
        if mode not in ('r', 'w'): raise ValueError('mode argument must equal "r" or "w"')

        if mode == 'w':
            if os.path.exists(file_loc) and not allow_clobber:
                raise ClobberError(file_loc)

        # Set adjusted mode to reflect whether we are dealing with a
        # tar.gz tar.bz2 or just a tar.
        adjusted_mode = self._mode_string(mode)

        self._tarfile_obj = tarfile.open(name=file_loc, mode=adjusted_mode)
        self._tarfile_obj.errorlevel=2
        self._mode = mode
        self._filename = os.path.basename(file_loc)
        self._file_loc = file_loc

    def list_all_members(self):
        _check_mode(self._mode, 'r')

        f = lambda tarinfo_obj:  { 'name' : os.path.basename(os.path.normpath(tarinfo_obj.name)),
                                   'dir' : os.path.dirname(os.path.normpath(tarinfo_obj.name)),
                                   'file_type' : _file_type(tarinfo_obj),
                                   'identity_object' : tarinfo_obj }

        return map(f, self._tarfile_obj.getmembers())

    def extract_member(self, identity_object, root_dir, dir, new_filename, umask, force_file_permissions=None,
                       force_dir_permissions=None, allow_clobber=False):
        _check_mode(self._mode, 'r')

        tarinfo_obj = identity_object

        output_location = os.path.join(root_dir, dir, new_filename)

        if os.path.exists(output_location) and not allow_clobber:
            raise ClobberError(output_location)

        # Extract the file to the given location.

        saved_name = tarinfo_obj.name
        tarinfo_obj.name = os.path.join(dir, new_filename)
        saved_mode = tarinfo_obj.mode
        tarinfo_obj.mode = _calc_perms(tarinfo_obj.mode, umask) # Apply umask to permissions.

        try:
            self._tarfile_obj.extract(tarinfo_obj, root_dir)
        except EnvironmentError as e:
            if e.errno == 13:

                def f():
                    # Have already done this, but permissions might
                    # have caused a fallacious answer previously:
                    if os.path.exists(output_location) and not allow_clobber:
                        raise ClobberError(output_location)
                    elif os.path.exists(output_location) and allow_clobber:
                        if os.path.isdir(output_location):
                            # can ignore dirs; we can overwrite them
                            # whatever their current perms
                            pass
                        else:
                            # non-write permissions will prevent
                            # .extract method from overwriting, so
                            # unlink first:
                            os.unlink(output_location)
                    return self._tarfile_obj.extract(tarinfo_obj, root_dir)

                number_dotdot = _count_dotdot(dir)

                if number_dotdot != 0:
                    # This is the reason why allow_dotdot_paths = True is v. dangerous:
                    barrier_dir = None
#                     shunted_root_dir = os.path.join(root_dir, '../' * number_dotdot)
#                     normed_shunted_root_dir = os.path.normpath(shunted_root_dir)
#                     barrier_dir = normed_shunted_root_dir
                else:
                    barrier_dir=root_dir

                _provide_dir_with_perms_then_exec(dir=os.path.join(root_dir, dir), function=f, perms=0700, barrier_dir=barrier_dir)
            else:
                raise

        tarinfo_obj.name = saved_name
        tarinfo_obj.mode = saved_mode

        # If we've been asked to force permissions, do so:
        type = _file_type(tarinfo_obj)

        if type == 'regular':
            if force_file_permissions is not None:
                try:
                    os.chmod(output_location, force_file_permissions)
                except EnvironmentError as e:
                    if e.errno == 13:
                        f = lambda: os.chmod(output_location, force_file_permissions)
                        _provide_dir_with_perms_then_exec(dir=os.path.join(root_dir, dir), function=f, perms=0700, barrier_dir=root_dir)
                    else:
                        raise

        elif type == 'dir':
            if force_dir_permissions is not None:
                try:
                    os.chmod(output_location, force_dir_permissions)
                except EnvironmentError as e:
                    if e.errno == 13:
                        f = lambda: os.chmod(output_location, force_dir_permissions)
                        _provide_dir_with_perms_then_exec(dir=os.path.join(root_dir, dir), function=f, perms=0700, barrier_dir=root_dir)
                    else:
                        raise
        else:
            # We don't attempt to play with permissions of special
            # file types.
            pass

    def add_member(self, file_loc, archive_name=None, force_file_permissions=None, force_dir_permissions=None):
        _check_mode(self._mode, 'w')

        if archive_name is None:
            archive_name = file_loc

        tarinfo_obj = self._tarfile_obj.gettarinfo(name=file_loc, arcname=archive_name)

        if tarinfo_obj is None:
            if WARN_SKIP:
                sys.stderr.write("Skipping unsupported file type (eg. socket): %s\n" % (file_loc))
            return None

        if os.path.isdir(file_loc) and force_dir_permissions is not None:
            tarinfo_obj.mode = force_dir_permissions

        if os.path.isfile(file_loc) and force_file_permissions is not None:
            tarinfo_obj.mode = force_file_permissions

        if tarinfo_obj.isfile():
            self._tarfile_obj.addfile(tarinfo_obj, open(file_loc, 'rb'))
        else:
            self._tarfile_obj.addfile(tarinfo_obj)

class targzArchiveTool(tarArchiveTool):

    def _mode_string(string):
        return string + ':gz'

    _mode_string = staticmethod(_mode_string)

class tarbz2ArchiveTool(tarArchiveTool):

    def _mode_string(string):
        return string + ':bz2'

    _mode_string = staticmethod(_mode_string)

class zipArchiveTool(ArchiveTool):
    pass

class CompressTool:
    # Use to prevent trying to compress multiple files into the
    # unstructured gz file (if you want to do this, use a tar.gz,
    # tar.bz2, zip instead!):
    _write_protected = False

    def __init__(self, file_loc, mode, allow_clobber=False):
        """
        Overided child methods must set class properties:
        self._fh
        self._filename
        self._file_loc
        self._mode
        """
        self._mode = None
        self._ext = None
        self._filename = None
        self._fh = None

        raise Exception("Method must be overridden in child class")

    def list_all_members(self):
        _check_mode(self._mode, 'r')

        uncompressed_filename = re.sub(r'\.' + self._ext + r'$', '', string=self._filename, count=1)

        return [{ 'name' : uncompressed_filename,
                  'dir' : '',
                  'file_type' : 'regular',
                  'identity_object' : None } ]

    def extract_member(self, identity_object, root_dir, dir, new_filename, umask, force_file_permissions=None,
                       force_dir_permissions=None, allow_clobber=False):
        _check_mode(self._mode, 'r')

        output_location = os.path.join(root_dir, dir, new_filename)

        if os.path.exists(output_location) and not allow_clobber:
            raise ClobberError(output_location)
        elif os.path.exists(output_location) and allow_clobber:
            # unlink instead of just overwriting: this makes sure the
            # file permissions take the umask into account:
            os.unlink(output_location)

        output_fh = open(output_location, 'wb')
        output_fh.write(self._fh.read())
        output_fh.close()

        # See if we need to force the file permissions.  Otherwise, we
        # do nothing, since open call above will have obeyed the
        # system umask.
        if force_file_permissions is not None:
            os.chmod(output_location, force_file_permissions)

    def add_member(self, file_loc, archive_name=None, force_file_permissions=None, force_dir_permissions=None):

        if not os.path.isfile(file_loc):
            raise EZArchiveError("%s file format only supports compression of regular files: %s" % (self._ext, file_loc))

        if not self._write_protected:
            input_fh = open(file_loc, 'rb')
            self._fh.write(input_fh.read())

            input_fh.close()
            self._fh.close()

            self._write_protected = True
        else:
            raise EZArchiveError('tried to compress more than one file into a single %s file' % (self._ext))

class gzCompressTool(CompressTool):

    def __init__(self, file_loc, mode, allow_clobber=False):
        if mode not in ('r', 'w'): raise ValueError('mode argument must equal "r" or "w"')

        if mode == 'w':
            if os.path.exists(file_loc) and not allow_clobber:
                raise ClobberError(file_loc)

        self._fh = gzip.GzipFile(file_loc, mode=mode+'b')
        self._filename = os.path.basename(file_loc)
        self._file_loc = file_loc
        self._mode = mode
        self._ext = 'gz'

class bz2CompressTool(CompressTool):
    def __init__(self, file_loc, mode, allow_clobber=False):
        if mode not in ('r', 'w'): raise ValueError('mode argument must equal "r" or "w"')

        if mode == 'w':
            if os.path.exists(file_loc) and not allow_clobber:
                raise ClobberError(file_loc)

        if not _got_bz2:
            raise ImportError('Failed to import bz2 module.')
        self._fh = bz2.BZ2File(file_loc, mode=mode+'b')
        self._filename = os.path.basename(file_loc)
        self._file_loc = file_loc
        self._mode = mode
        self._ext = 'bz2'

available_tools = { 'tar' : tarArchiveTool,
                    'tar.gz' : targzArchiveTool,
                    'tar.bz2' : tarbz2ArchiveTool,
                    'zip' : zipArchiveTool,
                    'gz' : gzCompressTool,
                    'bz2' : bz2CompressTool }

# Errors:

class _ModeError(Exception):
    """
    This is a private error raised iff there is an attempt to use a
    class method that is not allowed by the 'mode' in which the class
    instance has been instantiated. Eg. If we have created a
    CompressTool in write mode, and we try to use a method intended
    only for use in read mode.

    This should only occur in the case of a programming error in the
    module.
    """

    pass

class _NotInArchive(Exception):
    """
    A private error raised iff there is an attempt to extract a file
    from a given archive that does not exist inside the archive.

    This should only occur in the case of a programming error in the
    module.
    """

    pass

class EZArchiveError(Exception):

    pass

class ClobberError(EZArchiveError):

    pass

def tester(tar):

    t = targzArchiveTool(tar, mode='r', allow_clobber=False)

    for mem in t.list_all_members():

        name = mem['name']
        dir = mem['dir']
        identity_object = mem['identity_object']

        t.extract_member(identity_object=identity_object, root_dir='/tmp', dir=dir, new_filename=name,
                         umask=0002, force_file_permissions=None, force_dir_permissions=None, allow_clobber=False)

def tester2(file):
    tar = tarfile.open(file, mode="r:gz")
    for tarinfo in tar:
        tar.extract(tarinfo, '/tmp/')
    tar.close()

