from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import File, Folder
import os
from ..extensions import db

def rename_file(file_id, parent_id):
  data = request.get_json()
  new_filename = data.get('name')
  file = File.query.get(file_id)

  if not file:
    return jsonify({'error': 'File not found'}), 404

  # Check if another file with the same name exists in the same parent folder
  existing_file = File.query.filter_by(parent_id=parent_id, filename=new_filename).first()
  
  if existing_file and file.id != existing_file.id:
    return jsonify({'error': 'A file with that name already exists in the parent folder'}), 400

  # Construct the old and new file paths
  old_filepath = file.filepath
  new_filepath = os.path.join(os.path.dirname(old_filepath), new_filename)

  # Rename the file on the filesystem
  try:
    os.rename(old_filepath, new_filepath)
  except Exception as e:
    return jsonify({'error': f'Failed to rename file on the filesystem: {str(e)}'}), 500

  # Update the filename and filepath in the database
  file.filename = new_filename
  file.filepath = new_filepath
  db.session.commit()

  return jsonify({'message': 'File renamed successfully'}), 200

def rename_folder(folder_id, parent_id):
  data = request.get_json()
  new_folder_name = data.get('name')
  folder = Folder.query.get(folder_id)

  if not folder:
    return jsonify({'error': 'Folder not found'}), 404

  # Check for existing folder with the same name
  existing_folder = Folder.query.filter_by(parent_id=parent_id, name=new_folder_name).first()
  if existing_folder and folder.id != existing_folder.id:
    return jsonify({'error': 'A folder with that name already exists in the parent folder'}), 400

  # Construct old and new folder paths
  old_folder_path = os.path.join(folder.mount_point, *folder.path_stack)
  new_folder_path = os.path.join(os.path.dirname(old_folder_path), new_folder_name)

  # Rename folder on the filesystem
  try:
    os.rename(old_folder_path, new_folder_path)
  except Exception as e:
    return jsonify({'error': f'Failed to rename folder on the filesystem: {str(e)}'}), 500

  # Update folder name and path stack
  folder.name = new_folder_name
  new_path_stack = folder.path_stack[:]
  new_path_stack.pop()
  new_path_stack.append(new_folder_name)
  folder.path_stack = new_path_stack  # Replace the last item with the new name

  # Update paths of files and folders within this folder
  update_paths_in_folder(folder, old_folder_path, new_folder_path)

  db.session.commit()  # Commit all changes at once

  return jsonify({'message': 'Folder renamed successfully'}), 200

def update_paths_in_folder(folder, old_folder_path, new_folder_path):
  # Update all child files
  files = File.query.filter_by(parent_id=folder.id).all()
  for file in files:
    old_file_path = file.filepath
    new_file_path = old_file_path.replace(old_folder_path, new_folder_path, 1)

    # Update file path in the database
    file.filepath = new_file_path

  # Update all child folders
  subfolders = Folder.query.filter_by(parent_id=folder.id).all()
  for subfolder in subfolders:
    old_subfolder_path = os.path.join(folder.mount_point, *subfolder.path_stack)
    new_subfolder_path = old_subfolder_path.replace(old_folder_path, new_folder_path, 1)

    # Update subfolder mount point and path stack in the database
    subfolder.mount_point = folder.mount_point
    new_folder_stack = folder.path_stack[:]
    new_folder_stack.append(subfolder.name)
    subfolder.path_stack = new_folder_stack

    # Recursively update paths in the subfolder
    update_paths_in_folder(subfolder, old_subfolder_path, new_subfolder_path)