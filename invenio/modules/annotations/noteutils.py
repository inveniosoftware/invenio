# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Utils for extracting notes from comments and manipulating them.

.. py:data:: MARKERS

   the note markers; references have a special type of location, e.g.
   "[Ellis98]"
"""

import re

from flask_login import current_user

from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User


# a note location can have one of the following structures (sans markers):
# P.1, P.1,3,7 (multiple locations), F.1a, S.1.1 (sub-locations)
LOCATION = r'[\w\.]+(?:[\,][\w\.]+)*'


MARKERS = {
    'P': {'longname': _('Page'), 'regex': r'[P]\.' + LOCATION},
    'F': {'longname': _('Figure'), 'regex': r'[F]\.' + LOCATION},
    'G': {'longname': _('General aspect'), 'regex': r'[G]'},
    'L': {'longname': _('Line'), 'regex': r'[L]\.' + LOCATION},
    'E': {'longname': _('Equation'), 'regex': r'[E]\.' + LOCATION},
    'T': {'longname': _('Table'), 'regex': r'[T]\.' + LOCATION},
    'S': {'longname': _('Section'), 'regex': r'[S]\.' + LOCATION},
    'PP': {'longname': _('Paragraph'), 'regex': r'[P]{2}\.' + LOCATION},
    'R': {'longname': _('Reference'),
          'regex': r'[R]\.' +
                   r'[\[][\w]+[\]](?:[\,][\[][\w]+[\]])*'}
}

# description of the notes' markup, to be used in GUI
# FIXME: move to Jinja2 template
HOWTO = _("To add an annotation use the following syntax:<br>\
P.1: an annotation on page one<br>\
P.1,2,3: an annotation on pages one to three<br>\
F.2a: an annotation on subfigure 2a<br>\
S.1.2: an annotation on subsection 1.2<br>\
P.1: T.2: L.3: an annotation on the third line of table two, which appears on \
the first page<br>\
G: an annotation on the general aspect of the paper<br>\
R.[Ellis98]: an annotation on a reference<br><br>\
The available markers are:")

for KEY, VALUE in MARKERS.items():
    HOWTO += '<br>' + KEY + ' - ' + VALUE['longname']


# concatenate all regexes in MARKERS
MARKER_REGEX = [r'(']
for m in MARKERS.keys():
    MARKER_REGEX += MARKERS[m]['regex'] + '|'
MARKER_REGEX[len(MARKER_REGEX) - 1] = r')+'  # remove the final OR
MARKER_REGEX = "".join(MARKER_REGEX)


# notes should be delimited by a newline; we do not want to extract this
# part, so we use a non-capturing group `?:`
PREFIX = r'(?:^|\n)+'


# a note prefix should be followed by a column and optional whitespace
SUFFIX = r'[\:][\s]*'


# the actual text; can be anything
TEXT = r'(.+)'


def extract_notes_from_comment(comment, bodyOnly=False):
    """Extracts notes from a comment.

    Notes are one-line blocks of text preceded by :py:data:`MARKERS` and
    locations (page numbers, figure names etc.).

    :param comment: the comment to parse
    :return: the list of parsed notes in the following JSON form below (
        if the ``body`` is a JSON, it means that the note has a child).

        .. code-block:: json

            {
                "marker": String,
                "location": String,
                "body": JSON|String
            }
    """
    if bodyOnly:
        text = comment
    else:
        text = comment.body
    notes = re.findall(PREFIX + MARKER_REGEX + SUFFIX + TEXT, text)
    results = []
    for note in notes:
        # recursively search for sub-notes; for example "P.1: F.2: a note on
        # page one, figure two" is a valid note
        marker = note[0]
        sub_notes = extract_notes_from_comment(note[1], True)
        if len(sub_notes) > 0:
            body = sub_notes[0]['what']
            marker += '_' + sub_notes[0]['where']['marker']
        else:
            body = note[1]
        result = {'what': body,
                  'where': {'marker': marker}}
        if not bodyOnly:
            result['who'] = User.query.get(comment.id_user)
            result['where']['record'] = comment.id_bibrec
            result['comment'] = comment.id
        results.append(result)
    return results


def get_original_comment(note):
    """Fetches the original comment of the note; in case of hierarchic notes, it
    goes up to the parent.

    :param note: the note
    :return: the comment in which the note appeared
    """
    from invenio.modules.comments.models import CmtRECORDCOMMENT
    from sqlalchemy.orm.exc import NoResultFound
    if "comment" in note:
        try:
            return CmtRECORDCOMMENT.query.filter(
                CmtRECORDCOMMENT.id == note["comment"]).one()
        except NoResultFound:
            pass
    return None


def get_note_title(location):
    """Convert a note/ marker combination to a human readable string.

    :param location: the note/ marker combination
    :return: the human-readable location
    """
    location = location.split('.')
    # certain marker types might not require a location, hence else ''
    try:
        marker = MARKERS[location[0]]['longname']
    except KeyError:
        return "Unknown"
    return marker + (' ' + location[1] if len(location) > 1 else '')


def tree_put(tree, keys, value, path=None):
    if path is None:
        path = ""
    l = len(keys)
    for i, k in enumerate(keys):
        if i == l - 1:
            if k not in tree:
                tree[k] = {"leaf": [], "path": path}
            tree[k]["leaf"].append(value)
            tree[k]["path"] += ("_" if len(path) else "") + k
        else:
            if k not in tree:
                tree[k] = {"leaf": [], "path": path}
            tree[k] = tree_put(tree[k], keys[i + 1:l], value,
                               path + ("_" if len(path) else "") + k)
            tree[k]["path"] = k
            break
    return tree


def prepare_notes(notes):
    tree = {}
    for note in notes:
        markers = note["where"]["marker"].split("_")
        tree = tree_put(tree, markers, note)
    return tree


def note_collapse(id_bibrec, path):
    """Collapses note category for user."""
    from .models import CmtNOTECOLLAPSED
    collapsed = CmtNOTECOLLAPSED(id_bibrec=id_bibrec,
                                 path=path,
                                 id_user=current_user.get_id())
    try:
        db.session.add(collapsed)
        db.session.commit()
    except:
        db.session.rollback()


def note_expand(id_bibrec, path):
    """Expands note category for user."""
    from .models import CmtNOTECOLLAPSED
    CmtNOTECOLLAPSED.query.filter(db.and_(
        CmtNOTECOLLAPSED.id_bibrec == id_bibrec,
        CmtNOTECOLLAPSED.path == path,
        CmtNOTECOLLAPSED.id_user == current_user.get_id())).\
        delete(synchronize_session=False)


def note_is_collapsed(id_bibrec, path):
    """Checks if a note category is collapsed."""
    from .models import CmtNOTECOLLAPSED
    return CmtNOTECOLLAPSED.query.filter(db.and_(
        CmtNOTECOLLAPSED.id_bibrec == id_bibrec,
        CmtNOTECOLLAPSED.path == path,
        CmtNOTECOLLAPSED.id_user == current_user.get_id())).count() > 0
