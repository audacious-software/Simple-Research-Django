# pylint: disable=line-too-long, no-member

import io
import importlib
import json
import os
import tempfile

import phonenumbers
import pytz

from django.conf import settings
from django.db import connection

from simple_data_export.utils import fetch_export_identifier, UnicodeWriter # pylint: disable=import-error

from .models import ResearchParticipation

def export_data_sources(params=None, requester=None): # pylint: disable=too-many-branches
    if params is None:
        params = {}

    data_sources = []

    if requester is not None:
        for study in requester.research_studies.all():
            for enrollment in study.participations.all():
                data_sources.append(('simple_research:%s' % enrollment.participant.pk, enrollment.participant.name, study.name))

    return data_sources

def prune_export_sources(sources):
    new_sources = []

    for source in sources:
        if source[0].startswith('simple_research:'):
            new_sources.append(source)

    return new_sources

def export_data_types(available_sources):
    return [
        # ('simple_messaging.conversation_transcripts', 'Conversation Transcripts',),
    ]
