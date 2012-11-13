from wtforms import Form, \
                    SubmitField

from invenio.webinterface_handler_flask_utils import _
from invenio.webdeposit_load_fields import fields
from invenio.webdeposit_field_widgets import date_widget, plupload_widget

globals().update(fields)
__all__ = ['ArticleForm']


class ArticleForm(Form):

    publisher = PublisherField(_('Publisher'))
    journal = JournalField(_('Journal Title'))
    issn = ISSNField('ISSN')
    title = TitleField(_('Document Title'))
    author = AuthorField(_('Author of the Document'))
    abstract = AbstractField(_('Abstract'))
    pagesnum = PagesNumberField(_('Number of Pages'))
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
                ("rus", _("Russian"))]
    language = LanguageField(label="Language", choices=languages)
    date = Date(_('Date of Document'), widget=date_widget)
    keywords = KeywordsField(_('Keywords'))
    notes = NotesField(_('Additional Notes or Comments'))
    file = FileUploadField(_('File'))
    plupload_file = FileUploadField(_('File'), widget=plupload_widget)
    submit = SubmitField()

    """ Form Configuration variables """
    _title = _("Submit an Article")
    _drafting = True  #enable and disable drafting
