#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import urllib
import urllib.parse
import httplib2


class RequestClient(object):
    """请求客户端"""

    def __init__(self, endpoint):
        """
        初始化函数

        Args:
            endpoint (str): 请求的接口地址

        Returns:
            None
        """
        self.endpoint = endpoint

    def sendRequest(self, api, method, params=None, body=None, headers=None):
        """
        发送请求到指定的uri，并返回响应结果

        Args:
            api (str): 请求的api
            method (str): 请求方法，支持GET, POST等
            params (dict, optional): 请求参数，默认为None
            body (dict, optional): 请求体，默认为None
            headers (dict, optional): 请求头，默认为None

        Returns:
            tuple: 包含响应状态和响应内容的元组，响应状态为httplib2.Response对象，响应内容为bytes类型

        """
        url = "https://{}{}".format(self.endpoint, api)
        if params:
            url += "?"
            for key, value in params.items():
                url += "{}={}".format(key, urllib.parse.quote(str(value))) + "&"
        url = ''.join(x for x in url if x != ' ')  # 去除url较长python自动换行加换行符的问题
        url = url.strip('&')
        h = httplib2.Http()
        print("---method:" + str(method))
        print("---url:" + str(url))
        print("---body:" + str(json.dumps(body)))
        if isinstance(body, dict):
            body = json.dumps(body).encode("utf-8")
        resp, content = h.request(url, method, body=body, headers=headers)
        print("---resp status code:" + str(resp.get("status", "")))
        return resp, content

