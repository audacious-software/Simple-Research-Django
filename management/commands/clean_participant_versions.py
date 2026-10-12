# pylint: disable=no-member, line-too-long
# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from quicksilver.decorators import handle_lock, handle_schedule, add_qs_arguments, handle_logging

from ...models import ResearchParticipant

class Command(BaseCommand):
    help = 'Periodically synchronizes with configured data sources.'

    @add_qs_arguments
    def add_arguments(self, parser):
        pass

    @handle_logging
    @handle_schedule
    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-branches
        for participant in ResearchParticipant.objects.all():
            deleted = participant.clean_versions()

            if deleted > 0:
                print('%s: %s' % (deleted, participant))
