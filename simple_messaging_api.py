# pylint: disable=line-too-long, no-member

import phonenumbers

from django.conf import settings

from .models import ResearchParticipant

def fetch_short_url_metadata(outgoing_message):
    metadata = {}

    out_formatted = outgoing_message.current_destination()

    try:
        parsed = phonenumbers.parse(out_formatted, settings.PHONE_REGION)
        out_formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        pass

    for participant in ResearchParticipant.objects.exclude(phone_number=None).exclude(phone_number=''):
        part_parsed = phonenumbers.parse(participant.phone_number, settings.PHONE_REGION)

        part_formatted = phonenumbers.format_number(part_parsed, phonenumbers.PhoneNumberFormat.E164)

        if out_formatted == part_formatted:
            metadata['simple_research.Participant'] = '%s:%s' % (settings.ALLOWED_HOSTS[0], participant.pk,)

    return metadata
