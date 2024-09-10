from .models.file_model import Folder
from .extensions import db

def get_upload_folder(current_user):
  existing_root_names = [folder.name for folder in Folder.query.filter_by(parent_id=None).all()]

  if current_user.settings.preferred_upload_folder:
    if current_user.settings.preferred_upload_folder in existing_root_names:
      return Folder.query.filter_by(name=current_user.settings.preferred_upload_folder, parent_id=None).first().name
    
  current_user.settings.preferred_upload_folder = existing_root_names[0]
  db.session.commit()
  return Folder.query.filter_by(name=current_user.settings.preferred_upload_folder, parent_id=None).first().name

def get_upload_folder_id(current_user):
  existing_root_names = [folder.name for folder in Folder.query.filter_by(parent_id=None).all()]

  if current_user.settings.preferred_upload_folder:
    if current_user.settings.preferred_upload_folder in existing_root_names:
      return Folder.query.filter_by(name=current_user.settings.preferred_upload_folder, parent_id=None).first().id

  current_user.settings.preferred_upload_folder = existing_root_names[0]
  db.session.commit()
  return Folder.query.filter_by(name=current_user.settings.preferred_upload_folder, parent_id=None).first().id
