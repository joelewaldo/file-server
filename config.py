from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

class Config:
  SECRET_KEY = os.getenv('SECRET_KEY', 'TOPSECRETKEY')
  UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
  CACHE_FOLDER = os.getenv('CACHE_FOLDER', 'cache/')
  ALLOWED_EXTENSIONS = {
    # Text extensions
    'txt', 'pdf', 'doc', 'docx', 'rtf', 'odt', 'md', 'log', 'csv', 'json', 'xml', 'yaml', 'yml', 'tex',

    # Image extensions
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'webp', 'arw',
    
    # Video extensions
    'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'mpeg', 'mpg',
    
    # Audio extensions
    'mp3', 'wav', 'aac', 'ogg', 'flac', 'wma', 'm4a',

    # Programming language extensions
    'py', 'js', 'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'rb', 'php', 'html', 'css', 'scss', 'less',
    'go', 'rs', 'swift', 'kt', 'kts', 'm', 'mm', 'sh', 'bat', 'ps1', 'r', 'pl', 'pm', 'lua',
    'sql', 'ts', 'jsx', 'tsx', 'vue', 'xml', 'jsp', 'asp', 'aspx', 'mdx', 'erl', 'ex', 'exs',
    'coffee', 'dart', 'jsonnet', 'tf', 'yaml', 'yml', 'ini', 'gradle', 'sbt', 'vb', 'fs', 'fsx',
    'd', 'nim', 'pas', 'pp', 'scala', 'hs', 'lhs', 'elm', 'clj', 'cljs', 'edn', 'lisp', 'cl',
    'vhdl', 'verilog', 'hdl', 'sv', 's', 'asm', 'nasm', 'tsv', 'xsl', 'xslt', 'rss', 'atom', 'cgi',
    'php3', 'php4', 'php5', 'php7', 'phtml', 'tpl'
  }
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