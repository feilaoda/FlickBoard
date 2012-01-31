# -*- coding: utf-8 -*-

import re
import httplib
import urllib
import traceback

from tornado.web import RequestHandler, HTTPError
from tornado.options import options
from tornado import template, ioloop, escape
from tornado.escape import json_encode

from lib import mail
from lib.exceptions import TemplateContextError
from app.base import const
from cache.files import fetch_cached_people

from mongoengine import connection

class BaseHandler(RequestHandler):
    _first_running = True
    db = None
    nosql = None

    def __init__(self, application, request, **kwargs):
        if BaseHandler._first_running:
            self._after_prefork()
            BaseHandler._first_running = False
        
        self.jinja2_env = application.settings.get("jinja2_env")
        
        super(BaseHandler, self).__init__(application, request, **kwargs)
    def _after_prefork(self):
        
        connection.connect(options.mongodb['database'])

    
        # logging access routine
        #ioloop.PeriodicCallback(logging_access_job, int(options.access_log["interval"]) * 1000).start()

    def get_current_user(self):
        people_id = self.get_secure_cookie("user")

        if not people_id:
            return None

        return fetch_cached_people(people_id)

    #def get_user_locale(self):
    #    return self.session['locale']

    #def get_browser_locale(self):
    #    return self.session['locale']

    def prepare(self):
        self._prepare_settings()
        self._remove_slash()
        
    def about(self, status_code, message=None):
        raise HTTPError(status_code)
                

    def render_json(self, json):
        self.set_header("Content-Type", "application/json")
        json_string = json_encode(json)
        return self.write(json_string)
    
    def render_string(self, template_name, **kwargs):
        assert "settings" not in kwargs, "settings is a reserved word for \
                template settings"
        kwargs['settings'] = self.project_settings
        
        
        if self.jinja2_env: 
            if self.application.settings.get("debug") or not getattr(RequestHandler, "_templates", None): 
                RequestHandler._templates = {} 
            template_path = self.application.settings.get("template_path") 
            if template_path not in RequestHandler._templates: 
                RequestHandler._templates[template_path] = self.jinja2_env

        return super(BaseHandler, self).render_string(template_name, **kwargs)

    def flush(self, include_footers=False):
        """Flushes the current output buffer to the network."""
        if self.application._wsgi:
            raise Exception("WSGI applications do not support flush()")

        chunk = "".join(self._write_buffer)
        # keep write buffer for cache
        # self._write_buffer = []
        if not self._headers_written:
            self._headers_written = True
            for transform in self._transforms:
                self._headers, chunk = transform.transform_first_chunk(
                    self._headers, chunk, include_footers)
            headers = self._generate_headers()
        else:
            for transform in self._transforms:
                chunk = transform.transform_chunk(chunk, include_footers)
            headers = ""

        # Ignore the chunk and only write the headers for HEAD requests
        if self.request.method == "HEAD":
            if headers: self.request.write(headers)
            return

        if headers or chunk:
            self.request.write(headers + chunk)

    def get_error_html(self, status_code, **kwargs):
        """Override to implement custom error pages.

        It will send email notification to admins if debug is off when internal 
        server error happening.
        
        """
        code = status_code
        message = httplib.responses[status_code]

        try:
            # add stack trace information
            exception = 'e ' #"%s\n\n%s" % (kwargs["exception"], traceback.format_exc())

            if options.debug:
                template = "error/%s_debug.html" % code
            else:
                template = "error/%s.html" % code

                ## comment send email for ec2 smtp limit
                if code == 500:
                    fr = options.email_from
                    to = options.admins

                    subject = "[%s]Internal Server Error" % options.sitename
                    body = self.render_string("500_email.html",
                                          code=code,
                                          message=message,
                                          exception=exception)

                    mail.send_email(fr, to, subject, body)
            
            return self.render_string(template,
                                      code=code,
                                      message=message,
                                      exception=exception)
        except Exception:
            return self.write('error')
            #return super(BaseHandler, self).get_error_html(status_code, **kwargs)

    @property
    def is_admin(self):
        return self.current_user.role >= const.Role.ADMIN if self.current_user else False

    @property
    def editor(self):
        return self.current_user.role >= const.Role.EDITOR if self.current_user else False

    def _prepare_settings(self):
        self.project_settings = ProjectSettings()
        self.project_settings.css = ['base.css', ]
        self.project_settings.js = ['base.js', ]
        self.project_settings.keywords = options.keywords
        self.project_settings.description = options.description
        self.project_settings.sitename = options.sitename
        self.project_settings.sub_sitename = options.sub_sitename
        self.project_settings.sitetitle = options.sitetitle
        self.project_settings.sitetitle_suffix = options.sitetitle_suffix
        self.project_settings.description = options.description
        self.project_settings.cache_enabled = options.cache_enabled
        self.project_settings.options = options

    def _remove_slash(self):
        if self.request.method == "GET":
            if _remove_slash_re.match(self.request.path):
                # remove trail slash in path
                uri = self.request.path.rstrip("/")
                if self.request.query:
                    uri += "?" + self.request.query

                self.redirect(uri)

    def _request_summary(self):
        #if options.access_log["on"] and self.request.method == "GET":
        #    Access().logging_access(self)

        return super(BaseHandler, self)._request_summary()


class AdminBaseHandler(BaseHandler):
    """Administrator base handler.
    
    It's a shortcut of decorators.admin for every method(get, post, head etc),
    so we need not write decorators.admin everywhere.
    
    """
    def prepare(self):
        if not self.current_user:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
                self.redirect(url)
                return
            raise HTTPError(403)
        elif not self.is_admin:
            if self.request.method == "GET":
                self.redirect(options.home_url)
                return
            raise HTTPError(403)
        else:
            pass

        super(AdminBaseHandler, self).prepare()


class StaffBaseHandler(BaseHandler):
    """Administrator base handler.
    
    It's a shortcut of decorators.staff.
        
    """
    def prepare(self):
        if not self.current_user:
            if self.request.method == "GET":
                url = self.get_login_url()
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.full_url()))
                self.redirect(url)
                return
            raise HTTPError(403)
        elif not self.is_staff:
            if self.request.method == "GET":
                self.redirect(options.home_url)
                return
            raise HTTPError(403)
        else:
            pass

        super(StaffBaseHandler, self).prepare()


class ErrorHandler(BaseHandler):
    """Default 404: Not Found handler."""
    def prepare(self):
        super(ErrorHandler, self).prepare()
        raise HTTPError(404)


class ProjectSettings(dict):
    """Template context container.
    
    A container which will return empty string silently if the key is not exist
    rather than raise AttributeError when get a item's value.
    
    It will raise TemplateContextError if debug is True and the key 
    does not exist.   
    
    The context item also can be accessed through get attribute. 
    
    """
    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        return str(self)

    def __iter__(self):
        return iter(self.items())

    def __getattr__(self, key):
        if key in self:
            return self[key]
        elif options.debug:
            raise TemplateContextError("'%s' does not exist in context" % key)
        else:
            return ""

    def __hasattr__(self, key):
        if key in self:
            return True
        else:
            return False


_remove_slash_re = re.compile(".+/$")
