# -*- coding: utf-8 -*-



from pymongo import DESCENDING
from pymongo.objectid import ObjectId

from datetime import datetime
import re
import time
import hashlib
import random
 
from mongoengine import *

from app.people.people_model import People


def now():
    return int(time.mktime(time.gmtime()))

def random_str():
    return hashlib.sha1(str(random.random())).hexdigest()


class OAuthToken(Document):
    EXPIRY_TIME = 3600*24*30
    
    meta = {'collection': 'oauth_token'}
    people_id = ObjectId()
    client_id = StringField(max_length=64, required=True)
    access_token = StringField(max_length=64, required=True)
    refresh_token = StringField(max_length=64)
    scope = StringField(max_length=64)
    expires = IntField(default=0)
    
    def save(self):
        self.access_token       = random_str()
        self.expires            = now() + self.EXPIRY_TIME
        super(OAuthToken, self).save()

    def refresh(self):
        if not self.refresh_token:
            return None # Raise exception?
            
        token = OAuthToken(
            client_id   = self.client_id, 
            people_id     = self.people_id,
            scope       = self.scope,
            refresh_token  = random_str())
        
        token.save()
        self.delete()
        return token
    
    def is_expired(self):
        return self.expires < now()
        
    def serialize(self, requested_scope=None):
        token = dict(
            access_token        = self.access_token,
            expires_in          = self.expires - now(), )
        if (self.scope and not requested_scope) \
            or (requested_scope and self.scope != requested_scope):
            token['scope']      = self.scope
        if self.refresh_token:
            token['refresh_token'] = self.refresh_token
        return token




class OAuthAuthorization(Document):
    EXPIRY_TIME = 3600
    
    meta = {'collection': 'oauth_auth'}
    
    people_id = ObjectId()
    client_id = StringField(max_length=64, required=True)
    redirect_uri = StringField(max_length=512)
    code = StringField(max_length=64)
    expires = IntField(default=0)
    
    
    def save(self):
        self.code       = random_str()
        self.expires    = now() + self.EXPIRY_TIME
        super(OAuthAuthorization, self).save()
    
    @classmethod
    def get_by_code(cls, code):
        return cls.objects(code=code).first()
    
    def is_expired(self):
        return self.expires < now()
        
    def validate_it(self, code, redirect_uri, client_id=None):
        valid = not self.is_expired() \
            and self.code == code \
            and self.redirect_uri == redirect_uri
        if client_id:
            valid &= self.client_id == client_id
        return valid
    
    def serialize(self, state=None):
        authz = {'code': self.code}
        if state:
            authz['state'] = state
        return authz
    
class OAuthClient(Document):
    EXPIRY_TIME = 3600
    
    meta = {'collection': 'oauth_client'}
    
    client_id = StringField(max_length=64)
    client_secret = StringField(max_length=64)
    redirect_uri = StringField(max_length=512)
    
    def save(self):
        self.client_id      = random_str()
        self.client_secret  = random_str()
        super(OAuthClient, self).save()
    
    @classmethod
    def get_by_client_id(cls, client_id):
        return cls.objects(client_id=client_id).first()
    
    @classmethod
    def authenticate(cls, client_id, client_secret):
        client = cls.get_by_client_id(client_id)
        if client and client.client_secret == client_secret:
            return client
        else:
            return None




