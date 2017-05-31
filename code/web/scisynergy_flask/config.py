'''
Created on 15/05/2016

@author: aurelio
'''

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = '#@$dqeqwe12e11w1cc'
    

class ProductionConfig(Config):
    DEBUG = False
    
class DevelConfig(Config):
    DEBUG = False