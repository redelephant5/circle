#!python3.6
# -*- coding: utf-8 -*-
# @Introduction : app初始化

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_redis import FlaskRedis
from config import config
from app.utils.model_util import ApiDurationTool

db = SQLAlchemy()
redis_store = FlaskRedis()
api_duration_toll = ApiDurationTool()


def create_app(config_name):
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config.from_object(config[config_name])
    db.app = app
    db.init_app(app)
    redis_store.init_app(app)
    api_duration_toll.init_app(app, db)
    from .api import api as api_buleprint
    app.register_blueprint(api_buleprint, url_prefix="/api")

    return app
