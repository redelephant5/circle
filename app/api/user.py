#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : users
# dependence

from sqlalchemy.orm import joinedload, contains_eager

from app import db
from app.api import api
from app.models import Users, UserTrip, UserFriend
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
def user_verify_data(verify_data, data_type):
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
    sex=("sex", True, CheckType.int),
    birthday=("birthday", False, CheckType.date)
)
def user_update(user_name, nick_name, email, sex, birthday):
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


@api.route("/user/user_info", methods=["GET"])
@user_required
@check_request_params(
    query_user=("query_user", True, CheckType.other)
)
def user_user_info(query_user):

    query_user = Users.query.filter_by(object_id=query_user, state=UserState.normal.value).first()
    if not query_user:
        return custom(msg="用户不存在或已注销!")
    else:
        return succeed(data=query_user.to_json())


@api.route("/user/query_users_by_phone", methods=["GET"])
@user_required
@check_request_params(
    phone=("phone", True, CheckType.other)
)
def user_query_users_by_phone(phone):
    query_user = Users.query.outerjoin(Users.to_friend)
    query_user = query_user.filter(Users.phone == phone,
                                   Users.state == UserState.normal.value,
                                   UserFriend.user_id == current_user.object_id)
    query_user = query_user.options(contains_eager(Users.to_friend)).first()
    if not query_user:
        return custom(msg="用户不存在或已注销!")
    else:
        return succeed(data=query_user.to_json_friend())


@api.route("/user/add_friend", methods=["GET"])
@user_required
@check_request_params(
    friend_id=("friend_id", True, CheckType.other),
    content=("content", False, CheckType.other)
)
def user_add_friend(friend_id, content):

    query_firend = Users.query.filter_by(object_id=friend_id, state=UserState.normal.value).first()
    if not query_firend:
        return custom(msg="用户已不存在或已注销!")
    friend = UserFriend.query.filter(UserFriend.user_id == current_user.object_id,
                                     UserFriend.friend_id == friend_id)
    friend_res = friend.filter(UserFriend.flag == 0).first()
    if friend_res:
        return custom(msg="该用户已申请,请不要重复提交")
    friend_res = friend.filter(UserFriend.flag == 1).first()
    if friend_res:
        return custom(msg="该用户已是好友")
    friend_res = friend.filter(UserFriend.flag == 3).first()
    if friend_res:
        return custom(msg="该用户已添加您好友,请进行验证")
    userfriend = UserFriend()
    userfriend.user_id = current_user.object_id
    userfriend.friend_id = friend_id
    userfriend.content = content
    userfriend.flag = 0
    usertofriend = UserFriend()
    usertofriend.user_id = friend_id
    usertofriend.friend_id = current_user.object_id
    usertofriend.content = content
    usertofriend.flag = 3
    db.session.add_all([userfriend, usertofriend])
    return usually(msg="已申请!")


@api.route("/user/my_friend", methods=["GET"])
@user_required
def user_query_friend():

    user_friends = UserFriend.query.join(UserFriend.user_friend)\
        .filter(Users.state == UserState.normal.value,
                UserFriend.flag == 1,
                UserFriend.user_id == current_user.object_id)
    user_friends = user_friends.options(joinedload(UserFriend.user_friend)).all()
    res = []
    for friend in user_friends:
        res.append(friend.to_json_with_user())
    return succeed(data=res)


@api.route("/user/other_flag_friend", methods=["GET"])
@user_required
@check_request_params(
    flag=("flag", False, CheckType.other)
)
def user_other_flag_friend(flag=False):

    res = []
    other_friends = UserFriend.query.join(UserFriend.user_friend).\
        filter(Users.state == UserState.normal.value,
               UserFriend.flag != 1,
               UserFriend.user_id == current_user.object_id)
    if flag:
        count = other_friends.count()
        return succeed(data=count)
    else:
        for friend in other_friends:
            res.append(friend.to_json_with_user())
        return succeed(data=res)


@api.route("/user/process_flag_friend", methods=["POST"])
@user_required
@check_request_params(
    friend_id=("friend_id", True, CheckType.other),
    flag=("flag", True, CheckType.int)
)
def user_accept_friend(friend_id, flag):

    user = UserFriend.query.join(UserFriend.user_friend).\
        filter(Users.state == UserState.normal.value,
               UserFriend.user_id == current_user.object_id,
               UserFriend.friend_id == friend_id)
    user = user.options(joinedload(UserFriend.user_friend)).first()
    if not user:
        return custom(msg="该用户不存在或已注销!")
    user.flag = flag
    friend = UserFriend.query.filter_by(user_id=friend_id, firend_id=current_user.object_id).first()
    if not friend:
        return custom(msg="用户异常!")
    friend.flag = flag  # todo 拒绝需要修改
    return usually(msg="添加成功!")
