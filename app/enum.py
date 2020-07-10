#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : 枚举
# dependence
from enum import IntEnum


class UserState(IntEnum):
    normal = 1  # 正常
    quit = 2    # 注销


class CheckType(IntEnum):
    int = 0
    email = 1
    phone = 2
    noEmoji = 3
    json = 4
    date = 5
    datetime = 6
    float = 7
    password = 8
    time = 9
    other = 999


class NotifyType(IntEnum):
    system = 0
    friend = 1
    circle = 2
    schedule = 3
