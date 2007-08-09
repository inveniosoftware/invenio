// $Id$

// This file is part of CDS Invenio.
// Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
//
// CDS Invenio is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// CDS Invenio is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
// 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

#ifndef INTBITSET_H
#define INTBITSET_H

typedef unsigned long long int word_t;
typedef unsigned char bool_t;

extern const size_t wordbytesize;
extern const size_t wordbitsize;

typedef struct {
    int size;
    size_t allocated;
    word_t universe;
    int tot;
    word_t *bitset;
} IntBitSet;

IntBitSet *intBitSetCreate(register const size_t size, const bool_t universe);
IntBitSet *intBitSetCreateFromBuffer(const void * const buf, const size_t bufsize);
IntBitSet *intBitSetResetFromBuffer(IntBitSet *const bitset, const void *const buf, const size_t bufsize);
IntBitSet *intBitSetReset(IntBitSet *const bitset);
void intBitSetDestroy(IntBitSet *const bitset);
IntBitSet *intBitSetClone(const IntBitSet * const bitset);
size_t intBitSetGetSize(IntBitSet * const bitset);
size_t intBitSetGetAllocated(const IntBitSet * const bitset);
size_t intBitSetGetTot(IntBitSet * const bitset);
void intBitSetResize(IntBitSet *const bitset, register const size_t allocated);
bool_t intBitSetIsInElem(const IntBitSet * const bitset, register const size_t elem);
void intBitSetAddElem(IntBitSet *const bitset, register const size_t elem);
void intBitSetDelElem(IntBitSet *const bitset, register const size_t elem);
bool_t intBitSetEmpty(const IntBitSet * const bitset);
IntBitSet *intBitSetUnion(IntBitSet *const x, IntBitSet *const y);
IntBitSet *intBitSetXor(IntBitSet *const x, IntBitSet *const y);
IntBitSet *intBitSetIntersection(IntBitSet *const x, IntBitSet *const y);
IntBitSet *intBitSetSub(IntBitSet *const x, IntBitSet *const y);
IntBitSet *intBitSetIUnion(IntBitSet *const dst, IntBitSet *const src);
IntBitSet *intBitSetIXor(IntBitSet *const dst, IntBitSet *const src);
IntBitSet *intBitSetIIntersection(IntBitSet *const dst, IntBitSet *const src);
IntBitSet *intBitSetISub(IntBitSet *const x, IntBitSet *const y);
size_t intBitSetAdapt(IntBitSet *const x, IntBitSet *const y);
int intBitSetGetNext(const IntBitSet *const x, register int last);
/** Compare.
 * Compare two intbitset.
 * Returns 0 if the two bitset are equals.
 * Returns 1 if x is proper subset of y
 * Returns 2 if y is proper subset of x
 * Returns 3 if x != y
 */
unsigned char intBitSetCmp(IntBitSet *const x, IntBitSet *const y);

#endif
