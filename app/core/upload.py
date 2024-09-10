import hashlib
import os
import mimetypes
from flask import current_app as app, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app.models.file_model import File, Folder
from ..extensions import db
from config import Config

def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def get_file_hash_and_size(file):
  hasher = hashlib.sha256()
  file_size = 0
    
  while True:
    chunk = file.read(8192)
    if not chunk:
      break
    hasher.update(chunk)
    file_size += len(chunk)
    
  file.seek(0)  # Reset file pointer to the beginning
  return hasher.hexdigest(), file_size

def upload_file(current_user):
  parent_id = request.form.get('parent_id')
  file = request.files['file']

  if not parent_id:
    parent_id = None
    
  if not file:
    return jsonify({'error': 'No file part in the request'}), 400
    
  if file.filename == '':
    return jsonify({'error': 'No selected file'}), 400
  
  filename = file.filename.split('/')[-1]
  
  if allowed_file(filename):
    file_hash, file_size = get_file_hash_and_size(file)

    existing_file = File.query.filter_by(filename=filename, parent_id=parent_id).first()
    if existing_file:
      return jsonify({'error': f'File already exists with the name "{filename}" in the specified folder.'}), 400
    
    # Check if file already exists in the database
    existing_file = File.query.filter_by(file_hash=file_hash).first()
    if current_user.settings.hashing and existing_file:
      return jsonify({'message': f'File already exists with ID {existing_file.id}', 'filename': existing_file.filename}), 200

    secured_filename = secure_filename(filename)

    parent_folder = None
    if parent_id:
      parent_folder = Folder.query.get(parent_id)

    if not parent_folder and parent_id:
      return jsonify({'error': 'Unknown Folder ID'}), 400
    
    if not parent_folder and not parent_id:
      return jsonify({'error': 'Can not create file in this directory'}), 400
    
    # if not parent_folder and not parent_id:
    #   if not os.path.exists(app.config['UPLOAD_FOLDER']):
    #     os.makedirs(app.config['UPLOAD_FOLDER'])

    file_path = os.path.join(parent_folder.mount_point, *parent_folder.path_stack, secured_filename)

    # if parent_folder:
    #   file_path = os.path.join(get_upload_folder(current_user), *parent_folder.path_stack, secured_filename)
  
    new_file = File(filename=filename, filepath=file_path, file_hash=file_hash, file_size=file_size, parent_id=parent_id, mimetype=mimetypes.guess_type(secured_filename)[0])
    db.session.add(new_file)
    db.session.commit()

    file.save(file_path)
    
    return jsonify({'message': f'File successfully uploaded with ID {new_file.id}'}), 200
  
  return jsonify({'error': 'File type not allowed'}), 400