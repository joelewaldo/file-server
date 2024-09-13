from datetime import datetime, timezone
from ..extensions import db

class SearchHistory(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  user = db.relationship('User', back_populates='search_history')

  term = db.Column(db.String(255), nullable=False, unique=True)
  timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))

  def __repr__(self):
    return f'<SearchHistory {self.whatthefuck} by User {self.user_id}>'