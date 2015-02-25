# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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


"""MARC formatted as JSON producer.

This producer could be used in several ways.

It could preserve the input tag from marc::

    title:
        ...
        producer:
            json_for_marc(), {'a': 'title'}

It will output the old marc tag followed by the subfield (dictionary key) and
the value of this key will be json['title']['title']
For example::

    ...
    <datafield tag="245" ind1="1" ind2="2">
      <subfield code="a">Awesome title</subfield>
    </datafield>
    ...

Will produce::

    [..., {'24512a': 'Awesome title'}, ...]


Also could also unify the input marc::

    title:
        ...
        producer:
            json_for_marc(), {'245__a': 'title'}

Using the same example as before it will produce::

    [..., {'245__a': 'Awesome title'}, ...]


The third way of using it is to create different outputs depending of the input
tag. Lets say this time we have this field definition::

    title:
        ...
        producer:
            json_for_marc('24511'), {'a': 'title'}
            json_for_marc('245__'), {'a': 'title', 'b': 'subtitle'}

The previous piece of MARC will produce the same output as before::

    [..., {'24512a': 'Awesome title'}, ...]

But if we use this one::

    ...
    <datafield tag="245" ind1=" " ind2=" ">
      <subfield code="a">Awesome title</subfield>
      <subfield code="b">Awesome subtitle</subfield>
    </datafield>
    ...

This will produce::

    [..., {'245__a': 'Awesome title'}, {'245__b': 'Awesome subtitle'},...]

This last approach should be used carefully as all the rules are applied,
therefore the rules should not overlap (unless this is the desired behavior).
"""

import re

from six import iteritems


def produce(self, fields=None):
    """Export the json in marc format.

    Produces a list of dictionaries will all the possible marc tags as keys.

    :param fields: list of fields to include in the output, if None or
                empty list all available tags will be included.
    """
    from invenio.base.utils import try_to_eval

    from invenio.modules.jsonalchemy.parser import get_producer_rules
    from invenio.modules.jsonalchemy.registry import functions

    if not fields:
        fields = self.keys()

    out = []

    for field in fields:
        if field.startswith('__') or self.get(field) is None:
            continue
        json_id = self.meta_metadata[field]['json_id']
        values = self.get(field)
        if not isinstance(values, (list, tuple)):
            values = (values, )
        for value in values:
            try:
                for rule in get_producer_rules(
                        json_id, 'json_for_marc',
                        self.additional_info['namespace']):
                    marc_tags = rule[0] if isinstance(rule[0], tuple) \
                        else (rule[0], )
                    if marc_tags and not any(
                            [re.match(m, t)
                             for m in marc_tags
                             for t in self.meta_metadata[field]['function']]):
                        # Not match, continue to next rule
                        continue
                    tmp_dict = dict()
                    for marc_tag, subfield in iteritems(rule[1]):
                        if len(marc_tag) == 1:
                            marc_tag = \
                                self.meta_metadata[field]['function'][0] + \
                                marc_tag
                        if not subfield:
                            tmp_dict[marc_tag] = value
                        else:
                            try:
                                tmp_dict[marc_tag] = value[subfield]
                            except:
                                try:
                                    # Evaluate only non keyword values.
                                    if subfield in __builtins__:
                                        raise ImportError
                                    tmp_dict[marc_tag] = try_to_eval(
                                        subfield,
                                        functions(
                                            self.additional_info.namespace
                                        ),
                                        value=value,
                                        self=self)
                                except ImportError:
                                    pass
                                except Exception as e:
                                    self.continuable_errors.append(
                                        "Producer CError - Unable to produce "
                                        "'%s'.\n %s" % (field, str(e)))
                    if tmp_dict:
                        out.append(tmp_dict)
            except Exception as e:
                self.continuable_errors.append(
                    "Producer CError - Unable to produce '%s'.\n %s"
                    % (field, str(e)))
    return out
