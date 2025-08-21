# pylint: disable=line-too-long, no-member

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
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
        search_query = search_query | Q(metadata__icontains=query)

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
