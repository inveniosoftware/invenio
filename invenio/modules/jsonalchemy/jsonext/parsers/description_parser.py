# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
# 60 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from pyparsing import QuotedString, Keyword

from invenio.modules.jsonalchemy.parser import FieldBaseExtensionParser, \
    ModelBaseExtensionParser, indentedBlock


class DescriptionParser(FieldBaseExtensionParser, ModelBaseExtensionParser):

    """
    Handle the description section in model and field definitions.

    .. code-block:: ini

        title:
            \"\"\"Description on title\"\"\"

        title:
            description:
                \"\"\"Description on title\"\"\"

    """

    @classmethod
    def parse_element(cls, indent_stack):
        """Set to the rule the description."""
        doc_double = QuotedString(quoteChar='"""', multiline=True)
        doc_single = QuotedString(quoteChar="'''", multiline=True)
        doc_string = indentedBlock((doc_double | doc_single), indent_stack)
        description = (Keyword('description:').suppress() + doc_string)
        return (description | doc_double | doc_single)\
            .setResultsName('description')

    @classmethod
    def create_element(cls, rule, namespace):
        """Simply return of the string."""
        return rule.description.strip() if rule.description else ''

    @classmethod
    def inherit_model(cls, current_value, base_value):
        """The description should remain the one from the child model."""
        return base_value if not current_value else current_value

    @classmethod
    def extend_model(cls, current_value, new_value):
        """The description should remain the one from the child model."""
        return current_value

    @classmethod
    def evaluate(cls, *args, **kwargs):
        """Evaluate parser.

        This method is implemented like this because this parser is made for
        both, fields and models, and each of them have a different signature.
        Moreover this method does nothing.
        """
        pass


parser = DescriptionParser
