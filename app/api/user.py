#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : users
# dependence
from flask import request

from app import db
from app.api import api
from app.models import Users
from app.decorators import check_request_params
from app.enum import CheckType
from app.utils.model_util import md5
from app.reponse import usually


@api.route("/user/create", methods=["POST"])
@check_request_params(
    user_name=("user_name", True, CheckType.other),
    nick_name=("nick_name", False, CheckType.other),
    email=("email", False, CheckType.email),
    phone=("phone", True, CheckType.phone),
    password=("password", True, CheckType.password),
    sex=("sex", True, CheckType.int)
)
def user_create(user_name, nick_name, email, phone, password, sex):
    user = Users()
    user.user_name = user_name
    user.user_pinyin = user.set_pinyin(user_name)
    user.nick_name = nick_name
    if nick_name:
        user.nick_pinyin = user.set_pinyin(nick_name)
    user.email = email
    user.phone = phone
    user.password = md5(password)
    user.sex = sex
    db.session.add(user)
    return usually(msg="注册成功!")
