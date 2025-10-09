# pylint: disable=line-too-long, no-member

import json
import time

import phonenumbers

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import ResearchStudy, ResearchParticipant

@staff_member_required
def dashboard_participants(request):
    context = {
        'include_search': True,
        'studies': ResearchStudy.objects.all().order_by('name'),
    }

    offset = int(request.GET.get('offset', '0'))
    limit = int(request.GET.get('limit', '25'))
    query = request.GET.get('q', None)

    participant_objects = ResearchParticipant.objects.all()

    if (query in (None, '')) is False:
        search_query = Q(name__icontains=query) | Q(address__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(phone_number__icontains=query) | Q(email__icontains=query) # pylint: disable=unsupported-binary-operation
        search_query = search_query | Q(metadata__icontains=query) # pylint: disable=unsupported-binary-operation

        participant_objects = ResearchParticipant.objects.filter(search_query)

    total = participant_objects.count()

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
