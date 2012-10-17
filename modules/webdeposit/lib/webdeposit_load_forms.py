import os
from wtforms import Form
from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer


def plugin_builder(plugin_name, plugin_code):
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        if issubclass(candidate, Form):
            return candidate

CFG_FORMS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'webdeposit_forms', '*.py'), \
                            plugin_builder=plugin_builder)


""" Change the names of the forms
    from the file names to the class names """
forms = []
for form in CFG_FORMS.itervalues():
    if form is not None:
        forms.append((form.__name__, form))

globals().update(forms)
