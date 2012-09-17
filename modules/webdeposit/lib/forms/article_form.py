from wtforms import Form, Field, TextField, TextAreaField, SelectMultipleField, DateField, FileField, SubmitField
from invenio.SherpaRomeo import SherpaRomeoSearch, SherpaRomeoXMLParser
from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer
import os


def plugin_builder(plugin_name, plugin_code):
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        if issubclass(candidate, Field):
            return candidate

CFG_FIELDS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'webdeposit_fields', '*.py'), plugin_builder=plugin_builder)

""" Change the names of the fields
    from the file names to the class names """
fields = []
for field in CFG_FIELDS.itervalues():
    fields.append((field.__name__, field))

globals().update(fields)

__all__ = ['ArticleForm']

class ArticleForm(Form):

    publisher = PublisherField('Publisher')
    journal = JournalField('Journal Title')
    issn = TextField('ISSN')
    doctitle = TitleField('Document Title')
    author = AuthorField('Author of the Document')
    abstract = TextAreaField('Abstract')
    pagesnum = IntegerTextField('Number of Pages')
    languages = [("en", "English"), \
                ("fre", "French"), \
                ("ger", "German"), \
                ("dut", "Dutch"), \
                ("ita", "Italian"), \
                ("spa", "Spanish"), \
                ("por", "Portuguese"), \
                ("gre", "Greek"), \
                ("slo", "Slovak"), \
                ("cze", "Czech"), \
                ("hun", "Hungarian"), \
                ("pol", "Polish"), \
                ("nor", "Norwegian"), \
                ("swe", "Swedish"), \
                ("fin", "Finnish"), \
                ("rus", "Russian") ]
    language = SelectMultipleField(choices=languages)
    date = DateField(u'Date of Document')
    keywords = TextField(u'Keywords',)
    notes = TextAreaField(u'Additional Notes or Comments')
    file = FileField(u'File')
    submit = SubmitField()
