# pylint: disable=line-too-long

import importlib
import traceback

import phonenumbers

from django.conf import settings

def dashboard_actions(metadata):
    actions = []

    email = metadata.get('email', None)

    if email is not None and email.strip() != '':
        actions.append({
            'name': 'Send E-Mail',
            'url': 'mailto:%s' % email,
            'icon': 'mail'
        })

    phone = metadata.get('phone', metadata.get('phone_number', None))

    if phone is not None:
        try:
            parsed = phonenumbers.parse(phone, settings.PHONE_REGION)

            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

            actions.append({
                'name': 'Phone Call',
                'url': 'tel:%s' % formatted,
                'icon': 'phone_enabled',
            })
        except phonenumbers.NumberParseException:
            pass

    return actions

def fetch_records(source_type, source_config):
    records = []

    try:
        integration = importlib.import_module('.integrations.%s' % source_type, package='simple_research')

        records.extend(integration.fetch_records(source_config))
    except ImportError:
        traceback.print_exc()
    except AttributeError:
        traceback.print_exc()

    return records
