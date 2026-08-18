# pylint: disable=line-too-long, no-member, import-error

import calendar
import json

import arrow
import phonenumbers

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from simple_messaging.models import IncomingMessage, OutgoingMessage

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


def fetch_parties():
    parties = []

    for participant in ResearchParticipant.objects.all():
        if participant.phone_number is not None:
            if (participant.phone_number in parties) is False:
                parties.append(participant.phone_number)

            try:
                part_parsed = phonenumbers.parse(participant.phone_number, settings.PHONE_REGION)

                part_formatted = phonenumbers.format_number(part_parsed, phonenumbers.PhoneNumberFormat.E164)

                if (part_formatted in parties) is False:
                    parties.append(part_formatted)
            except phonenumbers.phonenumberutil.NumberParseException:
                pass
        if (participant.email is not None) and (participant.email in parties) is False:
            parties.append(participant.email)

        for version in participant.versions.all():
            if version.phone_number is not None:
                if (version.phone_number in parties) is False:
                    parties.append(version.phone_number)

                try:
                    part_parsed = phonenumbers.parse(version.phone_number, settings.PHONE_REGION)

                    part_formatted = phonenumbers.format_number(part_parsed, phonenumbers.PhoneNumberFormat.E164)

                    if (part_formatted in parties) is False:
                        parties.append(part_formatted)
                except phonenumbers.phonenumberutil.NumberParseException:
                    pass

            if (version.email is not None) and (version.email in parties) is False:
                parties.append(version.email)

    return parties

def update_last_console_view(phone_number, last_view=None):
    if last_view is None:
        last_view = timezone.now()

    parsed_incoming = phonenumbers.parse(phone_number, settings.PHONE_REGION)

    if phonenumbers.is_valid_number(parsed_incoming):
        formatted_incoming = phonenumbers.format_number(parsed_incoming, phonenumbers.PhoneNumberFormat.E164)

        for participant in ResearchParticipant.objects.all().exclude(phone_number=None):
            parsed_participant = phonenumbers.parse(participant.phone_number, settings.PHONE_REGION)

            if phonenumbers.is_valid_number(parsed_participant):
                formatted_participant = phonenumbers.format_number(parsed_participant, phonenumbers.PhoneNumberFormat.E164)

                if formatted_participant == formatted_incoming:
                    participant.metadata['simple_messaging_last_console_view'] = calendar.timegm(last_view.timetuple())

                    if 'cached_new_message_count_lookup' in participant.metadata:
                        del participant.metadata['cached_new_message_count_lookup']

                    if 'cached_new_message_count' in participant.metadata:
                        del participant.metadata['cached_new_message_count']

                    participant.save()

def fetch_last_console_view(phone_number):
    try:
        parsed_incoming = phonenumbers.parse(phone_number, settings.PHONE_REGION)

        if phonenumbers.is_valid_number(parsed_incoming):
            formatted_incoming = phonenumbers.format_number(parsed_incoming, phonenumbers.PhoneNumberFormat.E164)

            for participant in ResearchParticipant.objects.all().exclude(phone_number=None):
                parsed_participant = phonenumbers.parse(participant.phone_number, settings.PHONE_REGION)

                if phonenumbers.is_valid_number(parsed_participant):
                    formatted_participant = phonenumbers.format_number(parsed_participant, phonenumbers.PhoneNumberFormat.E164)

                    if formatted_participant == formatted_incoming:
                        return participant.metadata.get('simple_messaging_last_console_view', 0)
    except phonenumbers.NumberParseException:
        pass

    return 0

def new_message_count(phone_number):
    if phone_number is None:
        return None

    try: # pylint: disable=too-many-nested-blocks
        parsed_incoming = phonenumbers.parse(phone_number, settings.PHONE_REGION)

        if phonenumbers.is_valid_number(parsed_incoming): # pylint: disable=too-many-nested-blocks
            formatted_incoming = phonenumbers.format_number(parsed_incoming, phonenumbers.PhoneNumberFormat.E164)

            for participant in ResearchParticipant.objects.all().exclude(phone_number=None):
                parsed_participant = phonenumbers.parse(participant.phone_number, settings.PHONE_REGION)

                if phonenumbers.is_valid_number(parsed_participant):
                    formatted_participant = phonenumbers.format_number(parsed_participant, phonenumbers.PhoneNumberFormat.E164)

                    if formatted_participant == formatted_incoming:
                        last_view = participant.metadata.get('simple_messaging_last_console_view', 0)

                        last_view = arrow.get(last_view)

                        message_query = IncomingMessage.objects.filter(receive_date__gte=last_view.datetime)

                        message_count = 0

                        for message in message_query:
                            if message.current_sender() == formatted_participant:
                                try:
                                    if settings.IS_UNREAD_MESSAGE(message):
                                        message_count += 1
                                except AttributeError:
                                    message_count += 1

                        participant.metadata['cached_new_message_count'] = message_count

                        participant.save()

                        return message_count
    except phonenumbers.NumberParseException:
        pass

    return None

def annotate_console_messages(messages): # pylint: disable=too-many-branches
    phone_name_cache = {}
    staff_name_cache = {}

    for message in messages: # pylint: disable=too-many-nested-blocks
        direction = message.get('direction', None)

        if direction == 'from-user':
            name = phone_name_cache.get(message.get('sender', 'unknown-sender'), None)

            if name is None:
                sender = message.get('sender', None)

                if sender is not None:
                    try:
                        participant = ResearchParticipant.objects.participant_for_phone_number(sender)

                        if participant is not None:
                            phone_name_cache[sender] = participant.name
                    except: # pylint: disable=bare-except
                        pass

            name = phone_name_cache.get(message.get('sender', 'unknown-sender'), None)

            if name is not None:
                message['ui_details'].append({
                    'label': 'Participant',
                    'value': name
                })

        elif direction == 'from-system':
            outgoing = OutgoingMessage.objects.filter(pk=message.get('message_id', -1)).first()

            if outgoing is not None:
                transmission_metadata = json.loads(outgoing.transmission_metadata)

                django_user = transmission_metadata.get('django.user', None)

                if django_user is not None:
                    staff_name = staff_name_cache.get(django_user, None)

                    if staff_name is None:
                        username = django_user.split(' ')[0]

                        user = get_user_model().objects.filter(username=username).first()

                        if user is not None:
                            staff_name_cache[django_user] = '%s %s' % (user.first_name, user.last_name)
                        else:
                            staff_name_cache[django_user] = django_user

                    message['ui_details'].append({
                        'label': 'Staff Member',
                        'value': staff_name_cache.get(django_user, django_user)
                    })

def annotate_view_messages(messages, request=None): # pylint: disable=too-many-branches, too-many-statements
    phone_name_cache = {}

    if request is not None and request.user is not None: # pylint: disable=too-many-nested-blocks
        to_remove = []

        participant_ids = []

        for study in request.user.research_studies.all():
            for participation in study.participations.all():
                if (participation.participant.pk in participant_ids) is False:
                    participant_ids.append(participation.participant.pk)

        for message in messages:
            direction = message.get('direction', None)

            if direction == 'incoming':
                sender = message.get('sender', None)

                if sender is not None:
                    try:
                        participant = ResearchParticipant.objects.participant_for_phone_number(sender)

                        if participant is not None:
                            if (participant.pk in participant_ids) is False:
                                to_remove.append(message)
                    except ResearchParticipant.MultipleObjectsReturned:
                        pass

            elif direction == 'outgoing':
                destination = message.get('destination', None)

                if destination is not None:
                    try:
                        participant = ResearchParticipant.objects.participant_for_phone_number(destination)

                        if participant is not None:
                            if (participant.pk in participant_ids) is False:
                                to_remove.append(message)
                    except ResearchParticipant.MultipleObjectsReturned:
                        pass

        for message in to_remove:
            messages.remove(message)

    for message in messages: # pylint: disable=too-many-nested-blocks
        direction = message.get('direction', None)

        if direction == 'incoming':
            name = phone_name_cache.get(message.get('sender', 'unknown-sender'), None)

            if name is None:
                sender = message.get('sender', None)

                if sender is not None:
                    try:
                        participant = ResearchParticipant.objects.participant_for_phone_number(sender)

                        if participant is not None:
                            name = participant.name
                            phone_name_cache[sender] = name
                    except ResearchParticipant.MultipleObjectsReturned:
                        pass

            if name is not None:
                message['sender_name'] = name

        elif direction == 'outgoing':
            name = phone_name_cache.get(message.get('destination', 'unknown-destination'), None)

            if name is None:
                destination = message.get('destination', None)

                if destination is not None:
                    try:
                        participant = ResearchParticipant.objects.participant_for_phone_number(destination)

                        if participant is not None:
                            name = participant.name
                            phone_name_cache[destination] = name
                    except ResearchParticipant.MultipleObjectsReturned:
                        pass

            if name is not None:
                message['destination_name'] = name
