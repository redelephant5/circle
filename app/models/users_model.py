#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         :
# @Author       : RedElephant
# @Introduction : users model
# dependence

from datetime import datetime

from sqlalchemy import func, text

from app import db
from app.enum import UserState
from .base_model import BaseModelUuidPk


class Users(BaseModelUuidPk):

    user_name = db.Column(db.String(50), comment="用户名称")
    user_pinyin = db.Column(db.String(255), comment="用户拼音")
    nick_name = db.Column(db.String(50), comment="昵称")
    nick_pinyin = db.Column(db.String(255), comment="昵称拼音")
    email = db.Column(db.String(255), default='', comment="邮箱")
    phone = db.Column(db.String(255), comment="手机号")
    password = db.Column(db.String(255), comment="密码")
    device_identifier = db.Column(db.String(255), comment="设备标示")
    sex = db.Column(db.Integer, default=3, comment="性别 1 男 2 女 3未配置")
    birthday = db.Column(db.Date, index=True, comment="生日")
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.now, server_default=func.now(),
                           comment="加入的时间")
    state = db.Column(db.Integer, default=UserState.normal.value, server_default=text('0'), index=True, comment="状态")
