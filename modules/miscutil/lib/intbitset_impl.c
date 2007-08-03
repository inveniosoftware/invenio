// $Id$
// CDS Invenio Access Control Engine in mod_python.

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


#include <stdlib.h>
#include <string.h>

#include "intbitset.h"

const size_t wordbytesize = sizeof(word_t);
const size_t wordbitsize = sizeof(word_t) * 8;
const short unsigned int wordbitpow = (sizeof(word_t) == 8) ? 6 : 5;
const short unsigned int wordbytepow = (sizeof(word_t) == 8) ? 3 : 2;


IntBitSet *intBitSetCreate(const register size_t size) {
    IntBitSet *ret = malloc(sizeof(IntBitSet));
    ret->size = (size / wordbitsize + 1);
    ret->bitset = calloc(ret->size, wordbytesize);
    ret->tot = 0;
    return ret;
}

IntBitSet *intBitSetCreateFull(const register size_t size) {
    register word_t *base;
    register word_t *end;
    register word_t i;
    IntBitSet *ret = malloc(sizeof(IntBitSet));
    ret->size = (size / wordbitsize + 1);
    ret->tot = size;
    base = ret->bitset = malloc(ret->size * wordbytesize);
    end = base + ret->size - 1;
    for (; base < end; ++base)
        *base = (word_t) ~0;
    *base = 0;
    for (i=0; i< (size % wordbitsize); ++i)
        *base |= ((word_t) 1 << i);
    return ret;
}

IntBitSet *intBitSetResetFromBuffer(IntBitSet *const bitset, const void *const buf, const size_t bufsize) {
    bitset->size = bufsize/wordbytesize;
    bitset->bitset = realloc(bitset->bitset, bufsize);
    bitset->tot = -1;
    memcpy(bitset->bitset, buf, bufsize);
    return bitset;
}

IntBitSet *intBitSetReset(IntBitSet *const bitset) {
    register word_t *base = bitset->bitset;
    const register word_t *end = bitset->bitset+bitset->size;
    for (; base<end; ++base)
        *base = 0;
    bitset->tot = 0;
    return bitset;
}


IntBitSet *intBitSetCreateFromBuffer(const void *const buf, const size_t bufsize) {
    IntBitSet *ret = malloc(sizeof(IntBitSet));
    ret->size = bufsize/wordbytesize;
    ret->bitset = malloc(bufsize);
    ret->tot = -1;
    memcpy(ret->bitset, buf, bufsize);
    return ret;
}


void intBitSetDestroy(IntBitSet *const bitset) {
    free(bitset->bitset);
    free(bitset);
}

IntBitSet *intBitSetClone(const IntBitSet * const bitset) {
    IntBitSet *ret = malloc(sizeof(IntBitSet));
    ret->size = bitset->size;
    ret->tot = bitset->tot;
    ret->bitset = malloc(ret->size * wordbytesize);
    memcpy(ret->bitset, bitset->bitset, ret->size * wordbytesize);
    return ret;
}

size_t intBitSetGetSize(const IntBitSet * const bitset) {
    return bitset->size * wordbitsize;
}

size_t intBitSetGetTot(IntBitSet *const bitset) {
    register word_t* base;
    register unsigned short int i;
    register size_t tot;
    const register word_t *end = bitset->bitset + bitset->size;
    if (bitset->tot < 0) {
        tot = 0;
        for (base = bitset->bitset; base < end; ++base)
            if (*base)
                for (i=0; i<wordbitsize; ++i)
                    if ((*base & ((word_t) 1 << i)) != 0) {
                        ++tot;
                    }
        bitset->tot = tot;
    }
    return bitset->tot;
}

void intBitSetResize(IntBitSet *const bitset, const register size_t size) {
    register size_t i;
    register size_t newsize = size / wordbitsize + 1;
    register word_t *ptr;
    if (newsize > bitset->size) {
        bitset->bitset = realloc(bitset->bitset, newsize * wordbytesize);
        for (i=bitset->size, ptr=bitset->bitset+bitset->size; i<newsize; ++i, ++ptr)
            *(ptr) = 0;
        bitset->size = newsize;
    }
}

bool_t intBitSetIsInElem(const IntBitSet * const bitset, const register size_t elem) {
    return ((elem < bitset->size * wordbitsize) ?
            (bitset->bitset[elem / wordbitsize] & ((word_t) 1 << ((word_t)elem % (word_t)wordbitsize))) != 0 : 0);
}

void intBitSetAddElem(IntBitSet *const bitset, const register size_t elem) {
    if (elem >= bitset->size * wordbitsize) intBitSetResize(bitset, elem+elem/10);
    bitset->bitset[elem / wordbitsize] |= ((word_t) 1 << (elem % wordbitsize));
    bitset->tot = -1;
}

void intBitSetDelElem(IntBitSet *const bitset, const register size_t elem) {
    if (elem >= bitset->size * wordbitsize) return;
    bitset->bitset[elem / wordbitsize] &= ~ (1 << (elem % wordbitsize));
    bitset->tot = -1;
}

bool_t intBitSetEmpty(const IntBitSet *const bitset) {
    register size_t i;
    register word_t *ptr;
    if (bitset->tot == 0) return 1;
    for (i = 0, ptr=bitset->bitset; i < bitset->size; ++i, ++ptr)
        if (*ptr) return 0;
    return 1;
}

IntBitSet *intBitSetUnion(IntBitSet *const x, IntBitSet *const y) {
    register word_t *xbase;
    register word_t *xend;
    register word_t *ybase;
    register word_t *retbase;
    register IntBitSet * ret = malloc(sizeof (IntBitSet));
    if (x->size > y->size)
        intBitSetResize(y, (x->size-1)*wordbitsize);
    if (y->size > x->size)
        intBitSetResize(x, (y->size-1)*wordbitsize);
    xbase = x->bitset;
    xend = x->bitset+x->size;
    ybase = y->bitset;
    retbase = ret->bitset = malloc(wordbytesize * x->size);
    ret->size = x->size;
    for (; xbase < xend; ++xbase, ++ybase, ++retbase)
        *(retbase) = *(xbase) | *(ybase);
    return ret;
}

IntBitSet *intBitSetXor(IntBitSet *const x, IntBitSet *const y) {
    register word_t *xbase;
    register word_t *xend;
    register word_t *ybase;
    register word_t *retbase;
    register IntBitSet * ret = malloc(sizeof (IntBitSet));
    if (x->size > y->size)
        intBitSetResize(y, (x->size-1)*wordbitsize);
    if (y->size > x->size)
        intBitSetResize(x, (y->size-1)*wordbitsize);
    xbase = x->bitset;
    xend = x->bitset+x->size;
    ybase = y->bitset;
    retbase = ret->bitset = malloc(wordbytesize * x->size);
    ret->size = x->size;
    for (; xbase < xend; ++xbase, ++ybase, ++retbase)
        *retbase = *xbase ^ *ybase;
    return ret;
}



IntBitSet *intBitSetIntersection(IntBitSet *const x, IntBitSet *const y) {
    register word_t *xbase;
    register word_t *xend;
    register word_t *ybase;
    register word_t *retbase;
    register size_t minsize = (x->size < y->size) ? x->size : y->size;
    register IntBitSet * ret = malloc(sizeof (IntBitSet));
    xbase = x->bitset;
    xend = x->bitset+minsize;
    ybase = y->bitset;
    retbase = ret->bitset = malloc(wordbytesize * minsize);
    ret->size = minsize;
    ret->tot = -1;
    for (; xbase < xend; ++xbase, ++ybase, ++retbase)
        *(retbase) = *(xbase) & *(ybase);
    return ret;
}

IntBitSet *intBitSetSub(IntBitSet *const x, IntBitSet *const y) {
    register word_t *xbase;
    register word_t *xend;
    register word_t *ybase;
    register word_t *retbase;
    register IntBitSet * ret = malloc(sizeof (IntBitSet));
    if (x->size > y->size)
        intBitSetResize(y, (x->size-1)*wordbitsize);
    if (y->size > x->size)
        intBitSetResize(x, (y->size-1)*wordbitsize);
    xbase = x->bitset;
    xend = x->bitset+x->size;
    ybase = y->bitset;
    retbase = ret->bitset = malloc(wordbytesize * x->size);
    ret->size = x->size;
    ret->tot = -1;
    for (; xbase < xend; ++xbase, ++ybase, ++retbase)
        *retbase = *xbase & ~(*xbase & *ybase);
    return ret;
}

IntBitSet *intBitSetIUnion(IntBitSet *const dst, IntBitSet *const src) {
    register word_t *dstbase;
    register word_t *dstend;
    register word_t *srcbase;
    register word_t *srcend;
    if (src->size > dst->size)
        intBitSetResize(dst, (src->size-1)*wordbitsize);
    dstbase = dst->bitset;
    dstend = dst->bitset + dst->size;
    srcbase = src->bitset;
    srcend = src->bitset + src->size;
    for (; srcbase < srcend; ++dstbase, ++srcbase)
        *dstbase |= *srcbase;
    dst->tot = -1;
    return dst;
}

IntBitSet *intBitSetIXor(IntBitSet *const dst, IntBitSet *const src) {
    register word_t *dstbase;
    register word_t *dstend;
    register word_t *srcbase;
    register word_t *srcend;
    if (src->size > dst->size)
        intBitSetResize(dst, (src->size-1)*wordbitsize);
    if (dst->size > src->size)
        intBitSetResize(src, (dst->size-1)*wordbitsize);
    dstbase = dst->bitset;
    dstend = dst->bitset + dst->size;
    srcbase = src->bitset;
    srcend = src->bitset + src->size;
    for (; srcbase < srcend; ++dstbase, ++srcbase)
        *dstbase ^= *srcbase;
    dst->tot = -1;
    return dst;
}


IntBitSet *intBitSetIIntersection(IntBitSet *const dst, IntBitSet *const src) {
    register word_t *dstbase;
    register word_t *dstend;
    register word_t *srcbase;
    register word_t *srcend;
    if (dst->size > src->size)
        intBitSetResize(src, (dst->size-1)*wordbitsize);
    dstbase = dst->bitset;
    dstend = dst->bitset + dst->size;
    srcbase = src->bitset;
    srcend = src->bitset + src->size;
    for (; dstbase < dstend; ++dstbase, ++srcbase)
        *dstbase &= *srcbase;
    dst->tot = -1;
    return dst;
}

IntBitSet *intBitSetISub(IntBitSet *const dst, IntBitSet *const src) {
    register word_t *dstbase = dst->bitset;
    register word_t *srcbase = src->bitset;
    register word_t *dstend = dst->bitset + ((dst->size < src->size) ? dst->size : src->size);

    for (; dstbase < dstend; ++dstbase, ++srcbase)
        *dstbase &= ~(*dstbase & *srcbase);
    dst->tot = -1;
    return dst;
}



int intBitSetGetNext(const IntBitSet *const x, register int last) {
    ++last;
    register word_t* base = x->bitset + last / wordbitsize;
    register unsigned short int i = last % wordbitsize;
    const register word_t *end = x->bitset + x->size;
    while(base < end) {
        if (*base)
            for (; i<wordbitsize; ++i)
                if ((*base & ((word_t) 1 << (word_t) i)) != 0)
                    return (int) i + (int) (base - x->bitset) * wordbitsize;
        i = 0;
        ++base;
    }
    return -2;
}

unsigned char intBitSetCmp(IntBitSet *const x, IntBitSet *const y) {
    register word_t *xbase;
    register word_t *xend;
    register word_t *ybase;
    register word_t *yend;
    register unsigned char ret = 0;
    if (x->size > y->size)
        intBitSetResize(y, (x->size-1)*wordbitsize);
    if (y->size > x->size)
        intBitSetResize(x, (y->size-1)*wordbitsize);
    xbase = x->bitset;
    xend = x->bitset+x->size;
    ybase = y->bitset;
    yend = y->bitset+y->size;
    for (; ret != 3 && xbase<xend; ++xbase, ++ybase)
        ret |= (*ybase != (*xbase | *ybase)) * 2 + (*xbase != (*xbase | *ybase));
    return ret;
}
