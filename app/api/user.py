#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : users
# dependence
from flask import request

from app.api import api
from app.models import Users
from app.decorators import check_request_params
