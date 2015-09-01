from google.appengine.ext import ndb


class Profile(ndb.Model):
    """Profile -- User profile object"""
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    teeShirtSize = ndb.StringProperty(default='NOT_SPECIFIED')
    conferenceKeysToAttend = ndb.StringProperty(repeated=True)
    sessionKeysWishlist = ndb.StringProperty(repeated=True)


class Conference(ndb.Model):
    """Conference -- Conference object"""
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty()
    organizerUserId = ndb.StringProperty()
    topics = ndb.StringProperty(repeated=True)
    city = ndb.StringProperty()
    startDate = ndb.DateProperty()
    month = ndb.IntegerProperty()
    endDate = ndb.DateProperty()
    maxAttendees = ndb.IntegerProperty()
    seatsAvailable = ndb.IntegerProperty()
    sessions = ndb.StringProperty(repeated=True)


class Speaker(ndb.Model):
    name = ndb.StringProperty(required=True)
    age = ndb.IntegerProperty()
    specialization = ndb.StringProperty()


class Session(ndb.Model):
    """Session -- Session object"""
    name = ndb.StringProperty(required=True)
    speaker = ndb.StructuredProperty(Speaker)
    websafeConferenceKey = ndb.StringProperty()
    startTime = ndb.IntegerProperty()
    duration = ndb.IntegerProperty()
    typeOfSession = ndb.StringProperty()
    date = ndb.DateProperty()
    highlights = ndb.StringProperty(repeated=True)
