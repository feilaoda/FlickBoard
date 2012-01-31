# -*- coding: utf-8 -*-


from datetime import datetime
import urllib2
import re
import urllib, hashlib
import string
from itertools import imap



def none2string(value):
    if value is None:
        return ''
    return value


def video(value):
    if value is None:
        return None
    videos = re.findall('(http://v.youku.com/v_show/id_[a-zA-Z0-9\=]+.html)\s?', value)
    if (len(videos) > 0):
        for video in videos:
            video_id = re.findall('http://v.youku.com/v_show/id_([a-zA-Z0-9\=]+).html', video)
            value = value.replace('http://v.youku.com/v_show/id_' + video_id[0] + '.html',
                                  '<div class="mediaVideo"><embed src="http://player.youku.com/player.php/sid/' + video_id[0] + '/v.swf" allowFullScreen="true" quality="high" width="480" height="400" align="middle" allowScriptAccess="always" type="application/x-shockwave-flash"></embed></div>')
        return value
    else:
        return urlink(value)
    

def download_urlize(value):
    if value is None:
        return None
    
    links = re.findall('(\[dl\]http://[a-zA-Z0-9\:\/\?=\-\_\.\&]+\[\/dl\])\s?', value)
    
    if (len(links) > 0):
        for link in links:
            url = re.findall('(http://[a-zA-Z0-9\/\?=\-\_\.\&]+)', link)
            if len(url) > 0:
                value = value.replace(link, '<a href="%s" target="_blank">Download</a>' % (url[0]))
        
        return value
    return None

def mentions(value):
    if value is None:
        return None
    ms = re.findall('(@[\w\_]+\.?)\s?', value)
    if (len(ms) > 0):
        for m in ms:
            m_id = re.findall('@([a-zA-Z0-9\_\x80-\xff]+\.?)', m)
            if (len(m_id) > 0):
                if (m_id[0].endswith('.') != True and len(m_id[0])<32):
                    value = value.replace('@' + m_id[0], '<a href="/member/info/' + m_id[0] + '" rel="external">@' + m_id[0] + '</a>')
        return value
    else:
        return value

# gravatar filter
def gravatar(value,arg):
    default = "http://v2ex.appspot.com/static/img/avatar_" + str(arg) + ".png"
    if type(value).__name__ != 'Member':
        return '<img src="' + default + '" border="0" align="absmiddle" />'
    if arg == 'large':
        number_size = 73
        member_avatar_url = value.avatar_large_url
    elif arg == 'normal':
        number_size = 48
        member_avatar_url = value.avatar_normal_url
    elif arg == 'mini':
        number_size = 24
        member_avatar_url = value.avatar_mini_url
        
    if member_avatar_url:
        return '<img src="'+ member_avatar_url +'" border="0" alt="' + value.username + '" />'
    else:
        gravatar_url = "http://www.gravatar.com/avatar/" + hashlib.md5(value.email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'s' : str(number_size), 'd' : default})
        return '<img src="' + gravatar_url + '" border="0" alt="' + value.username + '" align="absmiddle" />'

# avatar filter
def avatar(value, arg):
    default = "/static/img/avatar_" + str(arg) + ".png"
    if type(value).__name__ not in ['Member', 'Node']:
        return '<img src="' + default + '" border="0" />'
    if arg == 'large':
        number_size = 73
        member_avatar_url = value.avatar_large_url
    elif arg == 'normal':
        number_size = 48
        member_avatar_url = value.avatar_normal_url
    elif arg == 'mini':
        number_size = 24
        member_avatar_url = value.avatar_mini_url
        
    if value.avatar_mini_url:
        return '<img src="'+ member_avatar_url +'" border="0" />'
    else:
        return '<img src="' + default + '" border="0" />'

# github gist script support
def gist(value):
    return re.sub(r'(http://gist.github.com/[\d]+)', r'<script src="\1.js"></script>', value)

_base_js_escapes = (
    ('\\', r'\u005C'),
    ('\'', r'\u0027'),
    ('"', r'\u0022'),
    ('>', r'\u003E'),
    ('<', r'\u003C'),
    ('&', r'\u0026'),
    ('=', r'\u003D'),
    ('-', r'\u002D'),
    (';', r'\u003B'),
    (u'\u2028', r'\u2028'),
    (u'\u2029', r'\u2029')
)

# Escape every ASCII character with a value less than 32.
_js_escapes = (_base_js_escapes +
               tuple([('%c' % z, '\\u%04X' % z) for z in range(32)]))

def escapejs(value):
    """Hex encodes characters for use in JavaScript strings."""
    for bad, good in _js_escapes:
        value = value.replace(bad, good)
    return value


_word_split_re = re.compile(r'(\s+)')
_punctuation_re = re.compile(
    '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % (
        '|'.join(imap(re.escape, ('(', '<', '&lt;'))),
        '|'.join(imap(re.escape, ('.', ',', ')', '>', '\n', '&gt;')))
    )
)
_simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
_striptags_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
_entity_re = re.compile(r'&([^;]+);')
_letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
_digits = '0123456789'

# special singleton representing missing values for the runtime
missing = type('MissingType', (), {'__repr__': lambda x: 'missing'})()

# internal code
internal_code = set()



def urlink(text, trim_url_limit=None, nofollow=False, external=True):
    if text is None:
        return None
    
    #trim_url_limit=None, nofollow=False, external=True
    """Converts any URLs in text into clickable links. Works on http://,
    https:// and www. links. Links can have trailing punctuation (periods,
    commas, close-parens) and leading punctuation (opening parens) and
    it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text will be limited
    to trim_url_limit characters.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None \
                         and (x[:limit] + (len(x) >=limit and '...'
                         or '')) or x
    words = _word_split_re.split(unicode(text))
    nofollow_attr = nofollow and ' rel="nofollow" ' or ''
    external_attr = external and ' target="_blank" ' or ''
    for i, word in enumerate(words):
        match = _punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('www.') or (
                '@' not in middle and
                not middle.startswith('http://') and
                len(middle) > 0 and
                middle[0] in _letters + _digits and (
                    middle.endswith('.org') or
                    middle.endswith('.net') or
                    middle.endswith('.com')
                )):
                middle = '<a href="http://%s"%s%s>%s</a>' % (middle,
                    nofollow_attr, external_attr, trim_url(middle))
            if middle.startswith('http://') or \
               middle.startswith('https://'):
                middle = '<a href="%s"%s%s>%s</a>' % (middle,
                    nofollow_attr, external_attr, trim_url(middle))
            if '@' in middle and not middle.startswith('www.') and \
               not ':' in middle and _simple_email_re.match(middle):
                middle = '<a href="mailto:%s">%s</a>' % (middle, middle)
            if lead + middle + trail != word:
                words[i] = lead + middle + trail
    return u''.join(words)
    
    