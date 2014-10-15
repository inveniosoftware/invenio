# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from invenio.dbquery import run_sql
from invenio.webcomment_config import CFG_WEBCOMMENT_BODY_FORMATS
from invenio.webmessage_mailutils import email_quoted_txt2html

depends_on = ['invenio_release_1_1_0']


def info():
    return "New column 'body_format' for WebComment's cmtRECORDCOMMENT."


def do_upgrade():
    # First, insert the new column in the table.
    cmtRECORDCOMMENT_definition = run_sql("SHOW CREATE TABLE cmtRECORDCOMMENT")[0][1]
    if "body_format" not in cmtRECORDCOMMENT_definition:
        run_sql("""ALTER TABLE  cmtRECORDCOMMENT
                   ADD COLUMN   body_format VARCHAR(10) NOT NULL DEFAULT %s
                   AFTER        body;""",
                (CFG_WEBCOMMENT_BODY_FORMATS["TEXT"],)
               )

    number_of_comments = run_sql("""SELECT  COUNT(id)
                                    FROM    cmtRECORDCOMMENT""")[0][0]

    if number_of_comments > 0:

        # NOTE: Consider that the bigger the number of comments,
        #       the more powerful the server. Keep the number of
        #       batches fixed and scale the batch size instead.
        number_of_select_batches = 100

        select_batch_size = \
            number_of_comments >= (number_of_select_batches * number_of_select_batches) and \
            number_of_comments / number_of_select_batches or \
            number_of_comments

        number_of_select_iterations = \
            number_of_select_batches + \
            (number_of_comments % select_batch_size and 1)

        comments_select_query = """ SELECT  id,
                                            body,
                                            body_format
                                    FROM    cmtRECORDCOMMENT
                                    LIMIT   %s, %s"""

        comments_update_query = """ UPDATE  cmtRECORDCOMMENT
                                    SET     body = %s,
                                            body_format = %s
                                    WHERE   id = %s"""

        for number_of_select_iteration in xrange(number_of_select_iterations):

            comments = run_sql(
                comments_select_query,
                (number_of_select_iteration * select_batch_size,
                 select_batch_size)
            )

            for (comment_id, comment_body, comment_body_format) in comments:

                if comment_body_format == CFG_WEBCOMMENT_BODY_FORMATS["HTML"]:

                    comment_body = email_quoted_txt2html(
                        comment_body,
                        indent_html=("<blockquote>", "</blockquote>")
                    )

                    run_sql(
                        comments_update_query,
                        (comment_body,
                         CFG_WEBCOMMENT_BODY_FORMATS["HTML"],
                         comment_id)
                    )


def estimate():
    # TODO: The estimated time needed depends on the size of the table.
    #       Should we calculate this more accurately?
    return 1


def pre_upgrade():
    pass


def post_upgrade():
    pass
