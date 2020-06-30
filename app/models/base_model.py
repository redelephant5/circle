#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : 基础model
# dependence
import time
from datetime import datetime

from sqlalchemy import DateTime, Date, Time, func
from sqlalchemy.ext.declarative import AbstractConcreteBase, declared_attr

from app import db
from app.utils.model_util import get_uid


class JsonBaseMixin(object):

    def to_json(self, exclude_list=()):
        res = {}
        res["object_name"] = self.__class__.__name__
        for col in self.__tabls__.columns:

            col_name = col.name
            if col_name in exclude_list:
                continue
            value = getattr(self, col_name)
            if value is None:
                pass
            else:
                if isinstance(col.type, DateTime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(col.type, Date):
                    value = value.strftime("%Y-%m-%d")
                elif isinstance(col.type, Time):
                    value = value.strftime("H:%M:%S")
                elif isinstance(col.type, db.DECIMAL):
                    value = float(value)
            res[col_name] = value
        return res


class BaseModel(AbstractConcreteBase, db.Model, JsonBaseMixin):
    __abstract__ = True

    create_time = db.Column(db.DateTime, default=datetime.now, server_default=func.now(), index=True)
    timestamp = db.Column(db.Integer, default=time.time, index=True)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, server_default=func.now(),
                            index=True)
    is_valid = db.Column(db.Boolean, default=True, index=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class BaseModelIntPk(BaseModel):
    __abstract__ = True
    object_id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)


class BaseModelUuidPk(BaseModel):
    __abstract__ = True
    object_id = db.Column(db.String(32), primary_key=True, default=get_uid(), nullable=False)
