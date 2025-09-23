# pylint: disable=line-too-long,no-member

import phonenumbers
import requests

from django.conf import settings

from ..models import ResearchParticipant

def pull_participants(study): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    projects = study.metadata.get('redcap_projects', [])

    for project in projects: # pylint: disable=too-many-nested-blocks
        api_token = project.get('api_token', None)
        api_url =  project.get('api_url', None)

        if api_token is not None and api_url is not None:
            data = {
                'token': api_token,
                'content': 'record',
                'action': 'export',
                'format': 'json',
                'type': 'flat',
                'rawOrLabel': 'raw',
                'rawOrLabelHeaders': 'raw',
                'exportCheckboxLabel': 'false',
                'exportSurveyFields': 'false',
                'exportDataAccessGroups': 'false',
                'returnFormat': 'json'
            }

            event_index = 0

            for event in project.get('events', []):
                data['events[%s]' % event_index] = event

                event_index += 1

            try:
                responses = requests.post(api_url, data=data, timeout=300)

                for event in project.get('events', []):
                    for response in responses.json():
                        response_event = response.get('redcap_event_name', None)

                        if response_event == event:
                            record_id = response.get('record_id', None)

                            id_key = 'redcap_id_%s' % project.get('project_id', '')

                            if record_id is not None:
                                found = None

                                for participant in ResearchParticipant.objects.all():
                                    redcap_id = participant.metadata.get(id_key, None)

                                    if record_id == redcap_id:
                                        found = participant

                                        break

                                if project.get('create_participants', True) and found is None:
                                    default_name = 'New REDCap User (%s)' % record_id

                                    found = ResearchParticipant.objects.create(name=default_name)

                                    found.metadata[id_key] = record_id
                                    found.save()

                                updated = False

                                if found is not None:
                                    variable_map = project.get('variable_map', {})

                                    for key, value in response.items():
                                        local_key = '%s.%s' % (event, key)

                                        field = variable_map.get(local_key, None)

                                        if field is not None:
                                            if field == 'phone':
                                                parsed = phonenumbers.parse(value, settings.PHONE_REGION)

                                                destination = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

                                                if found.phone_number != destination:
                                                    found.phone_number = destination

                                                    updated = True

                                            if field == 'email':
                                                if found.email != value:
                                                    found.email = value

                                                    updated = True

                                            if field == 'address':
                                                if found.address != value:
                                                    found.address = value

                                                    updated = True

                                            if field == 'name':
                                                if found.name != value:
                                                    found.name = value

                                                    updated = True

                                                if found.sorted_name in ('', None):
                                                    found.sorted_name = value

                                                    updated = True

                                            if found.get(local_key, None) != value:
                                                found.metadata[local_key] = value

                                                updated = True

                                    if updated:
                                        found.save()

            except requests.exceptions.ReadTimeout:
                pass
