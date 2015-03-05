# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Modified JSON for indexer."""

from six import iteritems


def produce(self, fields=None):
    """Export the json for indexing purposes.

    :param fields: list of fields to include in the output, if None or
                   empty list all available tags will be included.
    """
    from invenio.base.utils import try_to_eval

    from invenio.modules.jsonalchemy.parser import get_producer_rules
    from invenio.modules.jsonalchemy.registry import functions

    out = self.dumps(without_meta_metadata=True, with_calculated_fields=True,
                     keywords=fields)

    for field, values in iteritems(out):
        with open("/root/test.txt", "a") as myfile:
            myfile.write("\n\n")
            myfile.write("field: "+field+"\n")
        if field.startswith('__'):
            continue
        json_id = self.meta_metadata[field]['json_id']
        production_rules = get_producer_rules(json_id, 'json_for_indexer',
                                              self.additional_info['namespace']
                                             )
        with open("/root/test.txt", "a") as myfile:
            myfile.write("production_rules: "+str(production_rules)+"\n")
        tmp_dict = dict()
        new_val = None
        if not isinstance(values, (list, tuple)):
            values = (values, )
        for value in values:
            with open("/root/test.txt", "a") as myfile:
                myfile.write("value: "+str(value)+"\n")
            try:
                for rule in production_rules:
                    with open("/root/test.txt", "a") as myfile:
                        myfile.write("rule: "+str(rule)+"\n")
                    # FIXME add support of indexer names.
                    # indexer_names = rule[0] if isinstance(rule[0], tuple) \
                    #     else (rule[0], )
                    # if indexer_names and not any(
                    #         [m == cfg['INDEXER_ENGINE'])
                    #         for m in indexer_names])
                    #     # Not match, continue to next rule
                    #     continue

                    # rule should not always return a dict
                    if isinstance(rule[1], dict):
                        for subfield, value_or_function in iteritems(rule[1]):
                            with open("/root/test.txt", "a") as myfile:
                                myfile.write("subfield: "+str(subfield)+" "+"val_or_fun: "+str(value_or_function)+ "\n")
                            try:
                                # Evaluate only non keyword values.
                                if value_or_function in __builtins__:
                                    raise ImportError
                                tmp_dict[subfield] = try_to_eval(
                                    value_or_function,
                                    functions(
                                        self.additional_info.namespace
                                    ),
                                    value=value,
                                    self=self)
                            except ImportError:
                                raise
                                pass
                            except Exception as e:
                                self.continuable_errors.append(
                                    "Producer CError - Unable to produce "
                                    "'%s'.\n %s" % (field, str(e)))
                        with open("/root/test.txt", "a") as myfile:
                            myfile.write("tmp_dict: "+str(tmp_dict)+"\n")
                        new_val = tmp_dict
                    else:
                        value_or_function = rule[1]
                        try:
                            # Evaluate only non keyword values.
                            if value_or_function in __builtins__:
                                raise ImportError
                            new_val = try_to_eval(
                                value_or_function,
                                functions(
                                    self.additional_info.namespace
                                ),
                                value=value,
                                self=self)
                        except ImportError:
                            raise
                            pass
                        except Exception as e:
                            self.continuable_errors.append(
                                "Producer CError - Unable to produce "
                                "'%s'.\n %s" % (field, str(e)))

                # substitute the old val with the new one
                if new_val:
                    out[field] = new_val
            except Exception as e:
                self.continuable_errors.append(
                    "Producer CError - Unable to produce '%s'.\n %s"
                    % (field, str(e)))
    return out
