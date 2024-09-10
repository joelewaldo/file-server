from datetime import datetime, timezone
from ..extensions import db # Import the SQLAlchemy instance

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    mount_point = db.Column(db.String(255), nullable=False)
    path_stack = db.Column(db.PickleType, nullable=False, default=[])
    
    def __repr__(self):
        return f'<Folder {self.name}>'

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    filepath = db.Column(db.String(120), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)
    tags = db.Column(db.String(120), nullable=True)
    upload_date = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    file_size = db.Column(db.Integer)  # Size in bytes
    mimetype = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)

    def __repr__(self):
        return f'<File {self.filename}>'