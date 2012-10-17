from wtforms import DateField
from wtforms.widgets import html_params, HTMLString

def date_widget(field, **kwargs):
    field_id = kwargs.pop('id', field.id)
    html = [u'<input class="datepicker" %s value="" type="text">' \
            % html_params(id=field_id, name=field_id)]
    kwargs['class'] = u'date'
    return HTMLString(u''.join(html))

def plupload_widget(field, **kwargs):
    field_id = kwargs.pop('id', field.id)
    html = [u'</td></tr><tr><td colspan="3"><div class="pluploader" %s>\
                <p>You browser doesn\'t have HTML5 support.</p>\
                </div></td></tr>' % html_params(id=field_id)]
    kwargs['class'] = u'plupload'
    return HTMLString(u''.join(html))
