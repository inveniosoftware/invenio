from wtforms import TextField

__all__ = ['TitleField']

class TitleField(TextField):

    def __init__(self, name, **kwargs):
        super(TitleField, self).__init__(name, **kwargs)

    def pre_validate(self):
        value = self.data
        if len(str(value)) < 4:
            return dict(error=1, \
                    errorMessage='Document Title must have at least 4 characters')
        return dict(error=0, errorMessage='')

    def autocomplete(self):
        return []
