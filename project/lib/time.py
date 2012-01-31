
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta



def timedelta_to_seconds(td):
    return td.days * (24*60*60) + td.seconds


def timeover(time):
    if not time:
         return ''
    now = datetime.now()
    delta = now - time
    s = timedelta_to_seconds(delta)
    #return "%s,%s" % (str(delta.days), str(delta.seconds))
    if s >= (2*24*60*60):
        return time.strftime('%Y-%m-%d %H:%M')
    elif s >= (24*60*60):
        days = int(s//(24*60*60))
        return u'%d天前' % days
    elif s >= 60*60:
        hours = int(s//(60*60))
        return u'%d小时前' % hours
    elif s >= 60:
        minutes = int(s//60)
        return u'%d分钟前' % minutes
    elif s >= 30:
        seconds = int(s)
        return u'%d秒前' % seconds
    else:
        return u'刚刚'

def timeout(time):
    now = datetime.now()
    delta = now - time
    s = timedelta_to_seconds(delta)
    return s    