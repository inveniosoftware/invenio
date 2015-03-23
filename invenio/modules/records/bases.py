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

"""
    invenio.modules.records.bases
    -----------------------------

    JSONAlchemy model extensions.
"""


from invenio.base.globals import cfg


class DocumentsHooks(object):

    """Record documents related hooks."""

    def acl_pre_authorized_hook(self, user_info, action, is_authorized):
        """Check access rights to the records that the document belong to.

        Depending on the value of
        :const:`~.config.RECORD_DOCUMENT_VIEWRESTR_POLICY` this hook will
        check if the user has rights over *ALL* the records that the document
        belong to or just *ANY*.

        :param user_info: an instance of
            :class:`~invenio.ext.login.legacy_user.UserInfo`
            (default: :class:`flask_login.current_user`)
        :param action: partial name of the action to be performed, for example
            `viewrestr`
        :param is_authorized: Current authorization value.

        :return: New authorization value or `is_authorized` if nothing has
            change. See :class:`~invenio.modules.access.bases.AclFactory:Acl`
        """
        #FIXME: once this method is refactorized this import should be updated
        from invenio.legacy.search_engine import check_user_can_view_record

        if is_authorized[0] != 0:
            return is_authorized

        if cfg['RECORD_DOCUMENT_VIEWRESTR_POLICY'] == 'ANY' and \
                not any([check_user_can_view_record(user_info, recid)[0] == 0
                         for recid in self.get('recids', [])]):
            return (1, 'You must be authorized to view at least on record that'
                    'this document belong to')
        elif cfg['RECORD_DOCUMENT_VIEWRESTR_POLICY'] != 'ANY' and \
                not all([check_user_can_view_record(user_info, recid)[0] == 0
                         for recid in self.get('recids', [])]):
            return (1, 'You must be authorized to view all the records that'
                    'this document belong to')

        return is_authorized
