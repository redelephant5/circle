#!python3.6
# -*- coding: utf-8 -*-
# @Introduction : 圈服务相关配置文件

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # 秘钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'redelephant_circle'
    # 配置
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 500
    SQLALCHEMY_ECHO = True

    #小程序
    APPID = "wxb505c615732aa3d4"
    APPSECRET = "3213038ab0c99fa45daeaf47e8b09b53"

    def init_app(self):
        pass


class DevelopConfig(Config):

    DEBUG = True

    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:mysql@127.0.0.1/circle?charset=utf8mb4'
    REDIS_URL = "redis://127.0.0.1:6379/0"


class TestingConfig(Config):
    pass


class ProductionConfig(Config):

    DEBUG = False

    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:mysql@127.0.0.1/circle?charset=utf8mb4'
    REDIS_URL = "redis://127.0.0.1:6379/0"


config = {
    'development': DevelopConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopConfig
}
