import os
#from wtforms import Form
#from invenio.config import CFG_PYLIBDIR
#from invenio.pluginutils import PluginContainer

"""def plugin_builder(plugin_name, plugin_code):
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        if issubclass(candidate, Form):
            return candidate

CFG_FORMS = PluginContainer(os.path.join(CFG_PYLIBDIR, \
                                         'invenio', \
                                         'webdeposit_forms', \
                                         '*.py'), \
                            plugin_builder=plugin_builder)
"""


"""
TODO: Create more doc types and load dynamically
"""
doc_types = {"First Group": \
                 [{"name": "Article", "type": "Article"}, \
                  {"name": "Thesis", "type": "Thesis"}, \
                  {"name": "Nice Poem", "type": "Poetry"}, \
                 ], \
             "Media": \
                 [{"name": "Photo", "type": "Photo"}, \
                  {"name": "Audio", "type": "Audio"}, \
                  {"name": "Video", "type": "Video"}, \
                 ], \
             "Third Group": []}

globals().update(doc_types)
