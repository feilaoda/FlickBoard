
from projects.base.handler import BaseHandler


class I18NHandler(BaseHandler):

    def initialize(self, request, response):
        webapp2.RequestHandler.initialize(self, request, response)
        self.request.COOKIES = Cookies(self)
        self.request.META = os.environ
        self.reset_language()

    def reset_language(self):

        # Decide the language from Cookies/Headers
        language = translation.get_language_from_request(self.request)
        translation.activate(language)
        self.request.LANGUAGE_CODE = translation.get_language()

        # Set headers in response
        self.response.headers['Content-Language'] = str(translation.get_language())