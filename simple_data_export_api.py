# pylint: disable=line-too-long, no-member

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

def export_data_types(available_sources): # pylint: disable=unused-argument
    return [
        # ('simple_messaging.conversation_transcripts', 'Conversation Transcripts',),
    ]
