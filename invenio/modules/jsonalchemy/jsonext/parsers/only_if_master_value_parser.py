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
    DecoratorOnEvalBaseExtensionParser


class OnlyIfMasterValueParser(DecoratorOnEvalBaseExtensionParser):

    """
    Handle the ``@only_if_master_value`` decorator.

    .. code-block:: ini

        files_to_upload:
            creator:
                @only_if_value(is_local_url(value['u']),
                               is_available_url(value['u']))
                marc, "8564_", {'hots_name': value['a'],
                                'access_number': value['b'],
                        ........
    """

    __parsername__ = 'only_if_master_value'

    @classmethod
    def parse_element(cls, indent_stack):
        """Set ``only_if_master_value`` attribute to the rule."""
        return (Keyword("@only_if_master_value").suppress() +
                originalTextFor(nestedExpr())
                ).setResultsName("only_if_master_value").setParseAction(
                    lambda toks: toks[0])

    @classmethod
    def create_element(cls, rule, field_def, content, namespace):
        """Simply return the list of boolean expressions."""
        return compile(content, '', 'eval')

    @classmethod
    def evaluate(cls, value, namespace, args):
        """Evaluate ``args`` with the master value from the input.

        :returns: a boolean depending on evaluated ``value``.
        """
        from invenio.modules.jsonalchemy.registry import functions
        evaluated = try_to_eval(args, functions(namespace), value=value)
        if not isinstance(evaluated, (list, tuple)):
            return evaluated
        else:
            return all(evaluated)

parser = OnlyIfMasterValueParser
