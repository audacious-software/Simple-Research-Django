# pylint: disable=no-member

from .models import ResearchParticipant

def evaluate_launch_keyword_context(sender, context):
    if 'enrolled' in context:
        participant = ResearchParticipant.models.participant_for_phone_number(sender)

        if participant is None and context.get('enrolled', None) is False:
            return True

        if participant is not None and context.get('enrolled', None) is True:
            return True

        return False

    if 'in_study' in context:
        participant = ResearchParticipant.models.participant_for_phone_number(sender)

        if participant is not None:
            studies = context.get('in_study', [])

            for study_name in participant.study_names():
                if study_name in studies:
                    return True

        return False

    return True
