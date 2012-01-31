
from markupsafe import escape
import re

from pymongo.objectid import ObjectId
from pymongo.errors import InvalidId


from app.people.people_model import People
from app.board.board_model import BoardTopic, BoardNode

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

from lib.filter import none2string,mentions,video, urlink
from lib.utils import html_escape, br_escape


cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': '/tmp/caches/data',
    'cache.lock_dir': '/tmp/caches/lock',
    'cache.regions': 'short_term, long_term',
    #'cache.short_term.type': 'ext:memcached',
    #'cache.short_term.url': '127.0.0.1.11211',
    'cache.short_term.type': 'file',
    'cache.short_term.expire': '1200',
    'cache.long_term.type': 'file',
    'cache.long_term.expire': '3600',
}


cache = CacheManager(**parse_cache_config_options(cache_opts))




@cache.region('short_term', 'cached_people')
def get_cached_people(people_id):
    try:
        people = People.objects.with_id(people_id)
        return people
    except InvalidId, error:
        pass
    
    return None




def fetch_cached_people(people_id, reflush=False):
    if reflush:
        cache.region_invalidate(get_cached_people, None, 'cached_people', people_id)

    return get_cached_people(people_id)


@cache.region('long_term', 'cached_board_topic')
def get_cached_board_topic(topic_id):
    try:
        
        topic = BoardTopic.objects.with_id(topic_id)
        if topic is None:
            return None
        
        if topic.content:
            topic.html_content = urlink(escape(topic.content))  #urlink((mentions(youku(escape(topic.content)) ) ) , trim_url_limit=30)
        else:
            topic.html_content = ''

        return topic
    except Exception, error:
        return None
    
    return None



def fetch_cached_board_topic(topic_id, reflush=False):
    if reflush:
        cache.region_invalidate(get_cached_board_topic, None, 'cached_board_topic', topic_id)

    return get_cached_board_topic(topic_id)


@cache.region('long_term', 'cached_board_topic_morecontent')
def get_cached_board_topic_morecontent(topic_id):
    try:
        topic = fetch_cached_board_topic(topic_id)
        if topic is None:
            return None
        html_more_content = ''
        if topic.more_content:
            html_more_content = br_escape(urlink(escape(topic.more_content)))  #urlink((mentions(youku(escape(topic.content)) ) ) , trim_url_limit=30)
        extra_content = ''
        if topic.video_urls:
            
            video_html = '<p></p>'
            for url in topic.video_urls:
                video_html += video(url)
            extra_content = video_html
        return html_more_content + extra_content
    except Exception, error:
        return None
    
    return None
def fetch_cached_board_topic_morecontent(topic_id, reflush=False):
    if reflush:
        cache.region_invalidate(get_cached_board_topic, None, 'cached_board_topic_morecontent', topic_id)

    return get_cached_board_topic_morecontent(topic_id)

    
@cache.region('long_term', 'cached_board_nodelist')
def get_cached_board_nodelist(cache='board_nodelist'):
    try:
        nodelist = BoardNode.get_top_nodes()
        return list(nodelist)
    except InvalidId, error:
        pass
    
    return None

def fetch_cached_board_nodelist(reflush=False):
    if reflush:
        cache.region_invalidate(get_cached_board_nodelist, None, 'cached_board_nodelist', 'board_nodelist')

    return get_cached_board_nodelist('board_nodelist')



