#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-07-03
# @Author       : RedElephant
# @Introduction : circle
# dependence


from app.api import api
from app.decorators import user_required, check_request_params, current_user
from app.enum import CheckType
from app.models import Circle, CircleUser
from app.reponse import custom, usually
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
    return usually(msg="创建完成")
