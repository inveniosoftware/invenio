from wtforms import SelectMultipleField

__all__ = ['LanguageField']


class LanguageField(SelectMultipleField):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-flag"></i>'
        super(LanguageField, self).__init__(**kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        return []
