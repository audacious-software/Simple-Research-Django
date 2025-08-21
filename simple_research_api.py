import phonenumbers

from django.conf import settings

def dashboard_actions(metadata):
    actions = []

    email = metadata.get('email', None)

    if email is not None:
        actions.append({
            'url': 'mailto:%s' % email,
            'icon': 'mail'
        })

    phone = metadata.get('phone', metadata.get('phone_number', None))

    if phone is not None:
        parsed = phonenumbers.parse(phone, settings.PHONE_REGION)

        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

        actions.append({
            'url': 'tel:%s' % formatted,
            'icon': 'phone_enabled',
        })

    return actions
