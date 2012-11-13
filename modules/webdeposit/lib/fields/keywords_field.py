from wtforms import TextField

__all__ = ['KeywordsField']


class KeywordsField(TextField):

    def __init__(self, name, **kwargs):
        self._icon_html = '<i class="icon-tags"></i>'
        super(KeywordsField, self).__init__(name, **kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        return []
