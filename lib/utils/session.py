import endpoints
from datetime import datetime
from lib.models import SessionForm
from .speaker import copySpeakerToForm



def getSessionData(request):
    if not request.name:
        raise endpoints.BadRequestException("Session 'name' field required")

    data = {field.name: getattr(request, field.name) for field in request.all_fields()}
    del data["websafeKey"]

    if data['date']:
        data['date'] = datetime.strptime(data['date'][:10], "%Y-%m-%d").date()

    return data


def copySessionToForm(session):
    sess_form = SessionForm()
    for field in sess_form.all_fields():
        if field.name == 'date':
            setattr(sess_form, field.name, str(getattr(sess_form, field.name)))
        elif field.name == "websafeKey":
            setattr(sess_form, field.name, session.key.urlsafe())
        elif field.name == "speaker":
            setattr(sess_form, field.name, copySpeakerToForm(session.speaker))
        elif hasattr(session, field.name):
            value = getattr(session, field.name)
            setattr(sess_form, field.name, value)

    return sess_form


