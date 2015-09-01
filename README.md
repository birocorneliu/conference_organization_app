App Engine application for the Udacity training course.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]

## Setup Instructions
1. Update the value of `application` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
1. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][4].
1. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
1. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
1. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting
   your local server's address (by default [localhost:8080][5].)
1. Generate your client library(ies) with [the endpoints tool][6].
1. Deploy your application.


## Tasks

### Task 1
1. Speaker is an entity that has the `name` as primary key. This was done not to create confusions betwen names when testing and to identify speakers more easly. This will be changed into a generated key. It contains the following fields:
    - name - StringProperty(required, unique)
    - age - IntegerProperty
    - specialization - StringProperty
1. Session is an entity containing the entity speaker inside it for quick access. All required fields as described below:
    - name - StringProperty(required)
    - speaker - StructuredProperty(Speaker)
    - websafeConferenceKey - StringProperty
    - startTime - IntegerProperty
    - duration - IntegerProperty
    - typeOfSession - StringProperty
    - date - DateProperty
    - highlights - StringProperty(repeated)
1. Endpoints implemented
    - getConferenceSessions(websafeConferenceKey)
    - getConferenceSessionsByType(websafeConferenceKey, typeOfSession)
    - getSessionsBySpeaker(speaker)
    - createSession(SessionForm, websafeConferenceKey))

### Task 2
1. Endpoints implemented
    - addSessionToWishlist(SessionKey)
    - getSessionsInWishlist()

### Task 3
1. I've created querySessionT3 endpoint witch supports time and sessionType params. I've solved the problem by enumerating all hours before 7pm. This way I've managed to avoid using 2 inequality filters but several equality ones and a single inequality filter.
1. Aditional endpoints implemented
    - getSession(SessionKey) - get session details with provided SessionKey
    - removeSessionFromWishlist(SessionKey) - remove session from wishlist(just because anyone can make a mistake)
    - querySessionT3(lastStartTimeHour, unwantedTypeOfSession)

### Task 4
1. Implement a method that ads speaker and session names to memcache if upon session creation speaker has another session on that conference.
1. Endpoints implemented
    - getFeaturedSpeaker()


[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool
