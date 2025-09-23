# pylint: disable=no-member,line-too-long,ungrouped-imports
# -*- coding: utf-8 -*-


from prettyjson import PrettyJSONWidget

from django.contrib import admin
from django.db.models import JSONField
from django.utils.safestring import mark_safe

from .models import ResearchStudy, ResearchParticipant, ResearchParticipation

class PrettyJSONWidgetFixed(PrettyJSONWidget):
    def render(self, name, value, attrs=None, **kwargs):
        return mark_safe(super().render(name, value, attrs=None, **kwargs)) # nosec

@admin.register(ResearchStudy)
class ResearchStudyAdmin(admin.ModelAdmin):
    list_display = ('name', 'recruitment_starts', 'recruitment_ends', 'study_starts', 'study_ends',)
    search_fields = ('name', 'description', 'contact_information', 'principle_investigators', 'metadata',)
    list_filter = ('recruitment_starts', 'recruitment_ends', 'study_starts', 'study_ends', 'staff_members',)

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidgetFixed(attrs={'initial': 'parsed'})}
    }

@admin.register(ResearchParticipant)
class ResearchParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_name', 'date_of_birth', 'phone_number', 'email',)
    search_fields = ('name', 'sort_name', 'address', 'phone_number', 'email', 'metadata',)
    list_filter = ('date_of_birth', 'participations__study',)

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidgetFixed(attrs={'initial': 'parsed'})}
    }

@admin.register(ResearchParticipation)
class ResearchParticipationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'study', 'contacted', 'enrolled', 'exited', 'exit_reason',)
    search_fields = ('participant', 'study', 'exit_reason', 'metadata',)
    list_filter = ('contacted', 'enrolled', 'exited', 'study',)

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidgetFixed(attrs={'initial': 'parsed'})}
    }
