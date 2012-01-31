import os
from hashlib import md5
from datetime import datetime
 
from mongoengine import *


class People(Document):
    meta = {'collection': 'people'}
    
    username = StringField(max_length=32, required=True)
    fullname = StringField(max_length=64, required=True)
    password = StringField(max_length=64, required=True)
    email = StringField(max_length=255, required=True)
    avatar_url =  StringField(max_length=200, required=True, default='/static/image/profile.png')
    create_time = DateTimeField(default=datetime.now)
    role = IntField(default=0)
    #username = StringField(max_length=32, required=True)
    #fullname = StringField(max_length=64, )
    #password = StringField(max_length=64, )
    #email = StringField(max_length=255, )
    #avatar_url =  StringField(max_length=200,  default='/static/image/profile.png')
    #create_time = DateTimeField(default=datetime.now)


    @classmethod
    def find_by_id(self, id):
        try:
            return People.objects.with_id(to_objectid(id))
        except Exception, err:
            return None
    
    # md5(password+"kongdai")
    def set_password(self, password):
        pwd = password
        self.password = md5(pwd).hexdigest()
    
    def validate_password(self, password_md5):
        return self.password == password_md5 #md5(password).hexdigest()
    
    def validate_oldpassword(self, password_nomd5):
        pwd = password_nomd5
        password_md5 = md5(pwd).hexdigest()
        return self.password == password_md5 #md5(password).hexdigest()
    
    @classmethod
    def find_by_name(self, username):
        return People.objects(username=username).first()   
    
    
    def get_role(self):
        return Role.objects(people=self).first()
    
#class Role(Document):
#    meta = {'collection': 'people_role'}
#    
#    name = StringField(max_length=32, required=True)
#    permission = StringField(max_length=64, required=True)  #master, admin, user
#    people = ReferenceField(People)
#    create_time = DateTimeField(default=datetime.now)



    