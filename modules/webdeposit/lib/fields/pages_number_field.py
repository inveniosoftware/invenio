from wtforms import TextField

__all__ = ['PagesNumberField']


class PagesNumberField(TextField):

    def __init__(self, name, **kwargs):
        self._icon_html = '<i class="icon-th"></i>'
        super(PagesNumberField, self).__init__(name, **kwargs)

    def pre_validate(self):
        value = self.data

        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        if not is_number(value):
            return dict(error=1, \
                        error_message='Pages number must be a number! duh')

    def autocomplete(self):
        return []
