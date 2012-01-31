# -*- coding: utf-8 -*-



from pymongo import DESCENDING
from datetime import datetime
import re

from mongoengine import *

from app.people.people_model import People


class BoardNode(Document):
    meta = {'collection': 'board_node'}
    name = StringField(max_length=32, required=True)
    desc = StringField(max_length=32, required=True)
    help = ListField(StringField(max_length=128))
    vote_type = IntField(default=0)  #0: none  #1: up only   #2: up and down
    anonymous = IntField(default=0) #0: No  1:Yes 匿名发表
    
    
    
    def init(self):
        self.name = None
        self.desc = None
        
    @classmethod
    def get_top_nodes(self):
        return BoardNode.objects()
    
    @classmethod
    def get_by_name(self, node_name):
        return BoardNode.objects(__raw__={'name':node_name}).first()

    #TODO
    def has_followed(self, people):
        pass
    

class BoardImage(EmbeddedDocument):
    small_url = URLField()
    url = URLField()
    text = StringField(max_length=512)



    
class BoardTopic(Document):
    meta = {'collection': 'board_topic',
            'index':['update_time', 'node']
            }
    people = ReferenceField(People, required=True)
    content = StringField(max_length=1024, required=True)
    more_content = StringField(max_length=10000)
    images = ListField(EmbeddedDocumentField(BoardImage))
    video_urls = ListField(URLField())
    attach_urls = ListField(URLField())
    
    logo = URLField()
    up_vote = IntField(min_value=0, default=1)
    down_vote = IntField(min_value=0, default=0)
    comment_count = IntField(min_value=0, default=0)
    create_time = DateTimeField(default=datetime.now)
    update_time = DateTimeField(default=datetime.now)
    node = ReferenceField(BoardNode, required=True)
    tags = ListField(StringField(max_length=32))
    
    
    
    html_content = None
    extra_content = None
    
    @classmethod
    def get_last_topics(self, limit=10, offset=0):
        rs = BoardTopic.objects().limit(limit).skip(offset).order_by('-update_time')
        return rs
    
    @classmethod
    def get_hot_topics(self, limit=10, offset=0):
        rs = BoardTopic.objects().limit(limit).skip(offset).order_by('-score')
        return rs
    
    def get_comments(self, limit=10, offset=0):
        comments = BoardComment.objects(__raw__={'topic.$id':self.id}).skip(offset).limit(limit)
        return comments
    
    @classmethod
    def get_last_node_topics(self, node, limit=10, offset=0):
        rs = BoardTopic.objects(__raw__={'node.$id' : node.id}).skip(offset).limit(limit).order_by('-update_time')
        return rs
    
    @classmethod
    def get_node_topics_count(self, node):
        count = BoardTopic.objects(__raw__={'node.$id' : node.id}).count()
        return count
    
    @classmethod
    def get_hot_node_topics(self, node, limit=10, offset=0):
        rs = BoardTopic.objects(__raw__={'node.$id' : node.id}).skip(offset).limit(limit).order_by('-score')
        return rs
    
    def is_author(self, people):
        if people is None:
            return False
        return people.id == self.people.id;
    
    def has_voted(self, people):
        if people.id == self.people.id:
            return True;
        return  BoardTopicVoter.has_voted(people=people)
    
    #TODO
    def has_followed(self, people):
        pass
    
    def add_comment(self, comment=None):
        if comment:
            now = datetime.now()    
            BoardTopic.objects(id=self.id).update_one(inc__comment_count=1,set__update_time=now)
            #fetch_cached_topic(self.id, reflush=True)
           
    def add_voter(self, voter=None):
        if voter:
            if voter.dir == 1:
                #score = hot_score(self.up_vote+1, self.create_time)
                #BoardTopic.objects(id=self.id).update_one(inc__up_vote=1, set__score=score)
                BoardTopic.objects(id=self.id).update_one(inc__up_vote=1)
            elif voter.dir == -1:
                BoardTopic.objects(id=self.id).update_one(inc__down_vote=1)
            
    
class BoardComment(Document):
    meta = {
            'collection': 'board_comment',
            'ordering': ['-create_time']
            }
    
    people = ReferenceField(People, required=True)
    content = StringField(max_length=1024, required=True)
    topic = ReferenceField('BoardTopic')
    parent_id = ObjectIdField()
    
    up_vote = IntField(min_value=0, default=0)
    down_vote = IntField(min_value=0, default=0)
    create_time = DateTimeField(default=datetime.now)
    
class BoardTopicVoter(Document):
    meta = {'collection': 'board_topic_voter'}
    people_id = ObjectIdField()
    topic_id = ObjectIdField()
    dir = IntField(default=1)#0:none   #1:up  #-1:down
    create_time = DateTimeField(default=datetime.now)

    @classmethod
    def has_voted(self, people_id, topic_id):
        try:
            voted_count = BoardTopicVoter.objects(__raw__ = {'people_id':people_id, 'topic_id': topic_id}).count()
            if voted_count > 0:
                return True
            else:
                return False
        except Exception, err:
            return False


class BoardTopicFollower(Document):
    meta = {
            'collection': 'board_topic_follower',
            'ordering': ['-create_time']
            }
    
    topic = ReferenceField(BoardTopic)
    people = ReferenceField(People)
    node = ReferenceField(BoardNode)
    
    create_time = DateTimeField(default=datetime.now)
    
    @classmethod
    def get_follower_node_topics(self, people, node):
        return BoardTopicFollower.objects(people=people, node=node)
    
    @classmethod
    def get_follower_topics(self, people):
        return BoardTopicFollower.objects(people=people)
    
    @classmethod
    def add_follower_topics(self, topic, people):
        follower = BoardTopicFollower(topic=topic, people=people, node=topic.node)
        follower.save()
        #return BoardTopicFollower.objects(id=self.id).update_one(push__nodes=self)


class BoardNodeFollower(Document):
    meta = {
            'collection': 'board_node_follower',
            'ordering': ['-create_time']
            }
    
    people = ReferenceField(People)
    nodes = ListField(ReferenceField(BoardNode))
    create_time = DateTimeField(default=datetime.now)
    
    @classmethod
    def get_follower_nodes(self, people):
        return BoardFollower.objects(people=people)
    
    @classmethod
    def add_follower(self, people):
        follower = BoardNodeFollower(people=people)
        follower.save()
        #return BoardFollower.objects(id=self.id).update_one(push__nodes=self)
        
    
        




