# -*- coding: utf-8 -*-


from app.base.handler import ErrorHandler
from tornado.web import StaticFileHandler

handlers = []
sub_handlers = []


import os
from tornado.options import options

from app.people import people_handler
from app.board import board_handler 
from app.admin import admin_handler
from app.base import about



static_file_dir = os.path.join(os.path.dirname(__file__), options.static_dir)
static_handler = [
            (r"/static/(.*)", StaticFileHandler, {"path": static_file_dir}),
            ]

handlers.extend(static_handler)
handlers.extend(admin_handler.handlers)
handlers.extend(people_handler.handlers)
handlers.extend(board_handler.handlers)
handlers.extend(about.handlers)


