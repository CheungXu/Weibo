#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# github:https://github.com/tangthis
# 使用Flask-WTF创建表单
from flask_wtf import FlaskForm
from wtforms import StringField,BooleanField,TextAreaField
from wtforms.validators import DataRequired,Length

#从Form类继承
class LoginForm(FlaskForm):
	openid = StringField('openid',validators = [DataRequired()])
	remember_me = BooleanField('remember_me',default = False)

class EditForm(FlaskForm):
	
	nickname = StringField('nickname', validators = [DataRequired()])
	about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 140)])

	def __init__(self,original_nickname,*args,**kwargs):
		FlaskForm.__init__(self,*args,**kwargs)
		self.original_nickname = original_nickname

	def validate(self):
		if not FlaskForm.validate(self):
			return False
		if self.nickname.data == self.original_nickname:
			return True

		user = User.query.filter_by(nickname = self.nickname.data).first()
		if user != None:
			self.nickname.errors.append('This nickname is already in use. Please choose another one.')
			return False
		return True

class PostForm(FlaskForm):
	post = StringField('post',validators = [DataRequired()])