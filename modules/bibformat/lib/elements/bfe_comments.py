# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
"""BibFormat element - Prints comments posted for the record
"""
__revision__ = "$Id$"

from invenio.webcomment import get_first_comments_or_remarks

def format(bfo, nbReviews='all', nbComments='all'):
    """
    Prints comments posted for the record.

    @param nbReviews: The max number of reviews to print
    @param nbComments: The max number of comments to print
    """

    nb_reviews = nbReviews
    if nb_reviews.isdigit():
        nb_reviews = int(nb_reviews)
    nb_comments = nbComments
    if nb_comments.isdigit():
        nb_comments = int(nb_comments)

    (comments, reviews) = get_first_comments_or_remarks(recID=bfo.recID,
                                                        ln=bfo.lang,
                                                        nb_comments=nb_comments,
                                                        nb_reviews=nb_reviews,
                                                        voted=-1,
                                                        reported=-1,
                                                        user_info=bfo.user_info)


    return comments + reviews

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
