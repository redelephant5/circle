#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : users
# dependence

from app import db
from app.api import api
from app.models import Users
from app.decorators import check_request_params, user_required, current_user
from app.enum import CheckType, UserState
from app.utils.model_util import md5
from app.reponse import usually, usually_with_callback, custom, succeed


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

    def callback(user):
        return user.to_json()
    return usually_with_callback(msg="注册成功!", callback=callback, parms=(user,))


@api.route("/user/verify_data", methods=["POST"])
@check_request_params(
    verify_data=("verify_data", True, CheckType.other),
    data_type=("data_type", True, CheckType.int)
)
def user_valify_data(verify_data, data_type):
    query_dict = {1: Users.phone, 2: Users.user_name, 3: Users.nick_name, 4: Users.email}
    user = Users.query.filter(query_dict[data_type] == verify_data,
                              Users.state == UserState.normal.value).first()
    if user:
        return custom(msg="已存在,请进行修改!")
    else:
        return succeed()


@api.route("/user/update", methods=["POST"])
@user_required
@check_request_params(
    user_name=("user_name", True, CheckType.other),
    nick_name=("nick_name", False, CheckType.other),
    email=("email", False, CheckType.email),
    phone=("phone", True, CheckType.phone),
    sex=("sex", True, CheckType.int),
    birthday=("birthday", False, CheckType.date)
)
def user_update(user_name, nick_name, email, phone, sex, birthday):
    current_user.user_name = user_name
    current_user.user_pinyin = current_user.set_pinyin(user_name)
    current_user.nick_name = nick_name
    if nick_name:
        current_user.nick_pinyin = current_user.set_pinyin(nick_name)
    current_user.email = email
    current_user.sex = sex
    current_user.birthday = birthday
    db.session.add(current_user)

    def callback(user):
        return user.to_json()
    return usually_with_callback(msg="更新成功!", callback=callback, parms=(current_user,))


@api.route("/user/update_password", methods=["POST"])
@user_required
@check_request_params(
    old_password=("old_password", True, CheckType.password),
    new_password=("new_password", True, CheckType.password)
)
def user_update_password(old_password, new_password):
    if current_user.password != md5(old_password):
        return custom(msg="原密码输入有误!")
    current_user.password = md5(new_password)
    return usually(msg="密码已修改!")
