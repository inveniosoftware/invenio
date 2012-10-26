import os
from wtforms import Form, TextField, TextAreaField, SelectMultipleField, DateField, FileField, SubmitField

from invenio.SherpaRomeo import SherpaRomeoSearch, SherpaRomeoXMLParser
from invenio.webinterface_handler_flask_utils import _
from invenio.webdeposit_load_fields import fields
from invenio.webdeposit_field_widgets import date_widget, plupload_widget

globals().update(fields)
__all__ = ['ArticleForm']

class ArticleForm(Form):

    publisher = PublisherField(_('Publisher'))
    journal = JournalField(_('Journal Title'))
    issn = TextField('ISSN')
    title = TitleField(_('Document Title'))
    author = AuthorField(_('Author of the Document'))
    abstract = TextAreaField(_('Abstract'))
    pagesnum = IntegerTextField(_('Number of Pages'))
    languages = [("en", _("English")), \
                ("fre", _("French")), \
                ("ger", _("German")), \
                ("dut", _("Dutch")), \
                ("ita", _("Italian")), \
                ("spa", _("Spanish")), \
                ("por", _("Portuguese")), \
                ("gre", _("Greek")), \
                ("slo", _("Slovak")), \
                ("cze", _("Czech")), \
                ("hun", _("Hungarian")), \
                ("pol", _("Polish")), \
                ("nor", _("Norwegian")), \
                ("swe", _("Swedish")), \
                ("fin", _("Finnish")), \
                ("rus", _("Russian")) ]
    language = SelectMultipleField(choices=languages)
    date = Date(_('Date of Document'), widget=date_widget)
    keywords = TextField(_('Keywords'))
    notes = TextAreaField(_('Additional Notes or Comments'))
    file = FileField(_('File'))
    plupload_file = FileField(_('File'), widget=plupload_widget)
    submit = SubmitField()

    #configuration variables
    _title = _("Submit an Article")
    _drafting = True #enable and disable drafting
