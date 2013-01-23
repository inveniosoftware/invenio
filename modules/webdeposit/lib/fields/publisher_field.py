from wtforms import TextField
from invenio.sherpa_romeo import SherpaRomeoSearch
from wtforms.validators import Required

__all__ = ['PublisherField']


class PublisherField(TextField):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-certificate"></i>'

        # Create our own Required data member
        # for client-side use
        print "awesome: s"
        print kwargs
        if kwargs.has_key('validators'):
            print 'has attribute'
            for v in kwargs.get("validators"):
                if type(v) is Required:
                    self.required = True

        super(PublisherField, self).__init__(**kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data

        s = SherpaRomeoSearch()
        response = s.search_publisher(value)
        return response
