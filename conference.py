#!/USO/bin/en's python

import endpoints
from protorpc import messages, message_types, remote
from google.appengine.api import taskqueue, memcache

from lib import queries, utils
from lib.utils.shared import getUserId, ensure_logged_in, formatFilters
from settings import WEB_CLIENT_ID, MEMCACHE_FEATURED_SPEAKER
from lib.models import (ProfileMiniForm, ProfileForm, BooleanMessage,
                        ConferenceForm, ConferenceForms, ConferenceQueryForms,
                        StringMessage, getConferenceForm, updateConferenceForm,
                        SpeakerMessage, SessionForm, SessionsForm,
                        createSessionForm, getSessionForm,
                        getConferenceSessionsByTypeForm, getSessionsTask3Form)


@endpoints.api(name='conference', version='v1',
               allowed_client_ids=[WEB_CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID],
               scopes=[endpoints.EMAIL_SCOPE])
###################################################################################################
class ConferenceApi(remote.Service):


    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path='profile',
                      http_method='GET', name='getProfile')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def getProfile(self, user, request):
        """Return user profile."""
        profile = queries.get_create_profile(user)
        profile = utils.updateProfile(profile)
        return utils.copyProfileToForm(profile)


    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path='profile',
                      http_method='POST', name='saveProfile')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def saveProfile(self, user, request):
        """Update & return user profile."""
        profile = queries.get_create_profile(user)
        profile = utils.updateProfile(profile, request)
        return utils.copyProfileToForm(profile)


    @endpoints.method(ConferenceForm, ConferenceForm,
                      path='conference',
                      http_method='POST', name='createConference')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def createConference(self, user, request):
        """Create new conference."""
        user_id = getUserId(user)
        response, data = utils.createConferenceObject(user_id, request)
        queries.create_conference(user_id, data)
        taskqueue.add(params={'email': user.email(), 'conferenceInfo': repr(response)},
                      url='/tasks/send_confirmation_email')

        return response


    @endpoints.method(updateConferenceForm, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='PUT', name='updateConference')
    #TODO
    #----------------------------------------------------------------------------------------------
    def updateConference(self, request):
        """Update conference w/provided fields & return w/updated info."""

        return self._updateConferenceObject(request)


    @endpoints.method(getConferenceForm, ConferenceForm,
                      path='conference/{websafeConferenceKey}',
                      http_method='GET', name='getConference')
    #----------------------------------------------------------------------------------------------
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        conf = queries.get_conference(request.websafeConferenceKey)
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)
        prof = conf.key.parent().get()

        return utils.copyConferenceToForm(conf, getattr(prof, 'displayName'))


    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path='queryConferences',
                      http_method='POST', name='queryConferences')
    #----------------------------------------------------------------------------------------------
    def queryConferences(self, request):
        """Query for conferences."""
        inequality_filter, filters = formatFilters(request.filters)
        conferences = queries.get_conferences_with_filters(inequality_filter, filters)
        names = queries.get_conferences_names(conferences)
        items = [utils.copyConferenceToForm(conf, names[conf.organizerUserId]) for conf in conferences]

        return ConferenceForms(items=items)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='getConferencesCreated',
                      http_method='POST', name='getConferencesCreated')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def getConferencesCreated(self, user, request):
        """Return conferences created by user."""
        user_id = getUserId(user)
        confs, prof = queries.get_user_conferences(user_id)
        items = [utils.copyConferenceToForm(conf, getattr(prof, 'displayName')) for conf in confs]

        return ConferenceForms(items=items)


    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path='conferences/attending',
                      http_method='GET', name='getConferencesToAttend')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def getConferencesToAttend(self, user, request):
        """Get list of conferences that user has registered for."""
        profile = queries.get_create_profile(user)
        conferences = queries.get_conferences_to_attend(profile)
        names = queries.get_conferences_names(conferences)
        items = [utils.copyConferenceToForm(conf, names[conf.organizerUserId]) for conf in conferences]

        return ConferenceForms(items=items)


    @endpoints.method(getConferenceForm, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='POST', name='registerForConference')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def registerForConference(self, user, request):
        """Register user for selected conference."""
        profile = queries.get_create_profile(user)
        wsck = request.websafeConferenceKey
        conference = queries.get_conference(request.websafeConferenceKey)
        if not conference:
            raise endpoints.NotFoundException('No conference found with key: %s' % wsck)

        return queries.register_to_conference(profile, conference, wsck)


    @endpoints.method(getConferenceForm, BooleanMessage,
                      path='conference/{websafeConferenceKey}',
                      http_method='DELETE', name='unregisterFromConference')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def unregisterFromConference(self, user, request):
        """Unregister user for selected conference."""
        profile = queries.get_create_profile(user)
        wsck = request.websafeConferenceKey
        conference = queries.get_conference(request.websafeConferenceKey)
        if not conference:
            raise endpoints.NotFoundException('No conference found with key: %s' % wsck)

        return queries.unregister_to_conference(profile, conference, wsck)


    @endpoints.method(createSessionForm, SessionForm,
                      path='createSession',
                      http_method='POST', name='createSession')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def createSession(self, user, request):
        """Create Session."""
        user_id = getUserId(user)
        wsck = request.websafeConferenceKey
        queries.get_user_conference(user_id, wsck)
        data = utils.getSessionData(request)
        session = queries.create_session(data, wsck)
        taskqueue.add(params={'speaker': session.speaker.name, "wsck": wsck},
                      url='/tasks/set_featured_speaker')

        return utils.copySessionToForm(session)


    @endpoints.method(getSessionForm, SessionForm,
                      path='session/{SessionKey}',
                      http_method='GET', name='getSession')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def getSession(self, user, request):
        """"Return requested session (by SessionKey)."""
        profile = queries.get_create_profile(user)
        wssk = request.SessionKey
        session = queries.get_session(wssk)
        if not session:
            raise endpoints.NotFoundException('No session found with key: %s' % wssk)

        return utils.copySessionToForm(session)


    @endpoints.method(message_types.VoidMessage, SessionsForm,
                      path='getSessions',
                      http_method='GET', name='getSessions')
    #----------------------------------------------------------------------------------------------
    def getSessions(self, request):
        """Get Sessions"""
        sessions = queries.get_sessions()
        items = [utils.copySessionToForm(sess) for sess in sessions]

        return SessionsForm(items=items)


    @endpoints.method(SpeakerMessage, SessionsForm,
                      path='getSessionsBySpeaker/{speaker}',
                      http_method='GET', name='getSessionsBySpeaker')
    #----------------------------------------------------------------------------------------------
    def getSessionsBySpeaker(self, request):
        """Return sessions by speaker"""
        sessions = queries.get_sessions_by_speaker(request.speaker)
        items = [utils.copySessionToForm(sess) for sess in sessions]

        return SessionsForm(items=items)


    @endpoints.method(updateConferenceForm, SessionsForm,
                      path='getConferenceSessions/{websafeConferenceKey}',
                      http_method='GET', name='getConferenceSessions')
    #----------------------------------------------------------------------------------------------
    def getConferenceSessions(self, request):
        """Return sessions from conference"""
        sessions = queries.get_conference_sessions(request.websafeConferenceKey)
        items = [utils.copySessionToForm(sess) for sess in sessions]

        return SessionsForm(items=items)


    @endpoints.method(getConferenceSessionsByTypeForm, SessionsForm,
                      path='getConferenceSessionsByType/{websafeConferenceKey}',
                      http_method='GET', name='getConferenceSessionsByType')
    #----------------------------------------------------------------------------------------------
    def getConferenceSessionsByType(self, request):
        """Return sessions from conference by type"""
        sessions = queries.get_conference_sessions(request.websafeConferenceKey,
                                                   request.typeOfSession)
        items = [utils.copySessionToForm(sess) for sess in sessions]

        return SessionsForm(items=items)


    @endpoints.method(message_types.VoidMessage, SessionsForm,
                      path='wishlist',
                      http_method='GET', name='getSessionsInWishlist')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def getSessionsInWishlist(self, user, request):
        """Get all sessions stored in wishlist."""
        profile = queries.get_create_profile(user)
        sessions = queries.get_sessions_in_wishlist(profile)
        items = [utils.copySessionToForm(sess) for sess in sessions]

        return SessionsForm(items=items)


    @endpoints.method(getSessionForm, BooleanMessage,
                      path='wishlist/{SessionKey}',
                      http_method='POST', name='addSessionToWishlist')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def addSessionToWishlist(self, user, request):
        """Add session to user's wishlist."""
        profile = queries.get_create_profile(user)
        wssk = request.SessionKey
        session = queries.get_session(wssk)
        if not session:
            raise endpoints.NotFoundException('No session found with key: %s' % wssk)

        return queries.add_session_to_wishlist(profile, wssk)


    @endpoints.method(getSessionForm, BooleanMessage,
                      path='wishlist/{SessionKey}',
                      http_method='DELETE', name='removeSessionFromWishlist')
    @ensure_logged_in
    #----------------------------------------------------------------------------------------------
    def removeSessionFromWishlist(self, user, request):
        """Remove session from user's wishlist."""
        profile = queries.get_create_profile(user)
        wssk = request.SessionKey
        session = queries.get_session(wssk)
        if not session:
            raise endpoints.NotFoundException('No session found with key: %s' % wssk)

        return queries.delete_session_from_wishlist(profile, wssk)



    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path='getFeaturedSpeaker',
                      http_method='GET', name='getFeaturedSpeaker')
    #----------------------------------------------------------------------------------------------
    def getFeaturedSpeaker(self, request):
        """Return Announcement from memcache."""
        message = memcache.get(MEMCACHE_FEATURED_SPEAKER)
        announcement = message if message else ""

        return StringMessage(data=announcement)


    @endpoints.method(getSessionsTask3Form, SessionsForm,
                      path='querySessionT3',
                      http_method='POST', name='querySessionT3')
    #----------------------------------------------------------------------------------------------
    def querySessionT3(self, request):
        """Query for conferences."""
        sessions = queries.query_session_task3(request.lastStartTimeHour,
                                               request.unwantedTypeOfSession)
        items = [utils.copySessionToForm(sess) for sess in sessions]

        return SessionsForm(items=items)


api = endpoints.api_server([ConferenceApi])
