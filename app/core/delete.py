import os
import shutil
from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import Folder, File
from ..extensions import db

def delete_file(file_id):
  file = File.query.get(file_id)
  if not file:
    return jsonify({'error': 'File not found'}), 404
  
  # Delete the file from the filesystem
  if os.path.exists(file.filepath):
    os.remove(file.filepath)
  
  db.session.delete(file)
  db.session.commit()
  
  return jsonify({'message': 'File deleted successfully'}), 200

def delete_folder(folder_id):
  folder = Folder.query.get(folder_id)
  if not folder:
    return jsonify({'error': 'Folder not found'}), 404
  
  if not folder.parent_id:
    return jsonify({'error': 'Unable to delete a mount point'}), 400
  
  folder_path = os.path.join(folder.mount_point, *folder.path_stack)
  
  # Recursively delete files and subfolders
  if os.path.exists(folder_path):
    # Delete all files in the folder
    files = File.query.filter_by(parent_id=folder_id).all()
    for file in files:
      delete_file(file.id)
    
    # Delete all subfolders
    subfolders = Folder.query.filter_by(parent_id=folder_id).all()
    for subfolder in subfolders:
      delete_folder(subfolder.id)
    
    # Finally, delete the folder itself
    shutil.rmtree(folder_path)
  
  db.session.delete(folder)
  db.session.commit()
  
  return jsonify({'message': 'Folder deleted successfully'}), 200