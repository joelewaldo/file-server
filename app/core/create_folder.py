import os
from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import Folder
from sqlalchemy.exc import IntegrityError
from ..extensions import db

def create_folder():
  folder_name = request.form.get('folder_name')
  parent_id = request.form.get('parent_id')

  if not parent_id:
    parent_id = None
  
  if not folder_name:
    return jsonify({'error': 'Folder name is required'}), 400
  
  previous_folder = Folder.query.filter_by(name=folder_name, parent_id=parent_id).first()
  
  if previous_folder:
    return jsonify({'error': 'Duplicate folder name'}), 400
  
  # Fetch current folder stack and append the new folder

  if not parent_id:
    new_path_stack = [folder_name]
    
    # Create the new folder in the database
    new_folder = Folder(name=folder_name, parent_id=None, path_stack=new_path_stack)
    db.session.add(new_folder)
    db.session.commit()
    
    # Create the folder in the filesystem
    new_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], *new_path_stack)
    if not os.path.exists(new_folder_path):
      os.makedirs(new_folder_path)
    
    return jsonify({'message': 'Folder created successfully', 'folder_id': new_folder.id}), 200

  parent_folder = Folder.query.get(parent_id)
  if not parent_folder:
    return jsonify({'error': 'Parent folder not found'}), 404

  new_path_stack = parent_folder.path_stack[:]
  new_path_stack.append(folder_name)
  
  # Create the new folder in the database
  new_folder = Folder(name=folder_name, parent_id=parent_id, path_stack=new_path_stack)
  db.session.add(new_folder)
  db.session.commit()
  
  # Create the folder in the filesystem
  new_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], *new_path_stack)
  if not os.path.exists(new_folder_path):
    os.makedirs(new_folder_path)
  
  return jsonify({'message': 'Folder created successfully', 'folder_id': new_folder.id}), 200