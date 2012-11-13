from wtforms import TextField

__all__ = ['ISSNField']


class ISSNField(TextField):

    def __init__(self, name, **kwargs):
        self._icon_html = '<i class="icon-barcode"></i>'
        super(ISSNField, self).__init__(name, **kwargs)

    def pre_validate(self):
        return dict(error=0, error_message='')

    def autocomplete(self):
        return []
