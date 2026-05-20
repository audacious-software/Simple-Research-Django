# pylint: disable=no-member, line-too-long
# -*- coding: utf-8 -*-

import importlib
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand

from quicksilver.decorators import handle_lock, handle_schedule, add_qs_arguments, handle_logging

from ...models import ResearchStudy

class Command(BaseCommand):
    help = 'Periodically synchronizes with configured data sources.'

    @add_qs_arguments
    def add_arguments(self, parser):
        pass

    @handle_logging
    @handle_schedule
    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-branches
        records = []

        for study in ResearchStudy.objects.filter(is_active=True):
            for key in study.metadata.keys():
                for app in settings.INSTALLED_APPS:
                    try:
                        research_api = importlib.import_module(app + '.simple_research_api')

                        records.extend(research_api.fetch_records(key, study.metadata[key]))
                    except ImportError:
                        if app == 'simple_research':
                            traceback.print_exc()
                        # pass
                    except AttributeError:
                        if app == 'simple_research':
                            traceback.print_exc()
                        # pass

            for app in settings.INSTALLED_APPS:
                try:
                    research_api = importlib.import_module(app + '.simple_research_api')

                    research_api.process_records(records)
                except ImportError:
                    pass
                except AttributeError:
                    pass
