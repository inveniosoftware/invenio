from wtforms import TextField
from wtforms.validators import Required
from invenio.sherpa_romeo import SherpaRomeoSearch

__all__ = ['JournalField']


class JournalField(TextField):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-book"></i>'

        # Create our own Required data member
        # for client-side use
        if kwargs.has_key('validators'):
            for v in kwargs.get("validators"):
                if type(v) is Required:
                    self.required = True

        super(JournalField, self).__init__(**kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data

        s = SherpaRomeoSearch()
        response = s.search_journal(value)
        return response
