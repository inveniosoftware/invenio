from wtforms import TextField

__all__ = ['TitleField']


class TitleField(TextField):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-book"></i>'
        super(TitleField, self).__init__(**kwargs)

    def pre_validate(self):
        value = self.data
        if len(str(value)) < 4:
            return dict(error=1, \
                   error_message='Document Title must have at' + \
                                'least 4 characters')
        return dict(error=0, error_message='')

    def autocomplete(self):
        return []
