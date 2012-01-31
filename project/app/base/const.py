# -*- coding: utf-8 -*-


class Status(object):
    LOCK = -2
    SPAM = -1
    INIT = 0
    PENDING = 1
    UNVERIFIED = 2
    ACTIVE = 9

class Role(object):
    NORMAL = 0
    EDITOR = 7
    MASTER = 8
    ADMIN = 9

class OpenID(object):
    GOOGLE = 1
    FACEBOOK = 2
    TWITTER = 3
    FRIENDFEED = 4

    NAME = {GOOGLE:"Google", FACEBOOK:"Facebook",
            TWITTER:"Twitter", FRIENDFEED:"Friendfeed"}

class Category(object):
    TOOLKIT = 1
    HOSTING = 2
    SERVER = 3
    DATABASE = 4
    FRAMEWORK = 5
    FRONTEND = 6
    LANGUAGE = 7
