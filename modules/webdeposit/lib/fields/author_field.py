from wtforms import TextField

__all__ = ['AuthorField']

class AuthorField(TextField):

    def __init__(self, name, **kwargs):
        super(AuthorField, self).__init__(name, **kwargs)

    def pre_validate(self):
        return dict(error=0, errorMessage='')

    def autocomplete(self):
        return []
