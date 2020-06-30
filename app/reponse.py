#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      : 1.0
# @Date         : 2020-06-30
# @Author       : RedElephant
# @Introduction : 所有响应方法
# dependence

from flask import jsonify

from app import db


def get_responde(code, msg='', data=None):
    response = jsonify({'code': code, 'msg': msg, 'data': data})
    response.status_code = 200
    return response


def custom(code=-1, msg='', data=''):
    db.session.rollback()
    res = get_responde(code, msg, data)
    return res


def success(code=200, msg='', data=''):
    res = get_responde(code, msg, data)
    return res
