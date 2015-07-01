import endpoints
from datetime import datetime

from lib import db
from lib import models
from lib.utils.shared import getUserId
from lib.models import ConflictException, ProfileForm, BooleanMessage, ConferenceForm, TeeShirtSize


def copyProfileToForm(prof):
    """Copy relevant fields from Profile to ProfileForm."""
    profile = models.ProfileForm()
    for field in profile.all_fields():
        if hasattr(prof, field.name):
            if field.name == 'teeShirtSize':
                setattr(profile, field.name, getattr(TeeShirtSize, getattr(prof, field.name)))
            else:
                setattr(profile, field.name, getattr(prof, field.name))
    profile.check_initialized()
    return profile


def updateProfile(prof, save_request=None):
    """Get user Profile and return to user, possibly updating it first."""
    if save_request:
        for field in ('displayName', 'teeShirtSize'):
            if hasattr(save_request, field):
                val = getattr(save_request, field)
                if val:
                    setattr(prof, field, str(val))
        prof.put()

    return prof
