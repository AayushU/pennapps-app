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

#FB
import fbconsole

#Opens a new browser tab instance and authenticates with the facebook API
#It redirects to an url like http://www.facebook.com/connect/login_success.html#access_token=[access_token]&expires_in=0

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/fbauth", FBHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    pass

class FBHandler(BaseHandler):
    def post(self):

        fbconsole.AUTH_SCOPE = ['user_interests', 'user_likes', 'friends_interests', 'friends_likes',
                                'user_location', 'friends_location']
        fbconsole.authenticate()
        self.write('aww yeah')


class HomeHandler(BaseHandler):
    def get(self):
        self.render("home.html");


def main(port='3000', address='127.0.0.1'):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

