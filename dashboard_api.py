from django.urls import reverse

def dashboard_pages():
    return [{
        'title': 'Research Participants',
        'icon': 'groups',
        'url': reverse('dashboard_participants'),
    }, {
        'title': 'Research Studies',
        'icon': 'assignment',
        'url': reverse('dashboard_studies'),
    }]
