

from lib.config import Config
from lib.cache import SimpleCache
import gettext
#from lib.app.geoip import GeoIP

class TranslationMixin(object):
    """Translation mixin class for support i18n by using methods from gettext library."""
    
    def get_lang_by_sid(self, sid):
        """
        Return user language code by sid.
    
        @type  sid: C{str}
        @param sid: The session id.
        @rtype:   C{str}
        @return:  The language code.
        """

        #need method to get lang from session
        if sid == 'zh-CN':
            lang = 'zh_CN'
        elif sid == 'zh-TW':
            lang = 'zh_TW'
        else:
            lang = 'en'
        
        return lang
        
    def get_lang_opts(self):
        """
        Return language options for "gettext.translation" method.
        
        @rtype:   C{dict}
        @return:  The language options - "{'domain':str,'localedir':str,'languages':list}".
        """
        sid = '1234561'
        
        user_lang = self.get_lang_by_sid(sid)
        cfg = self.get_lang_cfg()
        default_lang = cfg['default_lang']
        languages = cfg['languages']
        if not user_lang:
            header = self.getHeader('accept-language')
            if header:
                lst = header.split(',')
                user_lang = []
                if len(lst) > 1:
                    for lang in lst:
                        if not lang[0:2] in user_lang and lang[0:2] in languages:
                            user_lang.append(lang[0:2])
                    if len(user_lang) == 0:
                        user_lang = default_lang
                else:
                    user_lang = None
            if not user_lang:
                ip = self.getClientIP()
                country = None                
                #gip = GeoIP.instance()
                #country = gip.countryCodeByIp(ip)
                if country:
                    conf = Config()
                    if country in conf['app']['country_lang']:
                        user_lang = conf['app']['country_lang'][country]
                    else:
                        user_lang = default_lang
                else:
                    user_lang = default_lang
    
        domain = cfg['domain']
        localedir = cfg['localedir']
        if isinstance(user_lang,list):
            languages = user_lang
        else:
            if user_lang in languages:
                languages = sorted(languages, key=lambda l: l!=user_lang)
            else:
                languages = sorted(languages, key=lambda l: l!=default_lang)
        
        lang_opts = {'domain':domain,'localedir':localedir,'languages':languages}
        
        return lang_opts
        
    def set_user_lang (self, lang):
        #have to write lang to session
        self.user_lang = lang
        
    def _(self, str):
        """
        Return the localized translation of message as a Unicode string, based 
        on the current global domain, language, and locale directory.
        
        @rtype:   C{str}
        @return:  The message as a Unicode string.
        """
        #need get sid from session
        sid = '123456'
        user_lang = self.get_lang_by_sid(sid)
        sc = SimpleCache()
        translation = sc.get('gettext.%s' % user_lang,None)
        
        if not translation:
            lang_opts = self.get_lang_opts()
            translation = gettext.translation(lang_opts['domain'], localedir=lang_opts['localedir'],languages=lang_opts['languages'], codeset='utf-8')
            user_lang = lang_opts['languages'][0]
            sc.set('gettext.%s' % user_lang,translation)
    
        return translation.ugettext(str)
    
    def get_lang_cfg(self):
        """
        Return default application configuration for translation methods.
        
        @rtype:   C{dict}
        @return:  The configuration - "{'domain':str,'default_lang':str,
                'localedir':str,'languages':list}".
        """
        
        cfg = Config()
        
        domain = cfg['app']['domain']
        default_lang = cfg['app']['default_lang']
        localedir = '/'.join([cfg['pathes']['base'],cfg['app']['localedir']])
        languages = cfg['app']['languages']
        
        return {'domain':domain, 'default_lang':default_lang, 'localedir':localedir,'languages':languages}


