# -*- coding: utf-8 -*-
#

import uuid
import re
import hashlib
import formencode
import time
import tempfile
from datetime import datetime, timedelta
import Image

import tornado.auth
from tornado.web import asynchronous, HTTPError
from tornado.options import options
from tornado import escape

from lib.decorators import authenticated
from lib.exceptions import Error
from cache.files import fetch_cached_people
from app.base.form import BaseForm
from app.base.validator import Utf8MaxLength,Utf8MinLength
from app.base.handler import BaseHandler
from app.people.people_model import People



_chinese_character_re = re.compile(u"[\u4e00-\u9fa5]")

class LoginForm(BaseForm):
    allow_extra_fields = True
    filter_extra_fields = True
    login_name = formencode.validators.String(not_empty=True, strip=True, messages={"empty":u"请输入您的帐号"})
    login_md5password = formencode.validators.String(not_empty=True, messages={"empty":u"请输入帐号的密码"})
    next = formencode.validators.String(not_empty=False, strip=True)


class SignupForm(BaseForm):
    allow_extra_fields = True
    filter_extra_fields = True
    login_name = formencode.All(Utf8MaxLength(15, messages={"tooLong":u'请输入最多15个字的帐号'}),Utf8MinLength(3, messages={"tooShort":u'请输入至少3个字符的帐号'}),formencode.validators.String(not_empty=True, strip=True, messages={"empty":u"请输入您的帐号"}))
    login_email = formencode.validators.Email(not_empty=True, strip=True, messages={"empty":u"请输入您的邮箱地址"})
    login_password = formencode.validators.String(not_empty=True,strip=True, min=4, messages={"empty":u"请输入帐号的密码", "tooShort":u'请输入至少%(min)i 个字符的密码'})
    login_passwordtwo = formencode.validators.String(not_empty=True,strip=True, min=4, messages={"empty":u"请重复输入帐号的密码", "tooShort":u'请输入至少%(min)i 个字符的密码'})


class LoginHandler(BaseHandler):

    def get(self):
      
        next = self.get_argument("next", options.home_url)
        if next.startswith(options.login_url):
            self.redirect("/login")
            return

        self.render("people/login.html", next=next)
    

    def post(self):
        login_name_error = ''
        login_password_error = ''
        login_name = ''
        login_password = ''
        schema = LoginForm(self)
        next = self.get_argument("next", options.home_url)
        #login_name = self.get_argument('login_name', None)
        #form_result = schema.to_python(dict(self.request.arguments))
        #login_name = form_result.get('login_name')
        #login_password = form_result.get('login_md5password')
        if schema.validate():
            login_name = schema.params['login_name']
            login_password = schema.params['login_md5password']
            next = schema.params['next']
            
            
            people = People.find_by_name(login_name)
            if people: 
                
                if people.validate_password(login_password):
                    self.set_secure_cookie("user", str(people.id), domain=options.cookie_domain)
                    fetch_cached_people(people.id, reflush=True)
                    #session = request.session
                    #session['people_name'] = people.username
                    #session['people_id'] = people.getid()
        
                    #headers = repeople(request, people.username)
                    if login_name == 'admin':
                        url_from = '/admin'
                        
                    #return HTTPFound(location = url_from, headers = headers)
                    return self.redirect(next)
                else:
                    login_password_error = u'输入的密码不正确'
            else:
                login_name_error = login_name #u'用户名不存在'
                login_name = ''
        else:
            
            #errors = error.unpack_errors()
            login_name_error = schema.form_errors.get('login_name')
            login_password_error = schema.form_errors.get('login_password')
        
        self.render("people/login.html",
                    login_name_error = login_name_error,
                    login_password_error = login_password_error,
                    next = next,
                    login_name = login_name,
                    )

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user", domain=options.cookie_domain)
        self.redirect(self.get_argument("next", "/"))
        

class SignupHandler(BaseHandler):
    
    def get(self):
      
        self.render("people/signup.html", url_escape=escape.url_escape)
    
    
    def post(self):
        
        login_name = self.get_argument('login_name', '')
        login_email = self.get_argument('login_email','')
        login_password = self.get_argument('login_password','')
        login_passwordtwo = self.get_argument('login_passwordtwo','')
        login_name_error = None
        login_email_error = None
        login_password_error = None
        login_passwordtwo_error = None
        schema = SignupForm(self)
        try:
            if schema.validate():
                
                people = People()
                lower_name = login_name.lower()
                if people.find_by_name(lower_name):
                   login_name_error = u'用户名已经存在'
                   raise Error()
                
                people.username = login_name
                people.fullname = login_name
                people.set_password(login_password)
                
                people.email = login_email
                
                #people.avatar_url = default_url = '/static/avatar/profile.png'
                
                people.save()
            
                return self.redirect('/signupok?id=%s&name=%s'%(people.id, people.username))
            
            else:
                
                login_name_error = schema.form_errors.get('login_name')
                login_email_error = schema.form_errors.get('login_email')
                login_password_error = schema.form_errors.get('login_password')
                login_passwordtwo_error = schema.form_errors.get('login_passwordtwo')
                if login_password != login_passwordtwo:
                    login_password_error = u'2次输入的密码不一致'
                    
        except Exception,e:
            pass
        
        self.render("people/signup.html",
                        login_name_error = login_name_error,
                        login_email_error = login_email_error,
                        login_password_error = login_password_error,
                        login_passwordtwo_error = login_passwordtwo_error,
                        
                        login_name = login_name,
                        login_email = login_email,
                        )

class SignupOkHandler(BaseHandler):
    
    def get(self):
        self.render("people/signup_ok.html")


class SettingsHandler(BaseHandler):
    
    @authenticated
    def get(self):
        people = self.current_user
        xsrf_token=escape.xhtml_escape(self.xsrf_token)
        self.render("people/settings.html", people=people, token=xsrf_token)

class PeoplePasswordHandler(BaseHandler):
    @authenticated
    def post(self):
        people = self.current_user
        oldpwdmd5 = self.get_argument('oldpwdmd5', '')
        newpwdmd5 = self.get_argument('newpwdmd5', '')
        if not people.validate_password(oldpwdmd5):
            return self.render_json(dict(result='error', info= u'原密码输入有误'))
        
        people.set_password(newpwdmd5, with_md5=True)
        people.save()
        fetch_cached_people(people.id, reflush=True)
        
        return self.render_json(dict(result='ok', info='ok'))

class PeopleEmailHandler(BaseHandler):
    @authenticated
    def post(self):
        people = self.current_user
        email = self.get_argument('email', '')
        
        people.email = email
        people.save()
        fetch_cached_people(people.id, reflush=True)
        
        return self.render_json(dict(result='ok', info='ok'))


class PeopleProfileHandler(BaseHandler):
    @authenticated
    def get(self):
        people = self.current_user
        
        self.render("people/profile.html", people=people)

class PeopleAvatarHandler(BaseHandler):
    @authenticated
    def get(self):
        people = self.current_user
        self.render("people/avatar.html", people=people)
        
    @authenticated
    def post(self):
        if self.request.files:
            
            file = self.request.files['avatar'][0]
            people = self.current_user
            if file:
                rawname = file.get('filename')
                dstname = str(int(time.time()))+'.'+rawname.split('.').pop()
                thbname = "thumb_"+dstname
                # write a file
                # src = "./static/upload/src/"+dstname
                # file(src,'w+').write(f['body'])
                tf = tempfile.NamedTemporaryFile()
                tf.write(file['body'])
                tf.seek(0)
                 
                # create normal file
                # img = Image.open(src)
                img = Image.open(tf.name)
                img.thumbnail((60,60),resample=1)
                img.save("./static/avatar/"+dstname)
                tf.close()
                people.avatar_url = "/static/avatar/"+dstname
                people.save()
                fetch_cached_people(people.id, reflush=True)
                
                return self.redirect('/settings/avatar')






#
#
#class OpenidLoginHandler(BaseHandler):
#    _error_message = "OpenID auth failed!"
#
#    def _cache_next(self):
#        now = datetime.now()
#        key = self._next_key_gen()
#        val = self.get_argument("next", "/")
#
#        c = Cache()
#        c.key = key
#        c.value = val
#        c.expire = now + timedelta(seconds=600)
#
#        value = c.findby_key(key)
#        if value:
#            c.save(value["_id"])
#        else:
#            c.insert()
#
#    def _next_key_gen(self):
#        code = hashlib.md5()
#
#        # make a unique id for a un-logined user
#        # it may be duplicated for different users
#        code.update("user/next")
#        code.update(self.request.remote_ip)
#        code.update(self.request.headers.get("User-Agent", "Unknown-Agent"))
#        code.update(self.request.headers.get("Accept-Language", "en-us,en;q=0.5"))
#
#        return code.hexdigest()
#
#    @asynchronous
#    def get(self):
#        if self.get_argument("openid.mode", None):
#            self.get_authenticated_user(self.async_callback(self._on_auth))
#            return
#        self._cache_next()
#        self.authenticate_redirect()
#
#    def _login(self, user):
#        self.db.execute(
#                "UPDATE user SET login_ip = %s, login_date = UTC_TIMESTAMP(), login_c = %s "
#                "WHERE id = %s", self.request.remote_ip, user.login_c + 1, user.id)
#
#        self.set_secure_cookie("user", user.username, domain=options.cookie_domain)
#
#    def _create_user(self, openid_api, openid_id, openid_name, email, username):
#        self.db.execute("INSERT INTO user (openid_api,openid_id,openid_name,email,username,"
#                    "signup_ip,login_ip,signup_date,login_date,uuid_) "
#                    "VALUES (%s,%s,%s,%s,%s,"
#                    "%s,%s,UTC_TIMESTAMP(),UTC_TIMESTAMP(),%s)",
#                    openid_api, openid_id, openid_name, email, username,
#                    self.request.remote_ip, self.request.remote_ip, uuid.uuid4().hex
#                    )
#
#        self.set_secure_cookie("user", username, domain=options.cookie_domain)
#
#    def _login_redirect(self, status_):
#        key = self._next_key_gen()
#
#        c = Cache()
#        value = c.findby_key(key)
#        if value:
#            next = escape.utf8(value["value"])
#            c.remove(value["_id"])
#        else:
#            next = "/"
#
#        #next = self.get_argument("next", "/")
#        if status_ == const.Status.INIT:
#            self.redirect("/user/profile?next=%s" % next)
#        else:
#            self.redirect(next)
#
#
#class FacebookLoginHandler(OpenidLoginHandler, tornado.auth.FacebookMixin):
#    _error_message = "Facebook auth failed!"
#
#    @asynchronous
#    def get(self):
#        if self.get_argument("session", None):
#            self.get_authenticated_user(self.async_callback(self._on_auth))
#            return
#        self._cache_next()
#        self.authenticate_redirect()
#
#    def _on_auth(self, openid):
#        if not openid:
#            raise HTTPError(500, self._error_message)
#
#        user = self.db.get("select * from user where openid_api = %s and openid_id = %s",
#                           const.OpenID.FACEBOOK, openid["uid"])
#
#        if user:
#            status_ = user.status_
#            user.openid_name = openid["name"]
#
#            self._login(user)
#        else:
#            status_ = const.Status.INIT
#            try:
#                # try to use default account name as username (fb username -> username)
#                username = openid["username"].replace(".", "_").lower()
#                self._create_user(const.OpenID.FACEBOOK, openid["uid"], openid["name"], None, username)
#            except Exception:
#                username = uuid.uuid4().hex # Generate one randomly
#                self._create_user(const.OpenID.FACEBOOK, openid["uid"], openid["name"], None, username)
#
#        self._login_redirect(status_)
#
#
#class FriendfeedLoginHandler(OpenidLoginHandler, tornado.auth.FriendFeedMixin):
#    _error_message = "Friendfeed auth failed!"
#
#    @asynchronous
#    def get(self):
#        if self.get_argument("oauth_token", None):
#            self.get_authenticated_user(self.async_callback(self._on_auth))
#            return
#        self._cache_next()
#        self.authorize_redirect()
#
#    def _on_auth(self, openid):
#        if not openid:
#            raise HTTPError(500, self._error_message)
#
#        user = self.db.get("select * from user where openid_api = %s and openid_id = %s",
#                           const.OpenID.FRIENDFEED, openid["username"])
#
#        if user:
#            status_ = user.status_
#            user.openid_name = openid["name"]
#
#            self._login(user)
#        else:
#            status_ = const.Status.INIT
#            try:
#                # try to use default account name as username (ff id -> username)
#                username = openid["username"].lower()
#                self._create_user(const.OpenID.FRIENDFEED, openid["username"], openid["name"], None, username)
#            except Exception:
#                username = uuid.uuid4().hex # Generate one randomly
#                self._create_user(const.OpenID.FRIENDFEED, openid["username"], openid["name"], None, username)
#
#        self._login_redirect(status_)
#
#
#class GoogleLoginHandler(OpenidLoginHandler, tornado.auth.GoogleMixin):
#    _error_message = "Google auth failed!"
#
#    def _on_auth(self, openid):
#        if not openid:
#            raise HTTPError(500, self._error_message)
#
#        # update openid information
#        if _chinese_character_re.match(openid["name"]):
#            openid["name"] = openid["last_name"] + openid["first_name"]
#
#        user = self.db.get("select * from user where email = %s", openid["email"])
#
#        if user:
#            status_ = user.status_
#            user.openid_id = openid["name"]
#            user.openid_name = openid["name"]
#
#            self._login(user)
#        else:
#            status_ = const.Status.INIT
#            try:
#                # try to use default account name as username
#                username = openid["email"].split("@")[0].replace(".", "_").lower()
#                self._create_user(const.OpenID.GOOGLE, openid["name"], openid["name"], openid["email"], username)
#            except Exception:
#                username = uuid.uuid4().hex # Generate one randomly
#                self._create_user(const.OpenID.GOOGLE, openid["name"], openid["name"], openid["email"], username)
#
#        self._login_redirect(status_)
#
#
#class TwitterLoginHandler(OpenidLoginHandler, tornado.auth.TwitterMixin):
#    _error_message = "Twitter auth failed!"
#
#    @asynchronous
#    def get(self):
#        if self.get_argument("oauth_token", None):
#            self.get_authenticated_user(self.async_callback(self._on_auth))
#            return
#        self._cache_next()
#        self.authorize_redirect()
#
#    def _on_auth(self, openid):
#        if not openid:
#            raise HTTPError(500, self._error_message)
#
#        user = self.db.get("select * from user where openid_api = %s and openid_id = %s",
#                           const.OpenID.TWITTER, openid["username"])
#
#        if user:
#            status_ = user.status_
#            user.openid_name = openid["name"]
#
#            self._login(user)
#        else:
#            status_ = const.Status.INIT
#            try:
#                # try to use default account name as username (twitter screen_name -> username)
#                username = openid["username"].lower()
#                self._create_user(const.OpenID.TWITTER, openid["username"], openid["name"], None, username)
#            except Exception:
#                username = uuid.uuid4().hex # Generate one randomly
#                self._create_user(const.OpenID.TWITTER, openid["username"], openid["name"], None, username)
#
#        self._login_redirect(status_)
#
#
#class ProfileHandler(BaseHandler):
#    @authenticated
#    def get(self):
#        self._context.js.append("user.js")
#        self._context.next = self.get_argument("next", "/")
#        self._context.title = "Edit profile"
#        self._context.openid_name = const.OpenID.NAME[self.current_user.openid_api]
#
#        if self.current_user.email is None:
#            self.current_user.email = ""
#
#        if self.current_user.blog_name is None:
#            self.current_user.blog_name = ""
#
#        if self.current_user.blog_url is None:
#            self.current_user.blog_url = ""
#
#        self.render("user/profile.html", const=const)
#
#    @authenticated
#    def post(self):
#        fm = ProfileForm(self)
#        self._context.openid_name = const.OpenID.NAME[self.current_user.openid_api]
#        next = escape.url_unescape(fm._parmas.get("next", ""))
#        if not next:
#            next = "/"
#        self._context.next = next
#
#        if fm.validate():
#            self.redirect(self._context.next)
#        else:
#            fm.render("user/profile.html", const=const)
#
#
#class UserCheckHandler(BaseHandler):
#    @authenticated
#    def post(self):
#        email = self.request.arguments.get("email", False)
#        username = self.request.arguments.get("username", False)
#        r = {"r" : 1}
#
#        if email:
#            user = self.db.get("select id from user where email = %s", email[0])
#            if user and user.id != self.current_user.id:
#                r["r"] = 0
#            else:
#                r["r"] = 1
#        elif username:
#            user = self.db.get("select id from user where username = %s", username[0])
#            if user and user.id != self.current_user.id:
#                r["r"] = 0
#            else:
#                r["r"] = 1
#
#        self.write(r)
#
#
#class UserHandler(BaseHandler):
#    @cache.page(anonymous=True)
#    def get(self, username):
#        user = self.db.get("select * from user where username = %s" , username)
#        if not user:
#            raise HTTPError(404)
#
#        sites = self.db.query("select * from site where user_id = %s order by id DESC", user.id)
#        self._context.title = user.openid_name + " submitted sites"
#        self._context.keywords = ",".join((user.openid_name, user.username, self._context.keywords))
#        self._context.description = ",".join((self._context.title, self._context.options.domain))
#        self.render("user/user.html", sites=sites, user=user)

from tornado.web import RequestHandler, HTTPError
class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html", url_escape=escape.url_escape)


handlers = [
           
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/signup", SignupHandler),
            (r"/signupok", SignupOkHandler),
            (r"/settings", SettingsHandler),
            (r"/settings/profile", PeopleProfileHandler),
            (r"/settings/avatar", PeopleAvatarHandler),
            (r"/settings/password", PeoplePasswordHandler),
            (r"/settings/email", PeopleEmailHandler),
            #(r"/login/google", GoogleLoginHandler),
            #(r"/login/facebook", FacebookLoginHandler),
            #(r"/login/twitter", TwitterLoginHandler),
            #(r"/login/friendfeed", FriendfeedLoginHandler),
            #(r"/user/profile", ProfileHandler),
            #(r"/user/check", UserCheckHandler),
            #(r"/user/([a-z0-9\-_]{3,32})", UserHandler),
            ]
