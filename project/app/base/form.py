# -*- coding: utf-8 -*-
import re
import urlparse
import formencode
from formencode import htmlfill, validators

class BaseForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    form_errors = {}
    params = {}
    #_xsrf = validators.PlainText(not_empty=True, max=32)
    def __init__(self, handler):
        self._values = {}
        arguments = {}

        request = handler.request
        content_type = request.headers.get("Content-Type", "")

        if request.method == "POST":
            if content_type.startswith("application/x-www-form-urlencoded"):
                arguments = urlparse.parse_qs(request.body, keep_blank_values=1)

        for k, v in arguments.iteritems():
            if len(v) == 1:
                self._values[k] = v[0]
            else:
                self._values[k] = v
        self._handler = handler
        self.result = True

    def validate(self):
        try:
            self.params = self.to_python(self._values)
            self.result = True
            self.validate_after()
        except formencode.Invalid, error:
            self.params = error.value
            self.form_errors = error.error_dict or {}
            self.result = False
        except Exception, e:
            pass

        return self.result

    def add_error(self, attr, msg):
        self.result = False
        self.form_errors[attr] = msg

    def validate_after(self):
        pass


