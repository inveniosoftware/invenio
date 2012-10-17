import os
from wtforms import Field
from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer

def plugin_builder(plugin_name, plugin_code):
    try:
        all = getattr(plugin_code, '__all__')
        for name in all:
            candidate = getattr(plugin_code, name)
            if issubclass(candidate, Field):
                return candidate
    except AttributeError:
        pass

CFG_FIELDS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'webdeposit_fields', '*.py'), \
                             plugin_builder=plugin_builder)

""" Change the names of the fields
    from the file names to the class names """
fields = []
for field in CFG_FIELDS.itervalues():
    if field is not None:
        fields.append((field.__name__, field))

globals().update(fields)
