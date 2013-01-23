from wtforms import Form, \
                    SubmitField, \
                    TextField
from wtforms.validators import Required
from invenio.webinterface_handler_flask_utils import _
from invenio.webdeposit_field_widgets import date_widget, plupload_widget, bootstrap_submit

# Import custom fields
from invenio.webdeposit_load_fields import fields
__all__ = ['ArticleForm']


class ArticleForm(Form):

    publisher = fields.PublisherField(label=_('Publisher'), validators=[Required()])
    journal = fields.JournalField(label=_('Journal Title'), validators=[Required()])
    issn = fields.ISSNField(label='ISSN')
    title = fields.TitleField(label=_('Document Title'))
    author = fields.AuthorField(label=_('Author of the Document'))
    abstract = fields.AbstractField(label=_('Abstract'))
    pagesnum = fields.PagesNumberField(label=_('Number of Pages'))
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
    language = fields.LanguageField(label=_("Language"), choices=languages)
    date = fields.Date(label=_('Date of Document'), widget=date_widget)
    keywords = fields.KeywordsField(label=_('Keywords'))
    notes = fields.NotesField(label=_('Additional Notes or Comments'))
    file = fields.FileUploadField(label=_('File'))
    plupload_file = fields.FileUploadField(label=_('File'), widget=plupload_widget)
    submit = SubmitField(label=_('Submit Article'), widget=bootstrap_submit)

    """ Form Configuration variables """
    _title = _("Submit an Article")
    _drafting = True  #enable and disable drafting
