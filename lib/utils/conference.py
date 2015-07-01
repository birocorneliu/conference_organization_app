import endpoints
from datetime import datetime

from lib.models import ConflictException, ProfileForm, BooleanMessage, ConferenceForm, TeeShirtSize


DEFAULTS = {
    "city": "Default City",
    "maxAttendees": 0,
    "seatsAvailable": 0,
    "topics": ["Default", "Topic"],
}

def copyConferenceToForm(conf, displayName=None):
    """Copy relevant fields from Conference to ConferenceForm."""
    cf = ConferenceForm()
    for field in cf.all_fields():
        if hasattr(conf, field.name):
            # convert Date to date string; just copy others
            if field.name.endswith('Date'):
                setattr(cf, field.name, str(getattr(conf, field.name)))
            else:
                setattr(cf, field.name, getattr(conf, field.name))
        elif field.name == "websafeKey":
            setattr(cf, field.name, conf.key.urlsafe())
    if displayName:
        setattr(cf, 'organizerDisplayName', displayName)
    cf.check_initialized()
    return cf


def createConferenceObject(user_id, request):
    """Create or update Conference object, returning ConferenceForm/request."""
    # preload necessary data items
    if not request.name:
        raise endpoints.BadRequestException("Conference 'name' field required")

    # copy ConferenceForm/ProtoRPC Message into dict
    data = {field.name: getattr(request, field.name) for field in request.all_fields()}
    del data['websafeKey']
    del data['organizerDisplayName']

    # add default values for those missing (both data model & outbound Message)
    for df in DEFAULTS:
        if data[df] in (None, []):
            data[df] = DEFAULTS[df]
            setattr(request, df, DEFAULTS[df])

    # convert dates from strings to Date objects; set month based on start_date
    if data['startDate']:
        data['startDate'] = datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
        data['month'] = data['startDate'].month
    else:
        data['month'] = 0
    if data['endDate']:
        data['endDate'] = datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()

    # set seatsAvailable to be same as maxAttendees on creation
    if data["maxAttendees"] > 0:
        data["seatsAvailable"] = data["maxAttendees"]

    data['organizerUserId'] = request.organizerUserId = user_id

    return request, data


