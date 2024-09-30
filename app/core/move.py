import os
import shutil
from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import Folder, File
from ..extensions import db

def move_file(file_id, target_folder_id):
  # Get file and target folder from the database
  file = File.query.get(file_id)
  target_folder = Folder.query.get(target_folder_id)

  if not file or not target_folder or not target_folder_id or not file_id:
    return jsonify({"error": "File or target folder not found"}), 404

  # Construct the new file path
  old_filepath = file.filepath
  filename = os.path.basename(old_filepath)
  new_filepath = os.path.join(target_folder.mount_point, *target_folder.path_stack, filename)

  # Check if a file with the same name already exists in the target folder

  existing_file = File.query.filter_by(parent_id=target_folder_id, filename=file.filename).first()

  if os.path.exists(new_filepath or existing_file):
    return jsonify({"error": "A file with the same name already exists in the target folder"}), 409

  # Move the file on the filesystem
  try:
    shutil.move(old_filepath, new_filepath)
  except Exception as e:
    return jsonify({"error": f"Failed to move file: {str(e)}"}), 500

  # Update file's parent folder and filepath in the database
  file.parent_id = target_folder_id
  file.filepath = new_filepath
  
  db.session.commit()
  
  return jsonify({"success": "File moved successfully"}), 200

def move_folder(folder_id, target_folder_id):
  # Get the folder and target folder from the database
  folder = Folder.query.get(folder_id)
  target_folder = Folder.query.get(target_folder_id)

  if not folder or not target_folder or not target_folder_id or not folder_id:
    return jsonify({"error": "Folder or target folder not found"}), 404

  # Construct the old and new folder paths
  old_folderpath = os.path.join(folder.mount_point, *folder.path_stack)
  new_folderpath = os.path.join(target_folder.mount_point, *target_folder.path_stack, folder.name)

  # Check if a folder with the same name already exists in the target folder
  existing_folder = Folder.query.filter_by(parent_id=target_folder_id, name=folder.name).first()

  if os.path.exists(new_folderpath) or existing_folder:
    return jsonify({"error": "A folder with the same name already exists in the target folder"}), 409

  # Move the folder on the filesystem
  try:
    shutil.move(old_folderpath, new_folderpath)
  except Exception as e:
    return jsonify({"error": f"Failed to move folder: {str(e)}"}), 500

  # Update the folder's parent folder and mount point in the database
  folder.parent_id = target_folder_id
  folder.mount_point = target_folder.mount_point
  new_path_stack = target_folder.path_stack[:]
  new_path_stack.append(folder.name)
  folder.path_stack = new_path_stack

  # Update paths for all files in the moved folder
  for file in File.query.filter_by(parent_id=folder.id).all():
    file.filepath = os.path.join(new_folderpath, file.filename)

  # Recursively update paths for all subfolders within the moved folder
  def update_subfolder_paths(subfolder, parentfolder):
    subfolder.mount_point = parentfolder.mount_point
    new_path_stack = parentfolder.path_stack[:]
    new_path_stack.append(folder.name)
    subfolder.path_stack = new_path_stack
    new_folderpath = os.path.join(subfolder.mount_point, *subfolder.path_stack)
    for subfile in File.query.filter_by(parent_id=subfolder.id).all():
      subfile.filepath = os.path.join(new_folderpath, subfile.filename)
    for child in Folder.query.filter_by(parent_id=subfolder.id).all():
      update_subfolder_paths(child, subfolder)

  for subfolder in Folder.query.filter_by(parent_id=folder.id).all():
    update_subfolder_paths(subfolder, folder)

  db.session.commit()

  return jsonify({"success": "Folder moved successfully"}), 200