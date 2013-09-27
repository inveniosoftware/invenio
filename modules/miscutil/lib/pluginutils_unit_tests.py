# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012, 2013 CERN.
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

"""
Test unit for the miscutil/pluginutils module.
"""

__revision__ = "$Id$"

import os

from invenio.base.globals import cfg
from invenio.pluginutils import PluginContainer, create_enhanced_plugin_builder
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestPluginContainer(InvenioTestCase):
    """
    PluginContainer TestSuite.
    """
    def test_plugin_container_wrapping_bibformat_elements(self):
        """pluginutils - wrapping bibformat elements"""
        from invenio.bibformat_config import CFG_BIBFORMAT_ELEMENTS_PATH

        def format_signature(bfo, *dummy_args, **dummy_argd):
            pass

        def escape_values_signature(bfo):
            pass

        plugin_builder = create_enhanced_plugin_builder(
            compulsory_objects={
                'format_element' : format_signature,
            },
            optional_objects={
                'escape_values' : escape_values_signature,
            })
        bibformat_elements = PluginContainer(os.path.join(CFG_BIBFORMAT_ELEMENTS_PATH, 'bfe_*.py'),
            plugin_builder=plugin_builder)

        self.failUnless(bibformat_elements['bfe_fulltext'])
        self.failUnless(callable(bibformat_elements['bfe_fulltext']['format_element']))
        self.failUnless(len(bibformat_elements) >= 50)

    def test_plugin_container_wrapping_websubmit_functions(self):
        """pluginutils - wrapping websubmit functions"""
        websubmit_functions = PluginContainer(os.path.join(cfg['CFG_PYLIBDIR'], 'invenio', 'websubmit_functions', '*.py'))

        self.failUnless(websubmit_functions['Is_Referee'])
        self.failUnless(websubmit_functions['CaseEDS'])
        self.failUnless(callable(websubmit_functions['CaseEDS']))
        self.failUnless(len(websubmit_functions) >= 62, 'There should exist at least 62 websubmit_functions. Found: %s' % len(websubmit_functions))
        ## Retrieve_Data and Shared_Functions are not real plugins
        self.failUnless(len(websubmit_functions.get_broken_plugins()) >= 2)
        self.failIf(websubmit_functions.get('Shared_Functions'))
        self.failUnless('Shared_Functions' in websubmit_functions.get_broken_plugins())

    def test_plugin_container_wrapping_external_authentications(self):
        """pluginutils - wrapping external authentications"""
        from invenio.external_authentication import ExternalAuth

        def plugin_builder(plugin_name, plugin_code):
            for name in dir(plugin_code):
                candidate = getattr(plugin_code, name)
                try:
                    if issubclass(candidate, ExternalAuth):
                        return candidate
                except TypeError:
                    pass
            raise ValueError('%s is not a valid external authentication plugin' % plugin_name)

        external_authentications = PluginContainer(os.path.join(cfg['CFG_PYLIBDIR'], 'invenio', 'external_authentication_*.py'), plugin_signature=ExternalAuth, plugin_builder=plugin_builder)
        self.failUnless(issubclass(external_authentications['external_authentication_sso'], ExternalAuth))
        self.failIf(external_authentications.get('external_authentication_cern_wrapper'))
        self.failUnless(len(external_authentications) >= 1)
        self.failUnless(len(external_authentications.get_broken_plugins()) >= 2)

    def test_plugin_container_module_reloading(self):
        """pluginutils - plugin reloading"""
        websubmit_functions = PluginContainer(os.path.join(cfg['CFG_PYLIBDIR'], 'invenio', 'websubmit_functions', '*.py'))
        self.assertNotEqual(websubmit_functions['Is_Referee'].__doc__, "test_reloading")
        websubmit_functions['Is_Referee'].__doc__ = "test_reloading"
        self.assertEqual(websubmit_functions['Is_Referee'].__doc__, "test_reloading")

        websubmit_functions.reload_plugins(reload=True)
        self.assertNotEqual(websubmit_functions['Is_Referee'].__doc__, "test_reloading")

    def test_plugin_container_module_caching(self):
        """pluginutils - plugin caching"""
        websubmit_functions = PluginContainer(os.path.join(cfg['CFG_PYLIBDIR'], 'invenio', 'websubmit_functions', '*.py'))
        self.assertNotEqual(websubmit_functions['Is_Referee'].__doc__, "test_caching")
        websubmit_functions['Is_Referee'].__doc__ = "test_caching"
        self.assertEqual(websubmit_functions['Is_Referee'].__doc__, "test_caching")

        websubmit_functions.reload_plugins()
        websubmit_functions_new = PluginContainer(os.path.join(cfg['CFG_PYLIBDIR'], 'invenio', 'websubmit_functions', '*.py'))
        self.assertEqual(websubmit_functions_new['Is_Referee'].__doc__, "test_caching")

TEST_SUITE = make_test_suite(TestPluginContainer,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
