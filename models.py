# pylint: disable=line-too-long, no-member

import importlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

class ResearchStudy(models.Model):
    name = models.CharField(max_length=4096)

    description = models.TextField(max_length=(1024 * 1024), null=True, blank=True)

    contact_information = models.TextField(max_length=(1024 * 1024), null=True, blank=True)

    principle_investigators = models.TextField(max_length=(1024 * 1024), null=True, blank=True)

    staff_members = models.ManyToManyField(get_user_model(), related_name='research_studies')

    participants_target = models.IntegerField(null=True, blank=True)

    recruitment_starts = models.DateField(null=True, blank=True)
    recruitment_ends = models.DateField(null=True, blank=True)

    study_starts = models.DateField(null=True, blank=True)
    study_ends = models.DateField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return '%s' % self.name

    def staff_pks(self):
        return list(self.staff_members.all().values_list('pk', flat=True))

class ResearchParticipant(models.Model):
    name = models.CharField(max_length=4096)
    sort_name = models.CharField(max_length=4096, null=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    address = models.TextField(max_length=(1024 * 1024), null=True, blank=True)
    phone_number = models.CharField(max_length=4096, null=True, blank=True)
    email = models.CharField(max_length=4096, null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return '%s' % self.name

    def study_pks(self):
        return list(self.participations.all().values_list('study__pk', flat=True))

    def study_names(self):
        return list(self.participations.all().order_by('study__name').values_list('study__name', flat=True))

    def update_enrollments(self, studies):
        current = []

        for participation in self.participations.all():
            current.append(participation.study.pk)

        to_add = []

        for study in studies:
            if study.pk in current:
                current.remove(study.pk)

            to_add.append(study.pk)

        for study_pk in current:
            participation = self.participations.filter(study=study_pk).first()

            if participation is not None:
                participation.exited = timezone.now().date()
                participation.exit_reason = 'Removed in dashboard.'
                participation.save()

        for study_pk in to_add:
            study = ResearchStudy.objects.filter(pk=study_pk).first()

            if study is not None:
                participation = self.participations.filter(study=study).first()

                if participation is not None:
                    pass # Do nothing - already enrolled
                else:
                    participation = ResearchParticipation.objects.create(study=study, participant=self)
                    participation.enrolled = timezone.now().date()

                    participation.save()

    def dashboard_actions(self):
        actions = []

        metadata = {
            'name': self.name,
            'date_of_birth': self.date_of_birth,
            'address': self.address,
            'phone_number': self.phone_number,
            'email': self.email,
        }

        for app in settings.INSTALLED_APPS:
            try:
                research_module = importlib.import_module('.simple_research_api', package=app)

                module_actions = research_module.dashboard_actions(metadata)

                if module_actions is not None:
                    actions.extend(module_actions)
            except ImportError:
                pass
            except AttributeError:
                pass

        return actions

class ResearchParticipation(models.Model):
    study = models.ForeignKey(ResearchStudy, related_name='participations', on_delete=models.CASCADE)
    participant = models.ForeignKey(ResearchParticipant, related_name='participations',  on_delete=models.CASCADE)

    contacted = models.DateField(null=True, blank=True)
    enrolled = models.DateField(null=True, blank=True)
    exited = models.DateField(null=True, blank=True)

    exit_reason = models.CharField(max_length=4096, null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return '%s in %s' % (self.participant, self.study)
