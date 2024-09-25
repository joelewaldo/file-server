from flask import jsonify, request
import os
import mimetypes
import hashlib
from pathlib import Path
from collections import Counter
from app.models.file_model import Folder, File
from flask import current_app as app
from ..extensions import db

def update_hashing(current_user):
  data = request.get_json()
  hashing = data.get('hashing', False)
  
  # Update the user's settings
  current_user.settings.hashing = hashing
  db.session.commit()

  return jsonify({'success': True}), 200

def update_preferred_upload_folder(current_user):
  data = request.get_json()
  preferred_upload_folder = data.get('preferred_upload_folder', "")

  current_user.settings.preferred_upload_folder = preferred_upload_folder
  db.session.commit()

  return jsonify({'success': True}), 200

def restore_db():
  def add_folder_to_db(mount_point, folder_path, parent_id=None):
    folder_name = os.path.basename(folder_path)
    
    # Check if the folder already exists in the database
    existing_folder = Folder.query.filter_by(name=folder_name, parent_id=parent_id).first()
    if existing_folder:
      return existing_folder
    
    # Create a new folder in the database
    new_folder = Folder(name=folder_name, parent_id=parent_id, mount_point=mount_point)
    if parent_id:
      parent_folder = Folder.query.get(parent_id)
      new_folder.path_stack = parent_folder.path_stack[:] + [folder_name]
    else:
      new_folder.path_stack = [folder_name]

    db.session.add(new_folder)
    db.session.commit()
    return new_folder

  def add_file_to_db(file_path, parent_folder):
    filename = os.path.basename(file_path)
    
    # Check if the file already exists in the database
    file_hash = get_file_hash(file_path)
    existing_file = File.query.filter_by(file_hash=file_hash).first()
    if existing_file:
      return existing_file
    
    # Calculate file size and mimetype
    file_size = os.path.getsize(file_path)
    mimetype = mimetypes.guess_type(filename)[0]
    
    # Create a new file in the database
    new_file = File(
        filename=filename,
        filepath=file_path,
        file_hash=file_hash,
        file_size=file_size,
        mimetype=mimetype,
        parent_id=parent_folder.id
    )
    db.session.add(new_file)
    db.session.commit()
    return new_file

  def get_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
      while True:
        chunk = f.read(8192)
        if not chunk:
          break
        hasher.update(chunk)
    return hasher.hexdigest()

  # Iterate over the root upload folders defined in the app configuration
  for root_folder in app.config['UPLOAD_FOLDERS']:
    for foldername, subfolders, filenames in os.walk(root_folder):
      # Add the current folder to the database
      relative_path = os.path.relpath(foldername, root_folder)
      path_stack = relative_path.split(os.sep) if relative_path != "." else []

      if foldername == root_folder:
        parent_folder = None
      else:
        parent_folder = Folder.query.filter_by(mount_point=root_folder, path_stack=path_stack[:-1]).first()
      
      current_folder = add_folder_to_db(root_folder, foldername, parent_folder.id if parent_folder else None)
      
      # Add files in the current folder to the database
      for filename in filenames:
        file_path = os.path.join(foldername, filename)
        add_file_to_db(file_path, current_folder)

  return jsonify({'success': True}), 200

def delete_storage_records():
  try:
    db.session.query(File).delete()
    db.session.query(Folder).delete()

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

    return jsonify({'success': True}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({'success': False}), 400
  
def clear_cache():
  """Clear the cache directory by removing all cached thumbnail files."""
  cache_folder = app.config.get('CACHE_FOLDER', 'cache')
  
  # Check if the cache directory exists
  if os.path.exists(cache_folder):
    # Iterate over all files in the cache directory and remove them
    for filename in os.listdir(cache_folder):
      file_path = os.path.join(cache_folder, filename)
      try:
        if os.path.isfile(file_path):
          os.remove(file_path)
      except Exception as e:
        app.logger.error(f"Error removing file {file_path}: {e}")
  else:
      app.logger.warning("Cache folder does not exist.")

  return jsonify({'success': True}), 200