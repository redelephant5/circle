#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-07-03
# @Author       : RedElephant
# @Introduction : circle
# dependence

from sqlalchemy.orm import joinedload, contains_eager

from app.api import api
from app.decorators import user_required, check_request_params, current_user
from app.enum import CheckType
from app.models import Circle, CircleUser
from app.reponse import custom, usually, succeed, usually_with_callback
from app import db


@api.route("/circle/create_circle", methods=["POST"])
@user_required
@check_request_params(
    circle_name=("circle_name", True, CheckType.other),
    describe=("describe", False, CheckType.other),
    user_ids=("user_ids", True, CheckType.json),
    display_day=("display_day", True, CheckType.int),
    types=("types", True, CheckType.int)
)
def circle_create_circle(circle_name, describe, user_ids, display_day, types):

    circle = Circle.query.filter_by(name=circle_name).first()
    if circle:
        return custom(msg="改名称已存在,请修改!")
    circle = Circle()
    circle.name = circle_name
    circle.describe = describe
    circle.display_day = display_day
    circle.format_type = types
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
    describe=("describe", False, CheckType.other),
    display_day=("display_day", True, CheckType.int),
    types=("types", True, CheckType.int)
)
def circle_update_circle(circle_id, circle_name, describe, display_day, types):
    circle = Circle.query.filter_by(object_id=circle_id).first()
    if not circle:
        return custom(msg="改圈不存在!")
    circle_user = CircleUser.query.filter(CircleUser.user_id == current_user.object_id,
                                          CircleUser.circle_id == circle_id,
                                          CircleUser.is_organizer == 1).first()
    if not circle_user:
        return custom(msg="并不是创建人员,不允许进行修改!")
    circle.name = circle_name
    circle.describe = describe
    circle.display_day = display_day
    circle.format_type = types
    db.session.add(circle)
    return usually(msg="修改成功!")


@api.route("/circle/process_circle", methods=["GET"])
@user_required
@check_request_params(
    circle_id=("circle_id", True, CheckType.other),
    flag=("flag", True, CheckType.int)
)
def circle_process_circle(circle_id, flag):

    circle_user = CircleUser.query.join(CircleUser.circle)
    circle_user = circle_user.filter(Circle.is_valid == 1,
                                     CircleUser.circle_id == circle_id,
                                     CircleUser.user_id == current_user.object_id,
                                     CircleUser.is_join == 0
                                     ).first()
    if not circle_user:
        return custom(msg="该圈已不存在或已加入!")
    circle_user.is_join = flag
    db.session.add(circle_user)
    return usually(msg="ok")


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
    for friend in friend_ids:
        circle_user = CircleUser(circle_id=circle.object_id, user_id=friend)
        circle_user.circle = circle
        db.session.add(circle_user)
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