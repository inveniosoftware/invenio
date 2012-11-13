import os
from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer


def plugin_builder(plugin_name, plugin_code):
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        return candidate

CFG_DOC_METADATA = PluginContainer(os.path.join(CFG_PYLIBDIR, \
                                                'invenio', \
                                                'webdeposit_doc_types', \
                                                '*metadata.py'),
                                   plugin_builder=plugin_builder)

""" Create a dict with a doc_type => form_to_be_loaded relation """
doc_metadata = {}
for meta in CFG_DOC_METADATA.itervalues():
    if meta is not None:
        doc_metadata[meta['doc_type']] = meta['form']
