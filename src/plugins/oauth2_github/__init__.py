# -*- coding: utf-8 -*-
"""
    passport.plugins.oauth2_github
    ~~~~~~~~~~~~~~

    使用GitHub登录

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

#: Importing these two modules is the first and must be done.
#: 首先导入这两个必须模块
from __future__ import absolute_import
from libs.base import PluginBase
#: Import the other modules here, and if it's your own module, use the relative Import. eg: from .lib import Lib
#: 在这里导入其他模块, 如果有自定义包目录, 使用相对导入, 如: from .lib import Lib
from flask import Blueprint, request, jsonify, g, flash, redirect, url_for
from utils.web import OAuth2, analysis_cookie, dfr
from config import PLUGINS
from libs.auth import Authentication

#：Your plug-in name must be consistent with the plug-in directory name.
#：你的插件名称，必须和插件目录名称等保持一致.
__name__        = "oauth2_github"
#: Plugin describes information. What does it do?
#: 插件描述信息,什么用处.
__description__ = "Connection GitHub with OAuth2"
#: Plugin Author
#: 插件作者
__author__      = "Mr.tao <staugur@saintic.com>"
#: Plugin Version
#: 插件版本
__version__     = "0.1" 
#: Plugin Url
#: 插件主页
__url__         = "https://www.saintic.com"
#: Plugin License
#: 插件许可证
__license__     = "MIT"
#: Plugin License File
#: 插件许可证文件
__license_file__= "LICENSE"
#: Plugin Readme File
#: 插件自述文件
__readme_file__ = "README"
#: Plugin state, enabled or disabled, default: enabled
#: 插件状态, enabled、disabled, 默认enabled
__state__       = "enabled"

name = "github"
github = OAuth2(name,
    client_id = PLUGINS[name]["APP_ID"],
    client_secret = PLUGINS[name]["APP_KEY"],
    redirect_url = PLUGINS[name]["REDIRECT_URI"],
    authorize_url = "https://github.com/login/oauth/authorize",
    access_token_url = "https://github.com/login/oauth/access_token",
    get_userinfo_url = "https://api.github.com/user"
)

plugin_blueprint = Blueprint("oauth2_github", "oauth2_github")
@plugin_blueprint.route("/login")
def login():
    """ 跳转此OAuth应用登录以授权
    此路由地址：/oauth2/github/login
    """
    return github.authorize()

@plugin_blueprint.route("/authorized")
def authorized():
    """ 授权回调路由
    此路由地址：/oauth2/github/authorized
    """
    resp = github.authorized_response()
    resp = github.url_code(resp)
    print "authorized_response:",resp
    if resp and isinstance(resp, dict) and "access_token" in resp:
        user = github.get_userinfo(resp["access_token"])
        userinfo = dict(openid=user["id"], nick_name=user["name"], gender=2, avatar=user["avatar_url"], domain_name=user["login"], signature=user["bio"])
        # 处理第三方登录逻辑
        auth = Authentication(g.mysql, g.redis)
        ip = request.headers.get('X-Real-Ip', request.remote_addr)
        uid = analysis_cookie(request.cookies.get("sessionId")).get("uid")
        goinfo = auth.oauth2_go(name=name, signin=g.signin, tokeninfo=resp, userinfo=userinfo, register_ip=ip, uid=uid)
        goinfo = dfr(goinfo)
        if goinfo["pageAction"] == "goto_signIn":
            # 未登录流程->执行登录
            auth.brush_loginlog(dict(identity_type=auth.oauth2_name2type(name), uid=uid, success=True), login_ip=ip, user_agent=request.headers.get("User-Agent"))
            return github.goto_signIn()
        elif goinfo["pageAction"] == "goto_signUp":
            # 未登录流程->执行注册绑定功能
            flash(u"去注册")
            #return github.goto_signUp()
        else:
            # 已登录流程->反馈绑定结果
            if goinfo["success"]:
                # 绑定成功，返回原页面
                flash(u"已绑定")
            else:
                flash(goinfo["msg"])
        return redirect(url_for("index"))
    else:
        flash(u'Access denied: reason=%s error=%s resp=%s' % (
            request.args['error'],
            request.args['error_description']
        ))
    return redirect(url_for("index"))

#: 返回插件主类
def getPluginClass():
    return OAuth2_Github_Main

#: 插件主类, 不强制要求名称与插件名一致, 保证getPluginClass准确返回此类
class OAuth2_Github_Main(PluginBase):
    """ 继承自PluginBase基类 """

    def register_tep(self):
        """注册模板入口, 返回扩展点名称及扩展的代码, 其中include点必须是实际的HTML文件, string点必须是HTML代码."""
        tep = {"auth_signIn_socialLogin_string": """<a href="#" title="使用GitHub账号登录"><img src="/static/images/github.png" /></a>"""}
        return tep

    def register_bep(self):
        """注册蓝图入口, 返回蓝图路由前缀及蓝图名称"""
        bep = {"prefix": "/oauth2/github", "blueprint": plugin_blueprint}
        return bep