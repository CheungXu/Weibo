#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# github:https://github.com/tangthis

#创建Flask类应用对象，导入views视图模块
import os
from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_openid import OpenID
from flask_mail import Mail
from config import basedir

app = Flask(__name__) 
app.config.from_object('config')
db = SQLAlchemy(app)

lm = LoginManager()
lm.setup_app(app)
oid = OpenID(app,os.path.join(basedir,'tmp'))

mail = Mail(app)

from app import views, models