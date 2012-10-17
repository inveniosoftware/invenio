from wtforms import DateField

__all__ = ['Date']

class Date(DateField):

    def __init__(self, name, **kwargs):
        super(Date, self).__init__(name, **kwargs)

    def pre_validate(self):
        return dict(error=0, errorMessage='')

    def autocomplete(self):
        return []
