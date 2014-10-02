import invenio.bibauthorid_config as bconfig
import os
import shutil
from cPickle import dump, load, UnpicklingError
from invenio.bibauthorid_dbinterface import get_db_time
from invenio.bibauthorid_logutils import Logger
import h5py
import errno


class Bib_matrix(object):

    '''
    Contains the sparse matrix and encapsulates it.
    '''
    # please increment this value every time you
    # change the output of the comparison functions
    current_comparison_version = 0

    __special_items = ((None, -3.), ('+', -2.), ('-', -1.))
    special_symbols = dict((x[0], x[1]) for x in __special_items)
    special_numbers = dict((x[1], x[0]) for x in __special_items)

    def __init__(self, name, cluster_set=None, storage_dir_override=None):
        self.name = name
        self._f = None
        self._matrix = None
        self._use_temporary_file = True
        self._size = None

        self._storage_dir_override = storage_dir_override

        if cluster_set:
            self._bibmap = dict((b[1], b[0]) for b in enumerate(cluster_set.all_bibs()))
            width = len(self._bibmap)
            self._size = ((width + 1) * width) / 2
        else:
            self._bibmap = dict()

        self._matrix = None
        self.creation_time = get_db_time()

        self.logger = Logger("bib_matrix")

    def _initialize_matrix(self):
        self.open_h5py_file()
        self._matrix = self._f.create_dataset("array", (self._size, 2), 'f')
        self._matrix[...] = self.special_symbols[None]

    def _resolve_entry(self, bibs):
        first, second = bibs
        first, second = self._bibmap[first], self._bibmap[second]
        if first > second:
            first, second = second, first
        return first + (second * second + second) / 2

    def __setitem__(self, bibs, val):
        entry = self._resolve_entry(bibs)
        try:
            self._matrix[entry] = Bib_matrix.special_symbols.get(val, val)
        except TypeError:
            self._initialize_matrix()
            self._matrix[entry] = Bib_matrix.special_symbols.get(val, val)

    def __getitem__(self, bibs):
        entry = self._resolve_entry(bibs)
        try:
            ret = self._matrix[entry]
        except TypeError:
            self._initialize_matrix()
            ret = self._matrix[entry]
        return Bib_matrix.special_numbers.get(ret[0], tuple(ret))

    def getitem_numeric(self, bibs):
        return self._matrix[self._resolve_entry(bibs)]

    def __contains__(self, bib):
        return bib in self._bibmap

    def get_keys(self):
        return self._bibmap.keys()

    def get_file_dir(self):
        if self._storage_dir_override:
            return self._storage_dir_override

        sub_dir = self.name[:2]
        if not sub_dir:
            sub_dir = "empty_last_name"
        return "%s%s/" % (bconfig.TORTOISE_FILES_PATH, sub_dir)

    def get_map_path(self):
        return "%s%s-bibmap.pickle" % (self.get_file_dir(), self.name)

    def get_matrix_path(self):
        path = "%s%s.hdf5" % (self.get_file_dir(), self.name)
        if self._use_temporary_file:
            path = path + '.tmp'
        return path

    def open_h5py_file(self, create_empty_on_failure=True):
        self._prepare_destination_directory()
        path = self.get_matrix_path()

        try:
            self._f = h5py.File(path)
        except IOError as e:
            # If the file is corrupted h5py fails with IOErorr.
            # Give it a second try with an empty file before raising.
            if create_empty_on_failure:
                os.remove(path)
                self._f = h5py.File(path)
            else:
                raise e

    def load(self):
        self._use_temporary_file = False
        files_dir = self.get_file_dir()
        if not os.path.isdir(files_dir):
            self._bibmap = dict()
            self._matrix = None
            return False

        try:
            with open(self.get_map_path(), 'r') as fp:
                bibmap_v = load(fp)
            rec_v, self.creation_time, self._bibmap = bibmap_v  # pylint: disable=W0612
#                if (rec_v != Bib_matrix.current_comparison_version or
# you can use negative version to recalculate
#                    Bib_matrix.current_comparison_version < 0):
#                    self._bibmap = dict()
            self._use_temporary_file = False
            if self._f:
                self._f.close()
            self.open_h5py_file(create_empty_on_failure=False)
            self._matrix = self._f['array']

        except (IOError, UnpicklingError, KeyError, OSError) as e:

            if e.errno == errno.ENOENT:  # The file has not been created yet. If this the first time bib_matrix runs, it is fine.
                self.logger.log("Warning: The bibmap serialized file ",
                                self.get_map_path(),
                                "is not present. Will not load bibmap.")
            else:
                self.logger.log('Unexpected error occurred while loading bibmap, cleaning... ', str(type(e)), str(e))
            self._bibmap = dict()
            self._matrix = None

            try:
                os.remove(self.get_map_path())
            except OSError:
                pass
            try:
                os.remove(self.get_matrix_path())
            except OSError:
                pass
            self._use_temporary_file = True
            try:
                os.remove(self.get_matrix_path())
            except OSError:
                pass
            self._bibmap = dict()
            self._matrix = None
            self._use_temporary_file = True
            return False
        return True

    def _prepare_destination_directory(self):
        files_dir = self.get_file_dir()
        if not os.path.isdir(files_dir):
            try:
                os.mkdir(files_dir)
            except OSError as e:
                if e.errno == 17 or 'file exists' in str(e.strerror).lower():
                    pass
                else:
                    raise e

    def store(self):
        # save only if we are not completey empty:
        if self._bibmap:
            self._prepare_destination_directory()
            bibmap_v = (Bib_matrix.current_comparison_version, self.creation_time, self._bibmap)
            with open(self.get_map_path(), 'w') as fp:
                dump(bibmap_v, fp)

            if not self._matrix:
                self._initialize_matrix()

            if self._f:
                self._f.close()

                if self._use_temporary_file:
                    curpath = self.get_matrix_path()
                    self._use_temporary_file = False
                    finalpath = self.get_matrix_path()
                    try:
                        os.rename(curpath, finalpath)
                    except OSError as e:
                        raise e

    def duplicate_existing(self, name, newname):
        '''
        Make sure the original Bib_matrix have been store()-ed before calling this!
        '''
        self._use_temporary_file = False
        self.name = name
        srcmap = self.get_map_path()
        srcmat = self.get_matrix_path()
        self.name = newname
        dstmap = self.get_map_path()
        dstmat = self.get_matrix_path()

        shutil.copy(srcmap, dstmap)
        shutil.copy(srcmat, dstmat)

    def destroy(self):
        if self._f:
            self._f.close()
        try:
            os.remove(self.get_map_path())
        except OSError:
            pass
        try:
            os.remove(self.get_matrix_path())
        except OSError:
            pass
        self._use_temporary_file = True
        try:
            os.remove(self.get_matrix_path())
        except OSError:
            pass
        self._bibmap = dict()
        self._matrix = None
