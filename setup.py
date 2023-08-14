# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name="FlickBoard",
    version="0.1",
    install_requires=["pycurl>=7.18.2",
                      "tornado==6.3.3",
                      "pymongo==2.1.1",
                      "markdown==2.0.3",
                      "chardet>=1.0.1",
                      "beautifulsoup>=3.1.0.1",
                      "webhelpers>=1.0",
                      "formencode>=1.2.2",
                      "decorator>=3.2.0",
                      "mongoengine==0.5.0",
                      "PIL==1.1.7",
                      ],
    packages=find_packages(),
    author="feilaoda",
    author_email="azhenglive@gmail.com",
    url="http://www.yihoudu.com/board",
    description="yihoudu for reading later",
)
