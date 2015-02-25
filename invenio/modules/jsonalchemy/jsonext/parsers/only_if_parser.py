# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from pyparsing import Keyword, originalTextFor, nestedExpr

from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.parser import \
    DecoratorBeforeEvalBaseExtensionParser


class OnlyIfParser(DecoratorBeforeEvalBaseExtensionParser):

    """
    Handle the ``@only_if`` decorator.

    .. code-block:: ini

        number_of_copies:
            creator:
                @only_if('BOOK' in self.get('collection.primary', []))
                get_number_of_copies(self.get('recid'))
    """

    __parsername__ = 'only_if'

    @classmethod
    def parse_element(cls, indent_stack):
        return (Keyword("@only_if").suppress() +
                originalTextFor(nestedExpr())
                ).setResultsName("only_if").setParseAction(lambda toks: toks[0])

    @classmethod
    def create_element(cls, rule, field_def, content, namespace):
        return compile(content, '', 'eval')

    @classmethod
    def evaluate(cls, reader, args):
        """Evaluate parser.

        This is a special case where the real evaluation of the decorator
        is happening before the evaluation.
        """
        from invenio.modules.jsonalchemy.registry import functions
        evaluated = try_to_eval(
            args, functions(reader._json.additional_info.namespace),
            self=reader._json)
        if not isinstance(evaluated, (list, tuple)):
            return evaluated
        else:
            return all(evaluated)

parser = OnlyIfParser
