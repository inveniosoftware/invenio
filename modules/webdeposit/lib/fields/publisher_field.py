from wtforms import TextField
from invenio.sherpa_romeo import SherpaRomeoSearch

__all__ = ['PublisherField']


class PublisherField(TextField):

    def __init__(self, name, **kwargs):
        self._icon_html = '<i class="icon-certificate"></i>'
        super(PublisherField, self).__init__(name, **kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data

        s = SherpaRomeoSearch()
        response = s.search_publisher(value)
        return response
