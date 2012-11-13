from wtforms import TextField
from invenio.sherpa_romeo import SherpaRomeoSearch

__all__ = ['JournalField']


class JournalField(TextField):

    def __init__(self, name, **kwargs):
        self._icon_html = '<i class="icon-book"></i>'
        super(JournalField, self).__init__(name, **kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data

        s = SherpaRomeoSearch()
        response = s.search_journal(value)
        return response
