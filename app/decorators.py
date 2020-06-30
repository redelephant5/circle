#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : 装饰器工具
# dependence
import re
import json
from datetime import datetime

from functools import wraps
from flask import request

from app.enum import CheckType
from app.reponse import custom


def check_request_params(**checks):
    def check_request_params_fun(func=None):
        @wraps(func)
        def verify_fun(*args, **kwargs):
            errors = []
            for k, v in checks.items():
                name = v[0]
                if request.method in ["POST", "PUT", "DELETE"]:
                    value = request.form.get(k)
                else:
                    value = request.args.get(k)
                isexist = v[1]
                check = v[2]
                error, res = request_params_value_check(name, isexist, value, check)
                if error:
                    errors.append(error)
                kwargs[k] = res
            if errors:
                return custom(code=777, msg=','.join(errors))
            return func(*args, **kwargs)

        return verify_fun
    return check_request_params_fun


def request_params_value_check(name, isexist, value, check):
    res = value
    if isexist:
        if not value and not isinstance(value, int):
            return "%s不能为空" % name, res
    if check == CheckType.int:
        if value is not None:
            try:
                res = int(value)
            except Exception:
                return "%s应为整数" % name, res
    elif check == CheckType.email:
        if value and not re.compile(r'^[a-zA-Z0-9_]+@[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+$').match(value):
            return "%s应为email格式" % name, res
    elif check == CheckType.phone:
        if value and not re.compile(r'^1\d{10}$').match(value):
            return "%s应为手机格式" % name, res
    elif check == CheckType.noEmoji:
        if value and not re.compile(r'^[a-zA-Z0-9\u4E00-\u9FA5]+$').match(value):
            return "%s包含非法字符" % name, res
    elif check == CheckType.json:
        if value:
            try:
                res = json.loads(value)
            except Exception:
                return "%s应为json格式" % name, res
    elif check == CheckType.date:
        if value:
            try:
                res = datetime.strptime(value, "%Y-%m-%d")
            except Exception:
                return "%s应为date格式" % name, res
    elif check == CheckType.datetime:
        if value:
            try:
                if len(value) == 15:
                    res = datetime.strptime(value, "%Y-%m-%d %H:%M")
                else:
                    res = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return "%s应为datetime格式" % name, res
    elif check == CheckType.float:
        if value:
            try:
                res = float(value)
            except Exception:
                return "%s应为float格式" % name, res
    elif check == CheckType.time:
        if value:
            try:
                if len(value) == 5:
                    res = datetime.strptime(value, "%H:%M")
                else:
                    res = datetime.strptime(value, "%H:%M:%S")
            except Exception:
                return "%s应为time格式" % name, res
    return None, res
