#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-07-03
# @Author       : RedElephant
# @Introduction : circle
# dependence
from datetime import datetime, timedelta

from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy import or_, and_

from app.api import api
from app.decorators import user_required, check_request_params, current_user
from app.enum import CheckType, UserState, NotifyType
from app.models import Circle, CircleUser, Users, UserTrip, Notification, NotificationDetail
from app.reponse import custom, usually, succeed, usually_with_callback
from app import db


@api.route("/circle/create_circle", methods=["POST"])
@user_required
@check_request_params(
    circle_name=("circle_name", True, CheckType.other),
    describe=("describe", False, CheckType.other),
    user_ids=("user_ids", True, CheckType.json),
)
def circle_create_circle(circle_name, describe, user_ids):

    circle = Circle.query.filter_by(name=circle_name).first()
    if circle:
        return custom(msg="该名称已存在,请修改!")
    circle = Circle()
    circle.name = circle_name
    circle.describe = describe
    circle_organizer = CircleUser()
    circle_organizer.circle_id = circle.object_id
    circle_organizer.user_id = current_user.object_id
    circle_organizer.is_organizer = 1
    circle_organizer.is_join = 1
    db.session.add_all([circle, circle_organizer])
    circle.circle_user.append(circle_organizer)
    for user_id in user_ids:
        circle_user = CircleUser(circle_id=circle.object_id, user_id=user_id)
        circle_user.circle = circle
        db.session.add(circle_user)

    def callback(circle):
        return circle.to_json()
    return usually_with_callback(msg="创建完成", callback=callback, parms=(circle,))


@api.route("/circle/query_circle", methods=["GET"])
@user_required
def circle_query_circle():

    res = []
    circles = CircleUser.query.join(CircleUser.circle)
    circles = circles.filter(CircleUser.user_id == current_user.object_id,
                             Circle.is_valid == 1,
                             CircleUser.is_join.in_([0, 1]))
    circles = circles.options(joinedload(CircleUser.circle))
    for circle in circles:
        res.append(circle.to_json_circle())
    return succeed(data=res)


@api.route("/circle/update_circle", methods=["POST"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other),
    circle_name=("circle_name", True, CheckType.other),
    describe=("describe", False, CheckType.other)
)
def circle_update_circle(circle_id, circle_name, describe):
    circle = Circle.query.filter_by(object_id=circle_id).first()
    if not circle:
        return custom(msg="该圈不存在!")
    circle_user = CircleUser.query.filter(CircleUser.user_id == current_user.object_id,
                                          CircleUser.circle_id == circle_id,
                                          CircleUser.is_organizer == 1).first()
    if not circle_user:
        return custom(msg="并不是创建人员,不允许进行修改!")
    circle.name = circle_name
    circle.describe = describe
    db.session.add(circle)
    return usually(msg="修改成功!")


@api.route("/circle/process_circle", methods=["GET"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other),
    flag=("flag", True, CheckType.int)   # 1 同意  2 拒绝
)
def circle_process_circle(circle_id, flag):

    circle_user = CircleUser.query.join(CircleUser.circle)
    circle_user = circle_user.options(joinedload(CircleUser.circle))
    circle_user = circle_user.filter(Circle.is_valid == 1,
                                     CircleUser.circle_id == circle_id,
                                     CircleUser.user_id == current_user.object_id,
                                     CircleUser.is_join.in_([0, 3])
                                     ).first()
    if not circle_user:
        return custom(msg="该圈不存在或已加入!")
    circle_user.is_join = flag
    db.session.add(circle_user)
    notify_detail = NotificationDetail.query.join(NotificationDetail.notify)
    notify_detail = notify_detail.options(joinedload(NotificationDetail.notify))
    notify_detail = notify_detail.filter(NotificationDetail.user_id == current_user.object_id,
                                         NotificationDetail.extra['circle_id'] == circle_id,
                                         NotificationDetail.is_handle == 0).first()
    if notify_detail:
        notify_detail.is_read = 1
        notify_detail.is_handle = 1
        db.session.add(notify_detail)
    content = "{}用户同意加入{}".format(current_user.user_name, circle_user.circle.name)
    if flag == 2:
        content = "{}用户拒绝加入{}".format(current_user.user_name, circle_user.circle.name)

    def callback(sender_id, user_id, content):
        title = "用户圈处理通知"
        notify = Notification(types=2,
                              sender_id=sender_id,
                              title=title,
                              content=content)
        noti_detail = NotificationDetail(user_id=user_id,
                                         is_handle=1)
        noti_detail.notify = notify
        db.session.add_all([notify, noti_detail])
        try:
            db.session.commit()
            return 'ok'
        except Exception as err:
            print(err)
            db.session.rollback()
            return 'err'
    return usually_with_callback(msg='处理成功', callback=callback,
                                 parms=(current_user.object_id, notify_detail.notify.sender_id, content))


@api.route("/circle/add_friend_in_circle", methods=["POST"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other),
    friend_ids=("friend_ids", True, CheckType.json)
)
def circle_add_friend_in_circle(circle_id, friend_ids):
    circle = Circle.query.filter_by(object_id=circle_id).first()
    if not circle:
        return custom(msg="该圈不存在!")
    circle_users = CircleUser.query.join(CircleUser.users)
    circle_users = circle_users.options(joinedload(CircleUser.users))
    circle_users = circle_users.filter(CircleUser.circle_id == circle_id,
                                       CircleUser.user_id.in_(friend_ids))
    join_circle_users = circle_users.filter(CircleUser.is_join == 1).all()
    if join_circle_users:
        user_names = [circle_user.users.user_name for circle_user in join_circle_users]
        str_user_names = ','.join(user_names)
        return custom(msg="好友{}已加入该圈!".format(str_user_names))
    realy_join_circle_users = circle_users.filter(CircleUser.is_join == 0).all()
    if realy_join_circle_users:
        user_names = [circle_user.users.user_name for circle_user in realy_join_circle_users]
        str_user_names = ','.join(user_names)
        return custom(msg="好友{}已申请加入该圈,待对方同意,不要重复申请!".format(str_user_names))
    refuse_users = []
    circle_refuse_users = circle_users.filter(CircleUser.is_join == 2).all()
    for refuse_user in circle_refuse_users:
        refuse_user.is_join = 0
        refuse_users.append(refuse_user.user_id)
        db.session.add(refuse_user)
    title = "添加圈通知"
    content = "好友{},邀请您加入{}圈.".format(current_user.user_name, circle.name)
    notify = Notification(types=NotifyType.circle.value,
                          sender_id=current_user.object_id,
                          title=title,
                          content=content)
    db.session.add(notify)
    for friend in friend_ids:
        if friend not in refuse_users:
            circle_user = CircleUser(circle_id=circle.object_id, user_id=friend)
            circle_user.circle = circle
            db.session.add(circle_user)
        notify_detail = NotificationDetail(user_id=friend,
                                           extra={"circle_id": circle_id})
        notify_detail.notify = notify
        db.session.add(notify_detail)
    return usually(msg="已添加")


@api.route("/circle/delete_circle", methods=["POST"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other)
)
def circle_delete_circle(circle_id):
    circle = Circle.query.join(Circle.circle_user)
    circle = circle.filter(Circle.object_id == circle_id)
    circle = circle.options(joinedload(Circle.circle_user))
    base_circle = circle.first()
    if not base_circle:
        return custom(msg="该圈已删除!")
    circle = circle.filter(CircleUser.is_organizer == 1,
                           CircleUser.user_id == current_user.object_id)
    circle = circle.first()
    if not circle:
        return custom(msg="不是圈创建着不允许删除")
    for circle_user in base_circle.circle_user:
        db.session.delete(circle_user)
    db.session.delete(base_circle)
    return usually(msg="已删除!")


@api.route("/circle/quit_circle", methods=["GET"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other)
)
def circle_quit_circle(circle_id):

    circle_user = CircleUser.query.filter(CircleUser.circle_id == circle_id)
    count = circle_user.count()
    circle_user = circle_user.filter(CircleUser.is_join == 1,
                                     CircleUser.user_id == current_user.object_id).first()
    if count != 1 and circle_user.is_organizer == 1:
        return custom(msg="圈中还有其他人,圈的创建者不允许退出!")
    elif count == 1 and circle_user.is_organizer == 1:
        circle = Circle.query.get(circle_id)
        db.session.delete(circle_user)
        db.session.delete(circle)
        return usually(msg="已退出,并清除圈")
    else:
        db.session.delete(circle_user)
        return usually(msg="已退出!")


@api.route("/circle/in_circle_user_schedule", methods=["GET"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other),
    query_date=("query_date", True, CheckType.date)
)
def circle_in_circle_user_schedule(circle_id, query_date):
    res = {}
    circle_users = CircleUser.query.join(CircleUser.users).join(CircleUser.circle)
    circle_users = circle_users.filter(CircleUser.circle_id == circle_id,
                                       CircleUser.is_join == 1,
                                       Users.state == UserState.normal.value)
    circle_users = circle_users.options(joinedload(CircleUser.circle),
                                        joinedload(CircleUser.users))
    circle_users = circle_users.all()
    if not circle_users:
        return custom(msg="数据异常,请重新刷新!")
    user_ids = db.session.query(CircleUser.user_id).join(CircleUser.users).\
        filter(CircleUser.circle_id == circle_id,
               CircleUser.is_join == 1,
               Users.state == UserState.normal.value).subquery()
    circle = circle_users[0].circle
    user_trips = UserTrip.query.filter(UserTrip.is_valid == 1,
                                       UserTrip.user_id.in_(user_ids),
                                       or_(
                                           and_(
                                               UserTrip.start_time >= query_date,
                                               UserTrip.end_time < query_date + timedelta(days=1)
                                           ),
                                           and_(
                                               UserTrip.start_time <= query_date,
                                               UserTrip.end_time > query_date + timedelta(days=1)
                                           )
                                       )).\
        order_by(UserTrip.start_time).all()
    res["circle_info"] = circle.to_json()
    circle_user_dict = {}
    for circle_user in circle_users:
        circle_user_dict[circle_user.user_id] = circle_user.to_json_user()
        circle_user_dict[circle_user.user_id].update({"trip_info": []})
    for user_trip in user_trips:
        circle_user_dict[user_trip.user_id]["trip_info"].append(user_trip.to_json())
    res["circle_user_info"] = circle_user_dict
    return succeed(data=res)


# 组织者添加圈内所有用户日程
@api.route("/circle/add_circle_schedule", methods=["POST"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other),
    start_time=("start_time", True, CheckType.datetime),
    end_time=("end_time", True, CheckType.datetime),
    trip_name=("trip_name", True, CheckType.other)
)
def circle_add_circle_schedule(circle_id, start_time, end_time, trip_name):
    today_time = datetime.now()
    if end_time < today_time:
        return custom(msg="结束时间小于当前时间不能进行添加!")
    circle = Circle.query.get(circle_id)
    if not circle:
        return custom(msg="该圈已不存在!")
    circle_users = db.session.query(CircleUser.user_id).filter(CircleUser.circle_id == circle_id,
                                                               CircleUser.is_join == 1)
    circle_organizer = circle_users.filter(CircleUser.user_id == current_user.object_id,
                                           CircleUser.is_organizer == 1).first()
    if not circle_organizer:
        return custom(msg="非圈组织者不能添加全用户日程!")
    sub_circle_users = circle_users.subquery()
    users_trip = UserTrip.query.filter(UserTrip.user_id.in_(sub_circle_users),
                                       or_(
                                           and_(
                                               UserTrip.start_time <= start_time,
                                               UserTrip.end_time >= start_time
                                           ),
                                           and_(
                                               UserTrip.start_time <= end_time,
                                               UserTrip.end_time >= end_time)),
                                       UserTrip.is_adjust == 0,
                                       UserTrip.is_join == 1).all()
    if users_trip:
        return custom(msg="添加行程与用户行程冲突,不能添加!")
    users_join_trip = UserTrip.query.filter(UserTrip.user_id.in_(sub_circle_users),
                                            or_(
                                                and_(
                                                    UserTrip.start_time <= start_time,
                                                    UserTrip.end_time >= start_time
                                                ),
                                                and_(
                                                    UserTrip.start_time <= end_time,
                                                    UserTrip.end_time >= end_time)),
                                            UserTrip.schedule_source == 2,
                                            UserTrip.is_join == 0).all()
    if users_join_trip:
        return custom(msg="用户有未处理的团队行程,不能添加!")
    title = "圈内日程添加通知"
    content = "{}圈的组织者{}添加了{}至{}的{}日程安排,请知悉!".\
        format(circle.name, current_user.user_name,
               start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), trip_name)
    notify = Notification(types=NotifyType.schedule.value,
                          sender_id=current_user.object_id,
                          title=title,
                          content=content)
    db.session.add(notify)
    res_circle_users = circle_users.all()
    for circle_user in res_circle_users:
        user_trip = UserTrip()
        user_trip.user_id = circle_user[0]
        user_trip.start_time = start_time
        user_trip.end_time = end_time
        user_trip.name = trip_name
        user_trip.is_adjust = 0
        user_trip.is_see = 1
        user_trip.schedule_source = 2
        if circle_user[0] == current_user.object_id:
            user_trip.is_join = 1
            db.session.add(user_trip)
        else:
            user_trip.is_join = 0
            db.session.add(user_trip)
            db.session.flush()
            info = {'circle_id': circle.object_id,
                    'trip_id': user_trip.object_id}
            notify_detail = NotificationDetail(user_id=circle_user[0],
                                               extra=info)
            notify_detail.notify = notify
            db.session.add(notify_detail)

    return usually(msg="添加日程成功!")
