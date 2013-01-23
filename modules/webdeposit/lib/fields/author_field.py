from wtforms import TextField
from invenio.orcid import OrcidSearch

__all__ = ['AuthorField']


class AuthorField(TextField):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-user"></i>'
        super(AuthorField, self).__init__(**kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        orcid = OrcidSearch()
        value = self.data
        orcid.search_authors(value)
        return orcid.get_authors_names()
