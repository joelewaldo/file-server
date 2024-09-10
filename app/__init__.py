from flask import Flask
from flask_login import LoginManager
from .auth import auth_bp
from .main import main_bp
import math
from pathlib import Path
from collections import Counter
from .extensions import db

def create_app(config_class):
  app = Flask(__name__, static_folder="../static", template_folder="../templates")
  app.config.from_object(config_class)
  app.jinja_env.globals['math'] = math
    
  db.init_app(app)

  loginManager = LoginManager()
  loginManager.login_view = 'auth.login'
  loginManager.init_app(app)

  @loginManager.user_loader
  def load_user(user_id):
    from .models.user_model import User
    return User.query.get(int(user_id))

  with app.app_context():
    # Import routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp, url_prefix='/')

  return app

def setup_database(app):
  with app.app_context():
    # Initialize db
    db.create_all()

    from .models.file_model import Folder

    # Check for duplicates before proceeding
    upload_folder_names = {Path(folder).name for folder in app.config['UPLOAD_FOLDERS']}
    folder_name_counts = Counter(upload_folder_names)
    duplicate_folders = [name for name, count in folder_name_counts.items() if count > 1]

    if duplicate_folders:
      raise ValueError(f"Duplicate folder names found: {', '.join(duplicate_folders)}")

    for folder in app.config['UPLOAD_FOLDERS']:
      path = Path(folder)
      if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

      # Create a corresponding Folder model entry in the database
      existing_folder = Folder.query.filter_by(name=path.name, parent_id=None).first()
      if not existing_folder:
        new_folder = Folder(name=path.name, path_stack=[], mount_point=folder)
        db.session.add(new_folder)

    db.session.commit()