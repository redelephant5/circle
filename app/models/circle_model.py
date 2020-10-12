#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-07-01
# @Author       : RedElephant
# @Introduction : circle model
# dependence

from app import db
from app.models import BaseModelUuidPk, BaseModelIntPk, Users


class Circle(BaseModelUuidPk):

    name = db.Column(db.String(50), nullable=False, comment="名称")
    describe = db.Column(db.String(255), comment="描述")
    display_day = db.Column(db.Integer, default=1, comment="显示天数(字段未使用)")
    format_type = db.Column(db.Integer, default=1, comment="格式类型 1 天,2 上下午,3 小时(字段未使用)")


class CircleUser(BaseModelIntPk):
    __tablename__ = "circle_user"
    circle_id = db.Column(db.String(32), db.ForeignKey("circle.object_id"), nullable=False)
    user_id = db.Column(db.String(32), db.ForeignKey("users.object_id"), nullable=False)
    is_organizer = db.Column(db.Boolean, default=False, comment="是否组织者")
    is_join = db.Column(db.Integer, default=0, comment="是否加入 0 未加入 1 已加入 2 已拒绝")
    __table_args__ = (
        db.UniqueConstraint("user_id", "circle_id", name="uix_user_circle"),
    )

    def to_json_circle(self, exclude_list=()):
        res = self.to_json(exclude_list=exclude_list)
        if self.circle:
            res["circle_info"] = self.circle.to_json()
        return res

    def to_json_user(self, exclude_list=()):
        res = self.to_json(exclude_list=exclude_list)
        if self.users:
            res["user_info"] = self.users.to_json()
        return res


Users.circle_user = db.relationship("CircleUser", backref="users")
Circle.circle_user = db.relationship("CircleUser", backref="circle")
Circle.trips = db.relationship("UserTrip", backref="circle")
