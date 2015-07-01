from datetime import datetime

import endpoints
from google.appengine.ext import ndb
from google.appengine.api import taskqueue, memcache

from lib.db import Profile, Conference
from lib.models import ConflictException, ProfileForm, BooleanMessage, ConferenceForm, TeeShirtSize


MEMCACHE_ANNOUNCEMENTS_KEY = "RECENT_ANNOUNCEMENTS"


@ndb.transactional()
def _updateConferenceObject(self, request):
    user = endpoints.get_current_user()
    if not user:
        raise endpoints.UnauthorizedException('Authorization required')
    user_id = getUserId(user)

    # copy ConferenceForm/ProtoRPC Message into dict
    data = {field.name: getattr(request, field.name) for field in request.all_fields()}

    # update existing conference
    conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
    # check that conference exists
    if not conf:
        raise endpoints.NotFoundException(
            'No conference found with key: %s' % request.websafeConferenceKey)

    # check that user is owner
    if user_id != conf.organizerUserId:
        raise endpoints.ForbiddenException(
            'Only the owner can update the conference.')

    # Not getting all the fields, so don't create a new object; just
    # copy relevant fields from ConferenceForm to Conference object
    for field in request.all_fields():
        data = getattr(request, field.name)
        # only copy fields where we get data
        if data not in (None, []):
            # special handling for dates (convert string to Date)
            if field.name in ('startDate', 'endDate'):
                data = datetime.strptime(data, "%Y-%m-%d").date()
                if field.name == 'startDate':
                    conf.month = data.month
            # write to Conference object
            setattr(conf, field.name, data)
    conf.put()
    prof = ndb.Key(Profile, user_id).get()
    return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))


@staticmethod
def _cacheAnnouncement():
    """Create Announcement & assign to memcache; used by
    memcache cron job & putAnnouncement().
    """
    confs = Conference.query(ndb.AND(
        Conference.seatsAvailable <= 5,
        Conference.seatsAvailable > 0)
    ).fetch(projection=[Conference.name])

    if confs:
        # If there are almost sold out conferences,
        # format announcement and set it in memcache
        announcement = '%s %s' % (
            'Last chance to attend! The following conferences '
            'are nearly sold out:',
            ', '.join(conf.name for conf in confs))
        memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
    else:
        # If there are no sold out conferences,
        # delete the memcache announcements entry
        announcement = ""
        memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)

    return announcement
