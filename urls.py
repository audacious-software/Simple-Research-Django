# pylint: disable=line-too-long, wrong-import-position

import sys

if sys.version_info[0] > 2:
    from django.urls import re_path as url # pylint: disable=no-name-in-module
else:
    from django.conf.urls import url

from .views import dashboard_studies, dashboard_delete_study, dashboard_update_study, \
                   dashboard_participants, dashboard_delete_participant, dashboard_update_participant

urlpatterns = [
    url(r'^participants$', dashboard_participants, name='dashboard_participants'),
    url(r'^dashboard/participant/delete.json$', dashboard_delete_participant, name='dashboard_delete_participant'),
    url(r'^dashboard/participant/update.json$', dashboard_update_participant, name='dashboard_update_participant'),
    url(r'^studies$', dashboard_studies, name='dashboard_studies'),
    url(r'^dashboard/study/delete.json$', dashboard_delete_study, name='dashboard_delete_study'),
    url(r'^dashboard/study/update.json$', dashboard_update_study, name='dashboard_update_study'),
]
