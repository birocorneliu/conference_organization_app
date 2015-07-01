import endpoints
from datetime import datetime
from lib.models import SessionForm

def getSessionData(request):
    if not request.name:
        raise endpoints.BadRequestException("Session 'name' field required")

    data = {field.name: getattr(request, field.name) for field in request.all_fields()}
    del data["websafeKey"]

    if data['date']:
        data['date'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()

    return data


def copySessionToForm(session):
    sess_form = SessionForm()
    for field in sess_form.all_fields():
        if hasattr(session, field.name):
            value = getattr(session, field.name)
            setattr(sess_form, field.name, value)
        elif field.name == "websafeKey":
            setattr(sess_form, field.name, session.key.urlsafe())

    return sess_form


