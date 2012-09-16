# Python
import os
import json
import random
import urllib
import urllib2
import re
import textwrap
import heapq
import xmltodict

# Tornado
import tornado.httpserver
import tornado.httpclient
import tornado.options
import tornado.ioloop
import tornado.web

# Yelp
#from yelp import ReviewSearchApi

# Eventful
import eventful

eventful_api = eventful.API('5zPbkgmCjXhLpHT9')

# Mongo
import pymongo
from bson import json_util

#Foursquare
import foursquare

FSQOauthToken = "QYEIVBMULP11CPVHP4MSHXDB2VIZ12LDDUTMMJL2YSP2IJJA"
FSQOauthSecret = "L04TIELKXWIHKVXWI1PRENGM1YFSPHHX0PEUZQSUIMDVHDDU"

#FB
import fbconsole

#Sendgrid
import sendgrid

my_date = ""
movies = dict()
own_likes = ""
friend_tuples = {}

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/main", MainHandler),
            (r"/fsmain", FSMainHandler),
            (r"/FoursquareHandler", FoursquareHandler),
            (r"/doSearchHandler", DoSearchHandler),
            (r"/fbauth", FBHandler),
            (r"/autocomplete", AutocompleteHandler),
            (r"/DateHandler", DateHandler),
            (r"/emailhandler", EmailHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    pass

        
class DoSearchHandler(BaseHandler):
    def get(self):
        client = foursquare.Foursquare(client_id=FSQOauthToken, client_secret=FSQOauthSecret)
        data = client.venues.search(params={'query':'pizza', 'near':'New Haven, CT', 'radius':'10', 'intent':'browse'})
        self.write("<html><head><title>Pizza in New Haven</title></head><body>")
        for item in data["venues"]:
            self.write("<p>" + item["name"] + "</p>")
        self.write("</body></html>")

    def post(self):
        self.get()
                   

class FoursquareHandler(BaseHandler):
    def post(self):
        client = foursquare.Foursquare(client_id=FSQOauthToken, 
                               client_secret=FSQOauthSecret,
                               redirect_uri='http://localhost:3000/fsmain')

        # Build the authorization url for your app
        auth_uri = client.oauth.auth_url()        
        self.write('Hello World, redirecting to %s' % auth_uri)
        self.redirect(auth_uri)

class FSMainHandler(BaseHandler):
    def get(self):

        client = foursquare.Foursquare(client_id='QYEIVBMULP11CPVHP4MSHXDB2VIZ12LDDUTMMJL2YSP2IJJA', 
                               client_secret='L04TIELKXWIHKVXWI1PRENGM1YFSPHHX0PEUZQSUIMDVHDDU', 
                               redirect_uri='http://localhost:3000/fsmain')
        # Interrogate foursquare's servers to get the user's access_token
        access_token = client.oauth.get_token(self.get_argument("code"))

class FBHandler(BaseHandler):
    def post(self):

        fbconsole.AUTH_SCOPE = ['user_interests', 'user_likes', 'friends_interests', 'friends_likes',
                                'user_location', 'friends_location', 'user_activities', 'friends_activities']
        fbconsole.authenticate()
        self.redirect("/main");

class AutocompleteHandler(BaseHandler):
    def get(self):
        term = self.get_argument('term', "")
        print 'term is %s' % term

        friend_tuples = fbconsole.fql("SELECT name FROM user WHERE uid IN "
                                        "(SELECT uid2 FROM friend WHERE uid1 = me())")
        result = []
        for item in friend_tuples:
            if term in item['name']:
                result.append(item['name'])

        self.write(json.dumps(result))


class DateHandler(BaseHandler):
    def post(self):
        global movies
        global own_likes
        global friend_tuples

        my_date = self.get_argument('friend_name')

        target_uid = -1;
        for item in friend_tuples:
            if item['name'] == my_date:
                target_uid = item['uid']
                break
        print ("User id is %s" % target_uid)

        #gather the date's likes, represented by object_id
        #date_likes = fbconsole.fql("SELECT page_id FROM page_fan WHERE uid IN "
        #                            "(SELECT uid2 FROM friend WHERE uid1 = me() AND uid2 = %s)" % target_uid)

        my_movies = fbconsole.get('/me/movies')
        my_music = fbconsole.get('/me/music')
        my_tv = fbconsole.get('/me/television')
        my_activities = fbconsole.get('/me/activities')

        friend_movies = fbconsole.get('/%s/movies' % target_uid)
        friend_music = fbconsole.get('/%s/music' % target_uid)
        friend_tv = fbconsole.get('/%s/television' % target_uid)
        friend_activities = fbconsole.get('/%s/activities' % target_uid)

        print my_activities
        print friend_activities

        date_likes = fbconsole.fql("SELECT page_id FROM page_fan WHERE uid = %s" % target_uid)
        date_locale = fbconsole.fql("SELECT current_location FROM user WHERE uid = %s" % target_uid)

        #more_my_likes = fbconsole.fql("SELECT url FROM url_like WHERE user_id = %s" % target_uid)
        for item in date_likes:
            print json.dumps(item)
       
        #movies = eventful_api.call('/events/search', q='comedy', l=own_locale)
        while (len(movies) == 0):
            pass
        for movie in movies['search']['events']['event']:
            print "%s at %s" % (movie['title'], movie['venue_name'])
        
        print date_locale

        query_dict = {}
        venues = []
        fsQuery = ""
        for item in own_likes:
            if item in date_likes:
                page_id = item['page_id']
                page = fbconsole.fql("SELECT name,categories FROM page WHERE page_id = %s" % page_id)
                for it in page:
                    fsQuery += it["name"]  + " "
                    print ("Both people like " + it["name"])
        client = foursquare.Foursquare(client_id=FSQOauthToken, client_secret=FSQOauthSecret)
        data = client.venues.search(params={'query': fsQuery, 'near':'New Haven, CT', 'radius':'10', 'intent':'browse'})
        for aplace in data["venues"]:
				  heapq.heappush(venues, (aplace["stats"]["checkinsCount"], aplace["name"]))
        largest = heapq.nlargest(10, venues)
        for loc in largest:
        	self.write("<p>" + loc[1] + "</p>")
        #for item in venues:
        #    heapq.heappush(venue_queue, (item["stats"]["checkinsCount"], item["name"]))
        #top_venues = heapq.nlargest(5, venue_queue)
#self.write(len(top_venues))
    #self.write(json.dumps(page))

        self.render("final.html");


class EmailHandler(BaseHandler):
    def post(self):

        day = self.get_argument('day')
        time = self.get_argument('time')
        s = sendgrid.Sendgrid('AayushU', 'helloworld', secure=True)
        message = sendgrid.Message("aayushu@gmail.com", "Wanna chill soon?", "Hey %s, do you want to go " 
        "to dinner with me on %s at %s?" % (my_date, day,time), "")
        message.add_to("aayushu@gmail.com", my_date) 
        s.web.send(message)
        self.write("Done sending message!")


class HomeHandler(BaseHandler):
    def get(self):
        self.render("home.html");


class MainHandler(BaseHandler):
    def get(self):
        global own_likes
        global friend_tuples
        user = fbconsole.get('/me')
        uid = user['id']
        client = tornado.httpclient.HTTPClient()
        friend_tuples = fbconsole.fql("SELECT name,uid FROM user WHERE uid IN "
                                        "(SELECT uid2 FROM friend WHERE uid1 = me())")
        own_likes = fbconsole.fql("SELECT page_id FROM page_fan WHERE uid = %s" % uid)
        own_locale = fbconsole.fql("SELECT current_location FROM user WHERE uid = %s" % uid)

        #gather own locale
        city = own_locale[0]['current_location']['city']
        city = city.replace(' ',',')
        client = tornado.httpclient.AsyncHTTPClient()
        
        client.fetch("http://api.eventful.com/rest/events/search?" + \
                    urllib.urlencode({"app_key": "5zPbkgmCjXhLpHT9", "keywords":"movies", "location":city}),
                    callback=self.on_movie_response)

        self.render("main.html");

    def on_movie_response(self, response):
        print "caught response"
        global movies
        movies = xmltodict.parse(response.body)


def main(port='3000', address='127.0.0.1'):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

