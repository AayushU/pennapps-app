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

#eventful_api = eventful.API('5zPbkgmCjXhLpHT9')

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
my_loc = "" 

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
        global friend_tuples
        term = self.get_argument('term', "")
        print 'term is %s' % term

        result = []
        for item in friend_tuples:
            if term.lower() in item['name'].lower():
                result.append(item['name'])

        self.write(json.dumps(result))


class DateHandler(BaseHandler):
    def post(self):
        global movies
        global own_likes
        global friend_tuples
        global my_loc

        my_date = self.get_argument('friend_name')

        target_uid = -1;
        for item in friend_tuples:
            if item['name'] == my_date:
                target_uid = item['uid']
                break
        print ("User id is %s" % target_uid)

        #gather the date's likes, represented by object_id

        """my_movies = fbconsole.get('/me/movies')
        my_music = fbconsole.get('/me/music')
        my_tv = fbconsole.get('/me/television')
        my_activities = fbconsole.get('/me/activities')
        """
        my_likes = fbconsole.get('/me/likes')

        """friend_movies = fbconsole.get('/%s/movies' % target_uid)
        friend_music = fbconsole.get('/%s/music' % target_uid)
        friend_tv = fbconsole.get('/%s/television' % target_uid)
        friend_activities = fbconsole.get('/%s/activities' % target_uid)
        """
        friend_likes = fbconsole.get('/%s/likes' % target_uid)

        print friend_likes
        
        my_like_count = {}
        friend_like_count = {}

        for item in my_likes['data']:
            cat = str(item['category'])
            if cat in my_like_count:
                my_like_count[cat] += 1
            else:
                my_like_count[cat] = 1 

        for item in friend_likes['data']:
            cat = str(item['category'])
            if cat in friend_like_count:
                friend_like_count[cat] += 1
            else:
                friend_like_count[cat] = 1

        my_top_category = ""
        friend_top_category = ""

        for item in sorted(my_like_count, key = my_like_count.get, reverse=True):
            if item == "Community" or item == "Interest": # too vague
                continue
            else:
                if item == 'Musician/band':
                    item = 'band'
                elif item == 'Professional sports team':
                    item = "Sports"
                my_top_category = item
                break

        for item in sorted(friend_like_count, key = friend_like_count.get, reverse=True):
            if item == "Community" or item == "Interest": # too vague
                continue
            else:
                if item == 'Musician/band':
                    item = 'band'
                elif item == 'Professional sports team':
                    item = "Sports"
                friend_top_category = item
                break
            
        #print my_like_count
        #print friend_like_count

        #print "My top category is %s" % my_top_category
        #print "My date's top category is %s" % friend_top_category

        venues = []
        client = foursquare.Foursquare(client_id=FSQOauthToken, client_secret=FSQOauthSecret)
				#-------Searching 4Sq
        #data = client.venues.search(params={'query': fsQuery, 'near':'New Haven, CT', 'radius':'10', 'intent':'browse'})
        #for aplace in data["venues"]:
				#  heapq.heappush(venues, (aplace["stats"]["checkinsCount"], aplace["name"]))
        #largest = heapq.nlargest(10, venues)
        #for loc in largest:
        #	self.write("<p>" + loc[1] + "</p>")
		        #-------Exploring 4Sq
        
        self.write("<p> Here are the top locations for my preference, which is %s</p>" % my_top_category)
        data = client.venues.explore(params={'near' : my_loc, 'query': my_top_category})
        for it in data["groups"]:
            for item in it["items"]:
                heapq.heappush(venues, (item["venue"]["stats"]["checkinsCount"], item["venue"]))
        largest = heapq.nlargest(1, venues)
        for loc in largest:
            self.write("<p>" + loc[1]['name'] + "</p>")
            first_place = loc[1]
            print first_place
       
        venues = []
        self.write("<p> Here are the top locations for my date, which is %s</p>" % friend_top_category)
        data = client.venues.explore(params={'near' : my_loc, 'query':  friend_top_category })
        for it in data["groups"]:
            for item in it["items"]:
                heapq.heappush(venues, (item["venue"]["stats"]["checkinsCount"], item["venue"]))
        largest = heapq.nlargest(10, venues)
        for loc in largest:
            self.write("<p>" + loc[1]['name'] + "</p>")
            second_place = loc[1]
				
        venues = []
        self.write("<p> Here are the top restaurants in my area</p>")
        data = client.venues.explore(params={'near' : my_loc, 'section':'food' }) 
        for it in data["groups"]:
            for item in it["items"]:
                heapq.heappush(venues, (item["venue"]["stats"]["checkinsCount"], item["venue"]))
        largest = heapq.nlargest(1, venues)
        for loc in largest:
            self.write("<p>" + loc[1]['name'] + "</p>")
            third_place = loc[1]
            print third_place


        first_stats = {} 
        first_stats['address'] = first_place['location']['address']
        first_stats['phone'] = first_place['contact']['formattedPhone']
        if 'url' in first_place:
            first_stats['website'] = first_place['url'] 
        first_stats['lat'] = first_place['location']['lat']
        first_stats['lng'] = first_place['location']['lng']

        second_stats = {} 
        second_stats['address'] = second_place['location']['address']
        second_stats['phone'] = second_place['contact']['formattedPhone']
        if 'url' in second_place:
            second_stats['website'] = second_place['url'] 
        second_stats['lat'] = second_place['location']['lat']
        second_stats['lng'] = second_place['location']['lng']

        third_stats = {} 
        third_stats['address'] = third_place['location']['address']
        third_stats['phone'] = third_place['contact']['formattedPhone']
        if 'url' in third_place:
            third_stats['website'] = third_place['url'] 
        third_stats['lat'] = third_place['location']['lat']
        third_stats['lng'] = third_place['location']['lng']
				
				
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
        self.render("index.html")
		#self.render("home.html");


class MainHandler(BaseHandler):
    def get(self):
        global own_likes
        global friend_tuples
        global my_loc
        user = fbconsole.get('/me')
	name = user['first_name']
        uid = user['id']
        client = tornado.httpclient.HTTPClient()
        friend_tuples = fbconsole.fql("SELECT name,uid FROM user WHERE uid IN "
                                        "(SELECT uid2 FROM friend WHERE uid1 = me())")
        own_likes = fbconsole.fql("SELECT page_id FROM page_fan WHERE uid = %s" % uid)
        own_locale = fbconsole.fql("SELECT current_location FROM user WHERE uid = %s" % uid)
        my_loc = own_locale[0]['current_location']['name']

        #gather own locale
        city = own_locale[0]['current_location']['city']
        city = city.replace(' ',',')
    #    client = tornado.httpclient.AsyncHTTPClient()
        
   #     client.fetch("http://api.eventful.com/rest/events/search?" + \
   #                 urllib.urlencode({"app_key": "5zPbkgmCjXhLpHT9", "keywords":"movies", "location":city}),
    #                callback=self.on_movie_response)

        self.render("main.html", name = name);

    def on_movie_response(self, response):
        print "caught response"
        global movies
   #     movies = xmltodict.parse(response.body)


def main(port='3000', address='127.0.0.1'):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

