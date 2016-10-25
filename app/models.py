from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin
from . import db, login_manager
from datetime import datetime
import cgi
from helper_functions import random_string

class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #what for ???

tag_and_post = db.Table('tag_and_post',
                        db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
                        db.Column('post_id', db.Integer, db.ForeignKey('posts.id'))
                        )

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    preview = db.Column(db.Text)
    body = db.Column(db.Text)
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    permalink = db.Column(db.String)

    @staticmethod
    def validate_post_data(post_data):
        permalink = random_string(12)

        post_data['title'] = cgi.escape(post_data['title'])
        post_data['preview'] = cgi.escape(post_data['preview'], quote=True)
        post_data['body'] = cgi.escape(post_data['body'], quote=True)
        post_data['date'] = datetime.utcnow()
        post_data['permalink'] = permalink

        return post_data

    @classmethod
    def get_posts(cls,perpage):
        pagination = cls.query.order_by(
            cls.date.desc()).paginate(1, per_page=perpage, error_out=False)
        recent_posts=[]
        for each in pagination.items:
            adict = {}
            adict['title'] = each.title
            adict['id'] = each.id
            recent_posts.append(adict)

        return recent_posts


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tagname = db.Column(db.String(64), unique=True, index=True)
    posts = db.relationship('Post',
                            secondary=tag_and_post,
                            backref=db.backref('tags', lazy='dynamic'),
                            lazy='dynamic')

    @classmethod
    def get_tags(cls,perpage):
        pagination = cls.query.paginate(1, per_page=perpage, error_out=False)
        tags = []
        for each in pagination.items:
            tag = {}
            tag['title'] = each.tagname
            tag['count'] = each.posts.count()
            tags.append(tag)
        return tags









