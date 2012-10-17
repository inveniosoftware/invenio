from wtforms import IntegerField
from invenio.webdeposit_utils import is_number

__all__ = ['IntegerTextField']

class IntegerTextField(IntegerField):

    def __init__(self, name, **kwargs):
        super(IntegerTextField, self).__init__(name, **kwargs)

    def pre_validate(self):
        value = self.data
        from websubmit_form_fields import is_number
        if not is_number(value):
            return dict(error=1, \
                        errorMessage='Pages number must be a number! duh')

    def autocomplete(self):
        return []
