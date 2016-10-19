#-*- encoding:utf-8 -*-
from . import main
from flask_login import login_required, current_user
import cgi
from flask import  render_template, abort, url_for, request, flash, session, redirect, current_app
# from ..models import User, Role, Permission, Post
from .. import db
# from .forms import EditProfileAdminForm, EditProfileForm, PostForm
# from ..decorators import admin_required
from ..helper_functions import extract_tags
from ..models import Post, Tag
import sqlite3
from app.models import Post
@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.date.desc()).paginate(
        page, per_page=5,
        error_out=False)
    posts = []
    for eachpost in pagination.items:
        post = {}
        post['id'] = eachpost.id
        post['title'] = eachpost.title
        post['date'] = eachpost.date
        post['author'] = eachpost.author.username
        post['preview'] = eachpost.preview
        post['body'] = eachpost.body
        taglist = []
        for eachtag in eachpost.tags.all():
            taglist.append(eachtag.tagname)
        post['tags'] = taglist
        posts.append(post)

    return render_template('posts.html', posts=posts,
                           pagination=pagination)

@main.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    error = False
    error_type = 'validate'
    if request.method == 'POST':
        post_title = request.form.get('post-title').strip()
        post_full = request.form.get('post-full')

        if not post_title or not post_full:
            error = True
        else:
            tags = cgi.escape(request.form.get('post-tags'))
            tags_array = extract_tags(tags)
            post_data = {'title': post_title,
                         'preview': request.form.get('post-short'),
                         'body': post_full,
                         'tags': tags_array,
                         'author': current_user.username}
            new_post_data = Post.validate_post_data(post_data)
            if request.form.get('post-preview') == '1':
                session['post-preview'] = new_post_data
                session[
                    'post-preview']['action'] = 'edit' if request.form.get('post-id') else 'add'
                if request.form.get('post-id'): #for edit_post
                    session[
                        'post-preview']['post-id'] = int(request.form.get('post-id'))
                    session[
                        'post-preview']['redirect'] = url_for('main.post_edit', id=request.form.get('post-id'))
                else:
                    session['post-preview']['redirect'] = url_for('main.new_post')
                return redirect(url_for('main.post_preview'))
            else:
                session.pop('post-preview', None)

                if request.form.get('post-id'):
                    id = int(request.form.get('post-id'))
                    post = Post.query.get_or_404(id)
                    # db = r'D:\virtualenv\flasky\MyWorldOfCode\data_dev.sqlite'
                    # conn = sqlite3.connect(db)
                    # cur = conn.cursor()
                    # update_sql = "'UPDATE posts SET body=? WHERE posts.id = ?"
                    for each in post.tags.all():
                        post.tags.remove(each)
                    try:
                        post.title=new_post_data['title']
                        post.preview=new_post_data['preview']
                        post.body=new_post_data['body']
                        post.permalink=new_post_data['permalink']
                        post.author=current_user._get_current_object()
                        if tags_array:
                            for each in tags_array:
                                if Tag.query.filter_by(tagname=each).first():
                                    post.tags.append(Tag.query.filter_by(tagname=each).first())
                                else:
                                    tag = Tag(tagname=each)
                                    post.tags.append(tag)
                        db.session.add(post)
                        flash('Post updated!', 'success')
                    except:
                        error = True
                        error_type = 'post'
                        flash('Updating post error..', 'error')
                    return redirect(url_for('main.post_edit', id=id))
                    # response = Post.edit_post(
                    #     request.form['post-id'], post)
                    # if not response['error']:
                    #     flash('Post updated!', 'success')
                    # else:
                    #     flash(response['error'], 'error')
                    # return redirect(url_for('posts'))
        #         else:
        #     response = Post.create_new_post(post)

            # post_data['title'] = cgi.escape(post_data['title'])
            # post_data['preview'] = cgi.escape(post_data['preview'], quote=True)
            # post_data['body'] = cgi.escape(post_data['body'], quote=True)
            # post_data['date'] = datetime.datetime.utcnow()
            # post_data['permalink'] = permalink
            # try:
            #     post = Post(title=new_post_data['title'],
            #                 preview=new_post_data['preview'],
            #                 body=new_post_data['body'],
            #                 date=new_post_data['date'],
            #                 permalink=new_post_data['permalink'],
            #                 author = current_user._get_current_object())
            #     for each in tags_array:
            #         tag = Tag(tagname=each)
            #         post.tags.append(tag)
            #     db.session.add(post)
            #     flash('New post created!', 'success')
                else:
                    try:
                        post = Post(title=new_post_data['title'],
                                    preview=new_post_data['preview'],
                                    body=new_post_data['body'],
                                    permalink=new_post_data['permalink'],
                                    author = current_user._get_current_object())
                        if tags_array:
                            for each in tags_array:
                                if Tag.query.filter_by(tagname=each).first():
                                    post.tags.append(Tag.query.filter_by(tagname=each).first())
                                else:
                                    tag = Tag(tagname=each)
                                    post.tags.append(tag)
                        db.session.add(post)
                        flash('New post created!', 'success')
                    except:
                        error = True
                        error_type = 'post'
                        flash('Adding post error..', 'error')
            # if response['error']:
            #     error = True
            #     error_type = 'post'
            #     flash(response['error'], 'error')
            # else:
            #     flash('New post created!', 'success')
    else:
        if session.get('post-preview') and session['post-preview']['action'] == 'edit':
            session.pop('post-preview', None)
    return render_template('new_post.html',
                           error=error,
                           error_type=error_type)



# post_edit', id=request.form.get('post-id'
@main.route('/post_edit/id=<int:id>')
@login_required
def post_edit(id):
    post = Post.query.get_or_404(id)
    post_data = {}
    post_data['title'] = post.title
    post_data['preview'] = post.preview
    post_data['body'] = post.body
    alist = []
    for each in post.tags.all():
        alist.append(each.tagname)
    post_data['tags'] = ','.join(alist)

    return render_template('edit_post.html', post_data=post_data, id=id)

@main.route('/post_delete/id=<int:id>')
@login_required
def post_delete(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    return redirect(url_for('main.index'))

@main.route('/each_post/<int:id>')
def each_post(id):
    post = Post.query.get_or_404(id)
    tags = []
    for each in post.tags.all():
        tags.append(each.tagname)
    return render_template('each_post.html', post=post, tags=tags)

@main.route('/tag/<tag>')
def posts_by_tag(tag):
    page = request.args.get('page', 1, type=int)
    tag = Tag.query.filter_by(tagname=tag).first()
    posts_of_tag = tag.posts.all()
    posts=[]
    for eachpost in posts_of_tag:
        post = {}
        post['id'] = eachpost.id
        post['title'] = eachpost.title
        post['date'] = eachpost.date
        post['author'] = eachpost.author.username
        post['preview'] = eachpost.preview
        post['body'] = eachpost.body
        taglist = []
        for eachtag in eachpost.tags.all():
            taglist.append(eachtag.tagname)
        post['tags'] = taglist
        posts.append(post)

    return render_template('posts.html', posts=posts,
                           pagination=None)






@main.route('/post_preview')
@login_required
def post_preview():
    post = session.get('post-preview')
    return render_template('preview.html', post=post, meta_title='Preview post::' + post['title'])

# @main.route('/user/<username>')
# def user(username):
#     user = User.query.filter_by(username=username).first_or_404()
#     return render_template('user.html', user=user)
#
# @main.route('/edit-profile', methods=['GET', 'POST'])
# @login_required
# def edit_profile():
#     form = EditProfileForm()
#     if form.validate_on_submit():
#         current_user.name = form.name.data
#         current_user.location = form.location.data
#         current_user.about_me = form.about_me.data
#         db.session.add(current_user)
#         flash('Your profile has been updated.')
#         return redirect(url_for('.user', username=current_user.username)) #how about main.user???
#     form.name.data = current_user.name
#     form.location.data = current_user.location
#     form.about_me.data = current_user.about_me
#     return render_template('edit_profile.html', form=form)
#
#
# @main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def edit_profile_admin(id): #url_for('', id = user.id) id is int or str???
#     user = User.query.get_or_404(id) #User.query.filter_by(id=id).first_or_404()???
#     form = EditProfileAdminForm(user=user)
#     if form.validate_on_submit():
#         user.email = form.email.data
#         user.username = form.username.data
#         user.confirmed = form.confirmed.data
#         user.role = Role.query.get(form.role.data) #form.role.data???
#         user.name = form.name.data
#         user.location = form.location.data
#         user.about_me = form.about_me.data
#         db.session.add(user)
#         flash('The profile has been updated.')
#         return redirect(url_for('.user', username=user.username))
#     form.email.data = user.email
#     form.username.data = user.username
#     form.confirmed.data = user.confirmed
#     form.role.data = user.role_id #form.role.data
#     form.name.data = user.name
#     form.location.data = user.location
#     form.about_me.data = user.about_me
#     return render_template('edit_profile.html', form=form, user=user)
#
# @main.route('/post/<int:id>')
# def post(id):
#     post = Post.query.get_or_404(id)
#     return render_template('post.html', posts=[post])
#
# @main.route('/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit(id):
#     post = Post.query.get_or_404(id)
#     if current_user != post.author and \
#             not current_user.can(Permission.ADMINISTER):
#         abort(403)
#     form = PostForm()
#     if form.validate_on_submit():
#         post.body = form.body.data
#         db.session.add(post)
#         flash('The post has been updated.')
#         return redirect(url_for('.post', id=post.id)) #main, so .post???not main.post???
#     form.body.data = post.body
#     return render_template('edit_post.html', form=form)
#
