from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

class Config:
  SECRET_KEY = os.getenv('SECRET_KEY', 'TOPSECRETKEY')
  UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
  CACHE_FOLDER = os.getenv('CACHE_FOLDER', 'cache/')
  ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'arw', 'dvr', 'mp4'}
  MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024  # 10 GB
  DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't', 'yes', 'y']
  SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///file_server.db')
  SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable Flask-SQLAlchemy event system to save resources

class DevelopmentConfig(Config):
  DEBUG = True

class ProductionConfig(Config):
  DEBUG = False

config = {
  'development': DevelopmentConfig,
  'production': ProductionConfig,
  'default': DevelopmentConfig
}