#!python3.6
# _*_ coding:utf-8 _*_
#
# @Version      :
# @Date         :
# @Author       : RedElephant
# @Introduction : model util
# dependence

import uuid


def get_uid():

    return uuid.uuid4().hex


def md5(aaa):
    aaab = aaa + "www.xxx-aaa.com"
    import hashlib
    m = hashlib.md5()
    m.update(aaab.encode("iso-8859-1"))
    return m.hexdigest()
