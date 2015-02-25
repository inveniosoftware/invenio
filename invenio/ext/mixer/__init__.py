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

"""Mixer extension."""

from __future__ import absolute_import, print_function

import errno
import json
import logging
import os
import sys

from mixer.backend.flask import Mixer as _Mixer

from invenio.ext.sqlalchemy import db, models

from .registry import mixers


class InvalidMixerRequest(Exception):

    """Default Mixer exception."""

    pass


class JSONBlender(object):

    """Default blender.

    Uses json files as input for the values of the sqlalchemy objects
    providing a way to load and dump data from them.
    """

    class Dump(object):

        def __init__(self, scheme):
            self.__scheme = scheme
            self.__fixtures = []
            # If the file does not exit try to create it!
            directory = os.path.dirname(self.__scheme.__source__)
            try:
                os.makedirs(os.path.dirname(directory))
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(directory):
                    pass
                else:
                    raise
            self.__source = open(self.__scheme.__source__, 'w+')

        def __enter__(self):
            return self.dump

        def __exit__(self, type, value, traceback):
            json.dump(self.__fixtures, self.__source,
                      indent=4, sort_keys=True, separators=(',', ': '))
            self.__source.close()

        def dump(self, obj):
            """Track all the objects to be dumped on exit."""
            self.__fixtures.append(obj)

    class Load(object):

        def __init__(self, scheme, drop=False):
            self.__scheme = scheme
            self.__source = open(self.__scheme.__source__, 'r')
            if drop:
                self.__scheme.query.delete()

        def __enter__(self):
            return self.load

        def __exit__(self, type, value, traceback):
            self.__source.close()

        def load(self):
            """Retrieve one object from the json input."""
            for obj in json.load(self.__source):
                yield obj


class MixerMeta(type):

    """Meta class for the mixers.

    Sets the default value of several class arguments if not set already:

    * `__field__`: Name of the fields from the model to be load and dump using
    the mixer. By default all the fields from the model.
    * `__source__`: path of the json file. By default the path of the current
    mixer class `/sources/tablename.json`.
    * `__blender__`: Blender class to use. By default `JSONBlender`.
    """

    def __new__(mcs, name, bases, dict_):
        if '__model__' not in dict_:
            raise InvalidMixerRequest(
                'Class %s does not have a __model__ specified and does not '
                'inherit from an existing Model-Mixer class')

        if '__fields__' not in dict_:
            dict_['__fields__'] = tuple(
                c.name for c in dict_['__model__'].__table__.columns)

        if '__source__' not in dict_:
            path = os.path.dirname(sys.modules[dict_['__module__']].__file__)
            dict_['__source__'] = os.path.join(
                path, 'sources',
                '%s.json' % (dict_['__model__'].__tablename__, ))

        if '__blender__' not in dict_:
            dict_['__blender__'] = JSONBlender

        return super(MixerMeta, mcs).__new__(mcs, name, bases, dict_)


class Mixer(_Mixer):

    """Custom mixer to use external files as fixtures and not only random."""

    def __init__(self, fake=True, factory=None, loglevel=logging.WARN,
                 silence=False, **params):
        super(Mixer, self).__init__(fake=fake, factory=factory,
                                    loglevel=loglevel, silence=silence, commit=False)

    def blend(self, scheme, drop=True, **values):
        """Blend scheme object.

        :param scheme: A mixer object.
        :param drop: If true the table that holds the sheme object will be
            dropped.
        :param values: Default values to be use for some fields despite of the
            content of the json file.

        :return: List of objects saved to the data base.
        """
        result = []

        if drop:
            scheme.__model__.query.delete()

        with scheme.__blender__.Load(scheme) as load:
            for fixture_values in load():
                fixture_values.update(values)
                result.append(
                    super(Mixer, self).blend(scheme.__model__,
                                             **fixture_values)
                )

        return result

    def unblend(self, scheme, output_file=None, *criterion):
        """Unblend the content of the data base.

        :param scheme: A mixer object.
        :param output_file: If specified it will be used as output file.
        :param criterion: SQLAlchemy criteria to be use to fetch all the data
            from the database for the current scheme object.
        """
        if output_file:
            scheme.__source__ = output_file
        with scheme.__blender__.Dump(scheme) as dump:
            for row in scheme.__model__.query.filter(*criterion):
                dump(dict((key, value) for (key, value) in row.todict()
                          if key in scheme.__fields__))


mixer = Mixer()
"""Default instance."""


def blend_all(sender, yes_i_know=False, drop=True, **kwargs):
    """Blend all the possible models found in the package.

    :param drop: If `True` delete the previous data.
    """
    print('>>> Mixer: Blending DB')

    # Load all models
    list(models)

    for table in db.metadata.sorted_tables:
        if table.name in mixers:
            result = mixer.blend(mixers[table.name], drop)
            db.session.add_all(result)
            db.session.commit()


def unblend_all(sender, **kwargs):
    """Unblend all the possible models found in the package."""
    print('>>> Mixer: Unblending DB')

    # Load all models
    list(models)

    for table in db.metadata.sorted_tables:
        if table.name in mixers:
            mixer.unblend(mixers[table.name])


def setup_app(app):
    """Set up the extension for the given app."""
    mixer.init_app(app)
    # Subscribe to database post create and recreate command
    from invenio.base import signals
    from invenio.base.scripts.database import create, recreate, dump
    signals.post_command.connect(blend_all, sender=create)
    signals.post_command.connect(blend_all, sender=recreate)
    signals.post_command.connect(unblend_all, sender=dump)
