{% trans site_name=config.CFG_SITE_NAME_INTL.get(g.ln) %}Thanks for registering with {{site_name}}! To complete the registration, please validate your email address by clicking the link below:{% endtrans %}

{{activation_link|safe}}

{% trans %}Please note that this URL will only remain valid for about {{days}} days. If this request was not made by you, please ignore this message.{% endtrans %}
