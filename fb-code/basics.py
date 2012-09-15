#!/usr/bin/env python
from pyfb import Pyfb
import auth

#Your APP ID. It Needs to register your application on facebook
#http://developers.facebook.com/
FACEBOOK_APP_ID = '114757805341859'


permissions = [auth.USER_ALL_PERMISSIONS]#, auth.FRIENDS_ALL_PERMISSIONS]

facebook = Pyfb(FACEBOOK_APP_ID)
facebook.set_permissions(auth.USER_ALL_PERMISSIONS)

#Opens a new browser tab instance and authenticates with the facebook API
#It redirects to an url like http://www.facebook.com/connect/login_success.html#access_token=[access_token]&expires_in=0
facebook.authenticate()

#Copy the [access_token] and enter it below
token = raw_input("Enter the access_token\n")

#Sets the authentication token
facebook.set_access_token(token)

#Gets info about myself
me = facebook.get_myself()

print "-" * 40
print "Name: %s" % me.name
print "From: %s" % me.hometown.name
print "Now : %s" % me.location.name
print "Bio : %s" % me.bio

print "Favorite Teams:"
for team in me.favorite_teams:
	print "- %s" % team.name

print "Schools:"
for school in me.education:
	print "- %s" % school.school.name

print "Speaks:"
for language in me.languages:
    print "- %s" % language.name

interests = facebook._client.get_list(None, "interests")

print "Interests:"
for interest in interests:
	print "- %s" % interest.name

print "-" * 40
