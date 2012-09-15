    # Python
import os
import json
import random

# Tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web

# Mongo
import pymongo
from bson import json_util

#Foursquare
import foursquare

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/main", MainHandler),
            (r"/FoursquareHandler", FoursquareHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    pass

class FoursquareHandler(BaseHandler):
    def post(self):
        client = foursquare.Foursquare(client_id='QYEIVBMULP11CPVHP4MSHXDB2VIZ12LDDUTMMJL2YSP2IJJA', 
                               client_secret='L04TIELKXWIHKVXWI1PRENGM1YFSPHHX0PEUZQSUIMDVHDDU', 
                               redirect_uri='http://localhost:3000/main')

        # Build the authorization url for your app
        auth_uri = client.oauth.auth_url()        
        self.write('Hello World, redirecting to %s' % auth_uri)
        self.redirect(auth_uri)

class MainHandler(BaseHandler):
    def get(self):

        client = foursquare.Foursquare(client_id='QYEIVBMULP11CPVHP4MSHXDB2VIZ12LDDUTMMJL2YSP2IJJA', 
                               client_secret='L04TIELKXWIHKVXWI1PRENGM1YFSPHHX0PEUZQSUIMDVHDDU', 
                               redirect_uri='http://localhost:3000/main')
        # Interrogate foursquare's servers to get the user's access_token
        access_token = client.oauth.get_token(self.get_argument("code"))

        # Apply the returned access token to the client
        client.set_access_token(access_token)

        # Get the user's data
        user = client.users()
        self.write("Authenticated alright!")
        self.write(user)


class HomeHandler(BaseHandler):
    def get(self):
        self.render("home.html");


def main(port='3000', address='127.0.0.1'):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

