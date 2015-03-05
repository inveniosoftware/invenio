# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Implement nearest terms lookup."""

from flask import g

from invenio.modules.records import models
from invenio.modules.records.models import Record
from invenio.utils.text import strip_accents

from .hit_counter import *
from .models import IdxINDEX


def create_nearest_terms_box(urlargd, p, f, t='w', n=5, ln=None,
                             intro_text_p=True):
    """Return text box containing list of 'n' nearest terms above/below 'p'.

    Look in the field 'f' for matching type 't' (words/phrases) in language
    'ln'.  Propose new searches according to `urlargs' with the new words.  If
    `intro_text_p' is true, then display the introductory message, otherwise
    print only the nearest terms in the box content.
    """
    # load the right message language
    _ = gettext_set_language(ln or g.ln)

    if not CFG_WEBSEARCH_DISPLAY_NEAREST_TERMS:
        return _("Your search did not match any records.  Please try again.")
    nearest_terms = []
    if not p: # sanity check
        p = "."
    if p.startswith('%') and p.endswith('%'):
        p = p[1:-1] # fix for partial phrase
    index_id = get_index_id_from_field(f)
    if f == 'fulltext':
        if CFG_SOLR_URL:
            return _("No match found, please enter different search terms.")
        else:
            # FIXME: workaround for not having native phrase index yet
            t = 'w'
    # special indexes:
    if f == 'refersto' or f == 'referstoexcludingselfcites':
        return _("There are no records referring to %(x_rec)s.", x_rec=cgi.escape(p))
    if f == 'cataloguer':
        return _("There are no records modified by %(x_rec)s.", x_rec=cgi.escape(p))
    if f == 'citedby' or f == 'citedbyexcludingselfcites':
        return _("There are no records cited by %(x_rec)s.", x_rec=cgi.escape(p))
    # look for nearest terms:
    if t == 'w':
        nearest_terms = get_nearest_terms_in_bibwords(p, f, n, n)
        if not nearest_terms:
            return _("No word index is available for %(x_name)s.",
                   x_name=('<em>' + cgi.escape(get_field_i18nname(get_field_name(f) or f, ln, False)) + '</em>'))
    else:
        nearest_terms = []
        if index_id:
            nearest_terms = get_nearest_terms_in_idxphrase(p, index_id, n, n)
        if f == 'datecreated' or f == 'datemodified':
            nearest_terms = get_nearest_terms_in_bibrec(p, f, n, n)
        if not nearest_terms:
            nearest_terms = get_nearest_terms_in_bibxxx(p, f, n, n)
        if not nearest_terms:
            return _("No phrase index is available for %(x_name)s.",
                   x_name=('<em>' + cgi.escape(get_field_i18nname(get_field_name(f) or f, ln, False)) + '</em>'))

    terminfo = []
    for term in nearest_terms:
        if t == 'w':
            hits = get_nbhits_in_bibwords(term, f)
        else:
            if index_id:
                hits = get_nbhits_in_idxphrases(term, f)
            elif f == 'datecreated' or f == 'datemodified':
                hits = get_nbhits_in_bibrec(term, f)
            else:
                hits = get_nbhits_in_bibxxx(term, f)

        argd = {}
        argd.update(urlargd)

        # check which fields contained the requested parameter, and replace it.
        for px, dummy_fx in ('p', 'f'), ('p1', 'f1'), ('p2', 'f2'), ('p3', 'f3'):
            if px in argd:
                argd_px = argd[px]
                if t == 'w':
                    # p was stripped of accents, to do the same:
                    argd_px = strip_accents(argd_px)
                #argd[px] = string.replace(argd_px, p, term, 1)
                #we need something similar, but case insensitive
                pattern_index = string.find(argd_px.lower(), p.lower())
                if pattern_index > -1:
                    argd[px] = argd_px[:pattern_index] + term + argd_px[pattern_index+len(p):]
                    break
                #this is doing exactly the same as:
                #argd[px] = re.sub('(?i)' + re.escape(p), term, argd_px, 1)
                #but is ~4x faster (2us vs. 8.25us)
        terminfo.append((term, hits, argd))

    intro = ""
    if intro_text_p: # add full leading introductory text
        if f:
            intro = _("Search term %(x_term)s inside index %(x_index)s did not match any record. Nearest terms in any collection are:") % \
                     {'x_term': "<em>" + cgi.escape(p.startswith("%") and p.endswith("%") and p[1:-1] or p) + "</em>",
                      'x_index': "<em>" + cgi.escape(get_field_i18nname(get_field_name(f) or f, ln, False)) + "</em>"}
        else:
            intro = _("Search term %(x_name)s did not match any record. Nearest terms in any collection are:",
                     x_name=("<em>" + cgi.escape(p.startswith("%") and p.endswith("%") and p[1:-1] or p) + "</em>"))

    return websearch_templates.tmpl_nearest_term_box(p=p, ln=ln, f=f, terminfo=terminfo,
                                                     intro=intro)


def get_nearest_terms_in_bibwords(p, f, n_below, n_above):
    """Return list of +/-n nearest terms to word `p' in index for field `f'."""
    model = IdxINDEX.idxWORDF(f or "anyfield")
    if model is None:
        return list()

    res_below = model.query.filter(model.term < term).limit(
        n_below).order_by(model.term.asc()).values(model.term)
    res_above = model.query.filter(model.term > term).limit(
        n_above).order_by(model.term.desc()).values(model.term)

    return (reversed([row[0] for row in res_below]) +
            [row[0] for row in res_above])


def get_nearest_terms_in_idxphrase(p, f, n_below, n_above):
    """Browse (-n_above, +n_below) closest bibliographic phrases.

    For the given pattern p in the given field idxPHRASE table, regardless of
    collection. Return list of [phrase1, phrase2, ... , phrase_n].
    """
    model = IdxINDEX.idxPHRASEF(f, fallback=False)
    if model is None:
        return None

    res_below = model.query.filter(model.term < term).limit(
        n_below).order_by(model.term.asc()).values(model.term)
    res_above = model.query.filter(model.term > term).limit(
        n_above).order_by(model.term.desc()).values(model.term)

    return (reversed([row[0] for row in res_below]) +
            [row[0] for row in res_above])


def get_nearest_terms_in_idxphrase_with_collection(p, index_id, n_below,
                                                   n_above, collection):
    """Browse closest bibliographic phrases considering collection.

    For the given pattern p in the given field idxPHRASE table, considering the
    collection (intbitset).  Return list of [(phrase1, hitset), (phrase2,
    hitset), ... , (phrase_n, hitset)].
    """
    model = IdxINDEX.idxPHRASEF(f, fallback=False)
    if model is None:
        return None

    res_below = model.query.filter(model.term < term).limit(
        n_below).order_by(model.term.asc()).values(
        model.term, model.hitlist)
    res_above = model.query.filter(model.term > term).limit(
        n_above).order_by(model.term.desc()).values(
        model.term, model.hitlist)

    return (reversed(
        [(row[0], len(intbitset(row[1]) & collection)) for row in res_below]
    ) + [(row[0], len(intbitset(row[1]) & collection)) for row in res_above])


def get_nearest_terms_in_bibxxx(p, f, n_below, n_above):
    """Browse (-n_above, +n_below) closest bibliographic phrases
       for the given pattern p in the given field f, regardless
       of collection.
       Return list of [phrase1, phrase2, ... , phrase_n]."""
    # determine browse field:
    if not f and string.find(p, ":") > 0:  # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)

    # FIXME: quick hack for the journal index
    if f == 'journal':
        return get_nearest_terms_in_bibwords(p, f, n_below, n_above)

    # We are going to take max(n_below, n_above) as the number of
    # values to ferch from bibXXx.  This is needed to work around
    # MySQL UTF-8 sorting troubles in 4.0.x.  Proper solution is to
    # use MySQL 4.1.x or our own idxPHRASE in the future.

    index_id = get_index_id_from_field(f)
    if index_id:
        return get_nearest_terms_in_idxphrase(p, index_id, n_below, n_above)

    n_fetch = 2 * max(n_below, n_above)
    # construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f)  # 'f' seems to be okay as it starts by two digits
    else:
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
    # start browsing to fetch list of hits:
    browsed_phrases = {}
    # will hold {phrase1: 1, phrase2: 1, ..., phraseN: 1} dict of browsed
    # phrases (to make them unique)

    # always add self to the results set:
    browsed_phrases[p.startswith("%") and p.endswith("%") and p[1:-1] or p] = 1
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        model = getattr(models, 'Bib{0}{1}x'.format(digit1, digit2))

        if len(t) != 6 or t[-1:] == '%':
            # only the beginning of field 't' is defined, so add wildcard
            # character:
            condition = model.tag.like(t + '%')
        else:
            condition = model.tag == t

        res = set([item[0] for item in model.query.filter(
            model.value < p, condition
        ).order_by(model.value.desc()).limit(n_fetch).values(model.value)])
        res |= set([item[0] for item in model.query.filter(
            model.value > p, condition
        ).order_by(model.value.asc()).limit(n_fetch).values(model.value)])

    # select first n words only: (this is needed as we were searching
    # in many different tables and so aren't sure we have more than n
    # words right; this of course won't be needed when we shall have
    # one ACC table only for given field):
    phrases_out = list(res)
    phrases_out.sort(lambda x, y: cmp(string.lower(strip_accents(x)),
                                      string.lower(strip_accents(y))))
    # find position of self:
    try:
        idx_p = phrases_out.index(p)
    except ValueError:
        idx_p = len(phrases_out)/2
    # return n_above and n_below:
    return phrases_out[max(0, idx_p-n_above):idx_p+n_below]


def get_nearest_terms_in_bibrec(p, f, n_below, n_above):
    """Return list of nearest terms and counts from bibrec table.

    ``p`` is usually a date, and ``f`` either datecreated or datemodified.

    Note: below/above count is very approximative, not really respected.
    """
    column = (Record.modification_date if f == 'datemodified' else
              Record.creation_date)
    res_above = Record.query.filter(
        cast(column, db.String) > term).limit(n_above).values(column)
    res_below = Record.query.filter(
        cast(column, db.String) < term).limit(n_below).values(column)

    return sorted(
        [value.strftime('%Y-%m-%d %H:%M:%S') for value in res_below] +
        [value.strftime('%Y-%m-%d %H:%M:%S') for value in res_above]
    )
