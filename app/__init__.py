from flask import Flask
from flask_login import LoginManager
from .auth import auth_bp
from .main import main_bp
import math
# from .middleware import protect_routes
from .extensions import db

def create_app(config_class):
  app = Flask(__name__, static_folder="../static", template_folder="../templates")
  app.config.from_object(config_class)
  app.jinja_env.globals['math'] = math
    
  db.init_app(app)

  loginManager = LoginManager()
  loginManager.login_view = 'auth.login'
  loginManager.init_app(app)

  from .models.user_model import User

  @loginManager.user_loader
  def load_user(user_id):
    return User.query.get(int(user_id))

  with app.app_context():
    # Import routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')

    # Initialize db
    db.create_all()

  # protect_routes(app)

  return app