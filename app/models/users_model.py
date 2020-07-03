#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : users model
# dependence

from datetime import datetime, date

from sqlalchemy import func, text
from xpinyin import Pinyin

from app import db
from app.enum import UserState
from .base_model import BaseModelUuidPk, BaseModelIntPk
pinyin = Pinyin()


class Users(BaseModelUuidPk):

    user_name = db.Column(db.String(50), comment="用户名称")
    user_pinyin = db.Column(db.String(255), comment="用户拼音")
    nick_name = db.Column(db.String(50), comment="昵称")
    nick_pinyin = db.Column(db.String(255), comment="昵称拼音")
    email = db.Column(db.String(255), default='', comment="邮箱")
    phone = db.Column(db.String(255), index=True, comment="手机号")
    password = db.Column(db.String(255), comment="密码")
    device_identifier = db.Column(db.String(255), comment="设备标示")
    sex = db.Column(db.Integer, default=3, comment="性别 1 男 2 女 3未配置")
    birthday = db.Column(db.Date, index=True, comment="生日")
    entry_date = db.Column(db.DateTime, nullable=False, default=datetime.now, server_default=func.now(),
                           comment="加入的时间")
    state = db.Column(db.Integer, default=UserState.normal.value, server_default=text('0'), index=True, comment="状态")

    def to_json(self, exclude_list=()):
        res = super(Users, self).to_json(exclude_list=["password"])
        return res

    def to_json_friend(self, exclude_list=()):
        res = self.to_json(exclude_list=exclude_list)
        if self.to_friend:
            res["user_friend_info"] = [friend.to_json() for friend in self.to_friend]
        return res

    def set_pinyin(self, name):
        try:
            pinyin_name = pinyin.get_pinyin(name, '')
        except Exception:
            pinyin_name = ""
        return pinyin_name


class UserTrip(BaseModelUuidPk):

    __tablename__ = "user_trip"
    user_id = db.Column(db.String(32), db.ForeignKey("users.object_id"), nullable=False)
    trip_date = db.Column(db.Date, default=date.today, comment="行程日期")
    start_time = db.Column(db.DateTime, default=datetime.now, server_default=func.now(),
                           comment="行程开始时间")
    end_time = db.Column(db.DateTime, default=datetime.now, server_default=func.now(),
                         comment="行程结束时间")
    name = db.Column(db.String(255), default="就不告诉你", comment="行程名称")
    is_adjust = db.Column(db.Boolean, default=True, comment="是否可调整")
    is_see = db.Column(db.Boolean, default=True, comment="是否可见")


Users.trips = db.relationship("UserTrip", backref="user")


class UserFriend(BaseModelIntPk):

    __tablename__ = "user_friend"
    user_id = db.Column(db.String(32), db.ForeignKey("users.object_id"), nullable=False)
    friend_id = db.Column(db.String(32), db.ForeignKey("users.object_id"), nullable=False)
    content = db.Column(db.String(500), comment="申请附加信息")
    flag = db.Column(db.Integer, default=0, comment="验证标志 0 已申请 1 同意 2 已拒绝 3 待验证")
    verify_message = db.Column(db.String(50), comment="验证附加信息")

    __table_args__ = (
        db.UniqueConstraint("user_id", "friend_id", name="uix_user_friend"),
    )

    def to_json_with_user(self, exclude_list=()):
        res = self.to_json(exclude_list)
        if self.user_friend:
            res["friend_info"] = self.user_friend.to_json()
        return res


Users.friend = db.relationship("UserFriend", backref="user", foreign_keys="UserFriend.user_id")
Users.to_friend = db.relationship("UserFriend", backref="user_friend", foreign_keys="UserFriend.friend_id")
