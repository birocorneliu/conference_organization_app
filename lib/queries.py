import endpoints
from google.appengine.ext import ndb
from google.appengine.api import memcache

from settings import MESSAGE_FEATURED_SPEAKER, MEMCACHE_FEATURED_SPEAKER
from lib import models
from lib.db import Profile, Conference, Session, Speaker
from lib.utils.shared import getUserId


def get_conference(conf_key):
    conf = ndb.Key(urlsafe=conf_key).get()
    return conf


def get_session(sess_key):
    conf = ndb.Key(urlsafe=sess_key).get()
    return conf


def get_conference_sessions(wsck, typeOfSession=None):
    conference = ndb.Key(urlsafe=wsck)
    sessions = Session.query(ancestor=conference)
    if typeOfSession is not None:
        sessions = sessions.filter(Session.typeOfSession == typeOfSession)

    return sessions


def create_session(data, wsck):
    c_key = ndb.Key(urlsafe=wsck)
    s_id = Session.allocate_ids(size=1, parent=c_key)[0]
    s_key = ndb.Key(Session, s_id, parent=c_key)
    data['key'] = s_key
    speaker = get_create_speaker(data["speaker"])
    data["speaker"] = speaker
    session = Session(**data)
    session.put()

    return session


def create_conference(user_id, data):
    p_key = ndb.Key(Profile, user_id)
    c_id = Conference.allocate_ids(size=1, parent=p_key)[0]
    c_key = ndb.Key(Conference, c_id, parent=p_key)
    data['key'] = c_key

    Conference(**data).put()


def get_user_conferences(user_id):
    confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
    profile = ndb.Key(Profile, user_id).get()

    return confs, profile


def get_user_conference(user_id, wsck):
    conference = get_conference(wsck)
    conferences = Conference.query(ancestor=ndb.Key(Profile, user_id))
    if not conference in conferences:
        endpoints.UnauthorizedException("Not allowed!")

    return conference


def get_create_speaker(speaker):
    if hasattr(speaker, "name"):
        speaker_key = ndb.Key(Speaker, speaker.name)
    else:
        speaker_key = ndb.Key(Speaker, speaker)
    response = speaker_key.get()

    if not response:
        response = Speaker(
            key=speaker_key,
            name=speaker.name,
            age=speaker.age,
            specialization=speaker.specialization
            )
        response.put()
    return response



def get_create_profile(user):
    user_id = getUserId(user)
    p_key = ndb.Key(Profile, user_id)
    profile = p_key.get()

    # create new Profile if not there
    if not profile:
        size = str(models.TeeShirtSize.NOT_SPECIFIED)
        profile = Profile(
            key=p_key,
            displayName=user.nickname(),
            mainEmail=user.email(),
            teeShirtSize=size)
        profile.put()
    return profile


def get_conferences_names(conferences):
    organisers = [(ndb.Key(Profile, conf.organizerUserId)) for conf in conferences]
    profiles = ndb.get_multi(organisers)
    names = {}
    for profile in profiles:
        names[profile.key.id()] = profile.displayName

    return names


def get_conferences_to_attend(profile):
    conf_keys = [ndb.Key(urlsafe=wsck) for wsck in profile.conferenceKeysToAttend]
    return ndb.get_multi(conf_keys)


def get_sessions_in_wishlist(profile):
    conf_keys = [ndb.Key(urlsafe=wsck) for wsck in profile.sessionKeysWishlist]
    return ndb.get_multi(conf_keys)


def get_conferences_with_filters(inequality_filter, filters):
    """Return formatted query from the submitted filters."""
    query = Conference.query()
    if inequality_filter:
        query = query.order(ndb.GenericProperty(inequality_filter))
    query = query.order(Conference.name)

    for filtr in filters:
        if filtr["field"] in ["month", "maxAttendees"]:
            filtr["value"] = int(filtr["value"])
        formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
        query = query.filter(formatted_query)

    return query


@ndb.transactional(xg=True)
def register_to_conference(profile, conference, wsck):
    """Register or unregister user for selected conference."""
    retval = None

    # check if user already registered otherwise add
    if wsck in profile.conferenceKeysToAttend:
        message = "You have already registered for this conference"
        raise models.ConflictException(message)

    # check if seats avail
    if conference.seatsAvailable <= 0:
        raise models.ConflictException("There are no seats available.")

    # register user, take away one seat
    profile.conferenceKeysToAttend.append(wsck)
    conference.seatsAvailable -= 1
    retval = True

    # write things back to the datastore & return
    profile.put()
    conference.put()

    return models.BooleanMessage(data=retval)


def add_session_to_wishlist(profile, wssk):
    if wssk not in profile.sessionKeysWishlist:
        profile.sessionKeysWishlist.append(wssk)
        profile.put()
    return models.BooleanMessage(data=True)


def delete_session_from_wishlist(profile, wssk):
    retval = None
    if wssk in profile.sessionKeysWishlist:
        profile.sessionKeysWishlist.remove(wssk)
        profile.put()
        retval = True
    else:
        retval = False
    return models.BooleanMessage(data=retval)


@ndb.transactional(xg=True)
def unregister_to_conference(profile, conference, wsck):
    """Register or unregister user for selected conference."""
    retval = None
    # check if user already registered
    if wsck in profile.conferenceKeysToAttend:
        profile.conferenceKeysToAttend.remove(wsck)
        conference.seatsAvailable += 1
        retval = True
    else:
        retval = False

    # write things back to the datastore & return
    profile.put()
    conference.put()
    return models.BooleanMessage(data=retval)


def get_sessions():
    query = Session.query()
    return query.fetch()


def get_sessions_by_speaker(speaker_name):
    speaker = get_create_speaker(speaker_name)
    query = Session.query()
    query = query.filter(Session.speaker == speaker)

    return query


def set_featured_speaker(wsck, speaker_name):
    speaker = get_create_speaker(speaker_name)
    query = Session.query()
    query = query.filter(Session.speaker == speaker)
    sessions = query.filter(Session.websafeConferenceKey == wsck)
    if sessions.count() > 1:
        message = MESSAGE_FEATURED_SPEAKER.format(
            speaker_name,
            ", ".join([sess.name for sess in sessions]))
        memcache.set(MEMCACHE_FEATURED_SPEAKER, message)


def query_session_task3(last_hour, session_type):
    query = Session.query()
    query = query.filter(Session.startTime.IN(range(1, last_hour+1)))
    query = query.filter(Session.typeOfSession != session_type)
    return query


