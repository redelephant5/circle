#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : users
# dependence
from datetime import datetime, timedelta
import json

from flask import current_app
import requests
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy import distinct, or_, and_

from app import db, redis_store
from app.api import api
from app.models import Users, UserTrip, UserFriend, Notification, NotificationDetail, CircleUser
from app.decorators import check_request_params, user_required, current_user
from app.enum import CheckType, UserState, NotifyType
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


# 字段验证
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
    phone=("phone", False, CheckType.other),
    email=("email", False, CheckType.email),
    sex=("sex", True, CheckType.int),
    birthday=("birthday", False, CheckType.date)
)
def user_update(user_name, phone, email, sex, birthday):
    current_user.user_name = user_name
    current_user.phone = phone
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


@api.route("/user/logout", methods=["GET"])
@user_required
def user_logout():
    current_user.state = 2
    return usually(msg="用户已注销")


# 账号密码登录
@api.route("/user/login", methods=["POST"])
@check_request_params(
    phone=("phone", True, CheckType.other),
    password=("password", True, CheckType.other)
)
def user_login(phone, password):
    user = Users.query.filter_by(phone=phone, password=md5(password)).first()
    if not user:
        return custom(msg="手机号或密码错误!")
    return succeed(data=user.to_json())


# 小程序登录

@api.route("/user/wx_login", methods=["POST"])
@check_request_params(
    code=("code", True, CheckType.other),
    encryptedData=("encryptedData", True, CheckType.other),
    iv=("iv", True, CheckType.other),
    rawData=("rawData", True, CheckType.json),
    signature=("signature", True, CheckType.other)
)
def user_query_users_by_phone(code, encryptedData, iv, rawData, signature):

    app_id = current_app.config["APPID"]
    app_secret = current_app.config["APPSECRET"]
    url = "https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code".\
        format(app_id, app_secret, code)
    content = requests.get(url)
    res = json.loads(content.text)
    openid = res["openid"]
    user = Users.query.filter_by(openid=openid).first()
    if user:
        return succeed(data=user.to_json())
    user = Users()
    user.openid = openid
    user.sex = rawData.get("gender")
    user.city = rawData.get("province")
    user.wx_name = rawData.get("nickName")
    user.wx_head_portrait = rawData.get("avatarUrl")
    db.session.add(user)

    def callback(user):
        return user.to_json()

    return usually_with_callback(callback=callback, parms=(user,))


# 小程序同步信息
@api.route("/user/wx_sync_info", methods=["POST"])
@user_required
@check_request_params(
    encryptedData=("encryptedData", True, CheckType.other),
    iv=("iv", True, CheckType.other),
    rawData=("rawData", True, CheckType.json),
    signature=("signature", True, CheckType.other)
)
def user_wx_sync_info(encryptedData, iv, rawData, signature):
    current_user.sex = rawData.get("gender")
    current_user.city = rawData.get("province")
    current_user.wx_name = rawData.get("nickName")
    current_user.wx_head_portrait = rawData.get("avatarUrl")
    db.session.add(current_user)

    def callback(user):
        return user.to_json()

    return usually_with_callback(callback=callback, parms=(current_user,))


@api.route("/user/add_friend", methods=["GET"])
@user_required
@check_request_params(
    friend_id=("friend_id", True, CheckType.other),
    content=("content", False, CheckType.other)
)
def user_add_friend(friend_id, content):

    query_firend = Users.query.filter_by(object_id=friend_id, state=UserState.normal.value).first()
    if not query_firend:
        return custom(msg="用户不存在或已注销!")
    friend = UserFriend.query.filter(UserFriend.user_id == current_user.object_id,
                                     UserFriend.friend_id == friend_id)
    applied_friend = friend.filter(UserFriend.flag == 0).first()
    if applied_friend:
        return custom(msg="已申请,待对方添加!")
    friend_res = friend.filter(UserFriend.flag == 2).first()
    if friend_res:
        friend_res.flag = 0
        to_friend_res = UserFriend.query.filter_by(friend_id=current_user.object_id,
                                                   user_id=friend_id).first()
        if to_friend_res:
            to_friend_res.flag = 3
        db.session.add_all([friend_res, to_friend_res])
        return usually(msg="已重新申请!")
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

    def callback(user, friend):
        title = "添加好友通知"
        content = "用户:{} 请求添加好友".format(user.user_name)
        notify = Notification(types=NotifyType.friend.value,
                              sender_id=user.object_id,
                              title=title,
                              content=content)
        notify_detail = NotificationDetail(user_id=friend.user_id,
                                           extra={"friend_id": friend.friend_id})
        notify_detail.notify = notify
        db.session.add_all([notify, notify_detail])
        try:
            db.session.commit()
            return 'ok'
        except Exception as err:
            print(err)
            db.session.rollback()
            return 'err'

    return usually_with_callback(msg="已申请", callback=callback, parms=(current_user, usertofriend,))


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


@api.route("/user/process_flag_friend", methods=["GET", "POST"])
@user_required
@check_request_params(
    friend_id=("friend_id", True, CheckType.other),
    flag=("flag", True, CheckType.int)  # 1 同意  2 拒绝
)
def user_process_flag_friend(friend_id, flag):

    user = UserFriend.query.join(UserFriend.user_friend).\
        filter(Users.state == UserState.normal.value,
               UserFriend.user_id == current_user.object_id,
               UserFriend.friend_id == friend_id,
               UserFriend.flag == 3)
    user = user.options(joinedload(UserFriend.user_friend)).first()
    if not user:
        return custom(msg="该用户不存在或已是好友!")
    user.flag = flag
    friend = UserFriend.query.filter_by(user_id=friend_id, friend_id=current_user.object_id, flag=0).first()
    if not friend:
        return custom(msg="用户异常!")
    friend.flag = flag
    notification_detail = NotificationDetail.query.filter(NotificationDetail.user_id == current_user.object_id,
                                                          NotificationDetail.extra["friend_id"] == friend_id).first()
    if notification_detail:
        notification_detail.is_read = 1
        notification_detail.is_handle = 1
    content = "{}用户同意您的好友申请!".format(current_user.user_name)
    if flag == 2:
        friend.verify_message = "对方已拒绝"
        content = "{}用户拒绝您的好友申请!".format(current_user.user_name)

    def callback(sender_id, user_id, content):
        title = "用户好友处理通知"
        notify = Notification(types=1,
                              sender_id=sender_id,
                              title=title,
                              content=content)
        notify_detail = NotificationDetail(user_id=user_id,
                                           is_handle=1)
        notify_detail.notify = notify
        db.session.add_all([notify, notify_detail])
        try:
            db.session.commit()
            return 'ok'
        except Exception as err:
            print(err)
            db.session.rollback()
            return 'err'
    return usually_with_callback(msg="处理成功", callback=callback, parms=(current_user.object_id, friend_id, content,))


# 新增及更新行程
@api.route("/user/create_trip", methods=["POST"])
@user_required
@check_request_params(
    trip_id=("trip_id", False, CheckType.other),
    start_time=("start_time", True, CheckType.datetime),
    end_time=("end_time", True, CheckType.datetime),
    name=("name", True, CheckType.other),
    is_adjust=("is_adjust", True, CheckType.int),
    is_see=("is_see", True, CheckType.int)
)
def user_create_trip(trip_id, start_time, end_time, name, is_adjust, is_see):
    if trip_id:
        user_trip = UserTrip.query.get(trip_id)
        if not user_trip:
            return custom(msg="行程不存在,不能修改!")
    else:
        user_trip = UserTrip()
    user_trip.user_id = current_user.object_id
    user_trip.start_time = start_time
    user_trip.end_time = end_time
    user_trip.name = name
    user_trip.is_valid = is_adjust
    user_trip.is_see = is_see
    db.session.add(user_trip)
    circle_user = CircleUser.query.join(CircleUser.circle)
    circle_user = circle_user.filter(CircleUser.user_id == current_user.object_id,
                                     CircleUser.is_join == 1).all()

    def callback(circle_user):
        for circle in circle_user:
            redis_store.set('circle_no:' + circle.circle_id, '1', ex=3)
    return usually_with_callback(msg="行程添加成功!", callback=callback, parms=(circle_user,))


@api.route("/user/query_trip", methods=["GET"])
@user_required
@check_request_params(
    start_time=("start_time", True, CheckType.date),
    end_time=("end_time", True, CheckType.date),
    query_user_id=("query_user_id", False, CheckType.other)
)
def user_query_trip(start_time, end_time, query_user_id):
    if start_time > end_time:
        return custom(msg="开始日期不能大于结束日期")
    res = {}
    if query_user_id:
        user_id = query_user_id
    else:
        user_id = current_user.object_id
    user_trips = UserTrip.query.filter(UserTrip.user_id == user_id,
                                       or_(
                                           and_(
                                               UserTrip.start_time >= start_time,
                                               UserTrip.end_time < end_time + timedelta(days=1)
                                           ),
                                           and_(
                                               UserTrip.start_time <= start_time,
                                               UserTrip.end_time > end_time + timedelta(days=1)
                                           )
                                       ),
                                       UserTrip.is_valid == 1).\
        order_by(UserTrip.start_time).all()
    for user_trip in user_trips:
        days = (user_trip.end_time.date() - user_trip.start_time.date()).days
        if days >= 1:
            for i in range(days + 1):
                include_date = user_trip.start_time + timedelta(days=i)
                if start_time <= include_date <= end_time + timedelta(days=1):
                    if include_date.strftime("%Y-%m-%d") not in res:
                        res[(user_trip.start_time + timedelta(days=i)).strftime("%Y-%m-%d")] = [user_trip.object_id]
                    else:
                        res[(user_trip.start_time + timedelta(days=i)).strftime("%Y-%m-%d")].append(user_trip.object_id)
        else:
            if user_trip.start_time.strftime("%Y-%m-%d") not in res:
                res[user_trip.start_time.strftime("%Y-%m-%d")] = [user_trip.object_id]
            else:
                res[user_trip.start_time.strftime("%Y-%m-%d")].append(user_trip.object_id)
    return succeed(data=res)


@api.route("/user/query_day_trip_list", methods=["GET"])
@user_required
@check_request_params(
    trip_ids=("trip_ids", True, CheckType.json),
    query_user_id=("query_user_id", False, CheckType.other)
)
def user_query_day_trip_detail(trip_ids, query_user_id):
    if query_user_id:
        user_id = query_user_id
    else:
        user_id = current_user.object_id
    user_trips = UserTrip.query.filter(UserTrip.user_id == user_id,
                                       UserTrip.object_id.in_(trip_ids),
                                       UserTrip.is_valid == 1). \
        order_by(UserTrip.start_time).all()
    res = []
    for user_trip in user_trips:
        res.append(dict(trip_name=user_trip.name, start_time=user_trip.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        end_time=user_trip.end_time.strftime("%Y-%m-%d %H:%M:%S"), trip_id=user_trip.object_id))
    return succeed(data=res)


@api.route("/user/query_trip_detail", methods=["GET"])
@user_required
@check_request_params(
    trip_id=("trip_id", True, CheckType.other)
)
def user_query_trip_detail(trip_id):
    user_trip = UserTrip.query.filter_by(object_id=trip_id, is_valid=1).first()
    if not user_trip:
        return custom(msg="该行程不存在!")
    return succeed(data=user_trip.to_json())


@api.route("/user/delete_trip", methods=["GET"])
@user_required
@check_request_params(
    trip_id=("trip_id", True, CheckType.other)
)
def user_delete_trip(trip_id):
    trip = UserTrip.query.get(trip_id)
    if not trip:
        return custom(msg="该行程不存在!")
    if trip.trip_source == 2:
        if trip.is_join == 1:
            return custom(msg="该行程为圈内行程不能删除!")
        else:
            user_notify = NotificationDetail.query.join(Notification)
            user_notify = user_notify.filter(NotificationDetail.user_id == current_user.object_id,
                                             NotificationDetail.is_handle == 0,
                                             NotificationDetail.extra['trip_id'] == trip_id,
                                             Notification.types == NotifyType.trip.value).first()
            if user_notify and trip.end_time > datetime.now():
                return custom(msg="该行程还未进行处理,请处理后进行删除!")
    db.session.delete(trip)
    return usually(msg="行程已删除!")


# 圈内行程处理
@api.route("/user/processing_trip_in_circle", methods=["POST"])
@user_required
@check_request_params(
    trip_id=("trip_id", True, CheckType.other),
    flag=("flag", True, CheckType.int)  # 0 拒绝, 1 同意
)
def user_processing_trip_in_circle(trip_id, flag):
    trip = UserTrip.query.filter_by(object_id=trip_id,
                                    trip_source=2,
                                    is_join=0).first()
    if not trip:
        return custom(msg="该行程不存在!")
    today_time = datetime.now()
    if trip.end_time <= today_time and flag == 1:
        return custom(msg="行程已过期,不能进行添加!")
    trip.is_join = flag
    msg = "该行程已处理."
    db.session.add(trip)
    notify_detail = NotificationDetail.query.join(NotificationDetail.notify)
    notify_detail = notify_detail.filter(NotificationDetail.user_id == current_user.object_id,
                                         NotificationDetail.extra['trip_id'] == trip_id,
                                         NotificationDetail.is_handle == 0)
    notify_detail = notify_detail.options(joinedload(NotificationDetail.notify)).first()
    if notify_detail:
        notify_detail.is_read = 1
        notify_detail.is_handle = 1
        title = "用户行程处理通知"
        if flag == 1:
            content = "{}用户已添加您创建的{},时间为{}至{}的行程".\
                format(current_user.user_name, trip.name,
                       trip.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                       trip.end_time.strftime("%Y-%m-%d %H:%M:%S"),)
            msg = "行程已添加."
        else:
            content = "{}用户拒绝您创建的{},时间为{}至{}的行程". \
                format(current_user.user_name, trip.name,
                       trip.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                       trip.end_time.strftime("%Y-%m-%d %H:%M:%S"), )
            db.session.delete(trip)
            msg = "行程已拒绝并删除."
        notify = Notification(types=3,
                              sender_id=current_user.object_id,
                              title=title,
                              content=content)
        touser_notify_detail = NotificationDetail(user_id=notify_detail.notify.sender_id,
                                                  is_read=0,
                                                  is_handle=1)
        touser_notify_detail.notify = notify
        db.session.add_all([notify_detail, notify, touser_notify_detail])
    return usually(msg=msg)


# 用户未读消息及未处理消息
@api.route("/user/un_notice_count", methods=["GET"])
@user_required
def user_un_notice_count():
    notify_detail = NotificationDetail.query.filter_by(user_id=current_user.object_id)
    unread_notice = notify_detail.filter_by(is_read=0).count()
    unprocess_noticat = notify_detail.filter_by(is_handle=0).count()
    return succeed(data={"unread_count": unread_notice, "unprocess_count": unprocess_noticat})


# 用户读消息及处理消息详情
@api.route("/user/notice_detail", methods=["GET"])
@user_required
@check_request_params(
    flag=("flag", True, CheckType.int)  # 1 读消息  2 处理消息
)
def user_notice_detail(flag):
    res = []
    notify_details = NotificationDetail.query.join(NotificationDetail.notify)
    notify_details = notify_details.filter(NotificationDetail.user_id == current_user.object_id)
    notify_details = notify_details.options(joinedload(NotificationDetail.notify))
    if flag == 2:
        notify_details = notify_details.filter(NotificationDetail.is_handle == 0)
    for notify_detail in notify_details:
        res.append(notify_detail.to_json_with_notification())
    return succeed(data=res)


# 用户读消息
@api.route("/user/read_notice_detail", methods=["GET"])
@user_required
@check_request_params(
    notify_detail_id=("notify_detail_id", True, CheckType.other)
)
def user_read_notice_detail(notify_detail_id):
    notify_detail = NotificationDetail.query.join(NotificationDetail.notify)
    notify_detail = notify_detail.filter(NotificationDetail.object_id == notify_detail_id,
                                         NotificationDetail.user_id == current_user.object_id)
    notify_detail = notify_detail.options(joinedload(NotificationDetail.notify)).first()
    if not notify_detail:
        return custom(msg='消息不存在!')
    notify_detail.is_read = 1
    return usually(data=notify_detail.to_json_with_notification())


# 用户处理消息
@api.route("/user/process_notice_detail", methods=["POST"])
@user_required
@check_request_params(
    notify_detail_id=("notify_detail_id", True, CheckType.other),
    flag=("flag", True, CheckType.int)
)
def user_process_notice_detail(notify_detail_id, flag):
    notify_detail = NotificationDetail.query.join(NotificationDetail.notify)
    notify_detail = notify_detail.filter(NotificationDetail.object_id == notify_detail_id,
                                         NotificationDetail.user_id == current_user.object_id,
                                         NotificationDetail.is_handle == 0)
    notify_detail = notify_detail.options(joinedload(NotificationDetail.notify)).first()
    if not notify_detail:
        return custom(msg="该通知不存在或已处理!")
    if notify_detail.notify.types == 1:
        friend_id = notify_detail.extra['friend_id']
        flag = flag
        user_process_friend = user_process_flag_friend.__wrapped__
        user_process_friend = user_process_friend.__wrapped__
        return user_process_friend(friend_id, flag)
    elif notify_detail.notify.types == 2:
        circle_id = notify_detail.extra['circle_id']
        flag = flag
        from app.api.circle import circle_process_circle as process_circle
        user_process_circle = process_circle.__wrapped__.__wrapped__
        return user_process_circle(circle_id, flag)
    elif notify_detail.notify.types == 3:
        trip_id = notify_detail.extra['trip_id']
        flag = flag
        if flag == 2:
            flag = 0
        processing_trip_in_circle = user_processing_trip_in_circle.__wrapped__.__wrapped__
        return processing_trip_in_circle(trip_id, flag)


# 用户删除消息
@api.route("/user/delete_notice", methods=["POST"])
@user_required
@check_request_params(
    notify_detail_id=("notify_detail_id", True, CheckType.other)
)
def user_delete_notice(notify_detail_id):
    notify_detail = NotificationDetail.query.filter_by(user_id=current_user.object_id,
                                                       object_id=notify_detail_id).first()
    if not notify_detail:
        return custom(msg='消息不存在!')
    elif notify_detail.is_handle == 0:
        return custom(msg='消息还未处理不允许删除!')
    db.session.delete(notify_detail)
    return usually(msg='删除成功!')
