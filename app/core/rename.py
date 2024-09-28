from flask import current_app as app, request, jsonify, send_from_directory
from app.models.file_model import File, Folder
from ..extensions import db

def rename_file(file_id, parent_id):
  data = request.get_json()
  filename = data.get('name')
  file = File.query.get(file_id)

  if not file:
    return jsonify({'error': 'File not found'}), 404

  # Check if another file with the same name exists in the same parent folder
  existing_file = File.query.filter_by(parent_id=parent_id, filename=filename).first()
  
  if existing_file and file.id != existing_file.id:
    return jsonify({'error': 'A file with that name already exists in the parent folder'}), 400

  file.filename = filename
  db.session.commit()

  return jsonify({'message': 'File renamed successfully'}), 200

def rename_folder(folder_id, parent_id):
  data = request.get_json()
  folder_name = data.get('name')
  folder = Folder.query.get(folder_id)

  if not folder:
    return jsonify({'error': 'Folder not found'}), 404

  # Check if another folder with the same name exists in the same parent folder, excluding the current folder
  existing_folder = Folder.query.filter_by(parent_id=parent_id, name=folder_name).first()
  
  if existing_folder and folder.id != existing_folder.id:
    return jsonify({'error': 'A folder with that name already exists in the parent folder'}), 400

  folder.name = folder_name
  db.session.commit()

  return jsonify({'message': 'Folder renamed successfully'}), 200