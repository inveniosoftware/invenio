## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"
__apilevel__ = 1.04

"""
Defines an intbitset data object to hold unordered sets of unsigned
integers with ultra fast set operations, implemented via bit vectors
and Python C extension to optimize speed and memory usage.

Emulates the Python built-in set class interface with some additional
specific methods such as its own fast dump and load marshalling
functions.  Uses real bits to optimize memory usage, so may have
issues with endianness if you transport serialized bitsets between
various machine architectures.

Please note that no bigger than __maxelem__ elements can be added to
an intbitset and, if CFG_INTBITSET_ENABLE_SANITY_CHECKS is disabled,
you will receive unpredictable results.

Note to Invenio developers: If you make modification to this file you
have to manually regenerate intbitset.c by running:
  $ cython intbitset.pyx
and then commit generated intbitset.c to CVS.
"""

import zlib
import sys
from array import array
from invenio.config import CFG_INTBITSET_ENABLE_SANITY_CHECKS
from invenio.intbitset_helper import _

__all__ = ['intbitset']

cdef extern from "intbitset.h":
    ctypedef int Py_ssize_t

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)
    int PyObject_AsReadBuffer(object obj, void **buf, Py_ssize_t *buf_len)

cdef extern from "intbitset.h":
    ctypedef unsigned long long int word_t
    #ctypedef unsigned char bool_t
    ctypedef struct IntBitSet:
        int size
        int allocated
        word_t trailing_bits
        int tot
        word_t *bitset
    int wordbytesize
    int wordbitsize
    int maxelem
    IntBitSet *intBitSetCreate(int size, bint trailing_bits)
    IntBitSet *intBitSetCreateFromBuffer(void *buf, int bufsize)
    IntBitSet *intBitSetCreateNoAllocate()
    IntBitSet *intBitSetResetFromBuffer(IntBitSet *bitset, void *buf, int bufsize)
    IntBitSet *intBitSetReset(IntBitSet *bitset)
    void intBitSetDestroy(IntBitSet *bitset)
    IntBitSet *intBitSetClone(IntBitSet *bitset)
    int intBitSetGetSize(IntBitSet *bitset)
    int intBitSetGetAllocated(IntBitSet *bitset)
    int intBitSetGetTot(IntBitSet * bitset)
    bint intBitSetIsInElem(IntBitSet *bitset, int elem)
    void intBitSetAddElem(IntBitSet *bitset, int elem)
    void intBitSetDelElem(IntBitSet *bitset, int elem)
    bint intBitSetEmpty(IntBitSet *bitset)
    IntBitSet *intBitSetUnion(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetIntersection(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetSub(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetXor(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetIUnion(IntBitSet *dst, IntBitSet *src)
    IntBitSet *intBitSetIIntersection(IntBitSet *dst, IntBitSet *src)
    IntBitSet *intBitSetISub(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetIXor(IntBitSet *x, IntBitSet *y)
    int intBitSetGetNext(IntBitSet *x, int last)
    int intBitSetGetLast(IntBitSet *x)
    unsigned char intBitSetCmp(IntBitSet *x, IntBitSet *y)

__maxelem__ = maxelem

cdef class intbitset:
    """
    Defines an intbitset data object to hold unordered sets of
    unsigned integers with ultra fast set operations, implemented via
    bit vectors and Python C extension to optimize speed and memory
    usage.

    Emulates the Python built-in set class interface with some
    additional specific methods such as its own fast dump and load
    marshalling functions.  Uses real bits to optimize memory usage,
    so may have issues with endianness if you transport serialized
    bitsets between various machine architectures.

    The constructor accept the following parameters:
        rhs=0, int preallocate=-1, int trailing_bits=0,
        bint sanity_checks=CFG_INTBITSET_ENABLE_SANITY_CHECKS,
        int no_allocate=0:

    where:
        * rhs can be:
            - int/long for creating allocating empty intbitset that will hold at least
            rhs elements, before being resized
            - intbitset for cloning
            - str for retrieving an intbitset that was dumped into a string
            - array for retrieving an intbitset that was dumped into a string stored
            in an array
            - sequence made of integers for copying all the elements from the
            sequence. If minsize is specified than it is initially allocated
            enough space to hold up to minsize integers, otherwise the biggest
            element of the sequence will be used.
            - sequence made of tuples: then the first element of each tuple
            is considered as an integer (as in the sequence made of integers).
        * preallocate is a suggested initial upper bound on the numbers that will be
            stored, by looking at rhs a sequence of number.
        * trailing_bits is 1, then the set will contain "all" the positive integers
        * no_allocate is used internally and should never be set.
        after the biggest one added with rhs.
    """
    cdef IntBitSet *bitset
    cdef bint sanity_checks

    def __cinit__(self, rhs=0, int preallocate=-1, int trailing_bits=0, bint sanity_checks=CFG_INTBITSET_ENABLE_SANITY_CHECKS, int no_allocate=0):
        """
        Initialize intbitset.
        * rhs can be:
         - int/long for creating allocating empty intbitset that will hold at least
            rhs elements, before being resized
         - intbitset for cloning
         - str for retrieving an intbitset that was dumped into a string
         - array for retrieving an intbitset that was dumped into a string stored
            in an array
         - sequence made of integers for copying all the elements from the
            sequence. If minsize is specified than it is initially allocated
            enough space to hold up to minsize integers, otherwise the biggest
            element of the sequence will be used.
        * preallocate is a suggested initial upper bound on the numbers that will be
            stored, by looking at rhs a sequence of number.
        * trailing_bits is 1, then the set will contain "all" the positive integers
        * no_allocate is used internally and should never be set.
        after the biggest one added with rhs.
        """
        cdef Py_ssize_t size = 0
        cdef void *buf = NULL
        cdef int elem
        cdef int i
        cdef int last
        cdef int remelem
        cdef bint tuple_of_tuples
        self.sanity_checks = sanity_checks
        #print >> sys.stderr, "intbitset.__cinit__ is called"
        msg = "Error"
        self.bitset = NULL
        try:
            if no_allocate:
                return
            if type(rhs) in (int, long):
                if rhs < 0:
                    raise ValueError("rhs can't be negative")
                self.bitset = intBitSetCreate(rhs, trailing_bits)
            elif type(rhs) is intbitset:
                self.bitset = intBitSetClone((<intbitset>rhs).bitset)
            elif type(rhs) in (str, array):
                try:
                    if type(rhs) is array:
                        rhs = rhs.tostring()
                    tmp = zlib.decompress(rhs)
                    if PyObject_AsReadBuffer(tmp, &buf, &size) < 0:
                        raise Exception("Buffer error!!!")
                    if (size % wordbytesize):
                        ## Wrong size!
                        raise Exception()
                    self.bitset = intBitSetCreateFromBuffer(buf, size)
                except Exception, msg:
                    raise ValueError("rhs is corrupted: %s" % msg)
            elif hasattr(rhs, '__iter__'):
                tuple_of_tuples = rhs and type(rhs[0]) is tuple
                try:
                    if preallocate < 0:
                        if rhs and type(rhs[0]) is int:
                            preallocate = max(rhs)
                        else:
                            preallocate = 0
                    if self.sanity_checks:
                        if not (0 <= preallocate < maxelem):
                            raise OverflowError("Can't store integers bigger than %s" % maxelem)
                    self.bitset = intBitSetCreate(preallocate, trailing_bits)
                    if trailing_bits:
                        last = 0
                        if self.sanity_checks:
                            if tuple_of_tuples:
                                for tmp_tuple in rhs:
                                    elem = tmp_tuple[0]
                                    if elem < 0:
                                        raise ValueError("Negative numbers, not allowed")
                                    elif elem > maxelem:
                                        raise OverflowError("Elements must be <= %s" % maxelem)
                                    for remelem from last <= remelem < elem:
                                        intBitSetDelElem(self.bitset, remelem)
                                    last = elem + 1
                            else:
                                for elem in rhs:
                                    if elem < 0:
                                        raise ValueError("Negative numbers, not allowed")
                                    elif elem > maxelem:
                                        raise OverflowError("Elements must be <= %s" % maxelem)
                                    for remelem from last <= remelem < elem:
                                        intBitSetDelElem(self.bitset, remelem)
                                    last = elem + 1
                        else:
                            if tuple_of_tuples:
                                for tmp_tuple in rhs:
                                    elem = tmp_tuple[0]
                                    for remelem from last <= remelem < elem:
                                        intBitSetDelElem(self.bitset, remelem)
                                    last = elem + 1
                            else:
                                for elem in rhs:
                                    for remelem from last <= remelem < elem:
                                        intBitSetDelElem(self.bitset, remelem)
                                    last = elem + 1

                    else:
                        if self.sanity_checks:
                            if tuple_of_tuples:
                                for tmp_tuple in rhs:
                                    elem = tmp_tuple[0]
                                    if elem < 0:
                                        raise ValueError("Negative numbers, not allowed")
                                    elif elem > maxelem:
                                        raise OverflowError("Elements must be <= %s" % maxelem)
                                    intBitSetAddElem(self.bitset, elem)
                            else:
                                for elem in rhs:
                                    if elem < 0:
                                        raise ValueError("Negative numbers, not allowed")
                                    elif elem > maxelem:
                                        raise OverflowError("Elements must be <= %s" % maxelem)
                                    intBitSetAddElem(self.bitset, elem)
                        else:
                            if tuple_of_tuples:
                                for tmp_tuple in rhs:
                                    elem = tmp_tuple[0]
                                    intBitSetAddElem(self.bitset, elem)
                            else:
                                for elem in rhs:
                                    intBitSetAddElem(self.bitset, elem)
                except Exception, msg:
                    raise ValueError("retrieving integers from rhs is impossible: %s" % msg)
            else:
                raise TypeError("rhs is of unknown type %s" % type(rhs))
        except:
            intBitSetDestroy(self.bitset)
            raise

    def __dealloc__(self):
        #print >> sys.stderr, "intbitset.__dealloc__ is called"
        intBitSetDestroy(self.bitset)

    def __contains__(self, int elem):
        if self.sanity_checks:
            if elem < 0:
                raise ValueError("Negative numbers, not allowed")
            elif elem > maxelem:
                raise OverflowError("Element must be <= %s" % maxelem)
        return intBitSetIsInElem(self.bitset, elem) != 0

    def __cmp__(self, intbitset rhs not None):
        raise TypeError("cannot compare intbitset using cmp()")

    def __richcmp__(self, intbitset rhs not None, int op):
        cdef short unsigned int tmp
        tmp = intBitSetCmp((<intbitset>self).bitset, rhs.bitset)
        if op == 0: # <
            return tmp == 1
        if op == 1: # <=
            return tmp <= 1
        if op == 2: # ==
            return tmp == 0
        if op == 3: # !=
            return tmp > 0
        if op == 4: # >
            return tmp == 2
        if op == 5: # >=
            return tmp in (0, 2)

    def __len__(self):
        return intBitSetGetTot(self.bitset)

    def __hash__(self):
        return hash(PyString_FromStringAndSize(<char *>self.bitset.bitset, wordbytesize * (intBitSetGetTot(self.bitset) / wordbitsize + 1)))

    def __nonzero__(self):
        return not intBitSetEmpty(self.bitset)

    def __iadd__(self, rhs):
        cdef int elem
        if isinstance(rhs, (int, long)):
            if self.sanity_checks:
                if rhs < 0:
                    raise ValueError("Negative numbers, not allowed")
                elif rhs > maxelem:
                    raise OverflowError("rhs must be <= %s" % maxelem)
            intBitSetAddElem(self.bitset, rhs)
        elif isinstance(rhs, intbitset):
            intBitSetIUnion(self.bitset, (<intbitset> rhs).bitset)
        else:
            if self.sanity_checks:
                for elem in rhs:
                    if elem < 0:
                        raise ValueError("Negative numbers, not allowed")
                    elif elem > maxelem:
                        raise OverflowError("Elements must be <= %s" % maxelem)
                    intBitSetAddElem(self.bitset, elem)
            else:
                for elem in rhs:
                    if elem < 0:
                        raise ValueError("Negative numbers, not allowed")
                    elif elem > maxelem:
                        raise OverflowError("Elements must be <= %s" % maxelem)
                    intBitSetAddElem(self.bitset, elem)
        return self

    def __isub__(self, rhs):
        cdef int elem
        if isinstance(rhs, (int, long)):
            if self.sanity_checks:
                if rhs < 0:
                    raise ValueError("Negative numbers, not allowed")
                elif rhs > maxelem:
                    raise OverflowError("rhs must be <= %s" % maxelem)
            intBitSetDelElem(self.bitset, rhs)
        elif isinstance(rhs, intbitset):
            intBitSetISub(self.bitset, (<intbitset> rhs).bitset)
        else:
            if self.sanity_checks:
                for elem in rhs:
                    if elem < 0:
                        raise ValueError("Negative numbers, not allowed")
                    elif elem > maxelem:
                        raise OverflowError("Elements must be <= %s" % maxelem)
                    intBitSetDelElem(self.bitset, elem)
            else:
                for elem in rhs:
                    intBitSetDelElem(self.bitset, elem)
        return self

    def __deepcopy__(self, memo):
        return intbitset(self)

    def __del__(self, int elem):
        if self.sanity_checks:
            if elem < 0:
                raise ValueError("Negative numbers, not allowed")
            elif elem > maxelem:
                raise OverflowError("Element must be <= %s" % maxelem)
        intBitSetDelElem(self.bitset, elem)

    def __and__(self, intbitset rhs not None):
        ret = intbitset(no_allocate=1)
        (<intbitset>ret).bitset = intBitSetIntersection((<intbitset> self).bitset, rhs.bitset)
        return ret

    def __or__(self, intbitset rhs not None):
        ret = intbitset(no_allocate=1)
        (<intbitset>ret).bitset = intBitSetUnion((<intbitset> self).bitset, rhs.bitset)
        return ret

    def __xor__(self, intbitset rhs not None):
        ret = intbitset(no_allocate=1)
        (<intbitset>ret).bitset = intBitSetXor((<intbitset> self).bitset, rhs.bitset)
        return ret

    def __sub__(self, intbitset rhs not None):
        ret = intbitset(no_allocate=1)
        (<intbitset>ret).bitset = intBitSetSub((<intbitset> self).bitset, rhs.bitset)
        return ret

    def __iand__(self, intbitset rhs not None):
        intBitSetIIntersection(self.bitset, rhs.bitset)
        return self

    def __ior__(self, intbitset rhs not None):
        intBitSetIUnion(self.bitset, rhs.bitset)
        return self

    def __ixor__(self, intbitset rhs not None):
        intBitSetIXor(self.bitset, rhs.bitset)
        return self

    def __repr__(self):
        cdef int last
        cdef int maxelem
        cdef int next_last
        finite_list = self.extract_finite_list()
        if self.bitset.trailing_bits:
            return "intbitset(%s, trailing_bits=True)" % repr(finite_list)
        else:
            return "intbitset(%s)" % repr(finite_list)

    def __str__(self):
        cdef int tot
        tot = intBitSetGetTot(self.bitset)
        if tot < 0:
            begin_list = self.to_sorted_list(0, 10)
            ret = "intbitset(["
            for n in begin_list:
                ret = ret + '%i, ' % n
            ret = ret + "...])"
            return ret
        elif tot > 10:
            begin_list = self.to_sorted_list(0, 5)
            end_list = self.to_sorted_list(tot - 5, tot)
            ret = "intbitset(["
            for n in begin_list:
                ret = ret + '%i, ' % n
            ret = ret + "..., "
            for n in end_list:
                ret = ret + '%i, ' % n
            ret = ret[:-2]
            ret = ret + '])'
            return ret
        else:
            return self.__repr__()

    ## Buffer interface
    #def __getreadbuffer__(self, int i, void **p):
        #if i != 0:
            #return -1
        #p[0] = (<intbitset >self).bitset
        #return (<intbitset >self).size * wordbytesize

    #def __getwritebuffer__(self, int i, void **p):
        #if i != 0:
            #raise SystemError
        #p[0] = (<intbitset >self).bitset
        #return (<intbitset >self).size * wordbytesize

    #def __getsegcount__(self, int *p):
        #if p != NULL:
            #p[0] = (<intbitset >self).size * wordbytesize
        #return 1

    #def __getcharbuffer__(self, int i, char **p):
        #if i != 0:
            #return -1
        #p[0] = <char *> (<intbitset >self).bitset
        #return (<intbitset >self).size * wordbytesize

    # pickle interface
    def __reduce__(self):
        return _, (self.fastdump(),)

    __safe_for_unpickling__ = True

    # Iterator interface
    def __iter__(self):
        if self.bitset.trailing_bits:
            raise OverflowError("It's impossible to iterate over an infinite set.")
        return intbitset_iterator(self)

    # Customized interface
    def add(self, int elem):
        """Add an element to a set.
        This has no effect if the element is already present."""
        if self.sanity_checks:
            if elem < 0:
                raise ValueError("Negative numbers, not allowed")
            elif elem > maxelem:
                raise OverflowError("Element must be <= %s" % maxelem)
        intBitSetAddElem(self.bitset, elem)

    def clear(self):
        intBitSetReset(self.bitset)

    def difference(intbitset self, rhs):
        """Return the difference of two intbitsets as a new set.
        (i.e. all elements that are in this intbitset but not the other.)
        """
        return self.__sub__(rhs)

    def difference_update(self, rhs):
        """Remove all elements of another set from this set."""
        self.__isub__(rhs)

    def discard(self, int elem):
        """Remove an element from a intbitset if it is a member.
        If the element is not a member, do nothing."""
        if self.sanity_checks:
            if elem < 0:
                raise ValueError("Negative numbers, not allowed")
            elif elem > maxelem:
                raise OverflowError("Element must be <= %s" % maxelem)
        intBitSetDelElem(self.bitset, elem)

    def intersection(self, rhs):
        """Return the intersection of two intbitsets as a new set.
        (i.e. all elements that are in both intbitsets.)
        """
        return self.__and__(rhs)

    def intersection_update(self, rhs):
        """Update a intbitset with the intersection of itself and another."""
        self.__iand__(rhs)

    def union(self, rhs):
        """Return the union of two intbitsets as a new set.
        (i.e. all elements that are in either intbitsets.)
        """
        return self.__or__(rhs)

    def union_update(self, rhs):
        """Update a intbitset with the union of itself and another."""
        self.__ior__(rhs)

    def issubset(self, rhs):
        """Report whether another set contains this set."""
        return self.__le__(rhs)

    def issuperset(self, rhs):
        """Report whether this set contains another set."""
        return self.__ge__(rhs)

    def symmetric_difference(self, rhs):
        """Return the symmetric difference of two sets as a new set.
        (i.e. all elements that are in exactly one of the sets.)
        """
        return self.__xor__(rhs)

    def symmetric_difference_update(self, rhs):
        """Update an intbitset with the symmetric difference of itself and another.
        """
        self.__ixor__(rhs)

    # Dumping & Loading
    def fastdump(self):
        """Return a compressed string representation suitable to be saved
        somewhere."""
        cdef Py_ssize_t size
        size = intBitSetGetSize((<intbitset> self).bitset)
        tmp = PyString_FromStringAndSize(<char *>self.bitset.bitset, ( size + 1) * wordbytesize)
        return zlib.compress(tmp)

    def fastload(self, strdump):
        """Load a compressed string representation produced by a previous call
        to the fastdump method into the current intbitset. The previous content
        will be replaced."""
        cdef Py_ssize_t size
        cdef void *buf
        buf = NULL
        size = 0
        try:
            if type(strdump) is array:
                strdump = strdump.tostring()
            # tmp needed to not be garbage collected
            tmp = zlib.decompress(strdump)
            if PyObject_AsReadBuffer(tmp, &buf, &size) < 0:
                raise Exception()
            if (size % wordbytesize):
                ## Wrong size!
                raise Exception()
            intBitSetResetFromBuffer((<intbitset> self).bitset, buf, size)
        except:
            raise ValueError("strdump is corrupted")
        return self

    def copy(self):
        """Return a shallow copy of a set."""
        return intbitset(self)

    def pop(self):
        """Remove and return an arbitrary set element.

        @note: intbitset implementation of .pop() differs from the native C{set}
            implementation by guaranteeing returning always the largest element.
        """
        cdef int ret
        ret = intBitSetGetLast(self.bitset)
        if ret < 0:
            raise KeyError("pop from an empty or infinite intbitset")
        intBitSetDelElem(self.bitset, ret)
        return ret

    def remove(self, int elem):
        """Remove an element from a set; it must be a member.
        If the element is not a member, raise a KeyError.
        """
        if self.sanity_checks:
            if elem < 0:
                raise ValueError("Negative numbers, not allowed")
            elif elem > maxelem:
                raise OverflowError("Elements must be <= %s" % maxelem)
        if intBitSetIsInElem(self.bitset, elem):
            intBitSetDelElem(self.bitset, elem)
        else:
            raise KeyError(elem)

    def strbits(self):
        """Return a string of 0s and 1s representing the content in memory
        of the intbitset.
        """
        cdef int i
        cdef int last
        if (<intbitset> self).bitset.trailing_bits:
            raise OverflowError("It's impossible to print an infinite set.")
        last = 0
        ret = []
        for i in self:
            ret.append('0'*(i-last)+'1')
            last = i+1
        return ''.join(ret)

    def update_with_signs(self, rhs):
        """Given a dictionary rhs whose keys are integers, remove all the integers
        whose value are less than 0 and add every integer whose value is 0 or more"""
        cdef int value
        try:
            if self.sanity_checks:
                for value, sign in rhs.iteritems():
                    if value < 0:
                        raise ValueError("Negative numbers, not allowed")
                    elif value > maxelem:
                        raise OverflowError("Elements must <= %s" % maxelem)
                    if sign < 0:
                        intBitSetDelElem(self.bitset, value)
                    else:
                        intBitSetAddElem(self.bitset, value)
            else:
                for value, sign in rhs.iteritems():
                    if sign < 0:
                        intBitSetDelElem(self.bitset, value)
                    else:
                        intBitSetAddElem(self.bitset, value)
        except AttributeError:
            raise TypeError("rhs should be a valid dictionary with integers keys and integer values")

    def get_size(self):
        return intBitSetGetSize(self.bitset)

    def get_allocated(self):
        return intBitSetGetAllocated(self.bitset)

    def get_sorted_element(self, int index):
        """Return element at position index in the sorted representation of the
        set. Note that index must be less than len(self)"""
        cdef int l
        cdef int last
        cdef int i
        l = intBitSetGetTot(self.bitset)
        if index < 0:
            if self.bitset.trailing_bits:
                raise OverflowError("It's impossible to retrieve a negative item from an infinite set.")
            index = index + l
        elif index > maxelem:
            raise OverflowError("Index must be <= %s" % maxelem)
        if 0 <= index < l:
            last = intBitSetGetNext(self.bitset, -1)
            for i from 0 <= i < index:
                last = intBitSetGetNext(self.bitset, last)
        else:
            raise IndexError("intbitset index out of range")
        return last

    def to_sorted_list(self, int i, int j):
        """Return a sublist of the sorted representation of the set.
        Note, negative indices are not supported."""
        cdef int l
        cdef int last
        cdef int cnt
        if self.bitset.trailing_bits and (i < 0 or j < 0):
            raise OverflowError("It's impossible to retrieve a sublist using negative indices from an infinite set.")
        elif (i > maxelem or j > maxelem):
            raise OverflowError("Indexes must be <= %s" % maxelem)
        l = intBitSetGetTot(self.bitset)
        if i == 0 and j == -1:
            return intbitset(self)
        ret = intbitset()
        if i < 0:
            i = i + l
        if j < 0:
            j = j + l
        if i >= l:
            i = l
        if j >= l:
            j = l
        last = -1
        for cnt from 0 <= cnt < i:
            last = intBitSetGetNext(self.bitset, last)
        for cnt from i <= cnt < j:
            last = intBitSetGetNext(self.bitset, last)
            intBitSetAddElem((<intbitset> ret).bitset, last)
        return ret

    def is_infinite(self):
        """Return True if the intbitset is infinite. (i.e. trailing_bits=True
        was used in the constructor.)"""
        return self.bitset.trailing_bits != 0

    def extract_finite_list(self, int up_to=-1):
        """Return a finite list of elements sufficient to be passed to intbitset
        constructor toghether with the proper value of trailing_bits in order
        to reproduce this intbitset. At least up_to integer are looked for when
        they are inside the intbitset but not necessarily needed to build the
        intbitset"""
        cdef int true_up_to
        cdef int last
        if self.sanity_checks and up_to > maxelem:
            raise OverflowError("up_to must be <= %s" % maxelem)
        ret = []
        true_up_to = max(up_to, (intBitSetGetSize(self.bitset)) * wordbitsize)
        last = -1
        while last < true_up_to:
            last = intBitSetGetNext(self.bitset, last)
            if last == -2:
                break
            ret.append(last)
        return ret

    def get_wordbitsize(self):
        return wordbitsize

    def get_wordbytsize(self):
        return wordbytesize

    def tolist(self):
        """Legacy method to retrieve a list of all the elements inside an
        intbitset.
        """
        if self.bitset.trailing_bits:
            raise OverflowError("It's impossible to retrieve a list of an infinite set")
        return self.extract_finite_list()

    cdef object __weakref__

cdef class intbitset_iterator:
    cdef int last
    cdef IntBitSet *bitset
    cdef bint sanity_checks

    def __cinit__(self, intbitset bitset not None):
        #print >> sys.stderr, "intbitset_iterator.__cinit__ is called"
        self.last = -1
        ## A copy should be performed, in case the original bitset disappears
        ## as in "for x in intbitset([1,2,3])"!
        self.bitset = intBitSetClone(bitset.bitset)
        self.sanity_checks = CFG_INTBITSET_ENABLE_SANITY_CHECKS

    def __dealloc__(self):
        #print >> sys.stderr, "intbitset_iterator.__dealloc__ is called"
        intBitSetDestroy(self.bitset)

    def __next__(self):
        if self.last == -2:
            raise StopIteration()
        self.last = intBitSetGetNext(self.bitset, self.last)
        if self.sanity_checks and (self.bitset.allocated < self.bitset.size):
            raise MemoryError("intbitset corrupted: allocated: %s, size: %s" % (self.bitset.allocated, self.bitset.size))
        if self.last < 0:
            self.last = -2
            raise StopIteration()
        return self.last

    def __iter__(self):
        return self

    cdef object __weakref__
