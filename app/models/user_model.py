from datetime import datetime, timedelta, timezone
from flask_login import UserMixin
from ..extensions import db, bcrypt

class UserSettings(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
  user = db.relationship('User', back_populates='settings')
  
  # Settings
  hashing = db.Column(db.Boolean, default=False)
  preferred_upload_folder = db.Column(db.String(255), nullable=True)
  # notifications_enabled = db.Column(db.Boolean, default=True)
  # language = db.Column(db.String(20), default='en')

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  name = db.Column(db.String(1000), nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  api_key = db.Column(db.String(128), unique=True, nullable=True)
  api_key_expiration = db.Column(db.DateTime(timezone=True), nullable=True)
  created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

  settings = db.relationship('UserSettings', back_populates='user', uselist=False)
  search_history = db.relationship('SearchHistory', back_populates='user')

  def set_password(self, password):
    self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

  def check_password(self, password):
    return bcrypt.check_password_hash(self.password_hash, password)

  def generate_api_key(self):
    self.api_key = bcrypt.generate_password_hash(self.username + str(datetime.now(timezone.utc))).decode('utf-8')
    self.api_key_expiration = datetime.now(timezone.utc) + timedelta(days=1)  # Expiration set to 24 hours
    return self.api_key