# $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Fast BitSet C extension to hold unsigned integer."""

import zlib
from array import array

ctypedef unsigned long long int word_t
ctypedef unsigned int size_t
ctypedef unsigned short int bool_t
ctypedef unsigned long int Py_ssize_t

cdef extern from "Python.h":
    object PyBuffer_FromMemory(void *ptr, int size)
    object PyString_FromStringAndSize(char *s, int len)
    int PyObject_AsReadBuffer(object obj, void **buf, size_t *buf_len)
    object PySequence_Fast(object o, char *m)
    object PySequence_Fast_GET_ITEM(object o, Py_ssize_t i)
    Py_ssize_t PySequence_Fast_GET_SIZE(object o)

cdef extern from "intbitset.h":
    ctypedef struct IntBitSet:
        size_t size
        int tot
        word_t *bitset
    size_t wordbytesize
    size_t wordbitsize
    IntBitSet *intBitSetCreate(size_t size)
    IntBitSet *intBitSetCreateFull(size_t size)
    IntBitSet *intBitSetCreateFromBuffer(void *buf, size_t bufsize)
    IntBitSet *intBitSetResetFromBuffer(IntBitSet *bitset, void *buf, size_t bufsize)
    IntBitSet *intBitSetReset(IntBitSet *bitset)
    void intBitSetDestroy(IntBitSet *bitset)
    IntBitSet *intBitSetClone(IntBitSet *bitset)
    size_t intBitSetGetSize(IntBitSet *bitset)
    size_t intBitSetGetTot(IntBitSet * bitset)
    bool_t intBitSetIsInElem(IntBitSet *bitset, size_t elem)
    void intBitSetAddElem(IntBitSet *bitset, size_t elem)
    void intBitSetDelElem(IntBitSet *bitset, size_t elem)
    bool_t intBitSetEmpty(IntBitSet *bitset)
    IntBitSet *intBitSetUnion(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetIntersection(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetSub(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetXor(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetIUnion(IntBitSet *dst, IntBitSet *src)
    IntBitSet *intBitSetIIntersection(IntBitSet *dst, IntBitSet *src)
    IntBitSet *intBitSetISub(IntBitSet *x, IntBitSet *y)
    IntBitSet *intBitSetIXor(IntBitSet *x, IntBitSet *y)
    int intBitSetGetNext(IntBitSet *x, int last)
    unsigned char intBitSetCmp(IntBitSet *x, IntBitSet *y)

cdef class intbitset:
    """Fast BitSet C extension to hold unsigned integer."""
    cdef IntBitSet *bitset
    #def __init__(intbitset self, rhs=0, int minsize=-1):

        #if not self.bitset:
            #raise ValueError, "Impossible to create intbitset"
    def __new__(intbitset self, rhs=0, int minsize=-1):
        """Initialize intbitset. rhs can be:
        int/long for creating allocating empty intbitset that will hold at least
            rhs elements, before being resized
        intbitset for cloning
        str for retrieving an intbitset that was dumped into a string
        array for retrieving an intbitset that was dumpeg into a string stored
            in an array
        a sequence made of integers for copying all the elements from the
            sequence. If minsize is specified than it is initially allocated
            enough space to hold up to minsize integers, otherwise the biggest
            element of the sequence will be used.
        """
        cdef size_t size
        cdef void *buf
        cdef size_t elem
        cdef char *msg
        cdef size_t i
        msg = "Error"
        self.bitset = NULL
        if type(rhs) in (int, long):
            if rhs < 0:
                raise ValueError, "rhs can't be negative"
            self.bitset = intBitSetCreate(rhs)
        elif type(rhs) is intbitset:
            self.bitset = intBitSetClone((<intbitset>rhs).bitset)
        elif type(rhs) is str:
            try:
                tmp = zlib.decompress(rhs)
                PyObject_AsReadBuffer(tmp, &buf, &size)
                self.bitset = intBitSetCreateFromBuffer(buf, size)
            except:
                raise ValueError, "rhs is corrupted"
        elif type(rhs) is array:
            try:
                tmp = zlib.decompress(rhs.tostring())
                PyObject_AsReadBuffer(tmp, &buf, &size)
                self.bitset = intBitSetCreateFromBuffer(buf, size)
            except:
                raise ValueError, "rhs is corrupted"
        elif hasattr(rhs, '__iter__'):
            try:
                if minsize > -1:
                    self.bitset = intBitSetCreate(minsize)
                else:
                    if rhs:
                        self.bitset = intBitSetCreate(int(max(rhs)))
                    else:
                        self.bitset = intBitSetCreate(0)
                for elem in rhs:
                    intBitSetAddElem(self.bitset, elem)
            except Exception, msg:
                raise ValueError, "retrieving integers from rhs is impossible :%s" \
                    % msg
        else:
            raise TypeError, "rhs is of unknown type %s" % type(rhs)
    def __dealloc__(intbitset self):
        if self.bitset:
            intBitSetDestroy(self.bitset)
    def __contains__(intbitset self, unsigned int elem):
        return intBitSetIsInElem(self.bitset, elem) != 0
    def __cmp__(intbitset self, intbitset rhs):
        raise TypeError, "cannot compare intbitset using cmp()"
    def __richcmp__(intbitset self, intbitset rhs, int op):
        cdef short unsigned int tmp
        tmp = intBitSetCmp(self.bitset, rhs.bitset)
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
    def __len__(intbitset self):
        return intBitSetGetTot(self.bitset)
    def __hash__(intbitset self):
        return hash(PyString_FromStringAndSize(<char *>self.bitset.bitset, wordbytesize * (intBitSetGetTot(self.bitset) / wordbitsize + 1)))
    def __nonzero__(intbitset self):
        return not intBitSetEmpty(self.bitset)
    def __iadd__(intbitset self, rhs):
        cdef size_t elem
        if isinstance(rhs, (int, long)):
            intBitSetAddElem(self.bitset, rhs)
        elif isinstance(rhs, intbitset):
            intBitSetIUnion(self.bitset, (<intbitset> rhs).bitset)
        else:
            for elem in rhs:
                intBitSetAddElem(self.bitset, elem)
        return self
    def __isub__(intbitset self, rhs):
        cdef size_t elem
        if isinstance(rhs, (int, long)):
            intBitSetDelElem(self.bitset, rhs)
        elif isinstance(rhs, intbitset):
            intBitSetISub(self.bitset, (<intbitset> rhs).bitset)
        else:
            for elem in rhs:
                intBitSetDelElem(self.bitset, elem)
        return self
    def __deepcopy__(intbitset self, memo):
        return intbitset(self)
    def __del__(intbitset self, size_t elem):
        intBitSetDelElem(self.bitset, elem)
    def __and__(intbitset self, intbitset rhs):
        ret = intbitset()
        intBitSetDestroy((<intbitset>ret).bitset)
        (<intbitset>ret).bitset = intBitSetIntersection(self.bitset, rhs.bitset)
        return ret
    def __or__(intbitset self, intbitset rhs):
        ret = intbitset()
        intBitSetDestroy((<intbitset>ret).bitset)
        (<intbitset>ret).bitset = intBitSetUnion(self.bitset, rhs.bitset)
        return ret
    def __xor__(intbitset self, intbitset rhs):
        ret = intbitset()
        intBitSetDestroy((<intbitset>ret).bitset)
        (<intbitset>ret).bitset = intBitSetXor(self.bitset, rhs.bitset)
        return ret
    def __sub__(intbitset self, intbitset rhs):
        ret = intbitset()
        intBitSetDestroy((<intbitset>ret).bitset)
        (<intbitset>ret).bitset = intBitSetSub(self.bitset, rhs.bitset)
        return ret
    def __iand__(intbitset self, intbitset rhs):
        intBitSetIIntersection(self.bitset, rhs.bitset)
        return self
    def __ior__(intbitset self, intbitset rhs):
        intBitSetIUnion(self.bitset, rhs.bitset)
        return self
    def __ixor__(intbitset self, intbitset rhs):
        intBitSetIXor(self.bitset, rhs.bitset)
        return self
    def __repr__(intbitset self):
        ret = "intbitset(["
        last = -1
        while last >= -1:
            last = intBitSetGetNext(self.bitset, last)
            ret = ret + '%i, ' % last
        ret = ret[:-len('-2, ')]
        if ret.endswith(', '):
            ret = ret[:-2]
        ret = ret + '])'
        return ret
    def __iter__(intbitset self):
        return intbitset_iterator(self)
    def add(intbitset self, size_t elem):
        """Add an element to a set.
        This has no effect if the element is already present."""
        intBitSetAddElem(self.bitset, elem)
    def clear(intbitset self):
        intBitSetReset(self.bitset)
    def difference(intbitset self, intbitset rhs):
        """Return the difference of two intbitsets as a new set.
        (i.e. all elements that are in this intbitset but not the other.)
        """
        return self.__sub__(rhs)
    def difference_update(intbitset self, intbitset rhs):
        """Remove all elements of another set from this set."""
        self.__isub__(rhs)
    def discard(intbitset self, size_t elem):
        """Remove an element from a intbitset if it is a member.
        If the element is not a member, do nothing."""
        intBitSetDelElem(self.bitset, elem)
    def intersection(intbitset self, intbitset rhs):
        """Return the intersection of two intbitsets as a new set.
        (i.e. all elements that are in both intbitsets.)
        """
        return self.__and__(rhs)
    def intersection_update(intbitset self, intbitset rhs):
        """Update a intbitset with the intersection of itself and another."""
        self.__iand__(rhs)
    def union(intbitset self, intbitset rhs):
        """Return the union of two intbitsets as a new set.
        (i.e. all elements that are in either intbitsets.)
        """
        return self.__or__(rhs)
    def union_update(intbitset self, intbitset rhs):
        """Update a intbitset with the union of itself and another."""
        self.__ior__(rhs)
    def issubset(intbitset self, intbitset rhs):
        """Report whether another set contains this set."""
        return self.__le__(rhs)
    def issuperset(intbitset self, intbitset rhs):
        """Report whether this set contains another set."""
        return self.__ge__(rhs)
    def symmetric_difference(intbitset self, intbitset rhs):
        """Return the symmetric difference of two sets as a new set.
        (i.e. all elements that are in exactly one of the sets.)
        """
        return self.__xor__(rhs)
    def symmetric_difference_update(intbitset self, intbitset rhs):
        """Update an intbitset with the symmetric difference of itself and another.
        """
        self.__ixor__(rhs)
    def fastdump(intbitset self):
        """Return a compressed string representation suitable to be saved
        somewhere."""
        return zlib.compress(PyString_FromStringAndSize(<char *>self.bitset.bitset, self.bitset.size * wordbytesize))
    def copy(intbitset self):
        """Return a shallow copy of a set."""
        return intbitset(self)
    def pop(intbitset self):
        """Remove and return an arbitrary set element."""
        cdef int ret
        ret = intBitSetGetNext(self.bitset, -1)
        if ret < 0:
            raise KeyError, "pop from an empty intbitset"
        intBitSetDelElem(self.bitset, ret)
        return ret
    def remove(intbitset self, size_t elem):
        """Remove an element from a set; it must be a member.
        If the element is not a member, raise a KeyError.
        """
        if intBitSetIsInElem(self.bitset, elem):
            intBitSetDelElem(self.bitset, elem)
        else:
            raise KeyError, elem
    def fastload(intbitset self, strdump):
        """Return a compressed string representation suitable to be saved
        somewhere."""
        self = intbitset(strdump)
        return self
    def strbits(intbitset self):
        cdef size_t i
        cdef size_t last
        last = 0
        ret = ''
        for i in self:
            ret += '0'*(i-last)+'1'
            last = i+1
        return ret
    def update_with_signs(intbitset self, rhs):
        """Given a dictionary rhs whose keys are integers, remove all the integers
        whose value are less than 0 and add every integer whose value is 0 or more"""
        cdef size_t value
        try:
            for value, sign in rhs.items():
                if sign < 0:
                    intBitSetDelElem(self.bitset, value)
                else:
                    intBitSetAddElem(self.bitset, value)
        except AttributeError:
            raise TypeError, "rhs should be a valid dictionary with integers keys and integer values"

    def get_sorted_element(intbitset self, int index):
        """Return element at position index in the sorted representation of the
        set. Note that index must be less than len(self)"""
        cdef size_t l
        cdef int last
        cdef size_t i
        l = intBitSetGetTot(self.bitset)
        if index < 0:
            index = index + l
        if 0 <= index < l:
            last = intBitSetGetNext(self.bitset, -1)
            for i from 0 <= i < index:
                last = intBitSetGetNext(self.bitset, last)
        else:
            raise IndexError, "intbitset index out of range"
        return last

    def to_sorted_list(intbitset self, int i, int j):
        """Return a sublist of the sorted representation of the set.
        Note, negative indices are not supported."""
        cdef size_t l
        cdef int last
        cdef size_t cnt
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

def intbitsetfull(size_t size):
    """Build a intbiset containing 0..size-1 elements."""
    ret = intbitset()
    intBitSetDestroy((<intbitset> ret).bitset)
    (<intbitset> ret).bitset = intBitSetCreateFull(size)
    return ret

cdef class intbitset_iterator:
    cdef int last
    cdef IntBitSet *bitset
    def __new__(intbitset_iterator self, intbitset bitset):
        self.last = -1
        self.bitset = bitset.bitset
    def __next__(intbitset_iterator self):
        self.last = intBitSetGetNext((<intbitset_iterator>self).bitset, self.last)
        if self.last < 0:
            self.last = -2
            raise StopIteration
        return self.last
    def __iter__(intbitset_iterator self):
        return self
