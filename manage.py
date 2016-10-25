import os
from app import create_app,db
from flask_script import Manager,Shell
from flask_migrate import Migrate, MigrateCommand
from app.helper_functions import generate_csrf_token
from flaskext.markdown import Markdown
from app.mdx_github_gists import GitHubGistExtension
from app.mdx_strike import StrikeExtension
from app.mdx_quote import QuoteExtension
from app.mdx_code_multiline import MultilineCodeExtension
from app.models import Post, Tag

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

md = Markdown(app)
md.register_extension(GitHubGistExtension)
md.register_extension(StrikeExtension)
md.register_extension(QuoteExtension)
md.register_extension(MultilineCodeExtension)

@app.template_filter('formatdate')
def format_datetime_filter(input_value, format_="%a, %d %b %Y"):
    return input_value.strftime(format_)

@app.before_request
def set_globals():
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    app.jinja_env.globals['recent_posts'] = Post.get_posts(10)
    app.jinja_env.globals['tagslist'] = Tag.get_tags(10)



manager = Manager(app)
migrate = Migrate(app, db)


manager.add_command('db',MigrateCommand)

if __name__ == '__main__':
    manager.run()
