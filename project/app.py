#!/usr/bin/env python


import os
import sys

os.environ["PYTHON_EGG_CACHE"] = "/tmp/egg"

import tornado
from tornado import web
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options




try:
    import project
except ImportError:
    print os.path.dirname(__file__)
    sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from lib.utils import parse_config_file



import jinja2 
class Jinja2Environment( jinja2.Environment ): 
    def load( self, template_path ):
        tmpl = self.get_template( template_path ) 
        if tmpl: 
            setattr(tmpl, "generate", tmpl.render) 
        return tmpl
    def reset(self):
        pass
    



class Application(web.Application):
    def __init__(self):
        from project.urls import handlers #, sub_handlers, ui_modules
        template_filepath=os.path.join(os.path.dirname(__file__), options.template_dir)
        jinja2env = Jinja2Environment( loader = jinja2.FileSystemLoader ( template_filepath ), extensions=['jinja2.ext.i18n'] )

        settings = dict(
            debug=options.debug,
            template_path=template_filepath,
            jinja2_env = jinja2env,
            
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=options.xsrf_cookies,
            cookie_secret=options.cookie_secret,
            login_url=options.login_url,
            static_url_prefix=options.static_url_prefix,



            # auth secret
            twitter_consumer_key=options.twitter_consumer_key,
            twitter_consumer_secret=options.twitter_consumer_secret,
            facebook_api_key=options.facebook_api_key,
            facebook_secret=options.facebook_secret,
        )
        
        super(Application, self).__init__(handlers, **settings)



def main():
    reload(sys)
    sys.setdefaultencoding('utf8') 
    parse_config_file("./settings.conf")
    tornado.options.parse_command_line()



    http_server = HTTPServer(Application(), xheaders=True)
    port = options.port
    num_processes = options.num_processes

    if options.debug:
        num_processes = 1
    http_server.bind(int(port))
    http_server.start(int(num_processes))

    IOLoop.instance().start()

if __name__ == "__main__":
    main()
