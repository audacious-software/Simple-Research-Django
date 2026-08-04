# pylint: disable=line-too-long, no-member

import importlib
import io
import json
import math
import time

import phonenumbers
import pandas

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import ResearchStudy, ResearchParticipant, ResearchParticipation

@staff_member_required
def dashboard_participants(request):
    context = {
        'include_search': True,
        'studies': ResearchStudy.objects.filter(staff_members=request.user).order_by('name'),
    }

    offset = int(request.GET.get('offset', '0'))
    limit = int(request.GET.get('limit', '25'))
    query = request.GET.get('q', None)

    study_name = request.GET.get('study', None)

    participant_objects = ResearchParticipant.objects.all()

    if (query in (None, '')) is False:
        search_query = Q(name__icontains=query) | Q(address__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(phone_number__icontains=query) | Q(email__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(metadata__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(participations__study__name__icontains=query) # pylint: disable=unsupported-binary-operation

        participant_objects = ResearchParticipant.objects.filter(search_query)

    if study_name is not None and len(study_name) > 0:
        participant_objects = ResearchParticipant.objects.filter(participations__study__name=study_name)
        context['study_name'] = study_name

    valid_studies = ResearchStudy.objects.filter(staff_members=request.user)

    participant_objects = participant_objects.filter(participations__study__in=valid_studies).distinct()

    total = participant_objects.count()

    additional_columns = []

    for app in settings.INSTALLED_APPS:
        try:
            research_module = importlib.import_module('.simple_research_api', package=app)

            module_values = research_module.dashboard_additional_columns()

            if module_values is not None:
                additional_columns.extend(module_values)
        except ImportError:
            pass
        except AttributeError:
            pass

    context['additional_columns'] = additional_columns

    context['participants'] = participant_objects.order_by('sort_name')[offset:(offset + limit)]
    context['total'] = total
    context['start'] = offset + 1
    context['end'] = offset + limit

    if context['end'] > total:
        context['end'] = total

    if (offset - limit) >= 0:
        context['previous'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_participants'), offset - limit, limit)

    if (offset + limit) < total:
        context['next'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_participants'), offset + limit, limit)

    context['first'] = '%s?offset=0&limit=%s' % (reverse('dashboard_participants'), limit)

    last = int(total / limit) * limit

    context['last'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_participants'), last, limit)
    context['study_url'] = '%s?limit=%s&study=' % (reverse('dashboard_participants'), limit)

    return render(request, 'dashboard/dashboard_participants.html', context=context)

@staff_member_required
def dashboard_delete_participant(request):
    payload = {
        'message': 'Unable to process request - please try again.'
    }

    if request.method == 'POST':
        identifier = request.POST.get('identifier', None)

        match = ResearchParticipant.objects.filter(pk=identifier).first()

        if match is not None:
            match.delete()

            payload = {
                'message': 'Participant deleted.'
            }

    return HttpResponse(json.dumps(payload, indent=2), content_type='application/json', status=200)

@staff_member_required
def dashboard_update_participant(request):
    payload = {
        'message': 'Unable to process request - please try again.'
    }

    if request.method == 'POST': # pylint: disable=too-many-nested-blocks
        name = request.POST.get('name', None)

        if name is not None:
            identifier = request.POST.get('identifier', '')

            if identifier == '':
                participant = ResearchParticipant.objects.create(name=name)

                participant.phone_number = request.POST.get('phone', None)
                participant.email = request.POST.get('email', None)
                participant.save()

                studies = request.POST.get('studies', None)

                enrollment_list = []

                for study_pk in studies.split(','):
                    if study_pk != '':
                        study = ResearchStudy.objects.filter(pk=int(study_pk)).first()

                        if study is not None:
                            enrollment_list.append(study)

                participant.update_enrollments(enrollment_list)

                payload = {
                    'message': 'Participant added.'
                }
            else:
                participant = ResearchParticipant.objects.filter(pk=int(identifier)).first()

                participant.phone_number = request.POST.get('phone', None)
                participant.email = request.POST.get('email', None)
                participant.name = request.POST.get('name', None)
                participant.save()

                studies = request.POST.get('studies', None)

                enrollment_list = []

                for study_pk in studies.split(','):
                    if study_pk != '':
                        study = ResearchStudy.objects.filter(pk=int(study_pk)).first()

                        if study is not None:
                            enrollment_list.append(study)

                participant.update_enrollments(enrollment_list)

                payload = {
                    'message': 'Participant updated.'
                }

    return HttpResponse(json.dumps(payload, indent=2), content_type='application/json', status=200)

@staff_member_required
def dashboard_studies(request):
    context = {
        'include_search': True
    }

    offset = int(request.GET.get('offset', '0'))
    limit = int(request.GET.get('limit', '25'))
    query = request.GET.get('q', None)

    study_objects = ResearchStudy.objects.all()

    if (query in (None, '')) is False:
        search_query = Q(name__icontains=query) | Q(description__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(contact_information__icontains=query) | Q(principle_investigators__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(metadata__icontains=query) # pylint: disable=unsupported-binary-operation

        study_objects = ResearchStudy.objects.filter(search_query)

    study_objects = study_objects.filter(staff_members=request.user)

    total = study_objects.count()

    context['studies'] = study_objects.order_by('name')[offset:(offset + limit)]
    context['total'] = total
    context['start'] = offset + 1
    context['end'] = offset + limit

    if context['end'] > total:
        context['end'] = total

    if (offset - limit) >= 0:
        context['previous'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_studies'), offset - limit, limit)

    if (offset + limit) < total:
        context['next'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_studies'), offset + limit, limit)

    context['first'] = '%s?offset=0&limit=%s' % (reverse('dashboard_studies'), limit)

    last = int(total / limit) * limit

    context['last'] = '%s?offset=%s&limit=%s' % (reverse('dashboard_studies'), last, limit)

    context['staff_members'] = get_user_model().objects.filter(is_staff=True).order_by('email')

    return render(request, 'dashboard/dashboard_studies.html', context=context)

@staff_member_required
def dashboard_delete_study(request):
    payload = {
        'message': 'Unable to process request - please try again.'
    }

    if request.method == 'POST':
        identifier = request.POST.get('identifier', None)

        match = ResearchStudy.objects.filter(pk=identifier).first()

        if match is not None:
            match.delete()

            payload = {
                'message': 'Study deleted.'
            }

    return HttpResponse(json.dumps(payload, indent=2), content_type='application/json', status=200)

@staff_member_required
def dashboard_update_study(request):
    payload = {
        'message': 'Unable to process request - please try again.'
    }

    if request.method == 'POST':
        name = request.POST.get('name', None)

        if name is not None:
            identifier = request.POST.get('identifier', '')

            if identifier == '':
                study = ResearchStudy.objects.create(name=name)

                staff_members = request.POST.get('staff_members', None)

                for member_pk in staff_members.split(','):
                    staff_member = get_user_model().objects.filter(pk=int(member_pk)).first()

                    if staff_member is not None:
                        study.staff_members.add(staff_member)

                study.save()

                payload = {
                    'message': 'Study created.'
                }
            else:
                study = ResearchStudy.objects.filter(pk=int(identifier)).first()

                staff_members = request.POST.get('staff_members', None)

                for member_pk in staff_members.split(','):
                    if member_pk != '':
                        staff_member = get_user_model().objects.filter(pk=int(member_pk)).first()

                        study.staff_members.clear()

                        if staff_member is not None:
                            study.staff_members.add(staff_member)

                study.save()

                payload = {
                    'message': 'Study updated.'
                }

    return HttpResponse(json.dumps(payload, indent=2), content_type='application/json', status=200)

def simple_research_profile(request, token): # pylint: disable=too-many-branches
    if token.endswith('.'):
        return redirect('simple_research_participant_preferences', token=token[:-1])

    context = {
        'token': token,
    }

    token_user = ResearchParticipant.objects.participant_with_token(token)

    if token_user is None:
        raise Http404

    now_timestamp = int(time.time())

    last_access = request.session.get('simple_research_last_profile_access', 0)

    if request.GET.get('expire', 'false') == 'true':
        last_access = 0

    needs_login = False

    if now_timestamp - last_access > settings.SIMPLE_RESEARCH_LOGIN_EXPIRE_SECONDS:
        needs_login = True

    if request.method == 'POST' and request.POST.get('auth_identifier', None) is not None:
        identifier = request.POST.get('auth_identifier', None)

        if '@' in identifier and (token_user.email in (None, '')) is False:
            if identifier.lower() != token_user.email.lower():
                needs_login = True
            else:
                needs_login = False

                context['participant'] = token_user
        elif (token_user.phone_number in (None, '')) is False:
            country_code = token_user.metadata.get('country_code', settings.SIMPLE_RESEARCH_DEFAULT_COUNTRY_CODE)

            try:
                parsed_number = phonenumbers.parse(identifier, country_code)
                formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

                token_parsed = phonenumbers.parse(token_user.phone_number, country_code)
                token_formatted = phonenumbers.format_number(token_parsed, phonenumbers.PhoneNumberFormat.E164)

                if token_formatted != formatted_number:
                    needs_login = True
                else:
                    needs_login = False

                    context['participant'] = token_user
            except phonenumbers.phonenumberutil.NumberParseException:
                needs_login = True

    if needs_login:
        return render(request, 'simple_research_profile_auth.html', context=context)

    context['participant'] = token_user

    request.session['simple_research_last_profile_access'] = now_timestamp

    if request.method == 'POST' and request.POST.get('auth_identifier', None) is None:
        # TO IMPLEMENT - Update record, take action, etc.

        response_json = {
            'error': 'Invalid request: %s' % request.POST
        }

        return HttpResponse(json.dumps(response_json, indent=2), content_type='application/json', status=500)

    return render(request, 'simple_research_profile.html', context=context)

@staff_member_required
def dashboard_participants_xlsx(request): # pylint: disable=too-many-locals,too-many-branches, too-many-statements
    if request.method == 'POST':
        uploaded_file = request.FILES['participant_upload_field']

        data_frame = pandas.read_excel(uploaded_file, sheet_name='Participants', engine='openpyxl')

        renamed = data_frame.rename(columns={
            'Internal ID': 'Internal_ID',
            'Sorted Name': 'Sorted_Name',
            'Date of Birth': 'Date_of_Birth',
            'Phone Number': 'Phone_Number',
            'E-Mail': 'E_Mail',
        })

        for data_item in renamed.itertuples():
            internal_id = data_item.Internal_ID
            name = data_item.Name
            sort_name = data_item.Sorted_Name
            date_of_birth = data_item.Date_of_Birth
            address = data_item.Address
            phone_number = data_item.Phone_Number
            email = data_item.E_Mail
            metadata_txt = data_item.Metadata
            studies = data_item.Studies

            participant = None

            if math.isnan(internal_id) is False:
                participant = ResearchParticipant.objects.filter(pk=internal_id).first()

            if participant is None:
                participant = ResearchParticipant()

            if pandas.isna(name):
                participant.name = None
            else:
                participant.name = name

            if pandas.isna(sort_name):
                participant.sort_name = None
            else:
                participant.sort_name = sort_name

            if pandas.isna(address):
                participant.address = None
            else:
                participant.address = address

            if pandas.isna(email):
                participant.email = None
            else:
                participant.email = email

            if pandas.isna(date_of_birth):
                participant.date_of_birth = None
            else:
                participant.date_of_birth = date_of_birth

            if pandas.isna(phone_number):
                participant.phone_number = None
            else:
                participant.phone_number = int(phone_number)

            try:
                participant.metadata = json.loads(metadata_txt)
            except json.decoder.JSONDecodeError:
                pass
            except TypeError:
                pass

            if participant.name is not None:
                participant.save()

                for study_name in studies.split(','):
                    study_name = study_name.strip()

                    study = ResearchStudy.objects.filter(name=study_name).first()

                    if study is not None:
                        participation = ResearchParticipation.objects.filter(participant=participant, study=study).first()

                        if participation is None:
                            ResearchParticipation.objects.create(participant=participant, study=study)

        return redirect('dashboard_participants')

    valid_studies = ResearchStudy.objects.filter(staff_members=request.user)

    participants = ResearchParticipant.objects.filter(participations__study__in=valid_studies).distinct()

    data = {
        'Internal ID': [],
        'Name': [],
        'Sorted Name': [],
        'Date of Birth': [],
        'Address': [],
        'Phone Number': [],
        'E-Mail': [],
        'Metadata': [],
        'Studies': [],
    }

    for participant in participants:
        data['Internal ID'].append(participant.pk)
        data['Name'].append(participant.name)
        data['Sorted Name'].append(participant.sort_name)
        data['Date of Birth'].append(participant.date_of_birth)
        data['Address'].append(participant.address)
        data['Phone Number'].append(participant.phone_number)
        data['E-Mail'].append(participant.email)
        data['Metadata'].append(participant.metadata)

        studies = []

        for participation in participant.participations.all():
            if (participation.study.name in studies) is False:
                studies.append(participation.study.name)

        data['Studies'].append(', '.join(studies))

    data_frame = pandas.DataFrame(data)

    buffer = io.BytesIO()

    with pandas.ExcelWriter(buffer, engine='openpyxl') as writer: # pylint: disable=abstract-class-instantiated
        data_frame.to_excel(writer, sheet_name='Participants', index=False)

    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    response['Content-Disposition'] = 'attachment; filename="participants.xlsx"'

    return response
