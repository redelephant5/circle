#!python3.6
# -*- coding: utf-8 -*-
# @Introduction : app初始化

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    db.app = app
    db.init_app(app)
    return app
