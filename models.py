# pylint: disable=line-too-long, no-member

import importlib
import traceback

import phonenumbers

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

PARTICIPANT_PHONE_CACHE = {}

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

    is_active = models.BooleanField(default=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return '%s' % self.name

    def staff_pks(self):
        return list(self.staff_members.all().values_list('pk', flat=True))

class ResearchParticipantManager(models.Manager): # pylint: disable=too-few-public-methods
    def participant_with_token(self, token):
        participants = self.filter(metadata__login_token=token)

        return participants.first()

    def participant_for_phone_number(self, phone_number): # pylint: disable=too-many-branches
        if phone_number is None:
            return None

        participant = PARTICIPANT_PHONE_CACHE.get(phone_number, None)

        if participant is not None:
            return participant

        try: # pylint: disable=too-many-nested-blocks
            parsed_incoming = phonenumbers.parse(phone_number, settings.PHONE_REGION)

            found = []

            if phonenumbers.is_valid_number(parsed_incoming): # pylint: disable=too-many-nested-blocks
                formatted_incoming = phonenumbers.format_number(parsed_incoming, phonenumbers.PhoneNumberFormat.E164)

                for participant in self.all().exclude(phone_number=None):
                    parsed_participant = phonenumbers.parse(participant.phone_number, settings.PHONE_REGION)

                    if phonenumbers.is_valid_number(parsed_participant):
                        formatted_participant = phonenumbers.format_number(parsed_participant, phonenumbers.PhoneNumberFormat.E164)

                        if formatted_participant == formatted_incoming:
                            if (participant.pk in found) is False:
                                found.append(participant.pk)

                for version in ResearchParticipantVersion.objects.all().exclude(phone_number=None).exclude(participant=None):
                    try:
                        parsed_participant = phonenumbers.parse(version.phone_number, settings.PHONE_REGION)

                        if phonenumbers.is_valid_number(parsed_participant):
                            formatted_participant = phonenumbers.format_number(parsed_participant, phonenumbers.PhoneNumberFormat.E164)

                            if formatted_participant == formatted_incoming:
                                if (version.participant.pk in found) is False:
                                    found.append(version.participant.pk)
                    except phonenumbers.phonenumberutil.NumberParseException:
                        pass
        except phonenumbers.phonenumberutil.NumberParseException:
            traceback.print_exc()

        if len(found) == 0:
            return None

        if len(found) > 1:
            raise ResearchParticipant.MultipleObjectsReturned('%s participants with phone number %s. Expected 1.' % (len(found), phone_number))

        participant = self.all().filter(pk=found[0]).first()

        PARTICIPANT_PHONE_CACHE[phone_number] = participant

        return participant

class ResearchParticipant(models.Model):
    objects = ResearchParticipantManager()

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

    def study_participations(self):
        return self.participations.all().order_by('-enrolled')

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

    def get_absolute_url(self):
        if self.metadata.get('login_token', None) is None:
            token = get_random_string(length=32)

            while ResearchParticipant.objects.participant_with_token(token) is not None:
                token = get_random_string(length=32)

            self.metadata['login_token'] = token # pylint: disable=unsupported-assignment-operation

            self.save()

        return '%s%s' % (settings.SITE_URL, reverse('simple_research_participant_preferences', args=[self.metadata.get('login_token', None)]))

    def dashboard_additional_columns(self):
        column_values = []

        for app in settings.INSTALLED_APPS:
            try:
                research_module = importlib.import_module('.simple_research_api', package=app)

                module_values = research_module.dashboard_additional_columns(self.to_dict())

                if module_values is not None:
                    column_values.extend(module_values)
            except ImportError:
                pass
            except AttributeError:
                pass

        return column_values

    def to_dict(self):
        dict_value = {}

        dict_value.update(self.metadata)

        dict_value['phone_number'] = self.phone_number
        dict_value['date_of_birth'] = self.date_of_birth
        dict_value['email'] = self.email
        dict_value['address'] = self.address

        return dict_value

class ResearchParticipantVersion(models.Model): # pylint: disable=too-many-instance-attributes
    participant = models.ForeignKey(ResearchParticipant, related_name='versions', null=True, blank=True, on_delete=models.SET_NULL)

    created = models.DateTimeField()

    name = models.CharField(max_length=4096)
    sort_name = models.CharField(max_length=4096, null=True, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    address = models.TextField(max_length=(1024 * 1024), null=True, blank=True)
    phone_number = models.CharField(max_length=4096, null=True, blank=True)
    email = models.CharField(max_length=4096, null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return '%s (%s)' % (self.participant, self.created)

@receiver(post_save, sender=ResearchParticipant)
def create_participant_version(sender, instance, **kwargs): # pylint: disable=unused-argument
    version = ResearchParticipantVersion(participant=instance)

    version.created = timezone.now()

    version.name = instance.name
    version.sort_name = instance.sort_name
    version.date_of_birth = instance.date_of_birth
    version.address = instance.address
    version.phone_number = instance.phone_number
    version.email = instance.email
    version.metadata = instance.metadata

    version.save()

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
