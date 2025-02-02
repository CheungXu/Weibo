#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# github:https://github.com/tangthis

#编写视图功能


from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app,db,lm,oid
from .models import User, Post, ROLE_USER,ROLE_ADMIN
from .forms import LoginForm,EditForm,PostForm
from datetime import datetime
from config import POSTS_PER_PAGE

@lm.user_loader
def load_user(id):
	return User.query.get(id)

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>',methods = ['GET','POST'])
@login_required
def index(page = 1):
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body = form.post.data ,timestamp = datetime.utcnow(),author = g.user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
	posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
	return render_template('index.html',
			title = 'Home',
			form = form,
			posts = posts)

@app.route('/login',methods = ['GET' , 'POST'])
@oid.loginhandler #它告诉Flask-OpenID这是我们的登录视图函数。 
def login():
	if g.user is not None and g.user.is_authenticated: #登录过就直接跳转到index
	#全局变量g是Flask设置的，在一个request生命周期中，用来存储和共享数据的变量。所以我猜你已经想到了，我们将把已经登录的用户放到g变量里。
		return redirect(url_for('index'))

	form = LoginForm()
	#接收参数
	if form.validate_on_submit():
		session['remember_me'] = form.remember_me.data
		print('Login requested for OpenID="' + form.openid.data + '", remember_me='+ str(form.remember_me.data))
		return oid.try_login(form.openid.data,ask_for=['nickname','email'])
		#通过Flask-OpenID来执行用户认证
	return render_template(
			'login.html',
			title = 'Sign In' , 
			form = form,
			providers = app.config['OPENID_PROVIDERS']
			)

#登录回调方法
@oid.after_login
def after_login(resp): #传给after_login方法的resp参数包含了OpenID provider返回的一些信息。
	if resp.email is None or resp.email == "":
		flash('Invalid login.Please try again.')
		redirect(url_for("login"))
	user = User.query.filter_by(email = resp.email).first()
	if user is None:
		nickname = resp.nickname
		if nickname is None or nickname == "":
			nickname = resp.email.split('@')[0]
		nickname = User.make_unique_nickname(nickname)
		user = User(nickname = nickname,email = resp.email,role = ROLE_USER)
		db.session.add(user)
		db.session.commit()
		# make the user follow self
		follow1 = user.follow(user);
		#print('==================',follow1)
		db.session.add(follow1)
		db.session.commit()
	remember_me = False
	if 'remember_me' in session:
		remember_me = session['remember_me']
		session.pop('remember_me',None)
	login_user(user,remember = remember_me)
	return redirect(request.args.get('next') or url_for('index'))

#任何一个被before_request装饰器装饰的方法将会在每次request请求被收到时提前与view方法执行
@app.before_request
def before_request():
	g.user = current_user
	if g.user.is_authenticated:
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('index'))



@app.route("/user/<nickname>")
@app.route("/user/<nickname>/<int:page>")
@login_required
def user(nickname,page = 1):
	user = User.query.filter_by(nickname = nickname).first()
	if user == None:
		flash('不存在用户:' + nickname + '!')
		return redirect(url_for('index'))
	posts = user.posts.paginate(page,POSTS_PER_PAGE,False)
	return render_template('user.html',
			user = user,
			posts = posts)


@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.nickname)
	if form.validate_on_submit():
		g.user.nickname = form.nickname.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		flash('Your changes have been saved.')
		return redirect(url_for('edit'))
	else:
		form.nickname.data = g.user.nickname
		form.about_me.data = g.user.about_me
	return render_template('edit.html',form = form)

@app.route('/follow/<nickname>')
def follow(nickname):
	user = User.query.filter_by(nickname = nickname).first()
	if user == None:
		flash('User ' + nickname + ' not found.')
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t follow yourself!')
		return redirect(url_for('user', nickname = nickname))
	u = g.user.follow(user)
	if u is None:
		flash('Cannot follow ' + nickname + '.')
		return redirect(url_for('user', nickname = nickname))
		db.session.add(u)
		db.session.commit()
		flash('You are now following ' + nickname + '!')
	return redirect(url_for('user', nickname = nickname))

@app.route('/unfollow/<nickname>')
def unfollow(nickname):
	user = User.query.filter_by(nickname = nickname).first()
	if user == None:
		flash('User ' + nickname + ' not found.')
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t unfollow yourself!')
		return redirect(url_for('user', nickname = nickname))
	u = g.user.unfollow(user)
	if u is None:
		flash('Cannot unfollow ' + nickname + '.')
		return redirect(url_for('user', nickname = nickname))
	db.session.add(u)
	db.session.commit()
	flash('You have stopped following ' + nickname + '.')
	return redirect(url_for('user', nickname = nickname))


'''
@app.errorhandler(404)
def internal_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500
'''