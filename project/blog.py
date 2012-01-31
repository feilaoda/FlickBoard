import unittest

from mongoengine import *
from mongoengine.connection import _get_db
from mongoengine.tests import query_counter
from datetime import datetime

from project.app.people.people_model import People

class BoardTopic(Document):
    meta = {'collection': 'board_topic',
            'index':['update_time', 'node']
            }
    people = ReferenceField(People)
    content = StringField(max_length=4096, required=True)
    #images = ListField(EmbeddedDocumentField(BoardImage))
    video_urls = ListField(URLField())
    attach_urls = ListField(URLField())
    
    logo = URLField()
    up_vote = IntField(min_value=0, default=1)
    down_vote = IntField(min_value=0, default=0)
    comment_count = IntField(min_value=0, default=0)
    create_time = DateTimeField(default=datetime.now)
    update_time = DateTimeField(default=datetime.now)
    #node = ReferenceField(BoardNode)
    tags = ListField(StringField(max_length=32))
    
    html_content = None
    extra_content = None
