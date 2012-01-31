# -*- coding: utf-8 -*-


import uuid
import re
import hashlib
import time
import formencode
from datetime import datetime, timedelta

from markupsafe import escape

import tornado.auth
from tornado.web import asynchronous, HTTPError
from tornado.options import options
from tornado import escape


from lib.utils import string2int, html_escape
from lib.time import timeover, timeout
from lib.decorators import authenticated


from app.base.pagination import Pagination
from app.base.form import BaseForm
from app.base.validator import Utf8MaxLength

from app.base.handler import AdminBaseHandler

from cache.files import fetch_cached_board_topic, fetch_cached_board_nodelist
from app.people.people_model import People
from app.board.board_model import BoardTopic,BoardComment,BoardImage, BoardTopicVoter,BoardNode, BoardNodeFollower

from mongoengine import *

PageMaxLimit=50


class BoardTopicDeleted(Document):
    meta = {'collection': 'board_topic_deleted'}
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

class AdminBoardNodeHandler(AdminBaseHandler):
    def get(self):
        action = self.get_argument('action', None)
        nid = self.get_argument('id', None)
        if nid is not None:
            node = BoardNode.objects.with_id(nid)
            if node is None:
                return self.write("node is NULL")
        if action == 'edit':

            node_help = ''
            for help in node.help:
                node_help = node_help + help + '\n'
            
            self.render("admin/board_node_edit.html", node=node, node_help=node_help)

        elif action == 'count':
            count = BoardTopic.objects(__raw__={'node.$id':node.id}).count()
            return self.write(u'Node "%s" 总共有 %d 条topic!' % (node.name, count))
            
        elif action == 'delete':
            if node:
                count = BoardTopic.objects(__raw__={'node.$id':node.id}).count()
                if count > 0:
                    return self.write(u'Node "%s" 有 %d 条topic, 不能删除!' % (node.name, count))
                node.delete()
                fetch_cached_board_nodelist(reflush=True)
                return self.redirect('/admin/board/node')
        
        nodes = BoardNode.objects().order_by('-update_time')
        return self.render("admin/board_node_list.html", nodes=nodes)
        
    def post(self):
        node_name = self.get_argument('node_name')
        node_desc = self.get_argument('node_desc')
        node_title = self.get_argument('node_title','')
        node_help = self.get_argument('node_help', '')
        
        
        action = self.get_argument('action')
        if action == 'edit':
            nid = self.get_argument('id')
            node = BoardNode.objects.with_id(nid)
            if node is None:
                return about(404)
            node.name = node_name
            node.title = node_title
            node.desc = node_desc
            
            helps = node_help.split('\n')
            help_list = []
            for help in helps:
                help = help.strip()
                if help:
                    help_list.append(help)
            node.help = help_list
            node.save()
            fetch_cached_board_nodelist(reflush=True)
            
            return self.redirect('/admin/board/node')
            
        elif action == 'create':
            node = BoardNode()
            node.name = node_name
            node.desc = node_desc
            node.title = node_title
            helps = node_help.split('\n')
            help_list = []
            for help in helps:
                help = help.strip()
                if help:
                    help_list.append(help)
            node.help = help_list
            fetch_cached_board_nodelist(reflush=True)
            node.save()
            return self.redirect('/admin/board/node')
            

class AdminBoardTopicHandler(AdminBaseHandler):
    def get(self):
        offset = self.get_argument('offset', 0)
        limit = PageMaxLimit
        action = self.get_argument('action', None)
        node_list = fetch_cached_board_nodelist()
        
        if action == 'delete':
            topic_id = self.get_argument('topic_id', None)
            if not topic_id:
                return about(404)
            topic = fetch_cached_board_topic(topic_id)
            deltopic = BoardTopicDeleted()
            
            
            deltopic.id = topic.id
            deltopic.people = topic.people
            deltopic.content = topic.content
            deltopic.more_content = topic.more_content
            deltopic.images = topic.images
            deltopic.video_urls = topic.video_urls
            deltopic.attach_urls = topic.attach_urls
            deltopic.logo = topic.logo
            deltopic.up_vote = topic.up_vote
            deltopic.down_vote = topic.down_vote
            deltopic.comment_count = topic.comment_count
            deltopic.create_time = topic.create_time
            deltopic.update_time = topic.update_time
            deltopic.node = topic.node
            deltopic.tags = topic.tags
            deltopic.save()
            tid = topic.id
            topic.delete()
            fetch_cached_board_topic(tid, reflush=True)
            return self.redirect('/admin/board/topic')
        elif action == 'list':
            
            node_name = self.get_argument('node', None)
            node = BoardNode.get_by_name(node_name)
            if not node:
                return about(404)
            topic_list = BoardTopic.get_last_node_topics(node,limit=limit,offset=offset)
            return self.render("/admin/board_topic_list.html", topic_list=topic_list, node_list=node_list)
        
        
        topic_list = BoardTopic.get_last_topics(limit=limit, offset=offset)
        return self.render("/admin/board_topic_list.html", topic_list=topic_list, node_list=node_list)
        

handlers = [
    (r"/admin/board/node", AdminBoardNodeHandler),
    (r"/admin/board/topic", AdminBoardTopicHandler),
   
            ]
