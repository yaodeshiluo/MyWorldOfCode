from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from datetime import datetime
import cgi
from helper_functions import random_string
# import hashlib
# import bleach
# from markdown import markdown
#
#
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0x80
#
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
#
#     @staticmethod
#     def insert_roles():
#         roles = {
#             'User' : (Permission.FOLLOW |
#                       Permission.COMMENT |
#                       Permission.WRITE_ARTICLES, True),
#             'Moderator' : (Permission.FOLLOW |
#                            Permission.COMMENT |
#                            Permission.WRITE_ARTICLES |
#                            Permission.MODERATE_COMMENTS, False),
#             'Administrator' : (0xff, False)
#         }
#         for r in roles:
#             role = Role.query.filter_by(name=r).first()
#             if role is None:
#                 role = Role(name=r)
#             role.permissions = roles[r][0]
#             role.default = roles[r][1]
#             db.session.add(role)
#         db.session.commit()
#     def __repr__(self):
#         return '<Role %r>' % self.name
#
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
#     name = db.Column(db.String(64))
#     location = db.Column(db.String(64))
#     about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow) #is DateTime not Datetime
#     avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
#
#
#     @staticmethod
#     def generate_fake(count=100):
#         from sqlalchemy.exc import IntegrityError
#         from random import seed
#         import forgery_py
#
#         seed()
#         for i in range(count):
#             u = User(email=forgery_py.internet.email_address(),
#                      username=forgery_py.internet.user_name(True),
#                      password=forgery_py.lorem_ipsum.word(),
#                      confirmed=True,
#                      name=forgery_py.name.full_name(),
#                      location=forgery_py.address.city(),
#                      about_me=forgery_py.lorem_ipsum.sentence(),
#                      member_since=forgery_py.date.date(True))
#             db.session.add(u)
#             try:
#                 db.session.commit()
#             except IntegrityError:
#                 db.session.rollback()
#
#
#     def __init__(self, **kwargs):
#         super(User, self).__init__(**kwargs)
#         if self.role is None:
#             if self.email == current_app.config['FLASKY_ADMIN']:
#                 self.role = Role.query.filter_by(permissions=0xff).first()
#             if self.role is None:
#                 self.role = Role.query.filter_by(default=True).first()
#         if self.email is not None and self.avatar_hash is None:
#             self.avatar_hash = hashlib.md5(
#                 self.email.encode('utf-8')).hexdigest()
#
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
#
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
#
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
#
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
#
#     def generate_reset_token(self, expiration=3600):
#         s = Serializer(current_app.config['SECRET_KEY'], expiration)
#         return s.dumps({'reset': self.id})
#
#     def reset_password(self, token, new_password):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             data = s.loads(token)
#         except:
#             return False
#         if data.get('reset') != self.id:
#             return False
#         self.password = new_password
#         db.session.add(self)
#         return True
#
#     def generate_email_change_token(self, new_email, expiration=3600):
#         s = Serializer(current_app.config['SECRET_KEY'], expiration)
#         return s.dumps({'change_email': self.id, 'new_email': new_email})
#
#     def change_email(self, token):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             data = s.loads(token)
#         except:
#             return False
#         if data.get('change_email') != self.id:
#             return False
#         new_email = data.get('new_email')
#         if new_email is None:
#             return False
#         if self.query.filter_by(email=new_email).first() is not None:
#             return False
#         self.email = new_email
#         db.session.add(self)
#         return True
#
#     def can(self, permissions):
#         return self.role is not None and \
#                (self.role.permissions & permissions) == permissions
#
#     def is_administrator(self):
#         return self.can(Permission.ADMINISTER)
#
#     def __repr__(self):
#         return '<User %r>' %self.username
#
#     def ping(self):
#         self.last_seen = datetime.utcnow()
#         db.session.add(self)
#
#     def gravatar(self, size=100, default='idention', rating='g'):
#         if request.is_secure:
#             url = 'https://secure.gravatar.com/avatar'
#         else:
#             url = 'http://www.gravatar.com/avatar'
#         hash = self.avatar_hash or hashlib.md5(
#             self.email.encode('utf-8')).hexdigest()
#         return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
#             url=url, hash=hash, size=size, default=default, rating=rating)
#
#
#
#
#
# class AnonymousUser(AnonymousUserMixin):
#     def can(self, permissions):
#         return False
#
#     def is_administrator(self):
#         return False
#
# login_manager.anonymous_user = AnonymousUser #in models,define anonymous_user
#
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
#     body_html = db.Column(db.Text)
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    permalink = db.Column(db.String)

    @staticmethod
    def validate_post_data(post_data):
        permalink = random_string(12)
        # exp = re.compile('\W')
        # whitespace = re.compile('\s')
        # temp_title = whitespace.sub("_", post_data['title'])
        # permalink = exp.sub('', temp_title)

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
        # pagination = Post.query.order_by(Post.date.desc()).paginate(
        #     page, per_page=5,
        #     error_out=False)
        recent_posts=[]
        for each in pagination.items:
            adict = {}
            adict['title'] = each.title
            adict['id'] = each.id
            recent_posts.append(adict)

        return recent_posts




#     @staticmethod
#     def generate_fake(count=100):
#         from random import seed, randint
#         import forgery_py
#
#         seed() #what is seed()???
#         user_count = User.query.count()
#         for i in range(count):
#             u = User.query.offset(randint(0,user_count - 1 )).first()
#             p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,5)),
#                      timestamp=forgery_py.date.date(True),
#                      author=u)
#             db.session.add(p)
#             db.session.commit() #if all together???
#
#     @staticmethod
#     def on_changed_body(target, value, oldvalue, initiator):
#         allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
#                         'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
#                         'h1', 'h2', 'h3', 'p']
#
#         target.body_html = bleach.linkify(bleach.clean(
#             markdown(value, output_format='html'),
#             tags=allowed_tags, strip=True))
#
# db.event.listen(Post.body, 'set', Post.on_changed_body) #'set'???

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









