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

"""
Unit test for the template extensions.
"""

from flask import url_for

from invenio.ext.template import render_template_to_string
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio.testsuite import unittest


class TemplateTest(InvenioTestCase):
    """
    jinja2utils TestSuite.
    """

    def tplEqualToString(self, tpl, text, **ctx):
        self.assertEqual(
            render_template_to_string(tpl, _from_string=True, **ctx),
            text)

    def test_wrap_equal_to_prefix_and_suffix(self):
        wrap_tpl = '{{ test_variable|wrap(prefix="***", suffix="###") }}'
        pxsx_tpl = '{{ test_variable|prefix("***")|suffix("###") }}'
        # None is printed as empty string
        self.tplEqualToString(wrap_tpl, '', test_variable=None)
        self.tplEqualToString(pxsx_tpl, '', test_variable=None)
        # Nothing is appended to empty string
        self.tplEqualToString(wrap_tpl, '', test_variable='')
        self.tplEqualToString(pxsx_tpl, '', test_variable='')
        # x|prefix|suffix is equal to x|wrap
        self.tplEqualToString(wrap_tpl, '***test###', test_variable='test')
        self.tplEqualToString(pxsx_tpl, '***test###', test_variable='test')


class TemplateLoaderCase(InvenioTestCase):

    @property
    def config(self):
        cfg = super(TemplateLoaderCase, self).config
        cfg['PACKAGES'] = [
            'invenio.testsuite.test_apps.first',
            'invenio.modules.*',
            'invenio.testsuite.test_apps.last',
        ]
        return cfg

    def test_fisrt_blueprint(self):
        response = self.client.get('/')
        self.assertEqual(response.data.strip(), 'First')
        self.assertNotEqual(response.data.strip(), 'Last')


class TemplateArgsTest(InvenioTestCase):

    """Test ``template_args`` decorator."""

    @classmethod
    def setup_app(cls, app):
        """Custom setup function."""
        from invenio.ext.template.context_processor import template_args
        from invenio.modules.collections.views.collections import index

        @template_args(index)
        def foo():
            return {'foo': 'foo', 'baz': 'baz'}

        @template_args('collections.index', app=app)
        def bar():
            return {'bar': 'bar', 'baz': 'BAZ'}

    @property
    def config(self):
        from invenio.base.config import EXTENSIONS
        cfg = super(TemplateArgsTest, self).config
        cfg['EXTENSIONS'] = EXTENSIONS + [
            'invenio.testsuite.test_ext_template.TemplateArgsTest']
        return cfg

    def test_template_args_loading(self):
        self.client.get(url_for('collections.index'))
        self.assertEqual(self.get_context_variable('foo'), 'foo')
        self.assertEqual(self.get_context_variable('bar'), 'bar')
        self.assertEqual(self.get_context_variable('baz'), 'BAZ')


class TemplateArgsLoadingTest(unittest.TestCase):

    """Test ``template_args`` decorator outside app context."""

    def test_broken_loading(self):
        from invenio.ext.template.context_processor import template_args

        def foo():
            return {'foo': 'foo'}

        self.assertRaises(Exception,
                          lambda: template_args('collections.index')(foo))


TEST_SUITE = make_test_suite(TemplateTest, TemplateLoaderCase,
                             TemplateArgsTest, TemplateArgsLoadingTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
