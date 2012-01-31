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
from cache.files import fetch_cached_board_topic, fetch_cached_board_nodelist
from app.base.form import BaseForm
from app.base.validator import Utf8MaxLength
from app.base.handler import BaseHandler
from app.base.pagination import Pagination
from app.people.people_model import People
from app.board.board_model import BoardTopic,BoardComment,BoardTopicVoter,BoardNode, BoardNodeFollower


PageMaxLimit = 10


class BoardTopicForm(BaseForm):
    topic_content = formencode.All(Utf8MaxLength(300), formencode.validators.String(not_empty=True, min=10, strip=True,  messages={'tooLong':u'最多只能输入 %(max)i 个字', 'empty':u'请输入主题内容', 'tooShort':u'请至少输入%(min)i 个字'}))
    topic_more_content = formencode.All(Utf8MaxLength(3000), formencode.validators.String(strip=True,  messages={'tooLong':u'最多只能输入 %(max)i 个字'}))
    
    #topic_tags = formencode.validators.String(not_empty=False, strip=True, max=200, messages={'tooLong':u'最多只能输入 %(max)i 个字'})
    topic_videos = formencode.validators.URL(strip=True, messages={'noTLD':u'请输入正确的视频地址'})
    #topic_images = formencode.validators.URL(strip=True)
   
    
class BoardCommentForm(BaseForm):
    topic_id = formencode.validators.String(not_empty=True, strip=True)
    topic_url = formencode.validators.String(not_empty=False, strip=True)
    comment_content = formencode.All(Utf8MaxLength(300), formencode.validators.String(strip=True, not_empty=True, min=10,  messages={'tooLong':u'最大只能输入 %(max)i 个字', 'empty':u'请输入评论内容'}))


class BoardTopicHandler(BaseHandler):
    def get(self, topic_id=None, comment_content_error=None, comment_content=''):
        if not topic_id:
            self.about(404)
        
        topic = fetch_cached_board_topic(topic_id)
        if not topic:
            self.about(404)
        node = topic.node
    
        topic_has_voted = False
        people_id = None
        people = None
        page = self.get_argument("page", "1")
        page = string2int(page)
        if page < 1:
            page = 1
    
        if people_id:
            topic_has_voted = topic.has_voted(people_id)
        limit = PageMaxLimit
        offset = (page-1) * PageMaxLimit
        comments = topic.get_comments(limit=limit, offset=offset)
        total_pages = topic.comment_count/limit
        last_page = topic.comment_count  % limit
        if last_page > 0:
            total_pages += 1
     

    
        node_list = fetch_cached_board_nodelist()
        to = timeout(topic.create_time)
        topic_can_edit = False
        if people and to < 600 and topic.is_author(people):
            topic_can_edit = True
        
        pagination = Pagination(page, total_pages)
        self.render("board/topic.html", timeover=timeover,  topic=topic, node=node, node_list=node_list,
                   xsrf_token=self.xsrf_token, pagination=pagination, comment_list=comments, topic_has_voted=topic_has_voted, topic_can_edit=topic_can_edit,
                   comment_content_error=comment_content_error, comment_content=comment_content)



class BoardCommentHandler(BaseHandler):
    def _get_topic(self, topic_id=None, comment_content_error=None, comment_content=''):
        if not topic_id:
            self.about(404)
        
        topic = fetch_cached_board_topic(topic_id)
        if not topic:
            self.about(404)
        node = topic.node
    
        topic_has_voted = False
        people_id = None
        people = None
        page = self.get_argument("page", "1")
        page = string2int(page)
        if page < 1:
            page = 1
    
        if people_id:
            topic_has_voted = topic.has_voted(people_id)
        limit = PageMaxLimit
        offset = (page-1) * PageMaxLimit
        comments = topic.get_comments(limit=limit, offset=offset)
        total_pages = topic.comment_count/limit
        last_page = topic.comment_count  % limit
        if last_page > 0:
            total_pages += 1
     

    
        node_list = fetch_cached_board_nodelist()
        to = timeout(topic.create_time)
        topic_can_edit = False
        if people and to < 600 and topic.is_author(people):
            topic_can_edit = True
        
        pagination = Pagination(page, total_pages)
        self.render("board/topic.html", timeover=timeover,  topic=topic, node=node, node_list=node_list,
                   xsrf_token=self.xsrf_token, pagination=pagination, comment_list=comments, topic_has_voted=topic_has_voted, topic_can_edit=topic_can_edit,
                   comment_content_error=comment_content_error, comment_content=comment_content)

    @authenticated
    def post(self, topic_id=None):
        
        if not topic_id:
            self.about(404)
        
        topic = fetch_cached_board_topic(topic_id)
        if not topic:
            self.about(404)
        node = topic.node
        people = self.current_user
        
        comment_schema = BoardCommentForm(self)
        comment_content = self.get_argument('comment_content', '')
        if comment_schema.validate():
            topic_id = comment_schema.params.get('topic_id')
            topic_url = comment_schema.params.get('topic_url')
            comment_content = comment_schema.params.get('comment_content')
            
            comment = BoardComment()
            comment.content = comment_content
            topic = fetch_cached_board_topic(topic_id)
            comment.topic = topic
            comment.people = people
            
            comment.save()
            topic.add_comment(comment)
            fetch_cached_board_topic(topic.id, reflush=True)
            
            comment_content = ''
            return self.redirect(topic_url)
        else:
            comment_content_error = comment_schema.form_errors.get('comment_content')
            #node_list = fetch_cached_board_nodelist()
            #limit = PageMaxLimit
            #total_pages = topic.comment_count/limit
            #last_page = topic.comment_count  % limit
            #if last_page > 0:
            #    total_pages += 1
            #pagination = Pagination(page, total_pages)
            #page = self.get_argument("page", "1")
            #page = string2int(page)
            #if page < 1:
            #    page = 1
            #offset = (page-1) * PageMaxLimit
            #comments = topic.get_comments(limit=limit, offset=offset)
            #comment_content = comment_schema.params.get('comment_content')
            #return self.render("board/topic.html", timeover=timeover,  topic=topic, node=node, node_list=node_list,
            #       xsrf_token=self.xsrf_token, pagination=pagination, comment_list=comments, topic_has_voted=topic_has_voted, topic_can_edit=topic_can_edit,
            #       comment_content_error=comment_content_error, comment_content=comment_content)

        return self._get_topic(topic_id, comment_content_error=comment_content_error, comment_content=comment_content)



class BoardTopicSubmitHandler(BaseHandler):

    @authenticated
    def get(self, node_name=None):
        if not node_name:
            self.about(404)
        node = BoardNode.get_by_name(node_name)
        if not node:
            self.about(404)
        self.render("board/submit.html", node=node)
    
    @authenticated
    def post(self, node_name=None):
        if not node_name:
            self.about(404)
        node = BoardNode.get_by_name(node_name)
        if not node:
            self.about(404)
            
        people = self.get_current_user()
        schema = BoardTopicForm(self)
        if schema.validate():
            topic_content = schema.params.get("topic_content", None)
            topic_more_content = schema.params.get("topic_more_content", None)
            topic_videos = schema.params.get("topic_videos", None)
            topic_tags = schema.params.get("topic_tags", None)
            
            topic = BoardTopic()
            topic.content = topic_content
            topic.more_content = topic_more_content
            topic.node = node
            topic.people = people #People.objects().first()
            
            if topic_videos:
                topic.videos = [topic_videos]
            topic.save()
            #try:
            #    topic.save()
            #except Exception, e:
            #    raise e
            
            return self.redirect('/board/node/%s' % node_name)
        else:
            
            topic_content = self.get_argument('topic_content', '')
            topic_more_content = self.get_argument('topic_more_content', '')
            
            topic_content_error = schema.form_errors.get('topic_content', '')
            topic_more_content_error = schema.form_errors.get('topic_more_content', '')
            topic_videos_error = schema.form_errors.get('topic_images', '')
            self.render("board/submit.html", node=node,
                        topic_content=topic_content,
                        topic_more_content=topic_more_content,
                        topic_content_error=topic_content_error,
                        topic_more_content_error=topic_more_content_error,
                        topic_videos_error=topic_videos_error)


class BoardIndexHandler(BaseHandler):

    def get(self):
        
        
        page = self.get_argument('page', '1')
        
        page_no = string2int(page, -1)
        if page_no == -1:
            self.about(404)
        if page_no < 1:
            page_no = 1
        offset = (page_no-1) * PageMaxLimit*2
        
        node_list = fetch_cached_board_nodelist()
        topics = BoardTopic.get_last_topics(limit=PageMaxLimit, offset=offset)
        topic_list = []
        for t in topics:
            topic = fetch_cached_board_topic(t.id)
            topic_list.append(topic)
        now = time.time()
        
        self.render("board/index.html", timeover=timeover, topic_list=topic_list, topic_count=len(topic_list), node_list=node_list, now_time=now,
                    page=page_no, offset=offset)
        
    

class BoardNodeHandler(BaseHandler):

    def get(self, node_name=None):
        if not node_name:
            self.about(404)
        
        
        node = BoardNode.get_by_name(node_name)
        if not node:
            self.about(404)
        
        
        page = self.get_argument('page', '1')
        
        page_no = string2int(page, -1)
        if page_no == -1:
            self.about(404)
        if page_no < 1:
            page_no = 1
        offset = (page_no-1) * PageMaxLimit
        
        node_list = fetch_cached_board_nodelist()
        topics = BoardTopic.get_last_node_topics(node, limit=PageMaxLimit, offset=offset)
        topic_list = []
        for t in topics:
            topic = fetch_cached_board_topic(t.id)
            topic_list.append(topic)
        now = time.time()
        total_count = BoardTopic.get_node_topics_count(node)
        total_pages = total_count / PageMaxLimit
        last_page = total_count  % PageMaxLimit
        if last_page > 0:
            total_pages += 1
            
        pagination = Pagination(page_no, total_pages)
        
        self.render("board/node.html", timeover=timeover, topic_list=topic_list, topic_count=len(topic_list), node_list=node_list, node = node, now_time=now,
                    pagination=pagination, offset=offset)
        
    

class BoardTagHandler(BaseHandler):
    def get(self, tag_name=None):
        self.render("home.html")

class BoardTopicVoteHandler(BaseHandler):
    
    def post(self, tag_name=None):
        people = self.current_user
        if self.current_user == None:
            return dict(result='redirect', url='/login')
        
        topic_id = self.get_argument('id', None)
        dir = self.get_argument('dir', None)
    
        topic = fetch_cached_board_topic(topic_id)
    
    
        if topic.people.id != people.id:
            #result = json.dumps(dict(result='error', info='people is the author'))
            return dict(result='error', info='people is the author')
    
        if BoardTopicVoter.has_voted(people.id, topic.id):
            #result = json.dumps(dict(result='error', info='topic has voted'))
            return dict(result='error', info='topic has voted')
        
        try:
            voter = BoardTopicVoter()
            voter.topic_id = topic.id
            voter.member_id = people.id
            voter.save()
            topic.add_voter(voter)
            fetch_cached_news_topic(topic.id, reflush=True)
   
            return dict(result='ok', vote=topic.up_vote+1)
            
        except OperationError, err:
            return dict(result='error', info='not vid')
        
        return dict(result='error', info='unknown error')
            
class BoardCommentListHandler(BaseHandler):
    def get(self):
        tid = self.get_argument('topic_id', None)
        if not tid:
            return self.write('')
        topic = fetch_cached_board_topic(tid)
        page = self.get_argument('page', 0)
        
        limit = PageMaxLimit
        start = string2int(page) * limit
        
        if topic:
            comment_list = topic.get_comments(limit=limit, offset=start)
            return self.render('board/comments.html', topic=topic, comment_list=comment_list, timeover=timeover)
        else:
            return self.write('')

handlers = [
    (r"/", BoardIndexHandler),
    (r"/board", BoardIndexHandler),
    (r"/board/submit/([a-zA-Z0-9\-_]{3,32})", BoardTopicSubmitHandler),
    (r"/board/commentlist", BoardCommentListHandler),
    (r"/board/vote", BoardTopicVoteHandler),
    
    
    (r"/board/tag/(.*)", BoardTagHandler),
    (r"/board/topic/([a-zA-Z0-9]*)", BoardTopicHandler),
    (r"/board/comment/([a-zA-Z0-9]*)", BoardCommentHandler),
    (r"/board/node/([a-zA-Z0-9\-_]{3,32})", BoardNodeHandler),
            ]
