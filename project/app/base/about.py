# -*- coding: utf-8 -*-

import uuid
import re
import hashlib
from datetime import datetime, timedelta

import tornado.auth
from tornado.web import asynchronous, HTTPError
from tornado.options import options
from tornado import escape

from app.base.handler import BaseHandler

class AboutHandler(BaseHandler):

    def get(self):
        self.render("about.html")



handlers = [
    (r"/about", AboutHandler),
            ]
