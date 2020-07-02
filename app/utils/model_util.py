#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         :
# @Author       : RedElephant
# @Introduction : model util
# dependence

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.ext.declarative import declared_attr
from flask import request


def get_uid():

    return uuid.uuid4().hex


def md5(aaa):
    aaab = aaa + "www.xxx-aaa.com"
    import hashlib
    m = hashlib.md5()
    m.update(aaab.encode("iso-8859-1"))
    return m.hexdigest()


class ApiDurationTool(object):

    def __init__(self, app=None, db=None):
        if app:
            self.app = app
        if db:
            self.db = db

    def init_app(self, app, db):
        self.app = app
        self.db = db

        class ApiDurationRecord(db.Model):
            import time

            create_time = db.Column(db.DateTime, server_default=func.now(), default=datetime.now, index=True)
            timestamp = db.Column(db.Integer, default=time.time)
            object_id = db.Column(db.Integer, primary_key=True, nullable=False)
            path = db.Column(db.String(64), index=True)
            query_count = db.Column(db.Integer, index=True)
            duration = db.Column(db.Float, index=True)

            @declared_attr
            def __tablename__(cls):
                return cls.__name__.lower()

        @app.after_request
        def after_request(response):

            from flask import current_app
            if current_app.config["SQLALCHEMY_RECORD_QUERIES"] and (
                    response.content_type == 'application/json' or response.content_type == 'text/html charset=utf-8'):
                from flask_sqlalchemy import get_debug_queries
                querys = get_debug_queries()
                count = len(get_debug_queries())
                if count > 0:
                    d = 0
                    for query in querys:
                        d = d + query.duration
                    print("查询次数与时间", count, d)
                    record = ApiDurationRecord(path=request.path, query_count=count, duration=d)
                    try:
                        db.session.add(record)
                        db.session.commit()
                    except Exception as e:
                        print(e)
                        db.session.rollback(record)
            return response
