#!python3.6
# -*- coding: utf-8 -*-
# @Introduction : app初始化

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.app = app
    db.init_app(app)

    return app
